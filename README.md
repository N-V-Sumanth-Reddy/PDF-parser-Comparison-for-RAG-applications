# PDF RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for PDF documents with multiple extraction methods and AI-powered question answering.

## 🚀 Features

- **Multiple PDF Extraction Methods**: TAMUS API, Ollama Vision, Docling, PyMuPDF, Unstructured.io
- **AI-Powered RAG**: Uses TAMUS API (Claude 3.5 Sonnet) for intelligent document understanding
- **Vector Search**: FAISS-based semantic search with HuggingFace embeddings
- **Local LLM Integration**: Ollama support for question answering
- **Comprehensive Comparison**: Detailed analysis of extraction method performance

## 📁 Project Structure

```
├── main.py                     # Main entry point
├── src/                        # Source code
│   ├── extractors/            # PDF extraction methods
│   │   ├── tamus_extraction.py
│   │   ├── ollama_vision_extraction.py
│   │   ├── docling_extraction.py
│   │   ├── pymupdf_extraction.py
│   │   └── unstructured_extraction.py
│   └── rag/                   # RAG system components
│       ├── rag_system_tamus.py
│       └── tamus_wrapper.py
├── input/                     # PDF files to process
├── outputs/                   # Extracted content and results
├── docs/                      # Documentation and comparisons
├── utils/                     # Utility functions
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variables template
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdf-rag-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Install system dependencies**
   - For Docling: `brew install poppler` (macOS) or equivalent
   - For Unstructured.io: `brew install tesseract` (macOS) or equivalent
   - For Ollama: Install from https://ollama.ai/

## 🎯 Quick Start

### Run Full RAG System
```bash
python main.py rag
```

### Extract with Specific Method
```bash
python main.py extract --method tamus        # TAMUS API extraction only
python main.py extract --method tamus-rag    # Full RAG system
python main.py extract --method ollama       # Local Ollama Vision LLM (⚠️ GPU issues possible)
python main.py extract --method pymupdf
python main.py extract --method docling
python main.py extract --method unstructured
```

### Compare All Methods
```bash
python main.py extract --method all
python main.py compare
```

## 📊 Extraction Methods Comparison

| Method | Speed | Quality | Cost | Best For |
|--------|-------|---------|------|----------|
| **TAMUS Images** | ⭐⭐ | ⭐⭐⭐⭐⭐ | 💰💰💰 | Maximum quality, complex layouts |
| **Ollama Vision** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Local AI, privacy, offline processing |
| **PyMuPDF** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Fast, comprehensive extraction |
| **Docling** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Advanced OCR, multiple formats |
| **Unstructured.io** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Industry standard, element classification |

## 🔧 Configuration

### Environment Variables
```bash
TAMUS_API_KEY=your_tamus_api_key
TAMUS_API_BASE=https://chat-api.tamu.ai
TAMUS_PDF_MODEL=protected.claude-sonnet-4
```

### Ollama Setup
```bash
# Install and start Ollama
ollama serve

# Pull required models
ollama pull llama3.1                    # For RAG Q&A
ollama pull llama3.2-vision             # For vision extraction
```

**⚠️ Ollama Vision Warning**: The vision model may cause GPU/Metal errors on some systems. If you experience hardware issues, use other extraction methods instead.

## 📖 Usage Examples

### Process a Specific PDF
```python
from src.rag.rag_system_tamus import main as rag_main
rag_main()
```

### Use Different Extractors
```python
from src.extractors.pymupdf_extraction import main as pymupdf_main
pymupdf_main()
```

## 🧪 Testing

The project includes comprehensive extraction testing with real scientific papers. Results are saved in `outputs/` directory for comparison.

## 📈 Performance

- **PyMuPDF**: 4 seconds, 15 tables, 12 images detected
- **Docling**: 28.5 seconds, advanced OCR capabilities
- **TAMUS Images**: ~10 minutes, highest quality extraction
- **Ollama Vision**: ~5-8 minutes, local AI processing, no API costs
- **Unstructured.io**: 24.7 seconds, 590 elements classified

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- TAMUS API for AI-powered extraction
- Docling for advanced PDF processing
- PyMuPDF for fast PDF parsing
- Unstructured.io for element classification
- Ollama for local LLM inference