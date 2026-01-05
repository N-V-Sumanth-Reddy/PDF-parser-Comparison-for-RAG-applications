"""
TAMUS API PDF Extraction using Image-based Processing
Converts PDF pages to images and uses Claude 3.5 Sonnet via TAMUS API for content extraction
"""

import os
import sys
import base64
import time
from typing import List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from rag.tamus_wrapper import get_tamus_client

load_dotenv()

class TAMUSExtractor:
    """
    PDF extractor using TAMUS API with image-based processing.
    Converts PDF pages to images and uses AI vision for content extraction.
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "./outputs"):
        """
        Initialize the TAMUS extractor.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted files
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.model = os.getenv("TAMUS_PDF_MODEL", "protected.claude-sonnet-4")
        
        # Validate PDF exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize TAMUS client
        try:
            self.client = get_tamus_client()
            print(f"[TAMUS] ✓ Client initialized with model: {self.model}")
        except ValueError as e:
            print(f"[TAMUS] ✗ Failed to initialize: {e}")
            raise

    def convert_pdf_to_images(self) -> List[str]:
        """Convert PDF pages to base64 encoded images"""
        from pdf2image import convert_from_path
        import io
        
        print(f"[TAMUS] Converting PDF to images: {self.pdf_path.name}")
        
        try:
            # Convert all pages to images
            images = convert_from_path(str(self.pdf_path), dpi=150)
            print(f"[TAMUS] ✓ Converted {len(images)} pages to images")
            
            image_base64_list = []
            for i, image in enumerate(images, 1):
                # Convert to base64
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                image_data = buffer.getvalue()
                image_base64 = base64.b64encode(image_data).decode()
                image_base64_list.append(image_base64)
                print(f"[TAMUS] ✓ Page {i}: {len(image_base64)} chars")
            
            return image_base64_list
        except Exception as e:
            print(f"[TAMUS] ✗ PDF conversion error: {e}")
            raise

    def extract_content_from_image(self, image_base64: str, page_num: int) -> str:
        """Extract content from a single PDF page image using TAMUS API"""
        system_prompt = """You are an expert at extracting and structuring content from document images. Please analyze this image from a PDF page and extract ALL text content, maintaining the structure and formatting.

For tables: Format them properly in markdown format, preserving all numerical data and relationships.
For text: Maintain paragraph structure and formatting.
For figures/charts: Describe them and extract any visible text or data.

Extract every piece of text content visible in this image. Do not exclude anything."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ],
            }
        ]

        print(f"[TAMUS] Extracting content from page {page_num}...")
        try:
            response = self.client.messages().create(
                model=self.model,
                messages=messages,
                max_tokens=8096,
                temperature=0.0,
            )
            content = response.content[0]["text"]
            print(f"[TAMUS] ✓ Page {page_num} extraction complete ({len(content)} chars)")
            return content
        except Exception as e:
            print(f"[TAMUS] ✗ Page {page_num} error: {e}")
            raise

    def extract_all(self) -> str:
        """
        Extract all content from PDF using TAMUS API.
        
        Returns:
            Complete extracted text content
        """
        print(f"[TAMUS] Starting extraction of: {self.pdf_path.name}")
        start_time = time.time()
        
        # Convert PDF to images
        image_base64_list = self.convert_pdf_to_images()
        
        # Extract content from each page
        structured_content = ""
        for i, image_base64 in enumerate(image_base64_list, 1):
            try:
                page_content = self.extract_content_from_image(image_base64, i)
                structured_content += f"\n\n--- PAGE {i} ---\n{page_content}"
            except Exception as e:
                print(f"[TAMUS] ✗ Page {i} error: {e}")
                structured_content += f"\n\n--- PAGE {i} ---\n[ERROR: Could not extract content from this page]"
                continue
        
        end_time = time.time()
        extraction_time = end_time - start_time
        
        print(f"[TAMUS] ✓ Extraction complete in {extraction_time:.2f} seconds")
        print(f"[TAMUS] ✓ Total content length: {len(structured_content)} characters")
        
        return structured_content

    def save_to_text(self, content: str) -> Path:
        """
        Save extracted content to text file.
        
        Args:
            content: Extracted text content
            
        Returns:
            Path to saved text file
        """
        output_path = self.output_dir / "extracted_content_tamus_images.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== TAMUS API EXTRACTED TEXT (IMAGE-BASED) ===\n")
            f.write(f"Extraction time: {datetime.now().isoformat()}\n")
            f.write(f"Configuration: TAMUS API with {self.model}\n")
            f.write(f"Method: PDF → Images → AI Vision Extraction\n")
            f.write(f"Content length: {len(content)} characters\n\n")
            f.write(content)
        
        print(f"[TAMUS] ✓ Saved extraction to: {output_path}")
        return output_path

    def save_summary_report(self, content: str, extraction_time: float) -> Path:
        """
        Save extraction summary report.
        
        Args:
            content: Extracted content
            extraction_time: Time taken for extraction
            
        Returns:
            Path to saved report
        """
        output_path = self.output_dir / f"{self.pdf_path.stem}_tamus_summary.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("TAMUS API PDF EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("METADATA\n")
            f.write("-" * 60 + "\n")
            f.write(f"Filename:.............. {self.pdf_path.name}\n")
            f.write(f"File size:............. {self.pdf_path.stat().st_size / (1024 * 1024):.2f} MB\n")
            f.write(f"Extraction method:..... TAMUS API + Images\n")
            f.write(f"Model:................. {self.model}\n")
            f.write(f"Extraction time:....... {extraction_time:.2f} seconds\n")
            f.write(f"Content length:........ {len(content)} characters\n")
            f.write(f"Timestamp:............. {datetime.now().isoformat()}\n")
        
        print(f"[TAMUS] ✓ Saved summary to: {output_path}")
        return output_path


def main():
    """Extract content using TAMUS API for comparison."""
    
    # Use the actual PDF file
    pdf_path = "input/AbdelMaksoud et al. - 2025 - Tracking metal pollution from illegal gold mining a health risk assessment in Edfu, Egypt_1.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("[TAMUS] Starting PDF extraction using TAMUS API...")
    print("=" * 60)
    
    # Initialize extractor
    try:
        extractor = TAMUSExtractor(pdf_path=pdf_path, output_dir="./outputs")
    except Exception as e:
        print(f"[TAMUS] ✗ Failed to initialize: {e}")
        return
    
    # Extract all content
    start_time = time.time()
    try:
        extracted_content = extractor.extract_all()
    except Exception as e:
        print(f"[TAMUS] ✗ Extraction failed: {e}")
        return
    
    end_time = time.time()
    extraction_time = end_time - start_time
    
    # Save outputs
    text_file = extractor.save_to_text(extracted_content)
    summary_file = extractor.save_summary_report(extracted_content, extraction_time)
    
    # Print summary
    print("\n" + "="*60)
    print("TAMUS API EXTRACTION COMPLETE")
    print("="*60)
    print(f"Extraction time: {extraction_time:.2f} seconds")
    print(f"Content length: {len(extracted_content)} characters")
    print(f"Lines: {len(extracted_content.splitlines())}")
    print(f"\nFiles created:")
    print(f"  - {text_file} (for comparison)")
    print(f"  - {summary_file}")
    print(f"\nNote: This method provides the highest quality extraction")
    print(f"but is slower and requires API usage costs.")


if __name__ == "__main__":
    main()