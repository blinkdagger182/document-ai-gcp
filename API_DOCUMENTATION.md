# Document AI API - Complete Documentation

## 🎯 Overview

Complete backend service for PDF-to-UI-to-PDF workflow with OCR, field detection, and overlay capabilities.

## 📡 Endpoints

### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

---

### 2. OCR Processing (Main Endpoint)

```http
POST /ocr
```

**Description:** Process PDF or image files, extract text with bounding boxes, classify fields, and generate UI schema.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF, JPG, PNG, BMP, TIFF)

**Example (cURL):**
```bash
curl -X POST http://localhost:8080/ocr \
  -F "file=@application_form.pdf"
```

**Example (JavaScript/React Native):**
```javascript
const formData = new FormData();
formData.append('file', {
  uri: pdfUri,
  type: 'application/pdf',
  name: 'form.pdf',
});

const response = await fetch('https://your-api.com/ocr', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
```

**Response:**
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
            "options": [
              "New Application",
              "Additional Card",
              "Damaged",
              "Lost"
            ]
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
          },
          {
            "id": "field_001_006",
            "type": "text_field",
            "title": "NRIC No.",
            "placeholder": "Enter nric no."
          },
          {
            "id": "field_001_007",
            "type": "text_field",
            "title": "Contact No.",
            "placeholder": "Enter contact no."
          }
        ]
      }
    ]
  },
  "ocr_blocks": [
    {
      "id": "field_001_001",
      "type": "checkbox",
      "label": "New Application",
      "bbox": [100, 150, 200, 150, 200, 170, 100, 170],
      "page": 1,
      "confidence": 0.95,
      "value": false
    },
    {
      "id": "field_001_005",
      "type": "text_field",
      "label": "Name (Mr/Ms/Madam):",
      "bbox": [100, 250, 300, 250, 300, 270, 100, 270],
      "page": 1,
      "confidence": 0.98,
      "value": ""
    }
  ],
  "pdf_metadata": {
    "pages": [
      {
        "page": 1,
        "width": 595.0,
        "height": 842.0
      }
    ],
    "total_pages": 1,
    "total_fields": 15
  },
  "field_types": {
    "checkbox": 4,
    "text_field": 8,
    "table_cell": 2,
    "title": 1,
    "label": 0,
    "non_fillable": 0
  }
}
```

---

### 3. PDF Overlay

```http
POST /overlay
```

**Description:** Overlay filled form data onto original PDF and return modified PDF.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Original PDF file
  - `filled_data`: JSON string with filled values

**filled_data Format:**
```json
{
  "fields": [
    {
      "id": "field_001_001",
      "page": 1,
      "bbox": [100, 150, 200, 150, 200, 170, 100, 170],
      "type": "checkbox",
      "value": true
    },
    {
      "id": "field_001_005",
      "page": 1,
      "bbox": [100, 250, 300, 250, 300, 270, 100, 270],
      "type": "text_field",
      "value": "John Doe"
    }
  ]
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8080/overlay \
  -F "file=@original.pdf" \
  -F 'filled_data={"fields":[{"id":"field_001_001","page":1,"bbox":[100,150,200,150,200,170,100,170],"type":"text_field","value":"John Doe"}]}' \
  --output filled_form.pdf
```

**Example (JavaScript/React Native):**
```javascript
const formData = new FormData();
formData.append('file', {
  uri: originalPdfUri,
  type: 'application/pdf',
  name: 'original.pdf',
});

const filledData = {
  fields: formValues.map(field => ({
    id: field.id,
    page: field.page,
    bbox: field.bbox,
    type: field.type,
    value: field.value
  }))
};

formData.append('filled_data', JSON.stringify(filledData));

const response = await fetch('https://your-api.com/overlay', {
  method: 'POST',
  body: formData,
});

// Download the PDF
const blob = await response.blob();
// Save or share the PDF
```

**Response:**
- Content-Type: `application/pdf`
- Body: Binary PDF file
- Filename: `filled_{original_filename}.pdf`

---

## 🎨 UI Schema Structure

### Field Types

#### 1. Dropdown
```json
{
  "id": "dropdown_field_001_001",
  "type": "dropdown",
  "title": "Application Category",
  "options": ["Option 1", "Option 2", "Option 3"]
}
```

#### 2. Text Field
```json
{
  "id": "field_001_005",
  "type": "text_field",
  "title": "Name",
  "placeholder": "Enter name"
}
```

#### 3. Checkbox
```json
{
  "id": "field_001_010",
  "type": "checkbox",
  "title": "I agree to terms",
  "value": false
}
```

### Smart Grouping Rules

1. **Multiple checkboxes in proximity** → Converted to dropdown
2. **Text with colon** → Text field
3. **Short text in structured layout** → Table cell
4. **Uppercase or section headers** → Title (excluded from fields)

---

## 🔧 Integration Examples

### React Native Complete Example

```javascript
import React, { useState } from 'react';
import { View, Text, TextInput, Button, Picker, CheckBox } from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';

const API_BASE = 'https://your-api.com';

const FormBuilder = () => {
  const [schema, setSchema] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [originalPdf, setOriginalPdf] = useState(null);

  // Step 1: Upload PDF and get schema
  const uploadPdf = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.pdf],
      });

      const formData = new FormData();
      formData.append('file', {
        uri: result[0].uri,
        type: result[0].type,
        name: result[0].name,
      });

      const response = await fetch(`${API_BASE}/ocr`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setSchema(data.ui_schema);
      setOriginalPdf(result[0]);
      
      // Initialize form values
      const initialValues = {};
      data.ocr_blocks.forEach(field => {
        initialValues[field.id] = field.value;
      });
      setFormValues(initialValues);
    } catch (err) {
      console.error('Upload error:', err);
    }
  };

  // Step 2: Render dynamic form
  const renderField = (field) => {
    switch (field.type) {
      case 'text_field':
        return (
          <View key={field.id}>
            <Text>{field.title}</Text>
            <TextInput
              value={formValues[field.id] || ''}
              onChangeText={(text) => 
                setFormValues({...formValues, [field.id]: text})
              }
              placeholder={field.placeholder}
            />
          </View>
        );

      case 'dropdown':
        return (
          <View key={field.id}>
            <Text>{field.title}</Text>
            <Picker
              selectedValue={formValues[field.id]}
              onValueChange={(value) =>
                setFormValues({...formValues, [field.id]: value})
              }
            >
              {field.options.map(opt => (
                <Picker.Item key={opt} label={opt} value={opt} />
              ))}
            </Picker>
          </View>
        );

      case 'checkbox':
        return (
          <View key={field.id}>
            <CheckBox
              value={formValues[field.id] || false}
              onValueChange={(value) =>
                setFormValues({...formValues, [field.id]: value})
              }
            />
            <Text>{field.title}</Text>
          </View>
        );

      default:
        return null;
    }
  };

  // Step 3: Submit and get filled PDF
  const submitForm = async () => {
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: originalPdf.uri,
        type: originalPdf.type,
        name: originalPdf.name,
      });

      // Map form values to OCR blocks format
      const filledData = {
        fields: schema.form_schema.flatMap(section =>
          section.fields.map(field => ({
            id: field.id,
            page: section.page,
            bbox: field.bbox, // You need to store this from ocr_blocks
            type: field.type,
            value: formValues[field.id]
          }))
        )
      };

      formData.append('filled_data', JSON.stringify(filledData));

      const response = await fetch(`${API_BASE}/overlay`, {
        method: 'POST',
        body: formData,
      });

      const blob = await response.blob();
      // Save or share the filled PDF
      const filePath = `${RNFS.DocumentDirectoryPath}/filled_form.pdf`;
      await RNFS.writeFile(filePath, blob, 'base64');
      
      console.log('PDF saved to:', filePath);
    } catch (err) {
      console.error('Submit error:', err);
    }
  };

  return (
    <View>
      <Button title="Upload PDF" onPress={uploadPdf} />
      
      {schema && (
        <>
          {schema.form_schema.map(section => (
            <View key={section.section}>
              <Text style={{fontSize: 18, fontWeight: 'bold'}}>
                {section.section}
              </Text>
              {section.fields.map(renderField)}
            </View>
          ))}
          
          <Button title="Submit Form" onPress={submitForm} />
        </>
      )}
    </View>
  );
};

