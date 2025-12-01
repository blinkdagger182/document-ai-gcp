# Document AI Backend - PDF to UI to PDF

Complete production-ready backend service for PDF-to-UI-to-PDF workflow with OCR, intelligent field detection, and PDF overlay capabilities.

## ✨ Features

- 📄 **PDF & Image Processing** - Accept PDF or image uploads
- 🔍 **Advanced OCR** - PaddleOCR with bounding box detection
- 🎯 **Smart Field Classification** - Checkbox, text field, table cell, title detection
- 🎨 **UI Schema Generation** - React Native ready form schemas
- 📝 **PDF Overlay** - Fill PDFs with form data programmatically
- 🚀 **Production Ready** - Docker, Cloud Run, scalable architecture

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8080

# Test
curl http://localhost:8080/health
```

### Docker
```bash
# Build
docker build -t document-ai-backend .

# Run
docker run -p 8080:8080 document-ai-backend
```

### Deploy to Google Cloud Run
```bash
gcloud run deploy document-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

## 🚀 Deployed Service (if applicable)

**Service URL:** `https://your-service-url.run.app`

## 📡 API Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. OCR Processing (Main Endpoint)
```bash
POST /ocr
```

Upload PDF or image and receive:
- UI schema for React Native
- OCR blocks with bounding boxes
- Field classifications
- PDF metadata

**Example Request:**
```bash
curl -X POST http://localhost:8080/ocr \
  -F "file=@application_form.pdf" \
  | jq .
```

### 3. PDF Overlay
```bash
POST /overlay
```

Fill PDF with form data and get modified PDF back.

**Example Request:**
```bash
curl -X POST http://localhost:8080/overlay \
  -F "file=@original.pdf" \
  -F 'filled_data={"fields":[...]}' \
  --output filled.pdf
```

## 🧪 Testing

Run the complete test suite:
```bash
./test_complete.sh
```

Or test individual endpoints:
```bash
# Health check
curl http://localhost:8080/health

# OCR test
curl -X POST http://localhost:8080/ocr \
  -F "file=@test.pdf" | jq .
```

**Response Format:**
```json
{
  "success": true,
  "ui_schema": {
    "form_schema": [
      {
        "section": "Application Category",
        "page": 1,
        "fields": [
          {
            "id": "dropdown_field_001_001",
            "type": "dropdown",
            "title": "Application Category",
            "options": ["New Application", "Additional Card", "Damaged", "Lost"]
          }
        ]
      },
      {
        "section": "Resident Details",
        "page": 1,
        "fields": [
          {
            "id": "field_001_005",
            "type": "text_field",
            "title": "Name (Mr/Ms/Madam)",
            "placeholder": "Enter name (mr/ms/madam)"
          }
        ]
      }
    ]
  },
  "ocr_blocks": [...],
  "pdf_metadata": {
    "pages": [...],
    "total_pages": 1,
    "total_fields": 15
  },
  "field_types": {
    "checkbox": 4,
    "text_field": 8,
    "table_cell": 2,
    "title": 1
  }
}
```

## 🎨 Field Types

The API automatically detects and classifies form fields:

- **checkbox**: Boolean fields, radio buttons → Grouped into dropdowns
- **text_field**: Input fields with labels (Name, NRIC, Contact, etc.)
- **table_cell**: Structured table data
- **title**: Section headers (excluded from form fields)
- **label**: Non-fillable text labels
- **non_fillable**: Descriptive content

### Smart Grouping Rules

1. **Multiple checkboxes** in proximity → Converted to dropdown
2. **Text ending with colon** → Text field
3. **Short structured text** → Table cell
4. **Uppercase/section headers** → Title

## 🔧 React Native Integration

See `ReactNativeExample.js` for a complete implementation.

**Quick Example:**
```javascript
// 1. Upload PDF and get schema
const formData = new FormData();
formData.append('file', {
  uri: pdfUri,
  type: 'application/pdf',
  name: 'form.pdf',
});

const response = await fetch('http://your-api.com/ocr', {
  method: 'POST',
  body: formData,
});

const { ui_schema, ocr_blocks } = await response.json();

// 2. Render dynamic form from schema
ui_schema.form_schema.map(section => (
  <View key={section.section}>
    <Text>{section.section}</Text>
    {section.fields.map(field => renderField(field))}
  </View>
));

// 3. Submit filled data
const filledData = {
  fields: ocr_blocks.map(field => ({
    ...field,
    value: formValues[field.id]
  }))
};

const overlayResponse = await fetch('http://your-api.com/overlay', {
  method: 'POST',
  body: createFormData(originalPdf, filledData),
});

const filledPdf = await overlayResponse.blob();
```

## 📦 Tech Stack

- **FastAPI** - High-performance web framework
- **PaddleOCR** - Advanced OCR engine (PP-OCRv4)
- **PyMuPDF (fitz)** - PDF manipulation and overlay
- **Pillow** - Image processing
- **Python 3.11** - Runtime environment

## 📚 Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference with examples
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deploy to Cloud Run, AWS, Azure, K8s
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Architecture and code organization
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## ⚡ Performance

- **Memory**: 2GB recommended
- **CPU**: 2 vCPUs recommended
- **Timeout**: 300 seconds for large PDFs
- **Cold Start**: ~3-5 seconds (models pre-cached)
- **Warm Request**: ~1-2 seconds per page

## 🔒 Security

- CORS enabled (configure for production)
- File type validation
- Automatic temp file cleanup
- Stateless architecture (no data persistence)

## 📝 Supported Formats

- **Input**: PDF, JPEG, PNG, BMP, TIFF
- **Output**: JSON (OCR), PDF (overlay)
- **Max file size**: 32MB (Cloud Run limit)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - feel free to use in your projects!
