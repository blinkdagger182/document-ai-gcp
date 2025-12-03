from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
import tempfile
import os
from typing import List, Dict, Any, Optional
import re
import json
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import magic

# Initialize PaddleOCR globally (once at startup, not per request)
ocr = PaddleOCR(use_gpu=False, use_angle_cls=True, lang='en')

app = FastAPI(
    title="Document AI - PDF to UI to PDF",
    description="Complete backend for PDF-to-UI-to-PDF with OCR, field detection, and overlay",
    version="2.0.0"
)

# Enable CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "ok", "version": "2.0.0"}


def pdf_to_images(pdf_path: str) -> List[Dict[str, Any]]:
    """Convert PDF pages to images for OCR processing"""
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render at 2x resolution for better OCR
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Save to temp file
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(temp_img.name, 'PNG')
        
        images.append({
            "page": page_num + 1,
            "path": temp_img.name,
            "width": page.rect.width,
            "height": page.rect.height,
            "dpi_scale": 2.0
        })
    
    doc.close()
    return images


def classify_field_type(text: str, bbox: List, nearby_texts: List[str] = None) -> str:
    """
    Classify field type based on text content and context
    Returns: checkbox, text_field, table_cell, title, label, non_fillable
    """
    text_lower = text.lower().strip()
    
    # Checkbox patterns
    checkbox_patterns = [
        r'^\s*[\[\]☐☑✓✗xX]\s*',  # Starts with checkbox symbol
        r'(new|additional|damaged|lost|yes|no|male|female|mr|ms|mrs)$',
        r'^\s*[○●]\s*'  # Radio button
    ]
    for pattern in checkbox_patterns:
        if re.search(pattern, text_lower):
            return "checkbox"
    
    # Table cell detection (short text, structured)
    if len(text) < 50 and any(keyword in text_lower for keyword in ['no.', 'date', 'name', 'nric', 'contact', 'address']):
        return "table_cell"
    
    # Text field labels (ends with colon or common field names)
    if text.endswith(':') or any(keyword in text_lower for keyword in [
        'name', 'nric', 'contact', 'address', 'email', 'phone', 'date of birth', 'occupation'
    ]):
        return "text_field"
    
    # Title detection (short, uppercase, or large font implied by position)
    if len(text) < 60 and (text.isupper() or any(keyword in text_lower for keyword in [
        'application', 'form', 'details', 'information', 'section'
    ])):
        return "title"
    
    # Label-only text
    if len(text) < 30:
        return "label"
    
    return "non_fillable"


def detect_component_type(text: str, box: List, y_position: float) -> Dict[str, Any]:
    """
    Analyze text and position to determine UI component type
    """
    text_lower = text.lower().strip()
    height = abs(box[2][1] - box[0][1])
    width = abs(box[1][0] - box[0][0])
    
    # Detect buttons (common button text patterns)
    button_keywords = ['submit', 'login', 'sign in', 'sign up', 'register', 'continue', 'next', 'back', 'cancel', 'ok', 'confirm', 'save', 'delete', 'add', 'create']
    if any(keyword in text_lower for keyword in button_keywords) or (len(text) < 20 and height < 50):
        return {
            "type": "button",
            "variant": "primary" if any(k in text_lower for k in ['submit', 'login', 'continue', 'confirm']) else "secondary"
        }
    
    # Detect input fields (labels ending with :)
    if text.endswith(':') or any(keyword in text_lower for keyword in ['email', 'password', 'username', 'name', 'phone', 'address']):
        input_type = "email" if 'email' in text_lower else "password" if 'password' in text_lower else "text"
        return {
            "type": "input",
            "inputType": input_type,
            "label": text.rstrip(':')
        }
    
    # Detect headings (larger text, typically at top)
    if y_position < 0.2 and (height > 30 or len(text) < 50):
        return {"type": "heading", "level": 1 if height > 40 else 2}
    
    # Detect checkboxes/radio (short text with specific patterns)
    if len(text) < 30 and any(keyword in text_lower for keyword in ['agree', 'accept', 'remember', 'terms', 'conditions']):
        return {"type": "checkbox"}
    
    # Detect links
    if any(keyword in text_lower for keyword in ['forgot', 'click here', 'learn more', 'terms', 'privacy']):
        return {"type": "link"}
    
    # Default to text
    return {"type": "text"}


