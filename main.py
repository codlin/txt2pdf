import re
import chardet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

# 注册静态 TTF 字体（Regular / Bold / Medium）
pdfmetrics.registerFont(TTFont("SourceHanSans-Regular", "fonts/SourceHanSansSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("SourceHanSans-Bold", "fonts/SourceHanSansSC-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SourceHanSans-Medium", "fonts/SourceHanSansSC-Medium.ttf"))

# 定义样式
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name='ChineseNormal',
    fontName='SourceHanSans-Regular',
    fontSize=14,              # 四号字体
    leading=21,               # 行距约为1.5倍字号
    firstLineIndent=24        # 首行缩进（约0.85 cm）
))

styles.add(ParagraphStyle(
    name='ChineseTitle',
    fontName='SourceHanSans-Bold',
    fontSize=26,              # 稍大标题
    leading=34,
    alignment=1,              # 居中
    spaceAfter=20
))

styles.add(ParagraphStyle(
    name='ChineseSubtitle',
    fontName='SourceHanSans-Regular',
    fontSize=16,
    leading=24,
    alignment=1,
    spaceAfter=20
))

styles.add(ParagraphStyle(
    name='ChineseH1',
    fontName='SourceHanSans-Bold',
    fontSize=20,
    leading=28,
    spaceBefore=18,
    spaceAfter=12
))

styles.add(ParagraphStyle(
    name='ChineseH2',
    fontName='SourceHanSans-Medium',
    fontSize=16,
    leading=24,
    spaceBefore=12,
    spaceAfter=8
))

styles.add(ParagraphStyle(
    name='ChineseTOC',
    fontName='SourceHanSans-Regular',
    fontSize=14,
    leftIndent=0,
    leading=21
))

def detect_encoding(path):
    with open(path, 'rb') as f:
        raw = f.read()
    encoding = chardet.detect(raw)['encoding']
    print(f"📘 檢測到編碼: {encoding}")
    return raw.decode(encoding or 'utf-8', errors='ignore')

def is_volume_title(line):
    return re.match(r'^第[一二三四五六七八九十百千0-9]+卷', line.strip()) or re.match(r'^(楔子|序章|番外|终章|后记|感言|凡人外传)', line.strip())

def is_chapter_title(line):
    return re.match(r'^第[一二两三四五六七八九十百千0-9]+章', line.strip())

class BookmarkCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._bookmarks = []

    def add_bookmark(self, key, title, level):
        self.bookmarkPage(key)
        self.addOutlineEntry(title, key, level=level, closed=False)

    def showPage(self):
        Canvas.showPage(self)

    def save(self):
        Canvas.save(self)

def on_page(canvas: Canvas, doc):
    canvas.saveState()
    canvas.setFont("SourceHanSans-Regular", 10)
    canvas.drawCentredString(A4[0] / 2.0, 1.5 * cm, str(canvas.getPageNumber()))
    canvas.restoreState()

def generate_pdf(input_file, output_file):
    text = detect_encoding(input_file)
    lines = text.splitlines()

    story = []
    title, author, intro_lines = "凡人修仙传", "忘语", []
    content_start = 0
    bookmarks = []
    toc_entries = []

    for i, line in enumerate(lines):
        if line.strip().startswith("内容简介："):
            intro_lines = [l.strip() for l in lines[i+1:i+6] if l.strip()]
            content_start = i + 6
            break

    if title:
        story.append(Spacer(1, 6 * cm))
        story.append(Paragraph(title, styles['ChineseTitle']))
    if author:
        story.append(Paragraph(author, styles['ChineseSubtitle']))
    story.append(PageBreak())

    if intro_lines:
        story.append(Paragraph("内容简介", styles['ChineseH1']))
        for para in intro_lines:
            story.append(Paragraph(para, styles['ChineseNormal']))
        story.append(PageBreak())
    
    # print(f"📘 内容开始: {lines[content_start]}")

    story.append(Paragraph("目录", styles['ChineseH1']))
    toc_placeholder_index = len(story)
    story.append(PageBreak())

    for line in lines[content_start:]:
        line = line.strip()
        # print(f"📘 内容: {line}")
        
        if not line:
            continue
        elif is_volume_title(line):
            key = f"vol_{len(bookmarks)}"
            bookmarks.append((key, line, 0))
            toc_entries.append((line, key, 0))
            story.append(Paragraph(f'<a name="{key}"/>{line}', styles['ChineseH1']))
            story.append(PageBreak())
        elif is_chapter_title(line):
            key = f"chap_{len(bookmarks)}"
            bookmarks.append((key, line, 1))
            toc_entries.append((line, key, 1))
            story.append(Paragraph(f'<a name="{key}"/>{line}', styles['ChineseH2']))
        else:
            story.append(Paragraph(line, styles['ChineseNormal']))

    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            BaseDocTemplate.__init__(self, filename, **kwargs)
            frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='F1')
            template = PageTemplate(id='TP', frames=[frame], onPage=on_page)
            self.addPageTemplates([template])

    def my_canvas_maker(*args, **kwargs):
        can = BookmarkCanvas(*args, **kwargs)
        current_level = -1
        for key, title, level in bookmarks:
            while level - current_level > 1:
                filler_key = f"filler_{current_level+1}"
                can.bookmarkPage(filler_key)
                can.addOutlineEntry("...", filler_key, level=current_level + 1, closed=False)
                current_level += 1
            can.add_bookmark(key, title, level)
            current_level = level
        return can

    toc_paragraphs = []
    for text, key, level in toc_entries:
        indent = level * 20
        line = f'<a href="#{key}" color="blue">{text}</a>'
        p = Paragraph(line, ParagraphStyle('TOCLine', parent=styles['ChineseTOC'], leftIndent=indent))
        toc_paragraphs.append(p)

    story[toc_placeholder_index:toc_placeholder_index] = toc_paragraphs

    doc = MyDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm
    )

    doc.build(story, canvasmaker=my_canvas_maker)
    print(f"✅ PDF 生成完成：{output_file}")

if __name__ == "__main__":
    generate_pdf("input.txt", "output.pdf")
