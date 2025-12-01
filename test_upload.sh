#!/bin/bash

# Test script for PaddleOCR UI Builder API

API_URL="https://paddleocr-ui-builder-62nie56atq-uc.a.run.app"

echo "🔍 Testing PaddleOCR UI Builder API..."
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${API_URL}/health")
echo "Response: $HEALTH_RESPONSE"
echo ""

# Test 2: Check if image file exists
if [ ! -f "test-image.jpg" ] && [ ! -f "test-image.png" ]; then
    echo "⚠️  No test image found. Please provide a test-image.jpg or test-image.png file"
    echo ""
    echo "You can create a simple test image with text using:"
    echo "  - Take a screenshot of any UI"
    echo "  - Or use: convert -size 400x200 -pointsize 30 -gravity center label:'Hello World' test-image.jpg"
    echo ""
    exit 1
fi

# Find the test image
TEST_IMAGE=""
if [ -f "test-image.jpg" ]; then
    TEST_IMAGE="test-image.jpg"
elif [ -f "test-image.png" ]; then
    TEST_IMAGE="test-image.png"
fi

echo "2️⃣ Testing /ui/generate endpoint with $TEST_IMAGE..."
echo ""

# Test 3: Upload image
RESPONSE=$(curl -s -X POST \
  "${API_URL}/ui/generate" \
  -F "file=@${TEST_IMAGE}" \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Success! Response:"
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
else
    echo "❌ Error! Response:"
    echo "$BODY"
fi

echo ""
echo "📝 To test from React Native, use the code in ReactNativeExample.js"
echo "🌐 To test from browser, open test_api.html in your browser"
