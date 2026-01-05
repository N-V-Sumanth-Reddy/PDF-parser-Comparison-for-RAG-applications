"""
Ollama Vision PDF Extraction using Local LLM
Uses Llama 3.2 Vision model for PDF content extraction via image processing
"""

import os
import sys
import base64
import time
import ollama
from typing import List
from pathlib import Path
from datetime import datetime
from PIL import Image
import io

# Force CPU mode to prevent GPU crashes
os.environ['OLLAMA_NUM_GPU'] = '0'

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.utils import PDFToJPGConverter


class OllamaVisionExtractor:
    """
    PDF extractor using Ollama's Llama 3.2 Vision model.
    Converts PDF pages to images and uses local LLM vision for content extraction.
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "./outputs"):
        """
        Initialize the Ollama Vision extractor.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted files
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.model = "llama3.2-vision"
        self.fallback_model = "llava:7b"  # Smaller fallback model
        self.temp_image_dir = Path("temp_images_ollama")
        
        # Validate PDF exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        # Create output and temp directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if Ollama model is available
        try:
            models = ollama.list()
            available_models = [model.model for model in models.models]
            model_found = any(self.model in model_name for model_name in available_models)
            if not model_found:
                print(f"[OLLAMA] ⚠️  Model {self.model} not found. Available models: {available_models}")
                print(f"[OLLAMA] Please install with: ollama pull {self.model}")
                raise ValueError(f"Model {self.model} not available")
            print(f"[OLLAMA] ✓ Model {self.model} is available")
            print(f"[OLLAMA] ✓ Using CPU-only mode to prevent GPU crashes")
            print(f"[OLLAMA] ⚠️  This will be slower but safer for your hardware")
        except Exception as e:
            print(f"[OLLAMA] ✗ Failed to check Ollama: {e}")
            print(f"[OLLAMA] Make sure Ollama is running: ollama serve")
            raise

    def convert_pdf_to_images(self) -> List[Path]:
        """Convert PDF pages to JPG images using the utility converter"""
        print(f"[OLLAMA] Converting PDF to images: {self.pdf_path.name}")
        
        try:
            # Use the existing PDF converter utility
            converter = PDFToJPGConverter()
            converted_files = converter.convert_pdf(str(self.pdf_path), str(self.temp_image_dir))
            
            # Convert string paths to Path objects
            image_paths = [Path(file_path) for file_path in converted_files]
            
            print(f"[OLLAMA] ✓ Converted {len(image_paths)} pages to images")
            return image_paths
            
        except Exception as e:
            print(f"[OLLAMA] ✗ PDF conversion error: {e}")
            raise

    def preprocess_image(self, image_path: Path, max_size: int = 1024) -> Path:
        """Reduce image size to prevent GPU memory issues"""
        try:
            img = Image.open(image_path)
            original_size = img.size
            
            # Resize if image is too large
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save resized image with new name
                resized_path = image_path.parent / f"resized_{image_path.name}"
                img.save(resized_path, format='JPEG', quality=85)
                print(f"[OLLAMA] ✓ Resized image from {original_size} to {img.size}")
                return resized_path
            
            return image_path
        except Exception as e:
            print(f"[OLLAMA] ⚠️  Could not resize image {image_path}: {e}")
            return image_path

    def encode_image_to_base64(self, image_path: Path) -> str:
        """Convert an image file to a base64 encoded string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"[OLLAMA] ✗ Error encoding image {image_path}: {e}")
            raise

    def extract_content_from_image(self, image_path: Path, page_num: int) -> str:
        """Extract content from a single image using Ollama Vision model"""
        system_prompt = """You are an expert at extracting and structuring content from document images. Please analyze this image from a PDF page and extract ALL text content, maintaining the structure and formatting.

For tables: Format them properly in markdown format, preserving all numerical data and relationships.
For text: Maintain paragraph structure and formatting.
For figures/charts: Describe them and extract any visible text or data.

