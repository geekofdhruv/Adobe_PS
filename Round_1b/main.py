import os
import json
from datetime import datetime
import time
from retrieval import DocumentRetriever
from config import (
    INPUT_DIR,
    OUTPUT_DIR,
    PERSONA,
    JOB_TO_BE_DONE,
    TOP_K_SECTIONS,
    TOP_K_SUBSECTIONS
)
from utils import save_json

def run_analysis_pipeline():
    """
    Main function to execute the persona-driven document intelligence pipeline.
    """
    start_time = time.time()
    print("🚀 Starting Advanced Document Intelligence Pipeline...")

    try:
        retriever = DocumentRetriever()
        print(f"✅ Retriever initialized successfully on device: {retriever.device}")
    except Exception as e:
        print(f"🔥 Fatal Error: Could not initialize DocumentRetriever. {e}")
        return

    try:
        pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"⚠️ Warning: No PDF files found in '{INPUT_DIR}'. Exiting.")
            return
        print(f"📂 Found {len(pdf_files)} documents for analysis: {pdf_files}")
    except FileNotFoundError:
        print(f"🔥 Fatal Error: Input directory '{INPUT_DIR}' not found.")
        return

    analysis_result = retriever.process_collection(
        pdf_files=pdf_files,
        persona=PERSONA,
        job_to_be_done=JOB_TO_BE_DONE,
        top_k_sections=TOP_K_SECTIONS,
        top_k_subsections=TOP_K_SUBSECTIONS
    )

    output_filename = f"advanced_analysis_output.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_json(analysis_result, output_path)

    end_time = time.time()
    total_duration = end_time - start_time

    print("\n" + "="*50)
    print("✅ PIPELINE COMPLETED")
    print(f"⏰ Total Processing Time: {total_duration:.2f} seconds")
    print(f"▶️ Input Documents: {len(pdf_files)}")
    print(f"▶️ Persona: {PERSONA}")
    print(f"▶️ Job: {JOB_TO_BE_DONE}")
    print(f"▶️ Top Sections Extracted: {len(analysis_result.get('extracted_sections', []))}")
    print(f"▶️ Sub-sections Analyzed: {len(analysis_result.get('subsection_analysis', []))}")
    print(f"💾 Output saved to: {output_path}")
    print("="*50)


if __name__ == "__main__":
    run_analysis_pipeline()