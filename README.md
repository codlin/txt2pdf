# txt2pdf

Convert txt files to PDF in A4 size.

## Usage

1. Download `SourceHanSans` Chinese fonts (Regular, Bold and Medium variants)
   and place the `.ttf` files under a `fonts/` directory:

   ```
   fonts/
     SourceHanSansSC-Regular.ttf
     SourceHanSansSC-Bold.ttf
     SourceHanSansSC-Medium.ttf
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the converter:

   ```bash
   python main.py
   ```

   This reads `input.txt` and outputs `output.pdf`.
