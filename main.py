#!/usr/bin/env python3
"""
PDF RAG System - Main Entry Point

This is the main entry point for the PDF RAG system that supports multiple extraction methods.
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(description="PDF RAG System with Multiple Extraction Methods")
    parser.add_argument(
        "command", 
        choices=["rag", "extract", "compare"],
        help="Command to run: 'rag' for full RAG system, 'extract' for extraction only, 'compare' for method comparison"
    )
    parser.add_argument(
        "--method",
        choices=["tamus", "tamus-rag", "ollama", "docling", "pymupdf", "unstructured", "all"],
        default="tamus-rag",
        help="Extraction method to use (default: tamus-rag)"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to PDF file (optional, will auto-detect from input/ directory)"
    )
    
    args = parser.parse_args()
    
    if args.command == "rag":
        print("🚀 Starting PDF RAG System...")
        from src.rag.rag_system_tamus import main as rag_main
        rag_main()
    
    elif args.command == "extract":
        print(f"📄 Starting PDF extraction using {args.method}...")
        
        if args.method == "tamus":
            from src.extractors.tamus_extraction import main as tamus_main
            tamus_main()
        elif args.method == "tamus-rag":
            from src.rag.rag_system_tamus import main as rag_main
            rag_main()
        elif args.method == "ollama":
            print("🔧 Using Ollama Vision with CPU-only mode for safety...")
            from src.extractors.ollama_vision_extraction import main as ollama_main
            ollama_main()
        elif args.method == "docling":
            from src.extractors.docling_extraction import main as docling_main
            docling_main()
        elif args.method == "pymupdf":
            from src.extractors.pymupdf_extraction import main as pymupdf_main
            pymupdf_main()
        elif args.method == "unstructured":
            from src.extractors.unstructured_extraction import main as unstructured_main
            unstructured_main()
        elif args.method == "all":
            print("Running all extraction methods for comparison...")
            print("⚠️  Note: Skipping Ollama Vision due to potential GPU issues.")
            print("⚠️  Run separately with --method ollama if needed.")
            
            from src.extractors.tamus_extraction import main as tamus_main
            from src.extractors.docling_extraction import main as docling_main
            from src.extractors.pymupdf_extraction import main as pymupdf_main
            from src.extractors.unstructured_extraction import main as unstructured_main
            
            print("\n1/4 Running TAMUS extraction...")
            tamus_main()
            
            print("\n2/4 Running Docling extraction...")
            docling_main()
            
            print("\n3/4 Running PyMuPDF extraction...")
            pymupdf_main()
            
            print("\n4/4 Running Unstructured.io extraction...")
            unstructured_main()
            
            print("\n✅ Safe extractions complete! Check outputs/ directory for results.")
            print("💡 For Ollama Vision: python main.py extract --method ollama")
    
    elif args.command == "compare":
        print("📊 Displaying extraction method comparison...")
        comparison_file = Path("docs/extraction_comparison_summary.md")
        if comparison_file.exists():
            with open(comparison_file, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print("❌ Comparison file not found. Run extractions first.")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()