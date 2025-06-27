"""
File analysis tool for examining file contents and metadata.
"""
import os
import hashlib
import mimetypes
import magic
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

# Try to use python-magic if available, otherwise fall back to mimetypes
try:
    import magic as python_magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

class FileAnalyzer:
    """
    A utility class for analyzing files and extracting metadata and content.
    """
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize the file analyzer with a file path.
        
        Args:
            file_path: Path to the file to analyze
        """
        self.file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self._file_info = {}
        self._content = None
        self._mime_type = None
        
        # Initialize magic if available
        self._magic = None
        if HAS_MAGIC:
            try:
                self._magic = python_magic.Magic(mime=True, mime_encoding=True)
            except Exception:
                pass
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the file.
        
        Returns:
            Dictionary containing file metadata and analysis results
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        self._file_info = {
            'path': str(self.file_path.absolute()),
            'name': self.file_path.name,
            'size': self.file_path.stat().st_size,
            'created': datetime.fromtimestamp(self.file_path.stat().st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(self.file_path.stat().st_mtime).isoformat(),
            'is_file': self.file_path.is_file(),
            'is_dir': self.file_path.is_dir(),
            'is_symlink': self.file_path.is_symlink(),
            'file_extension': self.file_path.suffix.lower(),
            'mime_type': self._get_mime_type(),
            'hash_md5': self._calculate_hash('md5'),
            'hash_sha1': self._calculate_hash('sha1'),
            'hash_sha256': self._calculate_hash('sha256'),
        }
        
        # Add content analysis for text files
        if self._is_text_file():
            self._file_info.update(self._analyze_text_content())
        
        return self._file_info
    
    def get_content(self, max_size: int = 10 * 1024 * 1024) -> Optional[str]:
        """
        Get the file content as text if it's a text file.
        
        Args:
            max_size: Maximum file size to read in bytes (default: 10MB)
            
        Returns:
            File content as string or None if not a text file or too large
        """
        if self._content is not None:
            return self._content
            
        if not self._is_text_file():
            return None
            
        if self.file_path.stat().st_size > max_size:
            return None
            
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self._content = f.read()
            return self._content
        except (UnicodeDecodeError, OSError):
            return None
    
    def _get_mime_type(self) -> str:
        """Get the MIME type of the file."""
        if self._mime_type is not None:
            return self._mime_type
            
        # Try python-magic first
        if self._magic is not None:
            try:
                self._mime_type = self._magic.from_file(str(self.file_path))
                return self._mime_type
            except Exception:
                pass
        
        # Fall back to mimetypes
        mime_type, _ = mimetypes.guess_type(str(self.file_path))
        self._mime_type = mime_type or 'application/octet-stream'
        return self._mime_type
    
    def _is_text_file(self) -> bool:
        """Check if the file is a text file."""
        mime_type = self._get_mime_type()
        return mime_type.startswith('text/') or mime_type in [
            'application/json',
            'application/xml',
            'application/x-yaml',
            'application/x-python',
            'application/javascript',
            'application/x-sh',
            'application/x-csh',
            'application/x-perl',
            'application/x-ruby',
            'application/x-php',
        ]
    
    def _calculate_hash(self, algorithm: str = 'md5') -> str:
        """
        Calculate a hash of the file content.
        
        Args:
            algorithm: Hash algorithm to use (md5, sha1, sha256, etc.)
            
        Returns:
            Hex digest of the file content
        """
        hash_func = getattr(hashlib, algorithm, None)
        if hash_func is None:
            return f"Unsupported hash algorithm: {algorithm}"
            
        try:
            with open(self.file_path, 'rb') as f:
                file_hash = hash_func()
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    file_hash.update(byte_block)
                return file_hash.hexdigest()
        except (IOError, OSError):
            return "Error calculating hash"
    
    def _analyze_text_content(self) -> Dict[str, Any]:
        """
        Analyze text content of the file.
        
        Returns:
            Dictionary with text analysis results
        """
        content = self.get_content()
        if content is None:
            return {}
            
        # Basic text statistics
        lines = content.splitlines()
        words = []
        for line in lines:
            words.extend(line.split())
            
        return {
            'line_count': len(lines),
            'word_count': len(words),
            'char_count': len(content),
            'is_binary': False,
            'encoding': 'utf-8',  # This is simplified
            'language': self._detect_language(content),
            'has_bom': content.startswith('\ufeff'),
            'line_endings': self._detect_line_endings(content)
        }
    
    def _detect_language(self, content: str) -> str:
        """
        Detect the programming/markup language of the file based on extension and content.
        
        Args:
            content: File content as string
            
        Returns:
            Detected language or 'unknown'
        """
        # Simple detection based on file extension
        ext = self.file_path.suffix.lower()
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript (JSX)',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (TSX)',
            '.java': 'Java',
            '.c': 'C',
            '.h': 'C Header',
            '.cpp': 'C++',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.pl': 'Perl',
            '.sh': 'Shell Script',
            '.ps1': 'PowerShell',
            '.bat': 'Batch',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.cfg': 'Config',
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.tex': 'LaTeX',
            '.sql': 'SQL',
            '.csv': 'CSV',
            '.tsv': 'TSV',
        }
        
        return lang_map.get(ext, 'Unknown')
    
    def _detect_line_endings(self, content: str) -> str:
        """
        Detect the line ending style used in the file.
        
        Args:
            content: File content as string
            
        Returns:
            Line ending style ('CRLF', 'LF', 'CR', or 'Mixed')
        """
        crlf = content.count('\r\n')
        lf = content.count('\n') - crlf
        cr = content.count('\r') - crlf
        
        if crlf > 0 and lf == 0 and cr == 0:
            return 'CRLF (Windows)'
        elif lf > 0 and crlf == 0 and cr == 0:
            return 'LF (Unix)'
        elif cr > 0 and crlf == 0 and lf == 0:
            return 'CR (Old Mac)'
        else:
            return 'Mixed'


def analyze_file(file_path: Union[str, Path], max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
    """
    Analyze a file and return its metadata and content analysis.
    
    Args:
        file_path: Path to the file to analyze
        max_size: Maximum file size to analyze in bytes (default: 10MB)
        
    Returns:
        Dictionary with file analysis results
    """
    file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
    
    if not file_path.exists():
        return {'error': 'File not found', 'path': str(file_path)}
    
    if file_path.is_dir():
        return {'error': 'Path is a directory', 'path': str(file_path)}
    
    if file_path.stat().st_size > max_size:
        return {
            'error': f'File too large (>{max_size/1024/1024}MB)',
            'path': str(file_path),
            'size': file_path.stat().st_size
        }
    
    try:
        analyzer = FileAnalyzer(file_path)
        return analyzer.analyze()
    except Exception as e:
        return {
            'error': str(e),
            'path': str(file_path),
            'exception': type(e).__name__
        }
