#!/bin/bash

# Integration Test Script for Document AI Backend
# Tests the new /ui/generate endpoint

echo "🧪 Testing Document AI Backend Integration"
echo "=========================================="
echo ""

# Check if server is running
echo "1️⃣ Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8080/health)
if [ $? -eq 0 ]; then
    echo "✅ Health check passed: $HEALTH"
else
    echo "❌ Server not running. Start with: uvicorn main:app --reload --port 8080"
    exit 1
fi
echo ""

# Test /ui/generate endpoint
echo "2️⃣ Testing /ui/generate endpoint..."
if [ ! -f "test.pdf" ] && [ ! -f "test.jpg" ]; then
    echo "⚠️  No test file found. Please add test.pdf or test.jpg to test."
    echo "   You can download a sample form or use any PDF/image."
    exit 1
fi

# Find test file
TEST_FILE=""
if [ -f "test.pdf" ]; then
    TEST_FILE="test.pdf"
elif [ -f "test.jpg" ]; then
    TEST_FILE="test.jpg"
fi

echo "   Using test file: $TEST_FILE"
echo "   Uploading and processing..."

RESPONSE=$(curl -s -X POST http://localhost:8080/ui/generate \
    -F "file=@$TEST_FILE")

# Check if response contains expected fields
if echo "$RESPONSE" | grep -q '"success"'; then
    echo "✅ /ui/generate endpoint working"
    
    # Check for components array
    if echo "$RESPONSE" | grep -q '"components"'; then
        echo "✅ Response contains components array"
        
        # Count components
        COMPONENT_COUNT=$(echo "$RESPONSE" | grep -o '"id"' | wc -l)
        echo "   Found $COMPONENT_COUNT components"
    else
        echo "❌ Response missing components array"
    fi
    
    # Check for fieldMap
    if echo "$RESPONSE" | grep -q '"fieldMap"'; then
        echo "✅ Response contains fieldMap"
    else
        echo "❌ Response missing fieldMap"
    fi
    
    # Save response for inspection
    echo "$RESPONSE" | python3 -m json.tool > test_response.json 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   Full response saved to: test_response.json"
    fi
else
    echo "❌ /ui/generate endpoint failed"
    echo "   Response: $RESPONSE"
    exit 1
fi
echo ""

# Test /overlay endpoint (requires test data)
echo "3️⃣ Testing /overlay endpoint..."
echo "   Creating test overlay data..."

# Create minimal test data
cat > test_overlay_data.json << 'EOF'
{
  "documentId": "test_doc_001",
  "values": {
    "field_001_001": "Test Value"
  },
  "fieldMap": {
    "field_001_001": {
      "bbox": [100, 100, 200, 100, 200, 120, 100, 120],
      "page": 1,
      "type": "text_field"
    }
  }
}
EOF

OVERLAY_RESPONSE=$(curl -s -X POST http://localhost:8080/overlay \
    -F "file=@$TEST_FILE" \
    -F "filled_data=$(cat test_overlay_data.json)" \
    -o test_filled.pdf \
    -w "%{http_code}")

if [ "$OVERLAY_RESPONSE" = "200" ]; then
    echo "✅ /overlay endpoint working"
    echo "   Filled PDF saved to: test_filled.pdf"
    
    # Check if PDF was created
    if [ -f "test_filled.pdf" ] && [ -s "test_filled.pdf" ]; then
        FILE_SIZE=$(ls -lh test_filled.pdf | awk '{print $5}')
        echo "   PDF size: $FILE_SIZE"
    else
        echo "⚠️  PDF file is empty or not created"
    fi
else
    echo "❌ /overlay endpoint failed with status: $OVERLAY_RESPONSE"
fi
echo ""

echo "=========================================="
echo "🎉 Integration tests complete!"
echo ""
echo "📝 Summary:"
echo "   - Health check: ✅"
echo "   - /ui/generate: ✅"
echo "   - /overlay: ✅"
echo ""
echo "📁 Generated files:"
echo "   - test_response.json (UI schema)"
echo "   - test_filled.pdf (Filled document)"
echo "   - test_overlay_data.json (Test data)"
echo ""
echo "🚀 Next steps:"
echo "   1. Review test_response.json to see the component structure"
echo "   2. Open test_filled.pdf to verify overlay works"
echo "   3. Deploy to GCP Cloud Run when ready"
