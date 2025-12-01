#!/bin/bash

# Complete API Test Script for Document AI Backend
# Tests all endpoints with sample data

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8080}"
TEST_DIR="./test_files"

echo "🧪 Document AI Backend - Complete Test Suite"
echo "=============================================="
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create test directory
mkdir -p "$TEST_DIR"

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Create a test image with text
echo -e "${YELLOW}Test 2: Creating test image${NC}"
if command -v convert &> /dev/null; then
    convert -size 800x600 xc:white \
        -pointsize 24 -fill black \
        -annotate +50+100 "Application Form" \
        -annotate +50+200 "Name:" \
        -annotate +50+250 "Email:" \
        -annotate +50+300 "Phone:" \
        -annotate +50+400 "☐ New Application" \
        -annotate +50+450 "☐ Renewal" \
        "$TEST_DIR/test_form.png"
    echo -e "${GREEN}✓ Test image created${NC}"
else
    echo -e "${YELLOW}⚠ ImageMagick not installed, skipping image creation${NC}"
    echo "Install with: brew install imagemagick (macOS) or apt-get install imagemagick (Linux)"
fi
echo ""

# Test 3: OCR Endpoint (if test image exists)
if [ -f "$TEST_DIR/test_form.png" ]; then
    echo -e "${YELLOW}Test 3: OCR Processing${NC}"
    OCR_RESPONSE=$(curl -s -X POST "$API_URL/ocr" \
        -F "file=@$TEST_DIR/test_form.png")
    
    if echo "$OCR_RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓ OCR processing successful${NC}"
        echo "$OCR_RESPONSE" | jq '.' > "$TEST_DIR/ocr_result.json"
        echo "Full response saved to: $TEST_DIR/ocr_result.json"
        
        # Extract key metrics
        TOTAL_FIELDS=$(echo "$OCR_RESPONSE" | jq -r '.pdf_metadata.total_fields // 0')
        TOTAL_PAGES=$(echo "$OCR_RESPONSE" | jq -r '.pdf_metadata.total_pages // 0')
        echo "  - Total fields detected: $TOTAL_FIELDS"
        echo "  - Total pages: $TOTAL_PAGES"
    else
        echo -e "${RED}✗ OCR processing failed${NC}"
        echo "Response: $OCR_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ Test 3 skipped (no test image)${NC}"
fi
echo ""

# Test 4: Create a test PDF
echo -e "${YELLOW}Test 4: Creating test PDF${NC}"
if command -v convert &> /dev/null; then
    # Create image first
    convert -size 800x600 xc:white \
        -pointsize 20 -fill black \
        -annotate +100+100 "RESIDENT APPLICATION FORM" \
        -annotate +100+200 "Name (Mr/Ms/Madam):" \
        -annotate +100+250 "NRIC No.:" \
        -annotate +100+300 "Contact No.:" \
        -annotate +100+350 "Address:" \
        -annotate +100+450 "☐ New Application" \
        -annotate +100+480 "☐ Additional Card" \
        -annotate +100+510 "☐ Damaged" \
        -annotate +100+540 "☐ Lost" \
        "$TEST_DIR/temp_form.png"
    
    # Convert to PDF
    convert "$TEST_DIR/temp_form.png" "$TEST_DIR/test_form.pdf"
    rm "$TEST_DIR/temp_form.png"
    echo -e "${GREEN}✓ Test PDF created${NC}"
else
    echo -e "${YELLOW}⚠ ImageMagick not installed, skipping PDF creation${NC}"
fi
echo ""

# Test 5: OCR on PDF
if [ -f "$TEST_DIR/test_form.pdf" ]; then
    echo -e "${YELLOW}Test 5: OCR on PDF${NC}"
    PDF_OCR_RESPONSE=$(curl -s -X POST "$API_URL/ocr" \
        -F "file=@$TEST_DIR/test_form.pdf")
    
    if echo "$PDF_OCR_RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓ PDF OCR successful${NC}"
        echo "$PDF_OCR_RESPONSE" | jq '.' > "$TEST_DIR/pdf_ocr_result.json"
        echo "Full response saved to: $TEST_DIR/pdf_ocr_result.json"
        
        # Show UI schema
        echo ""
        echo "UI Schema sections:"
        echo "$PDF_OCR_RESPONSE" | jq -r '.ui_schema.form_schema[].section'
    else
        echo -e "${RED}✗ PDF OCR failed${NC}"
        echo "Response: $PDF_OCR_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ Test 5 skipped (no test PDF)${NC}"
