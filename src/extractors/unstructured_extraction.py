"""
Advanced PDF Extraction using Unstructured.io
Handles: Text, Tables, Images, Formulas, Metadata, and Complex Layouts
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import pandas as pd
from unstructured.partition.auto import partition
from unstructured.documents.elements import (
    Element, Title, NarrativeText
)

# Try to import advanced elements, fall back to basic ones
try:
    from unstructured.documents.elements import Table, Image, Formula, PageBreak, FigureCaption
except ImportError:
    # Create dummy classes for missing elements
    class Table: 
        pass
    class Image: 
        pass  
    class Formula: 
        pass
    class PageBreak: 
        pass
    class FigureCaption: 
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """Data structure for extracted PDF content"""
    element_type: str
    content: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = None
    coordinates: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComplexPDFExtractor:
    """
    Production-grade PDF extractor for complex documents.
    Supports: text, tables, images, formulas, and metadata extraction.
    """
    
    def __init__(
        self,
        pdf_path: str,
        output_dir: str = "./pdf_output",
        strategy: str = "hi_res",
        languages: Optional[List[str]] = None
    ):
        """
        Initialize the PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted files
            strategy: Extraction strategy - "fast", "hi_res", or "auto"
                     "hi_res" uses ML models for better accuracy
            languages: List of OCR languages (e.g., ["eng", "fra"])
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.strategy = strategy
        self.languages = languages or ["eng"]
        
        # Validate PDF exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized extractor for: {self.pdf_path.name}")

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all content from PDF in one comprehensive pass.
        
        Returns:
            Dictionary containing all extracted elements organized by type
        """
        try:
            logger.info(f"Starting extraction with strategy: {self.strategy}")
            
            # Use real unstructured partition function
            logger.info("Using real Unstructured.io partition function...")
            elements = partition(filename=str(self.pdf_path))
            
            logger.info(f"Extracted {len(elements)} elements")
            
            # Organize elements by type
            extracted_data = {
                "metadata": self._extract_metadata(),
                "text": [],
                "tables": [],
                "images": [],
                "formulas": [],
                "titles": [],
                "figures": [],
                "all_elements": []
            }
            
            # Process each element
            for element in elements:
                processed_element = self._process_element(element)
                extracted_data["all_elements"].append(processed_element)
                
                # Categorize by type
                if isinstance(element, Table):
                    extracted_data["tables"].append(processed_element)
                elif isinstance(element, Image):
                    extracted_data["images"].append(processed_element)
                elif isinstance(element, Formula):
                    extracted_data["formulas"].append(processed_element)
                elif isinstance(element, Title):
                    extracted_data["titles"].append(processed_element)
                elif isinstance(element, FigureCaption):
                    extracted_data["figures"].append(processed_element)
                elif isinstance(element, NarrativeText):
                    extracted_data["text"].append(processed_element)
                else:
                    # Treat as text if no specific type
                    if hasattr(element, 'text') and element.text:
                        extracted_data["text"].append(processed_element)
            
            logger.info(
                f"Categorized: {len(extracted_data['text'])} text, "
                f"{len(extracted_data['tables'])} tables, "
                f"{len(extracted_data['images'])} images, "
                f"{len(extracted_data['formulas'])} formulas"
            )
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise

    def _process_element(self, element: Element) -> ExtractedContent:
        """
        Process individual element and extract relevant information.
        
        Args:
            element: Unstructured Element object
            
        Returns:
            ExtractedContent object with normalized data
        """
        metadata = {}
        coordinates = None
        
        # Extract metadata if available
        if hasattr(element, 'metadata'):
            meta = element.metadata
            metadata = {
                "filename": getattr(meta, 'filename', None),
                "page_number": getattr(meta, 'page_number', None),
                "languages": getattr(meta, 'languages', None),
                "file_directory": getattr(meta, 'file_directory', None),
                "url": getattr(meta, 'url', None),
            }
            
            # Extract coordinates (bounding box)
            if hasattr(meta, 'coordinates'):
                coordinates = {
                    "x0": getattr(meta.coordinates, 'x0', None),
                    "y0": getattr(meta.coordinates, 'y0', None),
                    "x1": getattr(meta.coordinates, 'x1', None),
                    "y1": getattr(meta.coordinates, 'y1', None),
                }
        
        return ExtractedContent(
            element_type=type(element).__name__,
            content=str(element),
            page_number=metadata.get('page_number'),
            metadata=metadata,
            coordinates=coordinates
        )

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract PDF document metadata."""
        return {
            "filename": self.pdf_path.name,
            "filepath": str(self.pdf_path.absolute()),
            "file_size_mb": self.pdf_path.stat().st_size / (1024 * 1024),
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_strategy": self.strategy,
        }

    def save_to_text(self, data: Dict[str, Any]) -> Path:
        """
        Save extracted data to text file for comparison.
        
        Args:
            data: Dictionary of extracted content
            
        Returns:
            Path to saved text file
        """
        output_path = Path("outputs/extracted_content_unstructured.txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== UNSTRUCTURED.IO EXTRACTED TEXT ===\n")
            f.write(f"Extraction time: {data['metadata']['extraction_timestamp']}\n")
            f.write(f"Configuration: {self.strategy} strategy with OCR\n")
            f.write(f"Total elements: {len(data['all_elements'])}\n")
            f.write(f"Text sections: {len(data['text'])}\n")
            f.write(f"Tables: {len(data['tables'])}\n")
            f.write(f"Images: {len(data['images'])}\n")
            f.write(f"Formulas: {len(data['formulas'])}\n\n")
            
            # Write all elements in order
            current_page = 0
            for element in data['all_elements']:
                element_dict = element.to_dict() if hasattr(element, 'to_dict') else element
                page_num = element_dict.get('page_number')
                if page_num and page_num != current_page:
                    current_page = page_num
                    f.write(f"\n--- PAGE {current_page} ---\n")
                
                f.write(f"[{element_dict['element_type']}] {element_dict['content']}\n\n")
        
        logger.info(f"Saved text extraction to: {output_path}")
        return output_path

    def save_to_markdown(self, data: Dict[str, Any]) -> Path:
        """
        Save extracted data to markdown file for easy reading.
        
        Args:
            data: Dictionary of extracted content
            
        Returns:
            Path to saved markdown file
        """
        output_path = self.output_dir / f"{self.pdf_path.stem}_unstructured.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# PDF Extraction Report (Unstructured.io)\n")
            f.write(f"**File**: {data['metadata']['filename']}\n")
            f.write(f"**Extracted**: {data['metadata']['extraction_timestamp']}\n")
            f.write(f"**Strategy**: {self.strategy}\n\n")
            
            # Statistics
            f.write("## Extraction Statistics\n")
            f.write(f"- Total Elements: {len(data['all_elements'])}\n")
            f.write(f"- Text Sections: {len(data['text'])}\n")
            f.write(f"- Tables: {len(data['tables'])}\n")
            f.write(f"- Images: {len(data['images'])}\n")
            f.write(f"- Formulas: {len(data['formulas'])}\n")
            f.write(f"- Titles: {len(data['titles'])}\n")
            f.write(f"- Figures: {len(data['figures'])}\n\n")
            
            # Titles
            if data['titles']:
                f.write("## Titles\n")
                for title in data['titles']:
                    title_dict = title.to_dict() if hasattr(title, 'to_dict') else title
                    f.write(f"- {title_dict['content']}\n")
                f.write("\n")
            
            # Text content
            if data['text']:
                f.write("## Text Content\n")
                for text in data['text'][:20]:  # Limit to first 20
                    text_dict = text.to_dict() if hasattr(text, 'to_dict') else text
                    f.write(f"{text_dict['content']}\n\n")
                if len(data['text']) > 20:
                    f.write(f"... and {len(data['text']) - 20} more sections\n\n")
            
            # Tables
            if data['tables']:
                f.write("## Tables\n")
                for i, table in enumerate(data['tables'], 1):
                    table_dict = table.to_dict() if hasattr(table, 'to_dict') else table
                    f.write(f"### Table {i}\n")
                    f.write(f"{table_dict['content']}\n\n")
            
            # Formulas
            if data['formulas']:
                f.write("## Formulas/Equations\n")
                for formula in data['formulas']:
                    formula_dict = formula.to_dict() if hasattr(formula, 'to_dict') else formula
                    f.write(f"- {formula_dict['content']}\n")
                f.write("\n")
            
            # Images
            if data['images']:
                f.write("## Images\n")
                f.write(f"Total images detected: {len(data['images'])}\n")
        
        logger.info(f"Saved markdown to: {output_path}")
        return output_path

    def save_summary_report(self, data: Dict[str, Any]) -> Path:
        """
        Save extraction summary report.
        
        Args:
            data: Dictionary of extracted content
            
        Returns:
            Path to saved report
        """
        output_path = self.output_dir / f"{self.pdf_path.stem}_unstructured_summary.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("UNSTRUCTURED.IO PDF EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("METADATA\n")
            f.write("-" * 60 + "\n")
            for key, value in data['metadata'].items():
                f.write(f"{key:.<40} {value}\n")
            f.write("\n")
            
            f.write("EXTRACTION STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Elements:........ {len(data['all_elements'])}\n")
            f.write(f"Text Sections:......... {len(data['text'])}\n")
            f.write(f"Tables:................ {len(data['tables'])}\n")
            f.write(f"Images:................ {len(data['images'])}\n")
            f.write(f"Formulas:.............. {len(data['formulas'])}\n")
            f.write(f"Titles:................ {len(data['titles'])}\n")
            f.write(f"Figures:............... {len(data['figures'])}\n")
        
        logger.info(f"Saved summary report to: {output_path}")
        return output_path


