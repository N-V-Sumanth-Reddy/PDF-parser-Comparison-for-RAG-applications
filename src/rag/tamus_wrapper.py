"""
TAMUS API Wrapper for Claude-compatible RAG System

This module provides a wrapper around the TAMUS API to replace direct Anthropic API calls.
It handles authentication, model selection, and maintains compatibility with the existing RAG code.

Author: RAG System
Date: 2025-12-16
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class TAMUSConfig:
    """Configuration for TAMUS API connection"""
    api_key: str
    api_base: str = "https://chat-api.tamu.ai"
    pdf_extraction_model: str = "protected.claude-sonnet-4"
    timeout: int = 120


class TAMUSAPIClient:
    """Wrapper client for TAMUS API that mimics Anthropic client interface"""
    
    def __init__(self, config: TAMUSConfig):
        self.config = config
        self.base_url = config.api_base
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _call_openai_compatible_endpoint(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int = 8096,
        temperature: float = 0.0,
    ) -> str:
        url = f"{self.base_url}/api/v1/chat/completions"
        
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        
        print(f"[TAMUS] POST {url}")
        print(f"[TAMUS] Model: {model}")
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=body,
                timeout=self.config.timeout,
            )
            
            print(f"[TAMUS] Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[TAMUS] Error: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValueError(f"Unexpected response format")
            
            message = data["choices"][0].get("message", {})
            content = message.get("content")
            
            if not content:
                raise ValueError("No content in response")
            
            return content
            
        except requests.RequestException as e:
            print(f"[TAMUS] Request failed: {e}")
            raise
        except (KeyError, ValueError) as e:
            print(f"[TAMUS] Parse failed: {e}")
            raise
    
    def messages(self):
        """Provide messages interface"""
        return MessagesInterface(self)


class MessagesInterface:
    """Mimics Anthropic's client.messages interface"""
    
    def __init__(self, client: TAMUSAPIClient):
        self.client = client
    
    def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 8096,
        **kwargs
    ) -> "MessageResponse":
        processed_messages = self._process_messages(messages)
        temperature = kwargs.get("temperature", 0.0)
        
        content = self.client._call_openai_compatible_endpoint(
            messages=processed_messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return MessageResponse(content=content)
    
    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        
        for msg in messages:
            if msg.get("role") not in ["user", "assistant", "system"]:
                continue
            
            if isinstance(msg.get("content"), list):
                # Handle multimodal content with documents
                content_parts = []
                for item in msg["content"]:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content_parts.append({
                                "type": "text",
                                "text": item.get("text", "")
                            })
                        elif item.get("type") == "document":
                            # Convert document to image format for TAMUS API
                            source = item.get("source", {})
                            if source.get("type") == "base64" and source.get("media_type") == "application/pdf":
                                content_parts.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{source.get('media_type')};base64,{source.get('data')}"
                                    }
                                })
                        elif item.get("type") == "image_url":
                            # Pass through image_url directly
                            content_parts.append(item)
                
                processed.append({
                    "role": msg["role"],
                    "content": content_parts
                })
            else:
                processed.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })
        
        return processed


class MessageResponse:
    """Response wrapper"""
    
    def __init__(self, content: str):
        self.content = [{"type": "text", "text": content}]
        self._text = content
    
    def __getitem__(self, index):
        return self.content[index]
    
    @property
    def text(self):
        return self._text


def get_tamus_client(
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    pdf_extraction_model: Optional[str] = None,
) -> TAMUSAPIClient:
    """Factory function to create TAMUS API client"""
    
    key = api_key or os.getenv("TAMUS_API_KEY")
    if not key:
        raise ValueError("TAMUS_API_KEY not set")
    
    base = api_base or os.getenv("TAMUS_API_BASE", "https://chat-api.tamu.ai")
    model = pdf_extraction_model or os.getenv("TAMUS_PDF_MODEL", "protected.claude-sonnet-4")
    
    config = TAMUSConfig(
        api_key=key,
        api_base=base,
        pdf_extraction_model=model,
    )
    
    return TAMUSAPIClient(config)


if __name__ == "__main__":
    try:
        client = get_tamus_client()
        print("[Demo] TAMUS client initialized!")
        
        response = client.messages().create(
            model="protected.claude-sonnet-4",
            messages=[{"role": "user", "content": "Say HELLO"}],
            max_tokens=100,
        )
        
        print(f"[Demo] Response: {response.content[0]['text']}")
    except Exception as e:
        print(f"[Demo] Error: {e}")