fi
echo ""

# Test 6: PDF Overlay
if [ -f "$TEST_DIR/test_form.pdf" ] && [ -f "$TEST_DIR/pdf_ocr_result.json" ]; then
    echo -e "${YELLOW}Test 6: PDF Overlay${NC}"
    
    # Create filled data from OCR results
    FILLED_DATA=$(cat "$TEST_DIR/pdf_ocr_result.json" | jq '{
        fields: [
            .ocr_blocks[0] | {
                id: .id,
                page: .page,
                bbox: .bbox,
                type: .type,
                value: (if .type == "checkbox" then true else "John Doe" end)
            }
        ]
    }')
    
    echo "Filled data:"
    echo "$FILLED_DATA" | jq '.'
    
    curl -s -X POST "$API_URL/overlay" \
        -F "file=@$TEST_DIR/test_form.pdf" \
        -F "filled_data=$FILLED_DATA" \
        --output "$TEST_DIR/filled_form.pdf"
    
    if [ -f "$TEST_DIR/filled_form.pdf" ] && [ -s "$TEST_DIR/filled_form.pdf" ]; then
        echo -e "${GREEN}✓ PDF overlay successful${NC}"
        echo "Filled PDF saved to: $TEST_DIR/filled_form.pdf"
        
        # Check file size
        FILE_SIZE=$(wc -c < "$TEST_DIR/filled_form.pdf")
        echo "  - File size: $FILE_SIZE bytes"
    else
        echo -e "${RED}✗ PDF overlay failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Test 6 skipped (missing prerequisites)${NC}"
fi
echo ""

# Test 7: Error handling - Invalid file type
echo -e "${YELLOW}Test 7: Error Handling - Invalid File Type${NC}"
echo "test" > "$TEST_DIR/test.txt"
ERROR_RESPONSE=$(curl -s -X POST "$API_URL/ocr" \
    -F "file=@$TEST_DIR/test.txt")

if echo "$ERROR_RESPONSE" | grep -q "detail"; then
    echo -e "${GREEN}✓ Error handling works correctly${NC}"
    echo "Error message: $(echo "$ERROR_RESPONSE" | jq -r '.detail')"
else
    echo -e "${YELLOW}⚠ Unexpected response${NC}"
    echo "Response: $ERROR_RESPONSE"
fi
echo ""

# Test 8: Performance test
echo -e "${YELLOW}Test 8: Performance Test${NC}"
if [ -f "$TEST_DIR/test_form.png" ]; then
    echo "Running 5 requests to measure average response time..."
    TOTAL_TIME=0
    for i in {1..5}; do
        START=$(date +%s%N)
        curl -s -X POST "$API_URL/ocr" \
            -F "file=@$TEST_DIR/test_form.png" > /dev/null
        END=$(date +%s%N)
        DURATION=$((($END - $START) / 1000000))
        echo "  Request $i: ${DURATION}ms"
        TOTAL_TIME=$(($TOTAL_TIME + $DURATION))
    done
    AVG_TIME=$(($TOTAL_TIME / 5))
    echo -e "${GREEN}✓ Average response time: ${AVG_TIME}ms${NC}"
else
    echo -e "${YELLOW}⚠ Test 8 skipped (no test image)${NC}"
fi
echo ""

# Summary
echo "=============================================="
echo -e "${GREEN}✅ Test Suite Complete${NC}"
echo ""
echo "Test files created in: $TEST_DIR"
echo "  - test_form.png (test image)"
echo "  - test_form.pdf (test PDF)"
echo "  - ocr_result.json (OCR response)"
echo "  - pdf_ocr_result.json (PDF OCR response)"
echo "  - filled_form.pdf (filled PDF output)"
echo ""
echo "Next steps:"
echo "  1. Review the generated files"
echo "  2. Test with your own PDF forms"
echo "  3. Integrate with React Native app"
echo ""
