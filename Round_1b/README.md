# Advanced Document Intelligence Pipeline

This repository contains an advanced Python pipeline that processes PDF documents, intelligently extracts and organizes content using pre-computed PDF outlines, and retrieves relevant sections based on a persona-driven query using state-of-the-art embedding models and algorithms like Maximal Marginal Relevance (MMR).

---

## Overview

The pipeline performs the following main steps:

1. **PDF Outline-Based Smart Chunking**:  
   Uses structured outlines (headings and titles) extracted from PDFs to segment documents into meaningful sections and subsections automatically. Each chunk consists of a heading plus all its associated content until the next heading of the same or higher hierarchy.

2. **HyDE (Hypothetical Document Embeddings)**:  
   Generates a hypothetical, elaborated representation of the input query to improve semantic embedding quality, enabling better retrieval accuracy.

3. **Embedding & Similarity Search**:  
   Uses a locally stored SentenceTransformer embedding model to convert chunks and queries into vector embeddings, allowing semantic similarity search.

4. **Maximal Marginal Relevance (MMR)**:  
   Applies MMR to select a diverse yet relevant subset of document sections, reducing redundancy in retrieval.

5. **Intelligent Summarization**:  
   For top-ranked sections, extracts the most relevant sentences with respect to the query to provide concise insights.

---

## 📁 Repository Structure

| File / Folder       | Description                                            |
|---------------------|--------------------------------------------------------|
| `retrieval.py`      | Core logic for chunk extraction, embedding, retrieval, MMR, and summarization. |
| `main.py`           | Orchestrates the pipeline execution and output saving.|
| `config.py`         | Configuration for model name, directories, persona, and retrieval parameters.|
| `utils.py`          | Utility functions, e.g., saving JSON output.           |
| `embedding_model/`  | Local folder containing the pre-trained SentenceTransformer model. |
| `input/`            | Place input PDF files here to be processed.            |
| `output/`           | Generated output JSON files (analysis results) saved here. |
| `output_round1a/`   | Contains pre-computed PDF outlines as JSON files, used for chunking. |
| `requirements.txt`  | Python package dependencies.                            |

---

## 🚀 Quick Start Guide

### 1. Install dependencies
pip install -r requirements.txt



### 2. Prepare input files

- Place your PDF documents inside the `input/` directory.
- Ensure the corresponding outline JSON files exist in `output_round1a/` for each PDF (generated by your outline extraction step).

### 3. Configure the pipeline

- Open `config.py`.
- Set the `PERSONA` variable to describe the user or role (e.g., `"Travel Planner"`).
- Set the `JOB_TO_BE_DONE` variable to specify the task or goal you want the system to perform (e.g., `"Plan a trip of 4 days for a group of 10 college friends."`).

Example snippet in `config.py`:
```
PERSONA = "Travel Planner"
JOB_TO_BE_DONE = "Plan a trip of 4 days for a group of 10 college friends."
```
### 3. Run the pipeline

python main.py


### 4. Check outputs

- Results will be saved as a JSON file (`advanced_analysis_output.json`) inside the `output/` directory.
- The JSON includes extracted sections, their rankings, and summarized subsections.

---

## 🧩 How It Works: Detailed Logic

### 1. Smart Chunking via PDF Outline

- For each PDF, the pipeline reads the pre-computed outline JSON describing the document’s hierarchical headings.
- Sections are created by taking each heading and extracting its associated content from the PDF:
  - Extraction starts right after the heading's bounding box on the heading’s page.
  - Extraction ends just before the next heading of the same or higher level (determined by both page number and vertical position on page).
- This "smart chunking" ensures sections correspond closely to meaningful semantic units such as chapters or subsections.

### 2. HyDE: Hypothetical Document Expansion

- The input query is reformulated into a more detailed descriptive text by the HyDE generator function (a simple template-based expansion).
- This hypothetical document improves embedding quality by providing additional context during retrieval.

### 3. Embedding & Similarity Search

- Both hypothetical query and chunks are converted into embeddings using the local SentenceTransformer model (`embedding_model`).
- Semantic similarity between query and chunks is computed to identify candidate relevant sections.

### 4. Maximal Marginal Relevance (MMR)

- MMR promotes both **relevance** and **diversity** among selected sections.
- It iteratively chooses chunks that have a high similarity to the query and low similarity to chunks already selected, governed by the `MMR_DIVERSITY` hyperparameter (default 0.5).

### 5. Intelligent Summarization

- For the top retrieved sections, the pipeline extracts the most relevant sentences w.r.t. the original query embedding.
- Sentences are embedded, scored by cosine similarity, and the top sentences (usually four) are concatenated to form a concise summary.

---

## ⚙️ Configuration (`config.py`)

- `MODEL_NAME`: Name of the embedding model (loaded from a local directory `embedding_model`).
- `BATCH_SIZE`: Controls embedding batch size for performance (recommended 32 for CPU).
- Directory paths:
  - `INPUT_DIR`: Where your PDFs reside.
  - `OUTLINE_DIR`: Where outline JSON files are located.
  - `OUTPUT_DIR`: Where output JSON will be saved.
- Persona & Job-to-be-Done: Used to formulate the master query dynamically.
- Retrieval parameters (`TOP_K_SECTIONS`, `TOP_K_SUBSECTIONS`, `MMR_DIVERSITY`) fine-tune the number of retrieved sections and MMR behavior.

---

## 💡 Usage Tips

- Ensure outlines match PDFs exactly (same filename base).
- Increase `TOP_K_SECTIONS` and `TOP_K_SUBSECTIONS` to retrieve more content.
- Adjust `MMR_DIVERSITY` between 0 (pure relevance) and 1 (pure diversity) to fit your needs.
- To update the embedding model, replace contents of `embedding_model/` with a newer SentenceTransformer model directory.

---

## 🔧 Troubleshooting

- **Model not found error**: Verify that the folder `embedding_model/` exists and contains the SentenceTransformer model files.
- **Outline file missing**: Make sure outline JSON files were generated for all PDFs in `output_round1a/`.
- **Low-quality results**: Try expanding the persona/job description, or tune retrieval parameters.
- **Performance issues**: Use a GPU or reduce batch size for embedding if running on limited hardware.