Extract every piece of text content visible in this image. Do not exclude anything."""

        print(f"[OLLAMA] Extracting content from page {page_num}...")
        
        try:
            # Preprocess image to reduce size and prevent GPU issues
            processed_image_path = self.preprocess_image(image_path)
            
            # Convert image to base64
            base64_image = self.encode_image_to_base64(processed_image_path)
            
            # Use Ollama vision model to extract text content (CPU mode)
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': system_prompt,
                    'images': [base64_image]
                }],
                options={
                    'num_gpu': 0,  # Force CPU processing
                    'temperature': 0.1,
                    'top_p': 0.9
                }
            )
            
            content = response['message']['content']
            print(f"[OLLAMA] ✓ Page {page_num} extraction complete ({len(content)} chars)")
            
            # Clean up resized image if created
            if processed_image_path != image_path and processed_image_path.exists():
                processed_image_path.unlink()
            
            return content
            
        except Exception as e:
            print(f"[OLLAMA] ✗ Page {page_num} error: {e}")
            print(f"[OLLAMA] ⚠️  GPU/Metal error detected. Consider using other extraction methods.")
            return f"[ERROR: Could not extract content from page {page_num}: GPU/Metal failure]"

    def extract_all(self) -> str:
        """
        Extract all content from PDF using Ollama Vision model.
        
        Returns:
            Complete extracted text content
        """
        print(f"[OLLAMA] Starting extraction of: {self.pdf_path.name}")
        start_time = time.time()
        
        # Convert PDF to images
        image_paths = self.convert_pdf_to_images()
        
        # Extract content from each image
        structured_content = ""
        for i, image_path in enumerate(image_paths, 1):
            try:
                page_content = self.extract_content_from_image(image_path, i)
                structured_content += f"\n\n--- PAGE {i} ---\n{page_content}"
            except Exception as e:
                print(f"[OLLAMA] ✗ Page {i} error: {e}")
                structured_content += f"\n\n--- PAGE {i} ---\n[ERROR: Could not extract content from this page]"
                continue
        
        end_time = time.time()
        extraction_time = end_time - start_time
        
        print(f"[OLLAMA] ✓ Extraction complete in {extraction_time:.2f} seconds")
        print(f"[OLLAMA] ✓ Total content length: {len(structured_content)} characters")
        
        # Clean up temporary images
        self.cleanup_temp_files()
        
        return structured_content

    def cleanup_temp_files(self):
        """Clean up temporary image files"""
        try:
            import shutil
            if self.temp_image_dir.exists():
                shutil.rmtree(self.temp_image_dir)
                print(f"[OLLAMA] ✓ Cleaned up temporary files")
        except Exception as e:
            print(f"[OLLAMA] ⚠️  Could not clean up temp files: {e}")

    def save_to_text(self, content: str) -> Path:
        """
        Save extracted content to text file.
        
        Args:
            content: Extracted text content
            
        Returns:
            Path to saved text file
        """
        output_path = self.output_dir / "extracted_content_ollama_vision.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== OLLAMA VISION EXTRACTED TEXT (LOCAL LLM) ===\n")
            f.write(f"Extraction time: {datetime.now().isoformat()}\n")
            f.write(f"Configuration: Ollama with {self.model}\n")
            f.write(f"Method: PDF → Images → Local Vision LLM\n")
            f.write(f"Content length: {len(content)} characters\n\n")
            f.write(content)
        
        print(f"[OLLAMA] ✓ Saved extraction to: {output_path}")
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
        output_path = self.output_dir / f"{self.pdf_path.stem}_ollama_summary.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("OLLAMA VISION PDF EXTRACTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("METADATA\n")
            f.write("-" * 60 + "\n")
            f.write(f"Filename:.............. {self.pdf_path.name}\n")
            f.write(f"File size:............. {self.pdf_path.stat().st_size / (1024 * 1024):.2f} MB\n")
            f.write(f"Extraction method:..... Ollama Vision (Local LLM)\n")
            f.write(f"Model:................. {self.model}\n")
            f.write(f"Extraction time:....... {extraction_time:.2f} seconds\n")
            f.write(f"Content length:........ {len(content)} characters\n")
            f.write(f"Timestamp:............. {datetime.now().isoformat()}\n")
        
        print(f"[OLLAMA] ✓ Saved summary to: {output_path}")
        return output_path


def main():
    """Extract content using Ollama Vision for comparison."""
    
    # Use the actual PDF file
    pdf_path = "input/AbdelMaksoud et al. - 2025 - Tracking metal pollution from illegal gold mining a health risk assessment in Edfu, Egypt_1.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("[OLLAMA] Starting PDF extraction using Ollama Vision...")
    print("=" * 60)
    
    # Initialize extractor
    try:
        extractor = OllamaVisionExtractor(pdf_path=pdf_path, output_dir="./outputs")
    except Exception as e:
        print(f"[OLLAMA] ✗ Failed to initialize: {e}")
        return
    
    # Extract all content
    start_time = time.time()
    try:
        extracted_content = extractor.extract_all()
    except Exception as e:
        print(f"[OLLAMA] ✗ Extraction failed: {e}")
        return
    
    end_time = time.time()
    extraction_time = end_time - start_time
    
    # Save outputs
    text_file = extractor.save_to_text(extracted_content)
    summary_file = extractor.save_summary_report(extracted_content, extraction_time)
    
    # Print summary
    print("\n" + "="*60)
    print("OLLAMA VISION EXTRACTION COMPLETE")
    print("="*60)
    print(f"Extraction time: {extraction_time:.2f} seconds")
    print(f"Content length: {len(extracted_content)} characters")
    print(f"Lines: {len(extracted_content.splitlines())}")
    print(f"\nFiles created:")
    print(f"  - {text_file} (for comparison)")
    print(f"  - {summary_file}")
    print(f"\nNote: This method uses local LLM processing")
    print(f"and requires no API costs or internet connection.")


if __name__ == "__main__":
    main()