# Round 1a - PDF Outline Extraction

This module extracts structured outlines from PDF documents using PyMuPDF, analyzing text styles, font sizes, and formatting to identify headings and create hierarchical document structures.

## Features

- **Smart Heading Detection**: Uses font size, boldness, numbering, and positioning to identify headings
- **Hierarchical Structure**: Classifies headings into H1, H2, H3 levels based on scoring algorithm
- **Style Analysis**: Analyzes document fonts to determine body text baseline
- **JSON Output**: Generates structured JSON files with document title and outline

## Requirements

- Python 3.9+
- PyMuPDF (for PDF processing)

## Installation

### Using Docker (Recommended)

```bash
# Build the Docker image
docker build -t round1a .

# Run with volume mounts for input/output
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output round1a