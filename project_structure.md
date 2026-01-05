# Project Structure Documentation

## Directory Organization

### `/src/` - Source Code
- **`extractors/`** - PDF extraction implementations
  - `tamus_extraction.py` - AI-powered extraction via TAMUS API
  - `ollama_vision_extraction.py` - Local AI vision extraction via Ollama
  - `docling_extraction.py` - Advanced local processing with OCR
  - `pymupdf_extraction.py` - Fast comprehensive extraction
  - `unstructured_extraction.py` - Industry standard element classification
  
- **`rag/`** - RAG system components
  - `rag_system_tamus.py` - Main RAG system with TAMUS API
  - `tamus_wrapper.py` - TAMUS API wrapper for Claude models

### `/input/` - Input Files
- PDF documents to be processed
- Currently contains: research paper on metal pollution

### `/outputs/` - Extracted Content
- `extracted_content_*.txt` - Text outputs from different methods
- `tamus_rag_output.txt` - RAG system output
- Comparison files and results

### `/docs/` - Documentation
- `extraction_comparison_summary.md` - Detailed method comparison
- `README.md` - Documentation overview

### `/utils/` - Utility Functions
- Helper functions and shared utilities

## Entry Points

### `main.py` - Primary Entry Point
- Command-line interface for all operations
- Supports: `rag`, `extract`, `compare` commands
- Method selection: `tamus`, `tamus-rag`, `ollama`, `docling`, `pymupdf`, `unstructured`, `all`

### Individual Scripts
- Each extractor can be run independently
- RAG system can be run standalone

## Configuration Files

- `.env` - Environment variables (API keys, endpoints)
- `requirements.txt` - Python dependencies
- `.env.example` - Template for environment setup

## Removed Files (Cleanup)
- `debug_tamus.py` - Debug script
- `check_tamus_capabilities.py` - Capability check
- `investigate_tamus_docs.py` - Investigation script
- `hybrid_rag_system.py` - Old hybrid system
- `local_pdf_rag.py` - Old local system
- `simple_rag_tamus.py` - Simple version
- `ALL_CODE_COPY_PASTE.md` - Large copy-paste file
- Temporary output directories (`__pycache__`, `scratch`, etc.)

## Import Structure

```python
# Main RAG system
from src.rag.rag_system_tamus import main as rag_main

# Individual extractors
from src.extractors.tamus_extraction import main as tamus_main
from src.extractors.ollama_vision_extraction import main as ollama_main
from src.extractors.docling_extraction import main as docling_main
from src.extractors.pymupdf_extraction import main as pymupdf_main
from src.extractors.unstructured_extraction import main as unstructured_main

# TAMUS wrapper
from src.rag.tamus_wrapper import get_tamus_client
```

## Output Organization

All outputs are now centralized in the `outputs/` directory:
- Extracted text files for comparison
- RAG system results
- Processing logs and summaries

This structure provides:
1. **Clear separation** of concerns
2. **Easy navigation** and maintenance
3. **Centralized outputs** for comparison
4. **Clean project root** without clutter
5. **Modular architecture** for easy extension