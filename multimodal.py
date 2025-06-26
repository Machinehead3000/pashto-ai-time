"""Multimodal processing capabilities for AI Chat."""
import os
import base64
import io
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import requests
from gtts import gTTS
import speech_recognition as sr
import pdfplumber
import pandas as pd
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import torch
from transformers import AutoProcessor, AutoModel
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse, urljoin

class MultiModalProcessor:
    """Handles multimodal interactions including image, voice, and file processing."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self._init_recognizer()
        self._init_image_model()
    
    def _init_recognizer(self):
        """Initialize speech recognition."""
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def _init_image_model(self):
        """Initialize image processing model."""
        try:
            self.image_processor = AutoProcessor.from_pretrained("microsoft/resnet-50")
            self.image_model = AutoModel.from_pretrained("microsoft/resnet-50")
        except Exception as e:
            print(f"Warning: Could not initialize image model: {e}")
            self.image_processor = None
            self.image_model = None
    
    def analyze_image(self, image_path: str) -> str:
        """Analyze image using local model or cloud vision API."""
        if not os.path.exists(image_path):
            return "Error: Image file not found"

        try:
            image = Image.open(image_path)
            if self.image_model and self.image_processor:
                # Local image analysis
                inputs = self.image_processor(images=image, return_tensors="pt")
                outputs = self.image_model(**inputs)
                # Process outputs to generate description
                return "Image analysis completed using local model"
            else:
                # Fallback to cloud API if configured
                api_key = self.api_keys.get('vision_api')
                if api_key:
                    return self._analyze_image_cloud(image_path, api_key)
                return "Error: No image analysis model available"
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        model: str = "dall-e-3",
        quality: str = "standard",
        style: str = "vivid"
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3 or similar model via OpenRouter.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (1024x1024, 1024x1792, or 1792x1024 for DALL-E 3)
            model: Model to use (dall-e-3, stable-diffusion-xl, etc.)
            quality: Quality setting (standard or hd for DALL-E 3)
            style: Style setting (vivid or natural for DALL-E 3)
            
        Returns:
            Dictionary with status, image path/URL, and metadata
        """
        api_key = self.api_keys.get('openrouter_api')
        if not api_key:
            return {"error": "OpenRouter API key not configured"}

        try:
            # Prepare the API request
            url = "https://openrouter.ai/api/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the payload based on model
            payload = {
                "model": f"openai/{model}",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "response_format": "b64_json"
            }
            
            # Add model-specific parameters
            if model == "dall-e-3":
                payload["quality"] = quality
                payload["style"] = style
            
            # Make the API request
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Process the response
            if "data" in result and result["data"]:
                # Create output directory if it doesn't exist
                os.makedirs("generated_images", exist_ok=True)
                
                # Generate a unique filename
                timestamp = int(time.time())
                filename = f"generated_images/image_{timestamp}.png"
                
                # Save the image
                image_data = result["data"][0]["b64_json"]
                image_bytes = base64.b64decode(image_data)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                return {
                    "status": "success",
                    "image_path": filename,
                    "metadata": {
                        "model": model,
                        "size": size,
                        "prompt": prompt,
                        "revision_prompt": result.get("revision_prompt", ""),
                        "created_at": result.get("created", int(time.time()))
                    }
                }
            else:
                return {"error": "No image data in response"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Error generating image: {str(e)}"}

    def text_to_speech(self, text: str, output_path: Optional[str] = None, lang: str = 'en') -> str:
        """Convert text to speech using gTTS."""
        try:
            output_path = output_path or 'output.mp3'
            tts = gTTS(text=text, lang=lang)
            tts.save(output_path)
            return output_path
        except Exception as e:
            return f"Error converting text to speech: {str(e)}"

    def speech_to_text(self, audio_path: str, language: str = 'en-US') -> str:
        """Convert speech to text using speech recognition."""
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language=language)
        except Exception as e:
            return f"Error converting speech to text: {str(e)}"

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze various file types (PDF, Excel, CSV) with enhanced processing."""
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        file_ext = Path(file_path).suffix.lower()
        try:
            if file_ext == '.pdf':
                with pdfplumber.open(file_path) as pdf:
                    text = '\n'.join(page.extract_text() for page in pdf.pages)
                    tables = []
                    for page in pdf.pages:
                        tables.extend(page.extract_tables())
                    return {
                        "type": "pdf",
                        "content": text,
                        "tables": tables,
                        "metadata": pdf.metadata
                    }
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                stats = df.describe()
                return {
                    "type": "excel",
                    "content": df.to_dict(),
                    "statistics": stats.to_dict(),
                    "columns": list(df.columns)
                }
            elif file_ext == '.csv':
                df = pd.read_csv(file_path)
                stats = df.describe()
                return {
                    "type": "csv",
                    "content": df.to_dict(),
                    "statistics": stats.to_dict(),
                    "columns": list(df.columns)
                }
            else:
                return {"error": "Unsupported file type"}
        except Exception as e:
            return {"error": f"Error analyzing file: {str(e)}"}

    def web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Perform real-time web search using OpenRouter's web search capability.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10)
            
        Returns:
            Dictionary with search results and metadata
        """
        api_key = self.api_keys.get('openrouter_api')
        if not api_key:
            return {"error": "OpenRouter API key not configured"}
            
        try:
            # Prepare the search query
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://pashto-ai.app",
                "X-Title": "Pashto AI"
            }
            
            # Use a model that supports web search
            payload = {
                "model": "google/gemini-1.5-flash",  # This model supports web search
                "messages": [
                    {
                        "role": "user",
                        "content": f"Perform a web search for: {query}\n\nReturn {num_results} most relevant results with URLs and short descriptions."
                    }
                ],
                "tools": [{"type": "web_search"}],
                "tool_choice": {"type": "web_search"}
            }
            
            # Make the API request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse the response
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]
                return {
                    "status": "success",
                    "query": query,
                    "results": self._parse_web_search_results(content),
                    "raw_response": result
                }
            else:
                return {"error": "No search results in response"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Search API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Error performing web search: {str(e)}"}
    
    def _parse_web_search_results(self, content: str) -> List[Dict[str, str]]:
        """Parse web search results from the model's response."""
        # This is a simple parser that looks for URL patterns and descriptions
        # In a production app, you might want to use more sophisticated parsing
        import re
        
        results = []
        url_pattern = r'https?://[^\s\n\]]+'
        
        # Split into individual results (assuming each result is on a new line)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        current_result = {}
        for line in lines:
            # Look for URLs
            urls = re.findall(url_pattern, line)
            if urls:
                if current_result:  # If we have a previous result, save it
                    results.append(current_result)
                current_result = {"url": urls[0], "snippet": line.replace(urls[0], '').strip()}
            elif current_result and line:  # Add to the current result's snippet
                current_result["snippet"] += "\n" + line
        
        # Add the last result
        if current_result:
            results.append(current_result)
            
        return results
    
    def edit_image(
        self,
        image_path: str,
        prompt: str,
        mask_path: Optional[str] = None,
        size: str = "1024x1024",
        model: str = "dall-e-2"
    ) -> Dict[str, Any]:
        """
        Edit an existing image using AI.
        
        Args:
            image_path: Path to the image to edit
            prompt: Text description of the desired edits
            mask_path: Optional path to a mask image (for inpainting)
            size: Output image size
            model: Model to use (dall-e-2 or other supported models)
            
        Returns:
            Dictionary with status, edited image path, and metadata
        """
        api_key = self.api_keys.get('openrouter_api')
        if not api_key:
            return {"error": "OpenRouter API key not configured"}
            
        if not os.path.exists(image_path):
            return {"error": "Source image not found"}
            
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the API request
            url = "https://openrouter.ai/api/v1/images/edits"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the payload
            payload = {
                "model": f"openai/{model}",
                "image": f"data:image/png;base64,{image_data}",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "response_format": "b64_json"
            }
            
            # Add mask if provided
            if mask_path and os.path.exists(mask_path):
                with open(mask_path, "rb") as mask_file:
                    mask_data = base64.b64encode(mask_file.read()).decode('utf-8')
                    payload["mask"] = f"data:image/png;base64,{mask_data}"
            
            # Make the API request
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Process the response
            if "data" in result and result["data"]:
                # Create output directory if it doesn't exist
                os.makedirs("edited_images", exist_ok=True)
                
                # Generate a unique filename
                timestamp = int(time.time())
                filename = f"edited_images/edited_{timestamp}.png"
                
                # Save the edited image
                image_data = result["data"][0]["b64_json"]
                image_bytes = base64.b64decode(image_data)
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                return {
                    "status": "success",
                    "image_path": filename,
                    "metadata": {
                        "model": model,
                        "size": size,
                        "prompt": prompt,
                        "created_at": result.get("created", int(time.time()))
                    }
                }
            else:
                return {"error": "No image data in response"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Error editing image: {str(e)}"}