def generate_ui_schema(fields: List[Dict]) -> Dict[str, Any]:
    """
    Generate clean UI schema for React Native from OCR fields
    Applies smart grouping and conversion rules
    """
    if not fields:
        return {"form_schema": []}
    
    # Group fields by page and vertical proximity
    sections = []
    current_section = None
    last_y = 0
    section_threshold = 100  # pixels
    
    # Sort by page and y-position
    sorted_fields = sorted(fields, key=lambda f: (f["page"], f["bbox"][1]))
    
    for field in sorted_fields:
        y_pos = field["bbox"][1]
        
        # Detect section breaks (titles or large gaps)
        if field["type"] == "title" or (current_section and abs(y_pos - last_y) > section_threshold):
            if current_section:
                sections.append(current_section)
            
            current_section = {
                "section": field["label"] if field["type"] == "title" else "Section",
                "page": field["page"],
                "fields": []
            }
        
        if not current_section:
            current_section = {
                "section": "Main Section",
                "page": field["page"],
                "fields": []
            }
        
        # Skip titles from fields list
        if field["type"] == "title":
            last_y = y_pos
            continue
        
        # Convert field to UI component
        ui_field = convert_field_to_ui(field)
        if ui_field:
            current_section["fields"].append(ui_field)
        
        last_y = y_pos
    
    # Add last section
    if current_section and current_section["fields"]:
        sections.append(current_section)
    
    # Group checkboxes into dropdowns
    sections = group_checkboxes_to_dropdowns(sections)
    
    return {"form_schema": sections}


def convert_field_to_ui(field: Dict) -> Optional[Dict]:
    """Convert OCR field to UI component"""
    field_type = field["type"]
    
    if field_type == "checkbox":
        return {
            "id": field["id"],
            "type": "checkbox",
            "title": field["label"],
            "value": False
        }
    
    elif field_type == "text_field":
        return {
            "id": field["id"],
            "type": "text_field",
            "title": field["label"].rstrip(':'),
            "placeholder": f"Enter {field['label'].rstrip(':').lower()}"
        }
    
    elif field_type == "table_cell":
        return {
            "id": field["id"],
            "type": "text_field",
            "title": field["label"],
            "row": field.get("row"),
            "col": field.get("col")
        }
    
    elif field_type == "label":
        # Skip pure labels
        return None
    
    return None


def group_checkboxes_to_dropdowns(sections: List[Dict]) -> List[Dict]:
    """
    Convert groups of checkboxes into dropdown components
    """
    for section in sections:
        fields = section["fields"]
        grouped_fields = []
        checkbox_group = []
        
        for field in fields:
            if field["type"] == "checkbox":
                checkbox_group.append(field)
            else:
                # Flush checkbox group if we have multiple
                if len(checkbox_group) > 1:
                    grouped_fields.append({
                        "id": f"dropdown_{checkbox_group[0]['id']}",
                        "type": "dropdown",
                        "title": section["section"],
                        "options": [cb["title"] for cb in checkbox_group]
                    })
                    checkbox_group = []
                elif len(checkbox_group) == 1:
                    grouped_fields.append(checkbox_group[0])
                    checkbox_group = []
                
                grouped_fields.append(field)
        
        # Flush remaining checkboxes
        if len(checkbox_group) > 1:
            grouped_fields.append({
                "id": f"dropdown_{checkbox_group[0]['id']}",
                "type": "dropdown",
                "title": section["section"],
                "options": [cb["title"] for cb in checkbox_group]
            })
        elif len(checkbox_group) == 1:
            grouped_fields.append(checkbox_group[0])
        
        section["fields"] = grouped_fields
    
    return sections


