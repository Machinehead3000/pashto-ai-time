# Pashto AI

A next-generation desktop AI application with persistent memory, multimodal capabilities, advanced tools, and custom profiles. Built with PyQt5 for a professional desktop experience across Windows, macOS, and Linux.

![Pashto AI Screenshot](docs/screenshot.png)

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pashto-ai.git
   cd pashto-ai
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements_light.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

### Web Deployment

The application is also available as a web app:
- **Live Demo**: [https://pashto-ai.windsurf.build](https://pashto-ai.windsurf.build)

## 🏆 Features at a Glance

### 🌟 Core Capabilities
- **Persistent Chat Memory**: Remembers conversation context, user preferences, and history
- **Multimodal Understanding**: Works with text, images, voice, and documents
- **Advanced Tools**: Built-in Python interpreter, web browsing, and file analysis
- **Custom AI Profiles**: Create and switch between different AI personalities and behaviors
- **Multi-language Support**: Built-in localization system for internationalization

### 🛠 Advanced Features
- **Code Execution**: Run and debug Python code directly in the chat
- **File Analysis**: Process and analyze various document formats (PDF, DOCX, XLSX, etc.)
- **Image Generation & Editing**: Create and modify images using AI
- **Web Browsing**: Integrated web search for real-time information
- **Model Switching**: Seamlessly switch between different AI models

### 🎨 User Experience
- **Cyberpunk Theme**: Modern, eye-friendly dark theme with customizable colors
- **Responsive Design**: Works across different screen sizes and platforms
- **Rich Text Support**: Markdown, code highlighting, and syntax highlighting
- **Intuitive Interface**: Drag-and-drop file uploads, keyboard shortcuts, and more

## ✨ Key Features

### Core Capabilities
- **Persistent Chat Memory**: Remembers your name, style, goals, and preferences across conversations
- **Multimodal Understanding**: Works with text, images, voice, and documents
- **Advanced Tools**: Built-in Python interpreter, web browsing, and file analysis
- **Custom AI Profiles**: Create and switch between different AI personalities and behaviors

### 📄 Document Processing
- **Document Preview**: View and navigate through various document formats
- **AI-Powered Summarization**: Generate concise, detailed, or key point summaries
- **Document Q&A**: Ask questions about the document content
- **Multiple Formats**: Supports PDF, DOCX, XLSX, CSV, JSON, and TXT
- **Metadata Analysis**: View detailed file information and statistics
- **Background Processing**: Smooth operation without UI freezing

#### Document Features
- **Smart Summarization**
  - Multiple summary types (concise, detailed, key points)
  - Handles large documents with intelligent truncation
  - Progress tracking during generation
  
- **Interactive Q&A**
  - Ask questions in natural language
  - Maintains conversation context
  - Handles follow-up questions
  - Works with document content for accurate answers

- **Rich Preview**
  - Clean, readable display of document content
  - Tabular data visualization for spreadsheets
  - Metadata and statistics
  - Responsive layout for different document types

### AI Models
- **Multiple Model Support**: 
  - DeepSeek-R1 (recommended for most tasks)
  - Mistral-7B (alternative model)
- **Model Switching**: Change models without losing context
- **Optimized Performance**: Efficient resource usage

### User Interface
- **Dark Theme**: Easy on the eyes during extended use
- **Responsive Design**: Works across different screen sizes
- **Rich Text Support**: Markdown, code highlighting, and more
- **Status Indicators**: Clear feedback on operations

## 📚 Documentation

### Document Features Guide
For detailed information on using document features, see our [Document Features Guide](docs/document_features_guide.md).

### Testing Document Features
To test document functionality, refer to our [Testing Guide](docs/document_features_testing.md).

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for development)
- At least 4GB RAM (8GB recommended)
- 1GB free disk space

