# Hybrid Worker Guide - AcroForm + OCR

## Overview

The hybrid worker intelligently detects PDF form fields using a two-tier approach:
1. **Primary:** AcroForm field detection (native PDF forms)
2. **Fallback:** OCR-based field detection (scanned/image PDFs)

## Architecture

```
PDF Upload
    ↓
Load with PyMuPDF
    ↓
Check for AcroForm
    ├─ Has AcroForm? → Extract Widget Annotations
    │                   ├─ Field Type (/FT)
    │                   ├─ Field Name (/T)
    │                   ├─ Field Value (/V)
    │                   ├─ Rect Coordinates
    │                   └─ Return: acroform=true
    │
    └─ No AcroForm? → OCR Fallback
                        ├─ Render pages to images
                        ├─ Run PaddleOCR
                        ├─ Infer field types from text
                        ├─ Extract bounding boxes
                        └─ Return: acroform=false
```

## API Endpoint

### POST /process

**Purpose:** Process PDF and extract field regions (called by Cloud Tasks)

**Request:**
```bash
curl -X POST http://localhost:8080/process \
  -F "file=@form.pdf"
```

**Response (AcroForm detected):**
```json
{
  "success": true,
  "documentId": "550e8400-e29b-41d4-a716-446655440000",
  "acroform": true,
  "field_regions": [
    {
      "id": "acro_0_0",
      "page": 1,
      "type": "text_field",
      "name": "applicant_name",
      "label": "Applicant Name",
      "value": "",
      "rect_normalized": {
        "x": 0.15,
        "y": 0.25,
        "width": 0.35,
        "height": 0.03
      },
      "rect_absolute": {
        "x0": 89.25,
        "y0": 210.5,
        "x1": 297.5,
        "y1": 235.8
      },
      "source": "acroform"
    }
  ],
  "page_count": 3,
  "total_fields": 15,
  "processing_time_ms": 245,
  "timestamp": "2025-12-03T10:30:00.000Z"
}
```

**Response (OCR fallback):**
```json
{
  "success": true,
  "documentId": "550e8400-e29b-41d4-a716-446655440001",
  "acroform": false,
  "field_regions": [
    {
      "id": "ocr_0_0",
      "page": 1,
      "type": "text_field",
      "name": "field_0_0",
      "label": "Name:",
      "value": "",
      "confidence": 0.95,
      "rect_normalized": {
        "x": 0.12,
        "y": 0.18,
        "width": 0.25,
        "height": 0.02
      },
      "rect_absolute": {
        "x0": 71.4,
        "y0": 151.6,
        "x1": 220.5,
        "y1": 168.4
      },
      "source": "ocr"
    }
  ],
  "page_count": 1,
  "total_fields": 8,
  "processing_time_ms": 1850,
  "timestamp": "2025-12-03T10:31:00.000Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "documentId": "550e8400-e29b-41d4-a716-446655440002",
  "error": "Invalid PDF file",
  "error_type": "ValueError",
  "processing_time_ms": 50,
  "timestamp": "2025-12-03T10:32:00.000Z"
}
```

## Field Types

### AcroForm Field Types
- `text_field` - Text input (FT: /Tx)
- `checkbox` - Checkbox (FT: /Btn with flag)
- `radio` - Radio button (FT: /Btn)
- `dropdown` - Combo box (FT: /Ch)
- `listbox` - List box (FT: /Ch)
- `signature` - Signature field (FT: /Sig)

### OCR-Inferred Field Types
- `text_field` - Text with colon or field keywords
- `checkbox` - Checkbox symbols (☐☑✓✗)
- `signature` - "Signature" or "Sign here" text
- `date_field` - Date-related text

## Coordinate Systems

### Normalized Coordinates (0-1 range)
Used for responsive UI rendering across different screen sizes.

```python
normalized_x = absolute_x / page_width
normalized_y = absolute_y / page_height
normalized_width = absolute_width / page_width
normalized_height = absolute_height / page_height
```

### Absolute Coordinates (PDF points)
Used for precise PDF overlay operations.

```python
{
  "x0": 100.5,  # Left
  "y0": 200.3,  # Top
  "x1": 300.7,  # Right
  "y1": 225.9   # Bottom
}
```

## AcroForm Detection Logic

```python
def detect_acroform_fields(doc: fitz.Document):
    # 1. Check catalog
    if not doc.catalog or "AcroForm" not in doc.catalog:
        return False, []
    
    # 2. Check fields array
    acro_form = doc.catalog["AcroForm"]
    if not acro_form or "Fields" not in acro_form:
        return False, []
    
    # 3. Iterate pages for widget annotations
    for page in doc:
        for annot in page.annots():
            if annot.type[0] == fitz.PDF_ANNOT_WIDGET:
                # Extract field data
                field_type = annot.field_type
                field_name = annot.field_name
                field_value = annot.field_value
                rect = annot.rect
                # ... build field_region
    
    return True, field_regions
```

