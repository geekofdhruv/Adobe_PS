# PDF Outline Extractor

A lightweight Python script that scans one or more PDF files, detects probable headings ( H1–H3 ) and the main document title, and writes a structured outline to JSON.  
It relies on **PyMuPDF** for text extraction and uses font size, boldness, numbering, and position heuristics to score each text block.

## 📂 Directory-level Workflow

| Folder / File | Purpose |
|---------------|---------|
| `input/` | Place **all PDFs** you want processed here. |
| `round1b/output_round1a/` | JSON files are written here (auto-created if absent). |
| `process.py` | The code shown below—run it to launch the batch process. |

## 🚀 Quick Start

```bash
# 1. Install dependency
pip install pymupdf     # (package name: "PyMuPDF")

# 2. Add PDFs to ./input
mkdir -p input
cp *.pdf input/

# 3. Run the script
python process.py   # or python3 process.py
```

After completion, each `input/.pdf` yields `round1b/output_round1a/.json`.

## 🔍 Input Logic (What the script does)

1. **Batch Discovery**  
   ```python
   for filename in os.listdir(INPUT_DIRECTORY):
       if filename.lower().endswith(".pdf"):
           ...
   ```
   Every `.pdf` file in `INPUT_DIRECTORY` is queued for analysis.

2. **Per-PDF Text Extraction**  
   ```python
   blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_SEARCH)["blocks"]
   ```
   Each page’s text is converted into a dictionary of “blocks”, “lines”, and “spans”.

3. **Determine “Body” Font**  
   - All `span` sizes and style flags are tallied (`Counter`).
   - The *most frequent* size is treated as the **body font size** (`body_size`).  
     This becomes the baseline for deciding whether something looks like a heading.

4. **Heading Candidate Tests**  
   For every block:
   - **Font-size ratio** > `1.05` compared to `body_size`.
   - **Optional bonuses**: bold text, ALL-CAPS, numbered prefixes (`3.2.1 Heading`), centered alignment, small left margin.
   - **Regex filters** reject boilerplate (page numbers, copyright lines, etc.).
   - A **score** is accumulated; score thresholds map to hierarchy:  
     - ≥ 35 → H1  
     - ≥ 25 → H2  
     - ≥ 15 → H3

5. **Title Detection**  
   Among all detected headings on pages 1–2, the one with the **highest score and suitable length** becomes the document’s `title`.

6. **Outline Assembly**  
   Each accepted heading is stored with its `level`, raw `text`, and 1-based `page` index.  
   Entries are sorted by page order.

## 📤 Output Format

Every PDF generates a peer-named JSON file:

```json
{
  "title": "An Example Document",
  "outline": [
    { "level": "H1", "text": "1 Introduction",          "page": 1 },
    { "level": "H2", "text": "1.1 Motivation",          "page": 2 },
    { "level": "H3", "text": "1.1.1 Historical Context","page": 3 },
    { "level": "H1", "text": "2 Methodology",           "page": 5 }
  ]
}
```

Field meanings  
* `title`  – first-level title automatically inferred (may be empty if none fits).  
* `outline` – ordered list of detected headings.

## 🛠️ Customization Tips

| Goal | Where to Tweak |
|------|----------------|
| Change input/output folders | Bottom of the script (`INPUT_DIRECTORY`, `OUTPUT_DIRECTORY`). |
| Relax or tighten heading thresholds | `classify_heading()` – edit score bonuses or cut-offs. |
| Add/remove “non-heading” phrases | `is_heading_text()` – expand `non_heading_patterns` regex list. |
| Support more heading levels (H4+) | Extend the score-to-level mapping logic in `classify_heading()`. |

## ⚠️ Troubleshooting

* **No headings found** – Your document uses exotic fonts or all-caps small fonts; lower the size ratio threshold (`1.05`) or add custom rules.  
* **Errors on specific PDFs** – The script catches exceptions and continues; failed filenames and Python tracebacks print to the console for diagnosis.  
* **False-positive headings** – Tighten regex filters or raise level thresholds.
