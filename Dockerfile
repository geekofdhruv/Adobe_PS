# Use Python 3.9 slim image for efficiency
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create input and output directories for both rounds
RUN mkdir -p /app/Round_1a/input \
    /app/Round_1a/output \
    /app/Round_1b/input \
    /app/Round_1b/output \
    /app/Round_1b/output_round1a
# Install system dependencies for PyMuPDF and other requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Round_1a requirements first
COPY Round_1a/requirements.txt ./Round_1a/requirements.txt
RUN pip install --no-cache-dir -r Round_1a/requirements.txt

# Copy and install Round_1b requirements (includes additional dependencies)
COPY Round_1b/requirements.txt ./Round_1b/requirements.txt
RUN pip install --no-cache-dir -r Round_1b/requirements.txt

# Copy Round_1a source code
COPY Round_1a/process.py ./Round_1a/process.py

# Copy Round_1b source code and embedding model
COPY Round_1b/config.py ./Round_1b/config.py
COPY Round_1b/main.py ./Round_1b/main.py
COPY Round_1b/retrieval.py ./Round_1b/retrieval.py
COPY Round_1b/utils.py ./Round_1b/utils.py
COPY Round_1b/embedding_model/ ./Round_1b/embedding_model/

# Copy the pipeline orchestrator script
COPY <<EOF /app/run_pipeline.py
#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def run_round_1a():
    """Run Round 1a PDF outline extraction"""
    print("🔍 Step 1: Running Round 1a - PDF Outline Extraction...")
    
    # Change to Round_1a directory and run process.py
    os.chdir('/app/Round_1a')
    
    # Modify the output directory in process.py to point to the shared location
    import process
    process.INPUT_DIRECTORY = "../input"
    process.OUTPUT_DIRECTORY = "../output_round1a"
    
    try:
        process.process_all_pdfs_in_directory(process.INPUT_DIRECTORY, process.OUTPUT_DIRECTORY)
        print("✅ Round 1a completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Round 1a failed: {e}")
        return False

def run_round_1b():
    """Run Round 1b Advanced Document Intelligence"""
    print("🧠 Step 2: Running Round 1b - Advanced Document Intelligence...")
    
    # Change to Round_1b directory and run main.py
    os.chdir('/app/Round_1b')
    
    try:
        import main
        main.run_analysis_pipeline()
        print("✅ Round 1b completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Round 1b failed: {e}")
        return False

def main():
    """Main pipeline orchestrator"""
    start_time = time.time()
    print("🚀 Starting Adobe Hackathon Complete Pipeline...")
    
    # Check if input directory has PDF files
    input_files = [f for f in os.listdir('/app/input') if f.lower().endswith('.pdf')]
    if not input_files:
        print("⚠️ No PDF files found in input directory. Please add PDF files to /app/input")
        sys.exit(1)
    
    print(f"📂 Found {len(input_files)} PDF files: {input_files}")
    
    # Run Round 1a
    if not run_round_1a():
        print("❌ Pipeline failed at Round 1a")
        sys.exit(1)
    
    # Check if Round 1a produced output
    outline_files = [f for f in os.listdir('/app/output_round1a') if f.lower().endswith('.json')]
    if not outline_files:
        print("❌ Round 1a did not produce any JSON outline files")
        sys.exit(1)
    
    print(f"📄 Round 1a produced {len(outline_files)} outline files")
    
    # Run Round 1b
    if not run_round_1b():
        print("❌ Pipeline failed at Round 1b")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print("\n" + "="*60)
    print("✅ COMPLETE PIPELINE FINISHED SUCCESSFULLY!")
    print(f"⏰ Total Processing Time: {total_time:.2f} seconds")
    print(f"📂 Input PDFs: {len(input_files)}")
    print(f"📄 Generated Outlines: {len(outline_files)}")
    print(f"💾 Final Output: /app/output/advanced_analysis_output.json")
    print("="*60)

if __name__ == "__main__":
    main()
EOF

# Make the pipeline script executable
RUN chmod +x /app/run_pipeline.py

# Set environment variables
ENV PYTHONPATH=/app:/app/Round_1a:/app/Round_1b
ENV CUDA_VISIBLE_DEVICES=-1

# Set working directory back to app root
WORKDIR /app

# Default command runs the complete pipeline
CMD ["python", "run_pipeline.py"]

# Alternative commands for running individual rounds:
# To run only Round 1a: docker run <image> python Round_1a/process.py
# To run only Round 1b: docker run <image> python Round_1b/main.py