## OCR Fallback Logic

```python
def detect_fields_via_ocr(doc: fitz.Document):
    for page in doc:
        # 1. Render to image (2x resolution)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # 2. Run PaddleOCR
        result = ocr.ocr(image_path, cls=True)
        
        # 3. Process each detected text
        for line in result[0]:
            box = line[0]  # Coordinates
            text = line[1][0]  # Text content
            confidence = line[1][1]  # Confidence score
            
            # 4. Infer field type from text
            field_type = infer_field_type_from_ocr(text)
            
            # 5. Build field_region
            # ...
    
    return field_regions
```

## Field Type Inference (OCR)

```python
def infer_field_type_from_ocr(text: str):
    text_lower = text.lower().strip()
    
    # Checkbox patterns
    if re.search(r'^\s*[\[\]☐☑✓✗xX○●]\s*', text_lower):
        return "checkbox"
    
    # Signature
    if 'signature' in text_lower or 'sign here' in text_lower:
        return "signature"
    
    # Date
    if 'date' in text_lower or 'dd/mm' in text_lower:
        return "date_field"
    
    # Text field (ends with colon)
    if text.endswith(':'):
        return "text_field"
    
    # Default
    return "text_field"
```

## Performance Characteristics

### AcroForm Detection
- **Speed:** ~100-300ms per document
- **Accuracy:** 100% (native PDF data)
- **Use case:** Modern fillable PDFs

### OCR Fallback
- **Speed:** ~1-3 seconds per page
- **Accuracy:** 85-95% (depends on image quality)
- **Use case:** Scanned documents, image-based PDFs

## Error Handling

The worker handles errors gracefully and returns structured error responses:

```python
try:
    # Process document
    ...
except Exception as e:
    return {
        "success": False,
        "documentId": document_id,
        "error": str(e),
        "error_type": type(e).__name__,
        "processing_time_ms": elapsed_time,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Cloud Tasks Integration

### Task Queue Configuration

```python
# Backend creates task
task = {
    'http_request': {
        'http_method': 'POST',
        'url': 'https://worker-url.run.app/process',
        'headers': {
            'Content-Type': 'multipart/form-data'
        },
        'body': pdf_file_bytes
    }
}

client.create_task(parent=queue_path, task=task)
```

### Worker Response Handling

```python
# Backend receives response
if response['success']:
    document_id = response['documentId']
    acroform = response['acroform']
    field_regions = response['field_regions']
    
    # Store in database
    db.save_document(document_id, field_regions, acroform)
else:
    # Handle error
    log_error(response['error'])
```

## Testing

### Test with AcroForm PDF
```bash
curl -X POST http://localhost:8080/process \
  -F "file=@fillable_form.pdf" \
  | jq .
```

### Test with Scanned PDF
```bash
curl -X POST http://localhost:8080/process \
  -F "file=@scanned_form.pdf" \
  | jq .
```

### Test Error Handling
```bash
curl -X POST http://localhost:8080/process \
  -F "file=@invalid.txt" \
  | jq .
```

## Deployment

Same as before - deploy to Cloud Run:

```bash
gcloud run deploy document-ai-worker \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --no-allow-unauthenticated  # Only Cloud Tasks can call
```

## Monitoring

### Key Metrics to Track
- **AcroForm detection rate:** % of PDFs with native forms
- **OCR fallback rate:** % of PDFs requiring OCR
- **Processing time:** Average time per document
- **Error rate:** % of failed processing attempts
- **Field detection accuracy:** Fields detected vs expected

### Logging
```python
# Log AcroForm detection
print(f"Document {document_id}: AcroForm={'detected' if has_acroform else 'not found'}")

# Log field count
print(f"Document {document_id}: Extracted {len(field_regions)} fields")

# Log processing time
print(f"Document {document_id}: Processed in {processing_time_ms}ms")
```

## Advantages of Hybrid Approach

1. **Speed:** AcroForm detection is 10x faster than OCR
2. **Accuracy:** Native form data is 100% accurate
3. **Fallback:** OCR ensures all PDFs can be processed
4. **Cost:** Faster processing = lower Cloud Run costs
5. **Flexibility:** Handles both modern and legacy PDFs

## Limitations

1. **OCR accuracy:** Depends on image quality
2. **Field inference:** OCR-based type detection is heuristic
3. **Complex layouts:** May struggle with multi-column forms
4. **Handwriting:** OCR doesn't handle handwritten text well

## Next Steps

1. Deploy worker to Cloud Run
2. Set up Cloud Tasks queue
3. Configure backend to call worker
4. Monitor performance metrics
5. Fine-tune field type inference rules
