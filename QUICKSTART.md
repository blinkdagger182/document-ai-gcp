# Quick Start Guide - Document AI Backend

Get up and running in 5 minutes!

## 🚀 Option 1: Local Development (Fastest)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Server
```bash
uvicorn main:app --reload --port 8080
```

### Step 3: Test
```bash
# Health check
curl http://localhost:8080/health

# Run test suite
chmod +x test_complete.sh
./test_complete.sh
```

**Done!** Server running at `http://localhost:8080`

---

## 🐳 Option 2: Docker (Recommended for Production)

### Step 1: Build Image
```bash
docker build -t document-ai-backend .
```

### Step 2: Run Container
```bash
docker run -p 8080:8080 document-ai-backend
```

### Step 3: Test
```bash
curl http://localhost:8080/health
```

**Done!** Server running at `http://localhost:8080`

---

## ☁️ Option 3: Deploy to Google Cloud Run

### Step 1: Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Initialize
gcloud init
```

### Step 2: Deploy
```bash
gcloud run deploy document-ai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

### Step 3: Get URL
```bash
gcloud run services describe document-ai-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

**Done!** Your API is live on Cloud Run!

---

## 📱 Test with React Native

### Step 1: Upload PDF
```javascript
const formData = new FormData();
formData.append('file', {
  uri: pdfUri,
  type: 'application/pdf',
  name: 'form.pdf',
});

const response = await fetch('http://localhost:8080/ocr', {
  method: 'POST',
  body: formData,
});

const data = await response.json();
console.log(data.ui_schema); // Form schema
console.log(data.ocr_blocks); // Field data
```

### Step 2: Render Form
```javascript
data.ui_schema.form_schema.map(section => (
  <View key={section.section}>
    <Text>{section.section}</Text>
    {section.fields.map(field => {
      if (field.type === 'text_field') {
        return <TextInput placeholder={field.placeholder} />;
      }
      if (field.type === 'dropdown') {
        return <Picker items={field.options} />;
      }
      // ... more field types
    })}
  </View>
));
```

### Step 3: Submit Filled Form
```javascript
const filledData = {
  fields: data.ocr_blocks.map(field => ({
    ...field,
    value: userInputs[field.id]
  }))
};

const formData = new FormData();
formData.append('file', originalPdf);
formData.append('filled_data', JSON.stringify(filledData));

const response = await fetch('http://localhost:8080/overlay', {
  method: 'POST',
  body: formData,
});

const filledPdf = await response.blob();
// Save or share the PDF
```

**Done!** You have a complete PDF form workflow!

---

## 🧪 Quick Test with cURL

### Test OCR
```bash
# Create a test PDF first (requires ImageMagick)
convert -size 800x600 xc:white \
  -pointsize 20 -fill black \
  -annotate +100+100 "Name:" \
  -annotate +100+150 "Email:" \
  test.png

convert test.png test.pdf

# Run OCR
curl -X POST http://localhost:8080/ocr \
  -F "file=@test.pdf" \
  | jq .
```

### Test Overlay
```bash
curl -X POST http://localhost:8080/overlay \
  -F "file=@test.pdf" \
  -F 'filled_data={"fields":[{"id":"field_001_001","page":1,"bbox":[100,100,200,100,200,120,100,120],"type":"text_field","value":"John Doe"}]}' \
  --output filled.pdf

# View the filled PDF
open filled.pdf  # macOS
xdg-open filled.pdf  # Linux
```

---

## 📚 What's Next?

1. **Read the docs**: Check out `API_DOCUMENTATION.md` for complete API reference
2. **Deploy**: See `DEPLOYMENT_GUIDE.md` for production deployment
3. **Customize**: Adjust field classification in `main.py` for your forms
4. **Integrate**: Use `ReactNativeExample.js` as a starting point

---

## 🆘 Troubleshooting

### Port already in use?
```bash
# Use a different port
uvicorn main:app --port 8000
```

### Docker build fails?
```bash
# Check Docker is running
docker ps

# Try with more memory
docker build --memory=4g -t document-ai-backend .
```

### OCR not detecting text?
- Ensure image quality is good (not too blurry)
- Check image is not rotated (or enable angle_cls)
- Try with higher DPI (adjust in code)

### Cloud Run deployment fails?
```bash
# Check you're logged in
gcloud auth list

# Check project is set
gcloud config get-value project

# Enable required APIs
gcloud services enable run.googleapis.com
```

---

## 💡 Pro Tips

1. **Pre-cache models**: Models are cached in Docker image for faster cold starts
2. **Adjust memory**: Use 4GB for large PDFs with many pages
3. **Use min-instances**: Set to 1 to avoid cold starts in production
4. **Monitor logs**: Use `gcloud run services logs read` to debug issues
5. **Test locally first**: Always test with Docker before deploying

---

## 🎉 You're Ready!

Your Document AI backend is now running. Start uploading PDFs and building amazing form experiences!

**Need help?** Check:
- `API_DOCUMENTATION.md` - Complete API reference
- `DEPLOYMENT_GUIDE.md` - Deployment options
- `TROUBLESHOOTING.md` - Common issues
- `IMPLEMENTATION_SUMMARY.md` - What's been built
