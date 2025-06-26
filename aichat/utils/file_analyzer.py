"""
File analysis utilities for processing different file types.
"""
import os
import io
import csv
import json
import PyPDF2
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union, BinaryIO, List
from docx import Document
from PIL import Image, UnidentifiedImageError

class FileAnalyzer:
    """Utility class for analyzing different file types."""
    
    @staticmethod
    def analyze_file(file_path: Union[str, Path], max_size: int = 10*1024*1024) -> Dict[str, Any]:
        """
        Analyze a file and return its content and metadata.
        
        Args:
            file_path: Path to the file to analyze
            max_size: Maximum file size to process in bytes (default: 10MB)
            
        Returns:
            Dict containing file metadata and content/analysis
            """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Get basic file info
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_size,
                'type': 'file',
                'error': f'File too large (>{max_size/1024/1024}MB)',
                'content': None
            }
        
        # Get file extension
        ext = file_path.suffix.lower()
        
        # Analyze based on file type
        try:
            if ext in ['.txt', '.md', '.log', '.py', '.js', '.html', '.css']:
                return FileAnalyzer._analyze_text_file(file_path)
            elif ext == '.pdf':
                return FileAnalyzer._analyze_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return FileAnalyzer._analyze_docx(file_path)
            elif ext in ['.csv']:
                return FileAnalyzer._analyze_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                return FileAnalyzer._analyze_excel(file_path)
            elif ext in ['.json']:
                return FileAnalyzer._analyze_json(file_path)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return FileAnalyzer._analyze_image(file_path)
            else:
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_size,
                    'type': 'file',
                    'error': 'Unsupported file type',
                    'content': None
                }
        except Exception as e:
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_size,
                'type': 'file',
                'error': f'Error processing file: {str(e)}',
                'content': None
            }
    
    @staticmethod
    def _analyze_text_file(file_path: Path) -> Dict[str, Any]:
        """Analyze a text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'type': 'text',
            'content': content,
            'line_count': len(content.splitlines()),
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    @staticmethod
    def _analyze_pdf(file_path: Path) -> Dict[str, Any]:
        """Extract text from a PDF file."""
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        
        content = '\n\n'.join(text)
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'type': 'pdf',
            'content': content,
            'page_count': num_pages,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    @staticmethod
    def _analyze_docx(file_path: Path) -> Dict[str, Any]:
        """Extract text from a Word document."""
        doc = Document(file_path)
        text = [paragraph.text for paragraph in doc.paragraphs]
        content = '\n'.join(text)
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'type': 'document',
            'content': content,
            'paragraph_count': len(text),
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    @staticmethod
    def _analyze_csv(file_path: Path) -> Dict[str, Any]:
        """Analyze a CSV file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few rows to determine structure
            sample = f.read(4096)
            f.seek(0)
            
            # Try to detect dialect
            try:
                dialect = csv.Sniffer().sniff(sample)
                has_header = csv.Sniffer().has_header(sample)
                f.seek(0)
                
                # Read the full file with detected dialect
                reader = csv.reader(f, dialect)
                rows = list(reader)
                
                # Get headers if present
                headers = rows[0] if has_header and len(rows) > 0 else []
                data = rows[1:] if has_header and len(rows) > 1 else rows
                
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': 'csv',
                    'content': {'headers': headers, 'data': data},
                    'row_count': len(data),
                    'column_count': len(headers) if headers else (len(data[0]) if data else 0)
                }
                
            except (csv.Error, UnicodeDecodeError):
                # Fallback to reading as text
                f.seek(0)
                content = f.read()
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': 'text',
                    'content': content,
                    'line_count': len(content.splitlines())
                }
    
    @staticmethod
    def _analyze_excel(file_path: Path) -> Dict[str, Any]:
        """Analyze an Excel file."""
        try:
            # Try reading with openpyxl first (better for .xlsx)
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except ImportError:
                # Fall back to xlrd for .xls files
                df = pd.read_excel(file_path, engine='xlrd')
            
            # Convert to list of dicts for JSON serialization
            data = df.to_dict(orient='records')
            
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'type': 'excel',
                'content': {
                    'headers': df.columns.tolist(),
                    'data': data,
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
                },
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
        except Exception as e:
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'type': 'file',
                'error': f'Error reading Excel file: {str(e)}',
                'content': None
            }
    
    @staticmethod
    def _analyze_json(file_path: Path) -> Dict[str, Any]:
        """Analyze a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': 'json',
                    'content': data
                }
            except json.JSONDecodeError as e:
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': 'text',
                    'error': f'Invalid JSON: {str(e)}',
                    'content': None
                }
    
    @staticmethod
    def _analyze_image(file_path: Path) -> Dict[str, Any]:
        """Analyze an image file."""
        try:
            with Image.open(file_path) as img:
                return {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'type': 'image',
                    'content': None,  # Don't include binary data in the response
                    'format': img.format,
                    'mode': img.mode,
                    'width': img.width,
                    'height': img.height
                }
        except UnidentifiedImageError:
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'type': 'file',
                'error': 'Unsupported or corrupted image',
                'content': None
            }

    @staticmethod
    def get_file_summary(analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of file analysis."""
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        file_type = analysis.get('type', 'file').upper()
        name = analysis.get('name', 'Unknown')
        size_mb = analysis.get('size', 0) / (1024 * 1024)
        
        if file_type == 'TEXT':
            lines = analysis.get('line_count', 0)
            words = analysis.get('word_count', 0)
            return f"{file_type}: {name} ({size_mb:.2f} MB, {lines} lines, {words} words)"
        
        elif file_type == 'PDF':
            pages = analysis.get('page_count', 0)
            words = analysis.get('word_count', 0)
            return f"{file_type}: {name} ({size_mb:.2f} MB, {pages} pages, {words} words)"
        
        elif file_type == 'DOCUMENT':
            paras = analysis.get('paragraph_count', 0)
            words = analysis.get('word_count', 0)
            return f"{file_type}: {name} ({size_mb:.2f} MB, {paras} paragraphs, {words} words)"
        
        elif file_type in ['CSV', 'EXCEL']:
            rows = analysis.get('row_count', 0)
            cols = analysis.get('column_count', 0)
            return f"{file_type}: {name} ({size_mb:.2f} MB, {rows} rows, {cols} columns)"
        
        elif file_type == 'JSON':
            # Try to determine if it's an array or object
            content = analysis.get('content', {})
            if isinstance(content, list):
                return f"{file_type}: {name} ({size_mb:.2f} MB, {len(content)} items)"
            elif isinstance(content, dict):
                return f"{file_type}: {name} ({size_mb:.2f} MB, {len(content)} keys)"
            return f"{file_type}: {name} ({size_mb:.2f} MB)"
        
        elif file_type == 'IMAGE':
            width = analysis.get('width', 0)
            height = analysis.get('height', 0)
            return f"{file_type}: {name} ({size_mb:.2f} MB, {width}x{height} pixels)"
        
        return f"{file_type}: {name} ({size_mb:.2f} MB)"
