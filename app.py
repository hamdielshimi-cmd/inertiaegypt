import streamlit as st
import pandas as pd
import io
import os
import re
import requests
import unicodedata
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import fitz  # PyMuPDF for image extraction

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="Universal Offer Letter Generator",
    page_icon="🏠",
    layout="wide"
)

# Colors
COLOR_PRIMARY = "#2C3E50"
COLOR_ACCENT = "#D4A373"
COLOR_BG = "#F9F7F2"

# Logo URL
LOGO_URL = "https://ik.imagekit.io/xtj3m9hth/image.png"

# CSS Styling
st.markdown(f"""
<style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1 {{ color: {COLOR_PRIMARY}; font-family: 'Helvetica', sans-serif; }}
    .stButton>button {{ background-color: {COLOR_PRIMARY}; color: white; border-radius: 5px; }}
    .stButton>button:hover {{ background-color: {COLOR_ACCENT}; color: {COLOR_PRIMARY}; }}
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def download_logo(url):
    """Downloads the logo image and returns it as a BytesIO object."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.warning(f"Could not download logo: {e}")
        return None

def normalize_text(text):
    """Advanced text normalization for searching."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text.lower().strip()

def extract_unit_types_from_pdf(pdf_bytes):
    """
    Auto-detect unit/villa types from PDF brochure.
    Returns a list of unique unit type names.
    """
    unit_types = set()
    keywords = ['villa', 'apartment', 'chalet', 'townhouse', 'twin house', 
                'residence', 'penthouse', 'duplex', 'studio']
    
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line_lower = line.lower()
                        # Look for patterns like "The Una Villa", "Two Bedroom Apartment", etc.
                        for keyword in keywords:
                            if keyword in line_lower:
                                # Clean up the line
                                cleaned = re.sub(r'[^\w\s]', '', line).strip()
                                if 10 < len(cleaned) < 80:  # Reasonable length
                                    unit_types.add(line.strip())
                                    break
    except Exception as e:
        st.error(f"Error extracting unit types: {e}")
    
    return sorted(list(unit_types))[:20]  # Limit to 20 most common

def extract_images_from_pdf_pages(pdf_bytes, page_indices, max_images=6):
    """
    Extract images from specific PDF pages.
    Returns list of PIL Image objects.
    """
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_idx in page_indices:
            if page_idx >= len(doc):
                continue
                
            page = doc[page_idx]
            image_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(image_list):
                if len(images) >= max_images:
                    break
                    
                try:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    pil_image = PILImage.open(BytesIO(image_bytes))
                    
                    # Filter out tiny images (likely logos/icons)
                    if pil_image.width > 200 and pil_image.height > 200:
                        images.append(pil_image)
                        
                except Exception:
                    continue
            
            if len(images) >= max_images:
                break
        
        doc.close()
        
    except Exception as e:
        st.error(f"Error extracting images: {e}")
    
    return images[:max_images]

def find_pages_in_pdf(pdf_bytes, search_term, limit=4):
    """Find pages containing search term."""
    found_pages = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            search_clean = normalize_text(search_term)
            
            for i, page in enumerate(pdf.pages):
                if len(found_pages) >= limit:
                    break
                
                text = page.extract_text()
                if text:
                    page_clean = normalize_text(text)
                    if search_clean in page_clean:
                        found_pages.append(i)
    except Exception as e:
        st.error(f"Error searching PDF: {e}")
    
    return found_pages

def generate_compact_offer_pdf(unit_data, images, logo_bytes):
    """
    Generate a compact, professional 3-4 page offer letter with images.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # --- CUSTOM STYLES ---
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor(COLOR_PRIMARY),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_subtitle = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor(COLOR_PRIMARY),
        alignment=TA_CENTER,
        spaceBefore=5,
        spaceAfter=20
    )
    
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor(COLOR_ACCENT),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    style_body = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=11,
        leading=15,
        spaceAfter=10
    )
    
    style_highlight = ParagraphStyle(
        'Highlight',
        parent=styles['BodyText'],
        fontSize=13,
        leading=18,
        textColor=colors.HexColor(COLOR_PRIMARY),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=15
    )
    
    # ==================== PAGE 1: COVER ====================
    if logo_bytes:
        try:
            img_reader = ImageReader(logo_bytes)
            img_width = 3 * inch
            img_height = (img_reader.getSize()[1] / img_reader.getSize()[0]) * img_width
            elements.append(Image(logo_bytes, width=img_width, height=img_height, hAlign='CENTER'))
            elements.append(Spacer(1, 0.4*inch))
        except:
            pass
    
    elements.append(Paragraph("RESERVATION & OFFER LETTER", style_title))
    elements.append(Paragraph("Exclusive Property Offer", style_subtitle))
    elements.append(Spacer(1, 0.6*inch))
    
    # Unit highlight box
    highlight_text = f"""
    <b>Unit Reference: {unit_data.get('Unit Number', 'N/A')}</b><br/>
    {unit_data.get('Dev Name', 'N/A')}
    """
    elements.append(Paragraph(highlight_text, style_highlight))
    
    elements.append(Spacer(1, 0.8*inch))
    
    # Date and company info
    current_date = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Date:</b> {current_date}", style_body))
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("Inertia Properties", style_body))
    elements.append(Paragraph("www.inertiaegypt.com", style_body))
    
    elements.append(PageBreak())
    
    # ==================== PAGE 2: UNIT DETAILS ====================
    elements.append(Paragraph("UNIT SPECIFICATIONS", style_title))
    elements.append(Spacer(1, 0.2*inch))
    
    # Quick summary
    summary = f"""
    {unit_data.get('Dev Name', 'N/A')} • 
    BUA {unit_data.get('BUA with Terraces', 'N/A')} m² • 
    {unit_data.get('No.Bedrooms', 'N/A')} Bedrooms • 
    Price: {unit_data.get('Final Price', 'N/A')} EGP
    """
    elements.append(Paragraph(summary, style_highlight))
    elements.append(HRFlowable(width="70%", thickness=2, color=colors.HexColor(COLOR_ACCENT), spaceAfter=20))
    
    # Details table
    table_data = [
        ['Unit Number', unit_data.get('Unit Number', 'N/A')],
        ['Development', unit_data.get('Dev Name', 'N/A')],
        ['Type', f"{unit_data.get('Type', 'N/A')} - {unit_data.get('Type 4', 'N/A')}"],
        ['Floor', unit_data.get('Floor', 'N/A')],
        ['Bedrooms', str(unit_data.get('No.Bedrooms', 'N/A'))],
        ['BUA with Terraces', f"{unit_data.get('BUA with Terraces', 'N/A')} m²"],
        ['Garden Area', f"{unit_data.get('Garden', 'N/A')} m²"],
        ['Final Price', f"{unit_data.get('Final Price', 'N/A')} EGP"],
        ['Maid Room', unit_data.get('Maid Room', 'N/A')],
        ['Delivery Date', unit_data.get('Delivery Date', 'N/A')],
        ['Status', unit_data.get('Status', 'N/A')],
    ]
    
    t = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COLOR_PRIMARY)),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment terms
    elements.append(Paragraph("PAYMENT TERMS", style_section))
    terms_text = """
    • 5% Down Payment required at reservation<br/>
    • Flexible payment plans available<br/>
    • Delivery as per schedule: {delivery}<br/>
    • All prices subject to maintenance charges and applicable taxes
    """.format(delivery=unit_data.get('Delivery Date', 'TBD'))
    
    elements.append(Paragraph(terms_text, style_body))
    elements.append(Spacer(1, 0.2*inch))
    
    # Validity
    elements.append(Paragraph("<i>This offer is valid for 14 days from the date of issue.</i>", style_body))
    
    elements.append(PageBreak())
    
    # ==================== PAGE 3-4: PROPERTY IMAGES ====================
    if images:
        elements.append(Paragraph("PROPERTY VISUALS", style_title))
        elements.append(Spacer(1, 0.3*inch))
        
        # Arrange images in a grid (2 per row)
        for i in range(0, len(images), 2):
            row_images = images[i:i+2]
            image_elements = []
            
            for img in row_images:
                # Resize image to fit nicely
                max_width = 3.2 * inch
                max_height = 2.4 * inch
                
                # Calculate aspect ratio
                aspect = img.width / img.height
                if aspect > (max_width / max_height):
                    img_width = max_width
                    img_height = max_width / aspect
                else:
                    img_height = max_height
                    img_width = max_height * aspect
                
                # Save to BytesIO
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                image_elements.append(Image(img_buffer, width=img_width, height=img_height))
            
            # Create table for side-by-side layout
            if len(image_elements) == 2:
                img_table = Table([image_elements], colWidths=[3.5*inch, 3.5*inch])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(img_table)
            else:
                elements.append(image_elements[0])
            
            elements.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def load_inventory_data(file):
    """
    Load inventory data from CSV or Excel file with proper encoding handling.
    Supports: .csv, .xlsx, .xls
    Returns the dataframe or None if error.
    """
    try:
        # Get file extension
        file_name = file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Reset file pointer to beginning
        file.seek(0)
        
        # Handle Excel files
        if file_ext in ['.xlsx', '.xls']:
            try:
                df = pd.read_excel(file, engine='openpyxl' if file_ext == '.xlsx' else None)
                df.columns = df.columns.str.strip()
                return df
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                return None
        
        # Handle CSV files
        elif file_ext == '.csv':
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings_to_try:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding=encoding)
                    df.columns = df.columns.str.strip()
                    return df
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            
            st.error("Could not read CSV file with any standard encoding.")
            return None
        
        else:
            st.error(f"Unsupported file format: {file_ext}. Please upload .csv, .xlsx, or .xls file.")
            return None
        
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# --- MAIN APPLICATION ---