### Supported Platforms
- Windows 10/11 (64-bit)
- macOS 10.15+
- Linux (Ubuntu 20.04+, Fedora 32+, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pashto-ai.git
   cd pashto-ai
   ```

2. **Set up a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Run the application**
   ```bash
   python -m aichat
   ```

## 🧪 Running Tests

Run the complete test suite:
```bash
python run_tests.py --all
```

Run specific test categories:
```bash
# Unit tests only
python run_tests.py --unit

# Performance tests
python run_tests.py --performance

# Edge case tests
python -m unittest discover -s tests/edge_cases -v

# Cross-platform tests
python -m unittest discover -s tests/cross_platform -v
```

## 🔧 Development

### Project Structure
```
pashto-ai/
├── aichat/                  # Main package
│   ├── models/             # AI model implementations
│   ├── ui/                 # User interface components
│   ├── learning/           # Learning and memory components
│   └── localization/       # Internationalization
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── performance/        # Performance tests
│   ├── edge_cases/         # Edge case tests
│   └── cross_platform/     # Cross-platform tests
├── docs/                   # Documentation
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

### Code Style
We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with a line length of 100 characters. Use `black` for code formatting and `flake8` for linting.

```bash
# Format code
black .

# Lint code
flake8
```

## 📚 Documentation

### API Reference
Detailed API documentation is available in the `docs/` directory. Build it with:

```bash
cd docs
make html
```

### Contributing
Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- PyQt5 for the GUI framework
- Transformers and PyTorch for AI capabilities
- All open-source libraries and tools used in this project
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📁 File Upload & Analysis

### Supported File Types
- **Documents**: PDF, DOCX, TXT, RTF, ODT
- **Spreadsheets**: XLSX, XLS, CSV, TSV
- **Code**: PY, IPYNB, JSON, MD
- **Images**: JPG, JPEG, PNG
- **Presentations**: PPTX, PPT

### How to Use
1. **Add Files**: Drag and drop files into the upload area or click "Browse"
2. **View Files**: See all uploaded files in the list with their status
3. **Analyze**: Click "Analyze Files" to process selected files
4. **View Results**: Right-click any file and select "View Details" to see the analysis

### Advanced Features
- **Context Menu**: Right-click files for quick actions
- **Progress Tracking**: Real-time updates during file processing
- **Error Handling**: Clear error messages for unsupported files
- **Batch Operations**: Select multiple files for analysis or removal

## 🛠 Development

### Project Structure
```
pashto-ai/
├── aichat/                  # Main application package
│   ├── models/              # AI model implementations
│   ├── ui/                  # User interface components
│   │   └── widgets/         # Custom UI widgets
│   ├── utils/               # Utility functions
│   ├── memory.py            # Persistent memory system
│   └── profiles.py          # AI profile management
├── tests/                   # Test suite
├── docs/                    # Documentation
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── main.py                  # Application entry point
```

### Running Tests

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run the test suite:
   ```bash
   pytest -v --cov=aichat --cov-report=term-missing
   ```

3. Generate HTML coverage report:
   ```bash
   pytest --cov=aichat --cov-report=html
   ```

### Code Style

We use `black` for code formatting and `flake8` for linting:

```bash
# Auto-format code
black .


# Check for style issues
flake8
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Guidelines

- Ensure your code passes all tests
- Update documentation as needed
- Add tests for new features
- Keep the code style consistent
- Write clear commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped improve this project
- Built with ❤️ using Python and PyQt5
- Special thanks to the open-source community for their invaluable tools and libraries

## 🛠 Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/neo-ai-chat.git
   cd neo-ai-chat
   ```

2. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

## 🚦 Running the Application

### Development Mode
```bash
python -m aichat
```

### Installed Mode (after pip install -e .)
```bash
aichat
```

## 🎨 Customization

### Themes
Choose from multiple built-in themes or customize your own in the settings.

### Keyboard Shortcuts
- `Ctrl+N`: New chat
- `Ctrl+S`: Save conversation
- `Ctrl+O`: Load conversation
- `Ctrl+Q`: Quit application
- `Ctrl+Shift+S`: Open settings

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/neo-ai-chat](https://github.com/yourusername/neo-ai-chat)