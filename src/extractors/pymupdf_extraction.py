"""
Advanced PDF Extraction using PyMuPDF (fitz)
Alternative to Unstructured.io for comprehensive PDF content extraction
Handles: Text, Tables, Images, Metadata, and Complex Layouts
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import base64

import fitz  # PyMuPDF
import pandas as pd

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
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PyMuPDFExtractor:
    """
    Advanced PDF extractor using PyMuPDF.
    Supports: text, tables, images, and metadata extraction.
    """
    
    def __init__(
        self,
        pdf_path: str,
        output_dir: str = "./pymupdf_output",
        extract_images: bool = True,
        extract_tables: bool = True
    ):
        """
        Initialize the PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted files
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        
        # Validate PDF exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized PyMuPDF extractor for: {self.pdf_path.name}")

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all content from PDF.
        
        Returns:
            Dictionary containing all extracted elements organized by type
        """
        try:
            logger.info("Starting PyMuPDF extraction...")
            
            # Open PDF document
            doc = fitz.open(str(self.pdf_path))
            
            # Initialize data structure
            extracted_data = {
                "metadata": self._extract_document_metadata(doc),
                "text": [],
                "tables": [],
                "images": [],
                "blocks": [],
                "all_elements": []
            }
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                
                # Extract text blocks with formatting
                text_blocks = self._extract_text_blocks(page, page_num + 1)
                extracted_data["text"].extend(text_blocks)
                extracted_data["all_elements"].extend(text_blocks)
                
                # Extract tables if enabled
                if self.extract_tables:
                    tables = self._extract_tables(page, page_num + 1)
                    extracted_data["tables"].extend(tables)
                    extracted_data["all_elements"].extend(tables)
                
                # Extract images if enabled
                if self.extract_images:
                    images = self._extract_images(page, page_num + 1)
                    extracted_data["images"].extend(images)
                    extracted_data["all_elements"].extend(images)
            
            doc.close()
            
            logger.info(
                f"Extraction complete: {len(extracted_data['text'])} text blocks, "
                f"{len(extracted_data['tables'])} tables, "
                f"{len(extracted_data['images'])} images"
            )
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise

    def _extract_document_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract PDF document metadata."""
        metadata = doc.metadata
        return {
            "filename": self.pdf_path.name,
            "filepath": str(self.pdf_path.absolute()),
            "file_size_mb": self.pdf_path.stat().st_size / (1024 * 1024),
            "page_count": len(doc),
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "PyMuPDF",
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
        }

    def _extract_text_blocks(self, page: fitz.Page, page_num: int) -> List[ExtractedContent]:
        """Extract text blocks with formatting information."""
        text_blocks = []
        
        # Get text blocks with formatting
        blocks = page.get_text("dict")
        
        for block in blocks["blocks"]:
            if "lines" in block:  # Text block
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                    block_text += "\n"
                
                if block_text.strip():
                    text_blocks.append(ExtractedContent(
                        element_type="TextBlock",
                        content=block_text.strip(),
                        page_number=page_num,
                        bbox=block.get("bbox"),
                        metadata={
                            "block_type": "text",
                            "font_info": self._extract_font_info(block)
                        }
                    ))
        
        return text_blocks

    def _extract_font_info(self, block: Dict) -> Dict[str, Any]:
        """Extract font information from text block."""
        fonts = set()
        sizes = set()
        
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    fonts.add(span.get("font", ""))
                    sizes.add(span.get("size", 0))
        
        return {
            "fonts": list(fonts),
            "sizes": list(sizes)
        }

    def _extract_tables(self, page: fitz.Page, page_num: int) -> List[ExtractedContent]:
        """Extract tables from page."""
        tables = []
        
        try:
            # Find tables using PyMuPDF's table detection
            table_list = page.find_tables()
            
            for i, table in enumerate(table_list):
                # Extract table data
                table_data = table.extract()
                
                # Convert to text representation
                table_text = self._format_table_as_text(table_data)
                
                tables.append(ExtractedContent(
                    element_type="Table",
                    content=table_text,
                    page_number=page_num,
                    bbox=table.bbox,
                    metadata={
                        "table_index": i,
                        "rows": len(table_data),
                        "cols": len(table_data[0]) if table_data else 0
                    }
                ))
        
        except Exception as e:
            logger.warning(f"Table extraction failed on page {page_num}: {e}")
        
        return tables

    def _format_table_as_text(self, table_data: List[List[str]]) -> str:
        """Format table data as readable text."""
        if not table_data:
            return ""
        
        # Create markdown-style table
        lines = []
        
        # Header row
        if table_data:
            header = " | ".join(str(cell) if cell else "" for cell in table_data[0])
            lines.append(f"| {header} |")
            
            # Separator
            separator = " | ".join("---" for _ in table_data[0])
            lines.append(f"| {separator} |")
            
            # Data rows
            for row in table_data[1:]:
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                lines.append(f"| {row_text} |")
        
        return "\n".join(lines)

    def _extract_images(self, page: fitz.Page, page_num: int) -> List[ExtractedContent]:
        """Extract images from page."""
        images = []
        
        try:
            image_list = page.get_images()
            
            for i, img in enumerate(image_list):
                # Get image data
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    # Convert to PNG bytes
                    img_data = pix.tobytes("png")
                    
                    # Save image
                    img_filename = f"page_{page_num}_image_{i}.png"
                    img_path = self.output_dir / img_filename
                    
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    
                    images.append(ExtractedContent(
                        element_type="Image",
                        content=f"Image saved as: {img_filename}",
                        page_number=page_num,
                        metadata={
                            "image_index": i,
                            "width": pix.width,
                            "height": pix.height,
                            "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                            "file_path": str(img_path)
                        }
                    ))
                
                pix = None  # Free memory
        
        except Exception as e:
            logger.warning(f"Image extraction failed on page {page_num}: {e}")
        
        return images

    def save_to_text(self, data: Dict[str, Any]) -> Path:
        """
        Save extracted data to text file for comparison.
        
        Args:
            data: Dictionary of extracted content
            
        Returns:
            Path to saved text file
        """
        output_path = Path("outputs/extracted_content_pymupdf.txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== PYMUPDF EXTRACTED TEXT ===\n")
            f.write(f"Extraction time: {data['metadata']['extraction_timestamp']}\n")
            f.write(f"Configuration: PyMuPDF with table and image extraction\n")
            f.write(f"Pages processed: {data['metadata']['page_count']}\n")
            f.write(f"Total elements: {len(data['all_elements'])}\n")
            f.write(f"Text blocks: {len(data['text'])}\n")
            f.write(f"Tables: {len(data['tables'])}\n")
            f.write(f"Images: {len(data['images'])}\n\n")
            
            # Write all elements in page order
            current_page = 0
            for element in data['all_elements']:
                element_dict = element.to_dict() if hasattr(element, 'to_dict') else element
                if element_dict['page_number'] != current_page:
                    current_page = element_dict['page_number']
                    f.write(f"\n--- PAGE {current_page} ---\n")
                
                f.write(f"[{element_dict['element_type']}] {element_dict['content']}\n\n")
        
        logger.info(f"Saved text extraction to: {output_path}")
        return output_path

    def save_summary_report(self, data: Dict[str, Any]) -> Path:
        """
        Save extraction summary report.
        
        Args:
            data: Dictionary of extracted content
            
        Returns:
            Path to saved report
        """
        output_path = self.output_dir / f"{self.pdf_path.stem}_pymupdf_summary.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("PYMUPDF PDF EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("METADATA\n")
            f.write("-" * 60 + "\n")
            for key, value in data['metadata'].items():
                f.write(f"{key:.<40} {value}\n")
            f.write("\n")
            
            f.write("EXTRACTION STATISTICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Elements:........ {len(data['all_elements'])}\n")
            f.write(f"Text Blocks:........... {len(data['text'])}\n")
            f.write(f"Tables:................ {len(data['tables'])}\n")
            f.write(f"Images:................ {len(data['images'])}\n")
        
        logger.info(f"Saved summary report to: {output_path}")
        return output_path