export default FormBuilder;
```

---

## 🚨 Error Handling

### Common Error Responses

```json
{
  "detail": "No file uploaded"
}
```

```json
{
  "detail": "Invalid file type. Use PDF or image files."
}
```

```json
{
  "detail": "Invalid JSON in filled_data"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad request (invalid input)
- `500` - Server error (processing failed)

---

## 🔒 Security Notes

- Maximum file size: 32MB (Cloud Run limit)
- Temporary files are automatically cleaned up
- No data persistence (stateless service)
- CORS enabled for all origins (configure for production)

---

## 📊 Performance Tips

1. **Optimize PDF size** before upload (compress images)
2. **Use images instead of PDF** for single-page forms (faster)
3. **Cache OCR results** on client side to avoid re-processing
4. **Batch process** multiple pages if possible

---

## 🧪 Testing

### Test with cURL

```bash
# Test health
curl http://localhost:8080/health

# Test OCR
curl -X POST http://localhost:8080/ocr \
  -F "file=@test.pdf" \
  | jq .

# Test overlay
curl -X POST http://localhost:8080/overlay \
  -F "file=@test.pdf" \
  -F 'filled_data={"fields":[{"id":"field_001_001","page":1,"bbox":[100,100,200,100,200,120,100,120],"type":"text_field","value":"Test"}]}' \
  --output result.pdf
```

### Test with Python

```python
import requests

# OCR test
with open('test.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/ocr',
        files={'file': f}
    )
    print(response.json())

# Overlay test
filled_data = {
    "fields": [
        {
            "id": "field_001_001",
            "page": 1,
            "bbox": [100, 100, 200, 100, 200, 120, 100, 120],
            "type": "text_field",
            "value": "John Doe"
        }
    ]
}

with open('test.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/overlay',
        files={'file': f},
        data={'filled_data': json.dumps(filled_data)}
    )
    
    with open('filled.pdf', 'wb') as out:
        out.write(response.content)
```
