import fitz  # PyMuPDF
import json
import os
import re
from collections import Counter

def get_text_styles(pdf_path):
    styles = {}
    font_counts = Counter()

    doc = fitz.open(pdf_path)
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_SEARCH)["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        font_counts[(s['size'], s['flags'])] += 1
    doc.close()

    if not font_counts:
        return {'body_size': 12.0}

    most_common_style = font_counts.most_common(1)[0][0]
    styles['body_size'] = most_common_style[0]
    return styles

def is_heading_text(text):
    non_heading_patterns = [
        r'^version\s+\d+',
        r'^\d{4}$',
        r'^page\s+\d+',
        r'^copyright',
        r'^all rights reserved',
        r'^international\s+software\s+testing',
        r'^qualifications\s+board',
        r'^\s*\d+\s*$',
        r'^[^\w]*$',
        r'^(the|and|or|but|in|on|at|to|for|of|with|by)$',
    ]

    for pattern in non_heading_patterns:
        if re.match(pattern, text.strip(), re.IGNORECASE):
            return False

    clean_text = text.strip()
    return 3 <= len(clean_text) <= 200

def merge_spans(block):
    if "lines" not in block:
        return [], None, None
    all_spans = [s for line in block['lines'] for s in line['spans']]
    full_text = " ".join([s['text'].strip() for s in all_spans if s['text'].strip()])
    if not all_spans:
        return "", None, None
    return full_text, all_spans[0]['size'], all_spans[0]['flags']

def classify_heading(block, doc_styles, page_width):
    text, size, font_flags = merge_spans(block)
    if not text or not is_heading_text(text):
        return None

    is_bold = (font_flags & 2**4) > 0
    size_ratio = size / doc_styles['body_size']
    
    # Print initial info for every text block
    print(f"\n--- Analyzing Text ---")
    print(f"Text: '{text}'")
    print(f"Font flags: {font_flags} | Is Bold: {is_bold} | Size ratio: {size_ratio:.2f}")
    
    # Loosened threshold
    if size_ratio < 1.05:
        print(f"REJECTED: Size ratio too small ({size_ratio:.2f} < 1.05)")
        return None

    score = 0

     # Font size
    if size_ratio >= 1.3:
        score += 30
        print(f"Font size bonus: +30 (ratio: {size_ratio:.2f})")
    elif size_ratio >= 1.2:
        score += 20
        print(f"Font size bonus: +20 (ratio: {size_ratio:.2f})")
    elif size_ratio >= 1.05:
        score += 10
        print(f"Font size bonus: +10 (ratio: {size_ratio:.2f})")

    if is_bold:
        score += 15
        print(f"Bold bonus: +15")

    if text.isupper() and 5 <= len(text) <= 50:
        score += 10
        print(f"All caps bonus: +10")

    number_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)', text)
    if number_match:
        score += 25
        print(f"Numbering bonus: +25")
        dot_count = number_match.group(1).count('.')
        level = 'H1' if dot_count == 0 else 'H2' if dot_count == 1 else 'H3'
        print(f"FINAL SCORE: {score} | LEVEL: {level}")
        return {'level': level, 'text': text, 'score': score}

    # Centered
    block_width = block['bbox'][2] - block['bbox'][0]
    center_pos = block['bbox'][0] + block_width / 2
    page_center = page_width / 2

    if abs(center_pos - page_center) < (page_width * 0.15):
        score += 15
        print(f"Centered bonus: +15")

    if block['bbox'][0] < 100:
        score += 5
        print(f"Left margin bonus: +5")
    print(f"FINAL SCORE: {score}")
    if score >= 35:
        level = 'H1'
    elif score >= 25:
        level = 'H2'
    elif score >= 15:
        level = 'H3'
    else:
        print(f"REJECTED: Score too low ({score} < 15)")
        return None
    print(f"ASSIGNED LEVEL: {level}")
    return {'level': level, 'text': text, 'score': score}

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    doc_styles = get_text_styles(pdf_path)
    all_candidates = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_SEARCH)["blocks"]
        for block in blocks:
            if block['type'] == 0 and "lines" in block:
                result = classify_heading(block, doc_styles, page.rect.width)
                if result:
                    result['page'] = page_num + 1
                    all_candidates.append(result)
    doc.close()

    title = ""
    title_candidates = [c for c in all_candidates if c['page'] <= 2]
    if title_candidates:
        title_candidate = max(title_candidates, key=lambda x: (x['score'], len(x['text'])))
        if title_candidate['score'] > 20 and len(title_candidate['text']) > 10:
            title = title_candidate['text']

    outline = []
    for candidate in all_candidates:
        if candidate['text'] != title:
            outline.append({
                "level": candidate['level'],
                "text": candidate['text'],
                "page": candidate['page']
            })

    outline.sort(key=lambda x: x['page'])

    return {
        "title": title,
        "outline": outline
    }

def process_all_pdfs_in_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing {pdf_path}...")
            try:
                outline_data = extract_outline(pdf_path)
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(output_dir, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=4, ensure_ascii=False)

                print(f"Successfully created {output_path}")
            except Exception as e:
                print(f"Could not process {pdf_path}. Error: {e}")

if __name__ == '__main__':
    INPUT_DIRECTORY = "./input"
    OUTPUT_DIRECTORY = "./round1b/output_round1a"
    process_all_pdfs_in_directory(INPUT_DIRECTORY, OUTPUT_DIRECTORY)