def main():
    """Extract content using PyMuPDF for comparison."""
    
    # Use the actual PDF file
    pdf_path = "input/AbdelMaksoud et al. - 2025 - Tracking metal pollution from illegal gold mining a health risk assessment in Edfu, Egypt_1.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("[PYMUPDF] Starting PDF extraction...")
    print("=" * 60)
    
    # Initialize extractor
    extractor = PyMuPDFExtractor(
        pdf_path=pdf_path,
        output_dir="./pymupdf_output",
        extract_images=True,
        extract_tables=True
    )
    
    # Extract all content
    start_time = datetime.now()
    extracted_data = extractor.extract_all()
    end_time = datetime.now()
    
    extraction_time = (end_time - start_time).total_seconds()
    
    # Save outputs
    text_file = extractor.save_to_text(extracted_data)
    summary_file = extractor.save_summary_report(extracted_data)
    
    # Print summary
    print("\n" + "="*60)
    print("PYMUPDF EXTRACTION COMPLETE")
    print("="*60)
    print(f"Extraction time: {extraction_time:.2f} seconds")
    print(f"Pages processed: {extracted_data['metadata']['page_count']}")
    print(f"Total elements: {len(extracted_data['all_elements'])}")
    print(f"Text blocks: {len(extracted_data['text'])}")
    print(f"Tables: {len(extracted_data['tables'])}")
    print(f"Images: {len(extracted_data['images'])}")
    print(f"\nFiles created:")
    print(f"  - {text_file} (for comparison)")
    print(f"  - {summary_file}")
    print(f"  - Output directory: {extractor.output_dir}")


if __name__ == "__main__":
    main()