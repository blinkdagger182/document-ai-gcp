# Document AI Backend - Project Structure

## 📁 Folder Structure

```
document-ai-backend/
├── main.py                      # Main FastAPI application
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container configuration
├── README.md                    # API documentation
├── DEPLOYMENT_SUMMARY.md        # Deployment guide
├── TROUBLESHOOTING.md          # Common issues and solutions
├── test_api.html               # Web-based API tester
├── test_upload.sh              # Shell script for testing
├── ReactNativeExample.js       # React Native integration example
└── PROJECT_STRUCTURE.md        # This file
```

## 🏗️ Architecture Overview

### Core Components

1. **OCR Engine** (`PaddleOCR`)
   - English language model
   - Angle classification enabled
   - Bounding box detection
   - Confidence scoring

2. **PDF Processing** (`PyMuPDF/fitz`)
   - PDF to image conversion
   - Text overlay on PDF
   - Page metadata extraction

3. **Field Classification**
   - Checkbox detection
   - Text field identification
   - Table cell recognition
   - Title/label classification

4. **UI Schema Generation**
   - Smart field grouping
   - Checkbox to dropdown conversion
   - Section organization
   - React Native compatible output

5. **PDF Overlay Engine**
   - Text insertion with auto-scaling
   - Checkmark rendering
   - Coordinate mapping
   - Font management

## 🔄 Data Flow

```
PDF/Image Upload
    ↓
PDF → Images (if PDF)
    ↓
OCR Processing (PaddleOCR)
    ↓
Field Classification
    ↓
UI Schema Generation
    ↓
Return to React Native
    ↓
User Fills Form
    ↓
Submit Filled Data + Original PDF
    ↓
Overlay Engine
    ↓
Return Filled PDF
```

## 📡 API Endpoints

### 1. `/health` (GET)
Health check for monitoring

### 2. `/ocr` (POST)
Main OCR endpoint
- Input: PDF or Image file
- Output: UI schema + OCR blocks + metadata

### 3. `/overlay` (POST)
PDF overlay endpoint
- Input: Original PDF + filled form data (JSON)
- Output: Modified PDF file

## 🔧 Key Functions

### OCR Processing
- `pdf_to_images()` - Convert PDF pages to images
- `process_ocr_on_image()` - Run OCR on single image
- `classify_field_type()` - Classify detected fields

### UI Schema Generation
- `generate_ui_schema()` - Create React Native schema
- `convert_field_to_ui()` - Convert OCR field to UI component
- `group_checkboxes_to_dropdowns()` - Smart checkbox grouping

### PDF Overlay
- `draw_checkmark()` - Render checkmarks
- `insert_text_in_box()` - Insert text with auto-scaling

## 🎯 Field Types

1. **checkbox** - Boolean fields, radio buttons
2. **text_field** - Input fields with labels
3. **table_cell** - Structured table data
4. **title** - Section headers
5. **label** - Non-fillable text
6. **non_fillable** - Descriptive content

## 🚀 Deployment

### Local Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Docker Build
```bash
docker build -t document-ai-backend .
docker run -p 8080:8080 document-ai-backend
```

### Google Cloud Run
```bash
gcloud run deploy document-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

## 📦 Dependencies

- **FastAPI** - Web framework
- **PaddleOCR** - OCR engine
- **PyMuPDF** - PDF manipulation
- **Pillow** - Image processing
- **Uvicorn** - ASGI server

## 🔐 Security Considerations

- CORS enabled for all origins (adjust for production)
- File type validation
- Temporary file cleanup
- No persistent storage (stateless)

## 📊 Performance

- Cold start: ~3-5 seconds
- Warm request: ~1-2 seconds per page
- Memory: 2GB recommended
- CPU: 2 vCPUs recommended
- Timeout: 300 seconds for large PDFs

## 🧪 Testing

Use `test_api.html` for web-based testing or `test_upload.sh` for CLI testing.

Example:
```bash
# Test OCR endpoint
curl -X POST http://localhost:8080/ocr \
  -F "file=@sample.pdf"

# Test overlay endpoint
curl -X POST http://localhost:8080/overlay \
  -F "file=@sample.pdf" \
  -F 'filled_data={"fields":[{"id":"field_001","page":1,"bbox":[100,100,200,100,200,120,100,120],"type":"text_field","value":"John Doe"}]}'
```
