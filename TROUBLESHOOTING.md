# Troubleshooting Guide

## Common Issues and Solutions

### 1. "Failed to load response data: unsupported method" Error

This error typically occurs when:

**Problem**: Testing tool or client doesn't support the HTTP method or has CORS issues.

**Solutions**:

#### A. If testing from Postman/Insomnia:
- Make sure you're using **POST** method (not GET)
- Set the body type to **form-data** (not JSON)
- Add a file field named `file`
- Select your image file

#### B. If testing from React Native:
```javascript
// ✅ CORRECT - Don't set Content-Type manually
const formData = new FormData();
formData.append('file', {
  uri: imageUri,
  type: 'image/jpeg',
  name: 'photo.jpg',
});

const response = await fetch(API_URL + '/ui/generate', {
  method: 'POST',
  body: formData,
  // Don't add headers - let fetch handle it
});

// ❌ WRONG - Don't do this
const response = await fetch(API_URL + '/ui/generate', {
  method: 'POST',
  body: formData,
  headers: {
    'Content-Type': 'multipart/form-data', // This breaks it!
  },
});
```

#### C. If testing from curl:
```bash
# ✅ CORRECT
curl -X POST \
  https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/ui/generate \
  -F "file=@your-image.jpg"

# ❌ WRONG
curl -X GET \
  https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/ui/generate
```

#### D. If testing from browser:
- Open `test_api.html` in your browser
- Or use the browser's fetch API:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/ui/generate', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(data => console.log(data));
```

### 2. CORS Errors

**Symptoms**: 
- "Access to fetch blocked by CORS policy"
- "No 'Access-Control-Allow-Origin' header"

**Solution**: 
The API already has CORS enabled for all origins. If you still see this:
- Make sure you're using HTTPS (not HTTP)
- Check if you're setting custom headers that trigger preflight
- Remove any `Content-Type` headers when using FormData

### 3. 400 Bad Request - "No file uploaded"

**Problem**: The file field is missing or named incorrectly.

**Solution**: 
- The field name MUST be `file` (lowercase)
- Make sure you're actually attaching a file

```javascript
// ✅ CORRECT
formData.append('file', imageFile);

// ❌ WRONG
formData.append('image', imageFile);
formData.append('photo', imageFile);
```

### 4. 400 Bad Request - "Invalid file type"

**Problem**: Unsupported image format.

**Solution**: 
Use one of these formats:
- JPEG/JPG
- PNG
- BMP
- TIFF

### 5. 500 Internal Server Error

**Problem**: Server-side processing error.

**Solutions**:
- Check if the image is corrupted
- Try a different image
- Check Cloud Run logs:
```bash
gcloud run services logs read paddleocr-ui-builder --region us-central1 --limit 50
```

### 6. Timeout Errors

**Problem**: Image processing takes too long.

**Solutions**:
- Use smaller images (< 5MB recommended)
- Reduce image resolution before uploading
- The API has a 300-second timeout, so very large images might fail

### 7. Empty Components Array

**Problem**: API returns `{"success": true, "components": []}`

**Reasons**:
- No text detected in the image
- Image is too blurry or low quality
- Text is too small or distorted

**Solutions**:
- Use higher quality images
- Ensure text is clearly visible
- Try images with larger, clearer text

## Testing the API

### Quick Health Check
```bash
curl https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/health
```

Expected response:
```json
{"status":"ok"}
```

### Test with Sample Image

1. Create or download a test image with text
2. Run the test script:
```bash
./test_upload.sh
```

3. Or test manually:
```bash
curl -X POST \
  https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/ui/generate \
  -F "file=@test-image.jpg" \
  | jq .
```

### Test from Browser
Open `test_api.html` in your browser and upload an image.

### Test from React Native
Use the code in `ReactNativeExample.js`

## Getting Help

If you're still having issues:

1. **Check the logs**:
```bash
gcloud run services logs read paddleocr-ui-builder --region us-central1 --limit 50
```

2. **Verify the service is running**:
```bash
gcloud run services describe paddleocr-ui-builder --region us-central1
```

3. **Test with a simple curl command**:
```bash
# This should work if the API is functioning
curl https://paddleocr-ui-builder-62nie56atq-uc.a.run.app/health
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/ui/generate` | POST | Generate UI components from image |
| `/ocr/process` | POST | Get raw OCR results |

## React Native Specific Issues

### Issue: FormData not working
```javascript
// Make sure you have the right imports
import FormData from 'form-data'; // If using Node.js
// Or use the built-in FormData in React Native
```

### Issue: Image picker URI format
```javascript
// iOS might return file:// URIs
// Android might return content:// URIs
// Both should work, but ensure you're passing the correct type

formData.append('file', {
  uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
  type: 'image/jpeg',
  name: 'photo.jpg',
});
```

### Issue: Network request failed
- Check if you're running on a real device or emulator
- Ensure the device has internet access
- On Android, add network permissions to AndroidManifest.xml:
```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## Still Not Working?

Create an issue with:
1. The exact error message
2. How you're testing (curl, Postman, React Native, etc.)
3. The request you're making (without sensitive data)
4. Any relevant logs