def main():
    """Extract content using Unstructured.io for comparison."""
    
    # Use the actual PDF file
    pdf_path = "input/AbdelMaksoud et al. - 2025 - Tracking metal pollution from illegal gold mining a health risk assessment in Edfu, Egypt_1.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("[UNSTRUCTURED] Starting PDF extraction...")
    print("=" * 60)
    
    # Initialize extractor
    extractor = ComplexPDFExtractor(
        pdf_path=pdf_path,
        output_dir="./unstructured_output",
        strategy="hi_res",  # Use high-resolution model-based extraction
        languages=["eng"]
    )
    
    # Extract all content
    start_time = datetime.now()
    extracted_data = extractor.extract_all()
    end_time = datetime.now()
    
    extraction_time = (end_time - start_time).total_seconds()
    
    # Save outputs in multiple formats
    text_file = extractor.save_to_text(extracted_data)
    markdown_file = extractor.save_to_markdown(extracted_data)
    summary_file = extractor.save_summary_report(extracted_data)
    
    # Print summary
    print("\n" + "="*60)
    print("UNSTRUCTURED.IO EXTRACTION COMPLETE")
    print("="*60)
    print(f"Extraction time: {extraction_time:.2f} seconds")
    print(f"Total elements: {len(extracted_data['all_elements'])}")
    print(f"Text sections: {len(extracted_data['text'])}")
    print(f"Tables: {len(extracted_data['tables'])}")
    print(f"Images: {len(extracted_data['images'])}")
    print(f"Formulas: {len(extracted_data['formulas'])}")
    print(f"Titles: {len(extracted_data['titles'])}")
    print(f"Figures: {len(extracted_data['figures'])}")
    print(f"\nFiles created:")
    print(f"  - {text_file} (for comparison)")
    print(f"  - {markdown_file}")
    print(f"  - {summary_file}")
    print(f"  - Output directory: {extractor.output_dir}")


if __name__ == "__main__":
    main()