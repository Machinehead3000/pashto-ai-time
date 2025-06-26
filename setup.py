from setuptools import setup, find_packages

# Core dependencies
install_requires = [
    'requests>=2.31.0',
    'PyYAML>=6.0',
    'python-dotenv>=1.0.0',
    'tqdm>=4.66.0',
    'pydantic>=2.0.0',
]

# Development dependencies
extras_require = {
    'dev': [
        'pytest>=7.4.0',
        'pytest-cov>=4.1.0',
        'pytest-mock>=3.11.1',
        'black>=23.7.0',
        'isort>=5.12.0',
        'flake8>=6.1.0',
        'mypy>=1.4.0',
        'types-requests>=2.31.0',
        'types-PyYAML>=6.0.0',
        'pytest-asyncio>=0.21.1',
    ],
    'nlp': [
        'torch>=2.0.0',
        'transformers>=4.30.0',
        'sentencepiece>=0.1.99',
        'accelerate>=0.20.0',
    ],
    'ui': [
        'PyQt5>=5.15.0',
        'PyQtWebEngine>=5.15.0',
    ]
}

# Read the README for the long description
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except (IOError, FileNotFoundError):
    long_description = "Advanced AI assistant with multi-model support"

setup(
    name="aichat",
    version="1.0.0",
    description="AI Chat Application with multi-model support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/pashto-ai",
    packages=find_packages(include=['aichat*']),
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires='>=3.11',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ]
)