def main():
    st.title("🏠 Universal Offer Letter Generator")
    st.markdown("*Professional offer letters for any property project*")
    st.markdown("---")
    
    # === STEP 1: FILE UPLOADS ===
    col1, col2 = st.columns(2)
    
    with col1:
        inventory_file = st.file_uploader(
            "📊 Upload Inventory File", 
            type=['csv', 'xlsx', 'xls'], 
            help="Upload your unit inventory (CSV or Excel)"
        )
    
    with col2:
        pdf_file = st.file_uploader(
            "📄 Upload Project E-Brochure PDF", 
            type=['pdf'], 
            help="Upload the project brochure"
        )
    
    st.markdown("---")
    
    # === STEP 2: AUTO-DETECT UNIT TYPES ===
    available_unit_types = []
    if pdf_file:
        with st.spinner("🔍 Analyzing brochure for unit types..."):
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            available_unit_types = extract_unit_types_from_pdf(pdf_bytes)
            
            if available_unit_types:
                with st.expander("📋 Detected Unit Types from Brochure", expanded=False):
                    for unit_type in available_unit_types[:10]:
                        st.write(f"• {unit_type}")
    
    # === STEP 3: UNIT SELECTION ===
    st.markdown("### 🎯 Select Unit Details")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        unit_input = st.text_input(
            "Unit Number",
            placeholder="e.g., JF11-VSV-001",
            help="Enter the exact unit number from your inventory file"
        )
    
    with col_b:
        # Smart selection: dropdown if types detected, otherwise text input
        if available_unit_types:
            search_term = st.selectbox(
                "Unit Type / Dev Name",
                options=[""] + available_unit_types,
                help="Select the unit type from detected options"
            )
        else:
            search_term = st.text_input(
                "Unit Type / Dev Name",
                placeholder="e.g., The Una Villa",
                help="Enter the unit/villa type name from the brochure"
            )
    
    # === PREVIEW UNIT DATA ===
    if inventory_file and unit_input:
        df = load_inventory_data(inventory_file)
        if df is not None:
            unit_row = df[df['Unit Number'].astype(str).str.strip() == unit_input.strip()]
            
            if not unit_row.empty:
                unit_data = unit_row.iloc[0].to_dict()
                
                with st.expander("✅ Unit Data Preview", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Dev Name", unit_data.get('Dev Name', 'N/A'))
                        st.metric("Bedrooms", unit_data.get('No.Bedrooms', 'N/A'))
                    with col2:
                        st.metric("BUA", f"{unit_data.get('BUA with Terraces', 'N/A')} m²")
                        st.metric("Floor", unit_data.get('Floor', 'N/A'))
                    with col3:
                        st.metric("Price", unit_data.get('Final Price', 'N/A'))
                        st.metric("Status", unit_data.get('Status', 'N/A'))
            else:
                st.error(f"❌ Unit number '{unit_input}' not found in inventory file.")
    
    st.markdown("---")
    
    # === GENERATE BUTTON ===
    if st.button("🚀 Generate Professional Offer Letter", type="primary", use_container_width=True):
        if not inventory_file or not pdf_file:
            st.error("⚠️ Please upload both inventory file and PDF brochure.")
            st.stop()
        
        if not unit_input or not search_term:
            st.error("⚠️ Please enter both Unit Number and Unit Type.")
            st.stop()
        
        # === PROCESSING ===
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 1. Logo
        status.text("📥 Fetching logo...")
        progress_bar.progress(10)
        logo_bytes = download_logo(LOGO_URL)
        
        # 2. Inventory Data
        status.text("📊 Loading unit data...")
        progress_bar.progress(25)
        df = load_inventory_data(inventory_file)
        if df is None:
            st.error("Failed to load inventory data.")
            st.stop()
        
        unit_row = df[df['Unit Number'].astype(str).str.strip() == unit_input.strip()]
        if unit_row.empty:
            st.error(f"Unit '{unit_input}' not found in inventory.")
            st.stop()
        
        unit_data = unit_row.iloc[0].to_dict()
        
        # 3. Find pages
        status.text(f"🔍 Searching brochure for '{search_term}'...")
        progress_bar.progress(40)
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        found_pages = find_pages_in_pdf(pdf_bytes, search_term, limit=4)
        
        if not found_pages:
            st.warning(f"⚠️ No pages found for '{search_term}'. Generating text-only offer.")
            images = []
        else:
            st.success(f"✅ Found {len(found_pages)} relevant pages")
            
            # 4. Extract images
            status.text("🖼️ Extracting property images...")
            progress_bar.progress(60)
            images = extract_images_from_pdf_pages(pdf_bytes, found_pages, max_images=6)
            st.info(f"📸 Extracted {len(images)} images from brochure")
        
        # 5. Generate PDF
        status.text("📝 Generating offer letter...")
        progress_bar.progress(80)
        
        try:
            final_pdf = generate_compact_offer_pdf(unit_data, images, logo_bytes)
            
            progress_bar.progress(100)
            status.text("✅ Complete!")
            
            st.success("🎉 Offer Letter Generated Successfully!")
            
            # Download
            st.download_button(
                label="📥 Download Offer Letter PDF",
                data=final_pdf,
                file_name=f"Offer_Letter_{unit_input}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Error generating PDF: {e}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