def process_ocr_on_image(image_path: str, page_num: int = 1, page_width: float = 0, page_height: float = 0) -> List[Dict]:
    """Process OCR on a single image and return structured field data"""
    result = ocr.ocr(image_path, cls=True)
    
    if not result or not result[0]:
        return []
    
    fields = []
    field_counter = 1
    
    for line in result[0]:
        box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text_info = line[1]  # (text, confidence)
        
        text = text_info[0]
        confidence = float(text_info[1])
        
        # Convert box to flat format [x1,y1,x2,y2,x3,y3,x4,y4]
        bbox = [coord for point in box for coord in point]
        
        # Classify field type
        field_type = classify_field_type(text, bbox)
        
        field_id = f"field_{page_num:03d}_{field_counter:03d}"
        
        field_data = {
            "id": field_id,
            "type": field_type,
            "label": text,
            "bbox": bbox,
            "page": page_num,
            "confidence": confidence,
            "value": False if field_type == "checkbox" else ""
        }
        
        # Add table cell metadata if applicable
        if field_type == "table_cell":
            field_data["row"] = None  # Would need table detection algorithm
            field_data["col"] = None
        
        fields.append(field_data)
        field_counter += 1
    
    return fields


def flatten_ui_schema_to_components(all_fields: List[Dict]) -> List[Dict]:
    """
    Convert OCR fields to flat components array for React Native
    Returns: [{ id, type, label, value, bbox, page }, ...]
    """
    components = []
    
    for field in all_fields:
        field_type = field["type"]
        
        # Skip non-fillable fields
        if field_type in ["title", "label", "non_fillable"]:
            continue
        
        component = {
            "id": field["id"],
            "label": field["label"],
            "bbox": field["bbox"],
            "page": field["page"]
        }
        
        # Map field types to component types
        if field_type == "checkbox":
            component["type"] = "checkbox"
            component["value"] = False
        elif field_type == "text_field":
            component["type"] = "input"
            component["value"] = ""
        elif field_type == "table_cell":
            component["type"] = "input"
            component["value"] = ""
        else:
            continue
        
        components.append(component)
    
    return components


def create_field_map(all_fields: List[Dict]) -> Dict[str, Dict]:
    """
    Create fieldMap for overlay: { field_id: { bbox, page } }
    """
    field_map = {}
    
    for field in all_fields:
        if field["type"] not in ["title", "label", "non_fillable"]:
            field_map[field["id"]] = {
                "bbox": field["bbox"],
                "page": field["page"],
                "type": field["type"]
            }
    
    return field_map


