# Document Features Testing Guide

This document outlines the test cases for the document preview, summarization, and Q&A features.

## Test Environment
- OS: Windows
- Python: 3.8+
- Required packages: See `requirements.txt`

## Test Cases

### 1. Document Loading
#### 1.1 Supported Formats
- [ ] PDF (.pdf)
- [ ] Word (.docx)
- [ ] Text (.txt)
- [ ] CSV (.csv)
- [ ] Excel (.xlsx, .xls)
- [ ] JSON (.json)

#### 1.2 Loading Methods
- [ ] File > Open Document
- [ ] Drag and drop file into application
- [ ] Command line argument

### 2. Document Preview
#### 2.1 Content Display
- [ ] Text content is properly formatted
- [ ] Tables are displayed correctly (for CSV/Excel)
- [ ] Large documents are paginated or scrollable
- [ ] Special characters and encoding are handled correctly

#### 2.2 Metadata Display
- [ ] File name
- [ ] File size
- [ ] Last modified date
- [ ] Page count (for PDF/DOCX)
- [ ] Word/character count (for text-based formats)
- [ ] Column headers (for tabular data)

### 3. Document Summarization
#### 3.1 Summary Types
- [ ] Concise (3-5 sentences)
- [ ] Detailed (2-3 paragraphs)
- [ ] Key points (bulleted list)

#### 3.2 Functionality
- [ ] Generate summary button works
- [ ] Progress indicator shows during generation
- [ ] Summary is displayed in the summary tab
- [ ] Summary is relevant to document content
- [ ] Error handling for empty/invalid documents
- [ ] Large document handling (truncation with notification)

### 4. Document Q&A
#### 4.1 Basic Functionality
- [ ] Can ask questions about document content
- [ ] Answers are relevant to the document
- [ ] Handles questions with no clear answer in document
- [ ] Maintains conversation history
- [ ] Handles follow-up questions with context

#### 4.2 Error Handling
- [ ] No document loaded
- [ ] Empty question
- [ ] Very large documents
- [ ] Unsupported question types
- [ ] Network/API errors

#### 4.3 Performance
- [ ] Response time for small documents (<1MB)
- [ ] Response time for medium documents (1-10MB)
- [ ] Response time for large documents (>10MB)
- [ ] Memory usage with multiple large documents

### 5. User Interface
#### 5.1 Document Preview
- [ ] Toggle visibility of document preview
- [ ] Resize document preview panel
- [ ] Switch between tabs (Content, Metadata, Summary, Q&A)

#### 5.2 Q&A Interface
- [ ] Input field is focused when tab is selected
- [ ] Enter key submits question
- [ ] Clear button works
- [ ] Scrollable conversation history
- [ ] Copy button for answers

## Test Data

### Sample Documents
1. **Short Text Document**
   - File: `test_short.txt`
   - Content: A paragraph of text (100-200 words)

2. **Long Text Document**
   - File: `test_long.txt`
   - Content: Multiple pages of text (10,000+ words)

3. **PDF Document**
   - File: `test.pdf`
   - Content: Formatted text with images

4. **CSV File**
   - File: `data.csv`
   - Content: Tabular data with headers

5. **Excel File**
   - File: `data.xlsx`
   - Content: Multiple sheets with data

## Test Questions

### For Text Documents
1. What is the main topic of this document?
2. List the key points.
3. What are the conclusions?
4. [Specific question based on document content]

### For Tabular Data
1. What are the column headers?
2. How many rows are in the data?
3. What is the average of [numerical column]?
4. Show me rows where [condition].

## Expected Results

1. **Summarization**
   - Concise: 3-5 sentence summary
   - Detailed: 2-3 paragraph summary
   - Key Points: Bulleted list of 5-8 main points

2. **Q&A**
   - Direct answers to factual questions
   - "I couldn't find that information" for unknown answers
   - Follow-up questions maintain context

## Known Issues
- [ ] None currently known

## Test Results

| Test Case | Status | Notes |
|-----------|--------|-------|
|           |        |       |

## How to Report Bugs

1. Note the document type and size
2. Describe the steps to reproduce
3. Include any error messages
4. Note the expected vs actual behavior
