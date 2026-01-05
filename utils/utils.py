"""Utility functions for PDF processing and base64 encoding"""

import base64
import os
from typing import List
import PyPDF2
from io import BytesIO
from pathlib import Path


def read_pdf_in_pairs(file_path: str, chunk_size: int = 25 * 1024 * 1024) -> List[str]:
    """
    Read PDF file and convert to base64 encoded strings in chunks
    
    Args:
        file_path (str): Path to the PDF file
        chunk_size (int): Size in bytes per chunk (default: 25MB for TAMUS API)
    
    Returns:
        List[str]: List of base64 encoded PDF chunks
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    # Read the entire PDF file
    with open(file_path, 'rb') as file:
        pdf_data = file.read()
    
    # Split into chunks if file is large
    chunks = []
    for i in range(0, len(pdf_data), chunk_size):
        chunk = pdf_data[i:i + chunk_size]
        base64_encoded = base64.b64encode(chunk).decode('utf-8')
        chunks.append(base64_encoded)
    
    return chunks


def split_pdf_by_pages(file_path: str, pages_per_chunk: int = 2) -> List[str]:
    """
    Split PDF into chunks by pages and return base64 encoded strings
    
    Args:
        file_path (str): Path to the PDF file
        pages_per_chunk (int): Number of pages per chunk
    
    Returns:
        List[str]: List of base64 encoded PDF chunks
    """
    base64_chunks = []
    
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        
        for start_page in range(0, total_pages, pages_per_chunk):
            end_page = min(start_page + pages_per_chunk, total_pages)
            
            # Create a new PDF with the chunk of pages
            pdf_writer = PyPDF2.PdfWriter()
            for page_num in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Write to bytes buffer
            buffer = BytesIO()
            pdf_writer.write(buffer)
            buffer.seek(0)
            
            # Encode to base64
            chunk_data = buffer.getvalue()
            base64_encoded = base64.b64encode(chunk_data).decode('utf-8')
            base64_chunks.append(base64_encoded)
    
    return base64_chunks


def validate_pdf(file_path: str) -> bool:
    """
    Validate if the file is a valid PDF
    
    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        with open(file_path, 'rb') as file:
            PyPDF2.PdfReader(file)
        return True
    except Exception:
        return False


class PDFToJPGConverter:
    """
    Utility class to convert PDF pages to JPG images
    """
    
    def __init__(self, dpi: int = 150, format: str = 'JPEG'):
        """
        Initialize the PDF to JPG converter
        
        Args:
            dpi (int): Resolution for image conversion (default: 150)
            format (str): Output image format (default: 'JPEG')
        """
        self.dpi = dpi
        self.format = format
    
    def convert_pdf(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Convert PDF pages to JPG images
        
        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Directory to save converted images
            
        Returns:
            List[str]: List of paths to converted image files
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError("pdf2image is required. Install with: pip install pdf2image")
        
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        # Validate PDF exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(str(pdf_path), dpi=self.dpi)
        
        # Save images and collect file paths
        converted_files = []
        for i, image in enumerate(images, 1):
            # Create filename
            filename = f"page_{i:03d}.jpg"
            file_path = output_dir / filename
            
            # Save image
            image.save(str(file_path), self.format)
            converted_files.append(str(file_path))
        
        return converted_files
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            int: Number of pages in the PDF
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            raise ValueError(f"Could not read PDF: {e}")