@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """
    Main OCR endpoint - accepts PDF or images
    Returns: UI schema, OCR blocks, PDF metadata, field types
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        contents = await file.read()
        
        # Detect actual file type from content (magic bytes)
        mime = magic.from_buffer(contents, mime=True)
        
        # Determine correct extension based on actual content
        if mime == 'application/pdf':
            file_ext = '.pdf'
        elif mime in ['image/jpeg', 'image/jpg']:
            file_ext = '.jpg'
        elif mime == 'image/png':
            file_ext = '.png'
        elif mime in ['image/bmp', 'image/x-ms-bmp']:
            file_ext = '.bmp'
        elif mime in ['image/tiff', 'image/x-tiff']:
            file_ext = '.tiff'
        else:
            # Fallback to filename extension
            file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Save uploaded file with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        all_fields = []
        page_metadata = []
        
        try:
            # Handle PDF
            if file_ext == '.pdf':
                images = pdf_to_images(tmp_path)
                
                for img_data in images:
                    page_fields = process_ocr_on_image(
                        img_data["path"], 
                        img_data["page"],
                        img_data["width"],
                        img_data["height"]
                    )
                    all_fields.extend(page_fields)
                    
                    page_metadata.append({
                        "page": img_data["page"],
                        "width": img_data["width"],
                        "height": img_data["height"]
                    })
                    
                    # Cleanup temp image
                    os.unlink(img_data["path"])
            
            # Handle images
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # Get image dimensions
                img = Image.open(tmp_path)
                width, height = img.size
                
                page_fields = process_ocr_on_image(tmp_path, 1, width, height)
                all_fields.extend(page_fields)
                
                page_metadata.append({
                    "page": 1,
                    "width": width,
                    "height": height
                })
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or image files.")
            
            # Generate UI schema
            ui_schema = generate_ui_schema(all_fields)
            
            return JSONResponse(content={
                "success": True,
                "ui_schema": ui_schema,
                "ocr_blocks": all_fields,
                "pdf_metadata": {
                    "pages": page_metadata,
                    "total_pages": len(page_metadata),
                    "total_fields": len(all_fields)
                },
                "field_types": {
                    "checkbox": len([f for f in all_fields if f["type"] == "checkbox"]),
                    "text_field": len([f for f in all_fields if f["type"] == "text_field"]),
                    "table_cell": len([f for f in all_fields if f["type"] == "table_cell"]),
                    "title": len([f for f in all_fields if f["type"] == "title"]),
                    "label": len([f for f in all_fields if f["type"] == "label"]),
                    "non_fillable": len([f for f in all_fields if f["type"] == "non_fillable"])
                }
            })
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.post("/ui/generate")
async def ui_generate_endpoint(file: UploadFile = File(...)):
    """
    React Native compatible endpoint - mirror of /ocr
    Returns flat components array for easy rendering
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        contents = await file.read()
        
        # Detect actual file type from content (magic bytes)
        mime = magic.from_buffer(contents, mime=True)
        
        # Determine correct extension based on actual content
        if mime == 'application/pdf':
            file_ext = '.pdf'
        elif mime in ['image/jpeg', 'image/jpg']:
            file_ext = '.jpg'
        elif mime == 'image/png':
            file_ext = '.png'
        elif mime in ['image/bmp', 'image/x-ms-bmp']:
            file_ext = '.bmp'
        elif mime in ['image/tiff', 'image/x-tiff']:
            file_ext = '.tiff'
        else:
            # Fallback to filename extension
            file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Save uploaded file with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        all_fields = []
        page_metadata = []
        
        try:
            # Handle PDF
            if file_ext == '.pdf':
                images = pdf_to_images(tmp_path)
                
                for img_data in images:
                    page_fields = process_ocr_on_image(
                        img_data["path"], 
                        img_data["page"],
                        img_data["width"],
                        img_data["height"]
                    )
                    all_fields.extend(page_fields)
                    
                    page_metadata.append({
                        "page": img_data["page"],
                        "width": img_data["width"],
                        "height": img_data["height"]
                    })
                    
                    # Cleanup temp image
                    os.unlink(img_data["path"])
            
            # Handle images
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # Get image dimensions
                img = Image.open(tmp_path)
                width, height = img.size
                
                page_fields = process_ocr_on_image(tmp_path, 1, width, height)
                all_fields.extend(page_fields)
                
                page_metadata.append({
                    "page": 1,
                    "width": width,
                    "height": height
                })
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or image files.")
            
            # Convert to flat components array
            components = flatten_ui_schema_to_components(all_fields)
            
            # Create field map for overlay
            field_map = create_field_map(all_fields)
            
            return JSONResponse(content={
                "success": True,
                "components": components,
                "fieldMap": field_map,
                "metadata": {
                    "pages": page_metadata,
                    "total_pages": len(page_metadata),
                    "total_fields": len(components)
                }
            })
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.post("/overlay")
async def overlay_pdf(
    file: UploadFile = File(...),
    filled_data: str = Form(...)
):
    """
    Overlay filled form data onto original PDF
    
    Input:
    - file: Original PDF
    - filled_data: JSON string with { documentId, values: { field_id: value } }
    
    Returns: Modified PDF with filled data
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        # Parse filled data
        try:
            data = json.loads(filled_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in filled_data")
        
        # Read PDF
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_in:
            tmp_in.write(contents)
            tmp_in_path = tmp_in.name
        
        # Create output PDF
        output_path = tempfile.mktemp(suffix='_filled.pdf')
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(tmp_in_path)
            
            # Get values and fieldMap
            values = data.get("values", {})
            field_map = data.get("fieldMap", {})
            
            print(f"DEBUG: Processing {len(values)} values")
            print(f"DEBUG: Field map has {len(field_map)} fields")
            print(f"DEBUG: Values: {values}")
            
            # Process each field
            for field_id, value in values.items():
                # Skip only if value is None or empty string, but allow False for checkboxes
                if (value is None or value == "") and value is not False:
                    continue
                    
                if field_id not in field_map:
                    print(f"DEBUG: Field {field_id} not in field_map")
                    continue
                
                print(f"DEBUG: Processing field {field_id} with value {value}")
                
                field_info = field_map[field_id]
                page_num = field_info.get("page", 1) - 1  # 0-indexed
                
                if page_num >= len(doc):
                    print(f"DEBUG: Page {page_num} out of range")
                    continue
                
                page = doc[page_num]
                bbox = field_info.get("bbox", [])
                field_type = field_info.get("type", "text_field")
                
                if len(bbox) != 8:
                    print(f"DEBUG: Invalid bbox length: {len(bbox)}")
                    continue
                
                # OCR was done at 2x scale, so divide coordinates by 2
                # Convert bbox [x1,y1,x2,y2,x3,y3,x4,y4] to rect
                x1, y1 = min(bbox[0], bbox[6]) / 2, min(bbox[1], bbox[3]) / 2
                x2, y2 = max(bbox[2], bbox[4]) / 2, max(bbox[5], bbox[7]) / 2
                rect = fitz.Rect(x1, y1, x2, y2)
                
                print(f"DEBUG: Drawing at rect {rect} on page {page_num}")
                
                # Handle different field types
                if field_type == "checkbox":
                    if value is True or str(value).lower() in ['true', '1', 'yes']:
                        # Draw checkmark
                        draw_checkmark(page, rect)
                else:
                    # Insert text
                    insert_text_in_box(page, rect, str(value))
            
            # Save modified PDF
            doc.save(output_path)
            doc.close()
            
            # Return file
            return FileResponse(
                output_path,
                media_type="application/pdf",
                filename=f"filled_{file.filename}",
                background=None
            )
        
        finally:
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            # Note: output_path will be cleaned up by FileResponse
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF overlay failed: {str(e)}")


def draw_checkmark(page: fitz.Page, rect: fitz.Rect):
    """Draw a checkmark in the given rectangle"""
    # Calculate checkmark points
    x1, y1 = rect.x0 + rect.width * 0.2, rect.y0 + rect.height * 0.5
    x2, y2 = rect.x0 + rect.width * 0.4, rect.y0 + rect.height * 0.7
    x3, y3 = rect.x0 + rect.width * 0.8, rect.y0 + rect.height * 0.3
    
    # Draw checkmark
    shape = page.new_shape()
    shape.draw_polyline([(x1, y1), (x2, y2), (x3, y3)])
    shape.finish(color=(0, 0, 0), width=1.5)
    shape.commit()


def insert_text_in_box(page: fitz.Page, rect: fitz.Rect, text: str):
    """Insert text into a box, scaling to fit"""
    if not text:
        return
    
    # Start with reasonable font size
    font_size = 10
    font_name = "helv"  # Helvetica
    
    # Try to fit text in box
    while font_size > 6:
        text_width = fitz.get_text_length(text, fontname=font_name, fontsize=font_size)
        if text_width <= rect.width * 0.95:
            break
        font_size -= 0.5
    
    # Calculate vertical center
    text_y = rect.y0 + (rect.height + font_size) / 2
    
    # Insert text
    page.insert_text(
        (rect.x0 + 2, text_y),
        text,
        fontsize=font_size,
        fontname=font_name,
        color=(0, 0, 0)
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
