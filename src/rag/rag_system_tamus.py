"""
PDF Content Extraction and Question Answering System with RAG Architecture
Modified to use TAMUS API instead of direct Anthropic API
"""

import sys
import os
import base64
from typing import List
from dotenv import load_dotenv

from langchain_ollama.llms import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .tamus_wrapper import get_tamus_client

project_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

try:
    client = get_tamus_client()
    print("[RAG] ✓ TAMUS client initialized")
except ValueError as e:
    print(f"[RAG] ✗ Failed: {e}")
    sys.exit(1)

TAMUS_MODEL = os.getenv("TAMUS_PDF_MODEL", "protected.claude-sonnet-4")
print(f"[RAG] Using model: {TAMUS_MODEL}")


def get_completion_from_tamus(messages: List[dict], model_name: str) -> str:
    """Call TAMUS API for PDF extraction"""
    try:
        response = client.messages().create(
            model=model_name,
            messages=messages,
            max_tokens=8096,
            temperature=0.0,
        )
        return response.content[0]["text"]
    except Exception as e:
        print(f"[RAG] Error: {e}")
        raise


def convert_pdf_to_images(pdf_path: str) -> List[str]:
    """Convert PDF pages to base64 encoded images"""
    from pdf2image import convert_from_path
    from PIL import Image
    import io
    
    print(f"[RAG] Converting PDF to images: {pdf_path}")
    
    try:
        # Convert all pages to images
        images = convert_from_path(pdf_path, dpi=150)
        print(f"[RAG] ✓ Converted {len(images)} pages to images")
        
        image_base64_list = []
        for i, image in enumerate(images, 1):
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_data = buffer.getvalue()
            image_base64 = base64.b64encode(image_data).decode()
            image_base64_list.append(image_base64)
            print(f"[RAG] ✓ Page {i}: {len(image_base64)} chars")
        
        return image_base64_list
    except Exception as e:
        print(f"[RAG] ✗ PDF conversion error: {e}")
        raise


def extract_content_from_image(image_base64: str, page_num: int) -> str:
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

    print(f"[RAG] Extracting content from page {page_num}...")
    response = get_completion_from_tamus(messages, TAMUS_MODEL)
    print(f"[RAG] ✓ Page {page_num} extraction complete")
    return response


def create_vector_store(texts: List[str]) -> FAISS:
    """Create vector store"""
    print("[RAG] Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L12-v2"
    )
    
    print(f"[RAG] Creating vector store from {len(texts)} chunks...")
    vector_store = FAISS.from_texts(texts, embeddings)
    print("[RAG] ✓ Vector store created")
    return vector_store


def get_qa_chain(vector_store: FAISS):
    """Create QA chain using modern LangChain approach"""
    print("[RAG] Initializing Ollama...")
    llm = OllamaLLM(model="llama3.1")
    print("[RAG] ✓ Ollama initialized")

    prompt_template = """Use the following pieces of context to answer the question at the end. Check context very carefully and reference and try to make sense of that before responding.

If you don't know the answer, just say you don't know. Don't try to make up an answer.

Answer must be to the point.

Think step-by-step.

Context: {context}

Question: {question}

Answer:"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("[RAG] ✓ QA chain created")
    return qa_chain, retriever





def main():
    """Main execution"""
    print("=" * 70)
    print("PDF RAG SYSTEM WITH TAMUS API")
    print("=" * 70)
    
    print("\n[STEP 1] Reading PDF file...")
    
    possible_paths = [
        "input/AbdelMaksoud et al. - 2025 - Tracking metal pollution from illegal gold mining a health risk assessment in Edfu, Egypt_1.pdf",
        "input/sample-4.pdf",
        "input/sample-1.pdf",
        "input/sample-2.pdf",
        "input/sample-3.pdf",
        "input/sample-5.pdf",
        "input/document.pdf",
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        print("[RAG] ✗ No PDF found in input/")
        print("[RAG] Please add a PDF file to the input/ directory")
        return
    
    print(f"[RAG] Using: {file_path}")
    
    try:
        image_base64_list = convert_pdf_to_images(file_path)
        print(f"[RAG] ✓ PDF converted to {len(image_base64_list)} image(s)")
    except Exception as e:
        print(f"[RAG] ✗ Error converting PDF: {e}")
        return

    print("\n[STEP 2] Extracting content from PDF images using TAMUS API...")
    structured_content = ""
    
    for i, image_base64 in enumerate(image_base64_list, 1):
        try:
            page_content = extract_content_from_image(image_base64, i)
            structured_content += f"\n\n--- PAGE {i} ---\n{page_content}"
        except Exception as e:
            print(f"[RAG] ✗ Page {i} error: {e}")
            continue

    if not structured_content.strip():
        print("[RAG] ✗ No content extracted from PDF")
        return

    output_file = "outputs/tamus_rag_output.txt"
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(structured_content)
        print(f"[RAG] ✓ Extracted content saved to {output_file}")
    except Exception as e:
        print(f"[RAG] Warning: Could not save output file: {e}")

    print("\n[STEP 3] Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=100,
        is_separator_regex=False
    )
    
    text_chunks = text_splitter.split_text(structured_content)
    print(f"[RAG] ✓ Created {len(text_chunks)} text chunks")

    print("\n[STEP 4] Creating vector store...")
    try:
        vector_store = create_vector_store(text_chunks)
    except Exception as e:
        print(f"[RAG] ✗ Vector store error: {e}")
        return

    print("\n[STEP 5] Setting up QA chain...")
    try:
        qa_chain, retriever = get_qa_chain(vector_store)
    except Exception as e:
        print(f"[RAG] ✗ QA chain error: {e}")
        print("[RAG] Make sure Ollama is running: ollama serve")
        return

    print("\n[STEP 6] Answering questions...")
    print("=" * 70)
    
    # Default questions - you can modify these
    questions = [
        "What is the main topic of this document?",
        "What are the key findings about metal pollution from illegal gold mining?",
        "What health risks are associated with the metal pollution in Edfu, Egypt?",
        "What methods were used to assess the metal pollution?",
        "What are the main conclusions and recommendations?",
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        print("-" * 70)
        
        try:
            # Get the answer using the new chain structure
            answer = qa_chain.invoke(question)
            print(f"✓ Answer: {answer}")
            
            # Get source documents separately
            source_docs = retriever.invoke(question)
            if source_docs:
                print("\nSource context:")
                for i, doc in enumerate(source_docs, 1):
                    preview = doc.page_content[:150].replace('\n', ' ')
                    print(f"  [{i}] {preview}...")
        except Exception as e:
            print(f"✗ Error answering question: {e}")
    
    print("\n" + "=" * 70)
    print("RAG System completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()