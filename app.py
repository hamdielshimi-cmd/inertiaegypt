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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF for image extraction

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="Inertia Offer Letter Generator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inertia Brand Colors
COLOR_PRIMARY = "#2A3932"  # Deep Slate
COLOR_ACCENT = "#07141D"   # Dark Navy (changed from green)
COLOR_BLUE = "#4A90E2"     # Sea Blue
COLOR_BG = "#FFFFFF"       # White
COLOR_TEXT = "#07141D"     # Dark Navy

# Logo URL
LOGO_URL = "https://ik.imagekit.io/xtj3m9hth/image.png"

# Enhanced CSS Styling with Animated Construction Background
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Playfair+Display:wght@400;700&display=swap');
    
    /* Main App Styling */
    .stApp {{
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        font-family: 'Inter', sans-serif;
    }}
    
    /* Animated Grid Background */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(90deg, rgba(7, 20, 29, 0.05) 1px, transparent 1px),
            linear-gradient(rgba(7, 20, 29, 0.05) 1px, transparent 1px);
        background-size: 60px 60px;
        animation: gridMove 25s linear infinite;
        pointer-events: none;
        z-index: 0;
    }}
    
    @keyframes gridMove {{
        0% {{ transform: translate(0, 0); }}
        100% {{ transform: translate(60px, 60px); }}
    }}
    
    /* Content Container */
    .block-container {{
        position: relative;
        z-index: 1;
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}
    
    /* Typography */
    h1 {{
        color: {COLOR_PRIMARY} !important;
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    h2 {{
        color: {COLOR_TEXT} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }}
    
    h3 {{
        color: {COLOR_PRIMARY} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
    }}
    
    /* Subtitle */
    .subtitle {{
        color: {COLOR_ACCENT};
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 300;
        text-align: center;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 3rem;
    }}
    
    /* Cards and Sections */
    .stApp section[data-testid="stFileUploader"],
    .stApp .element-container {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(42, 57, 50, 0.08);
        border: 1px solid rgba(7, 20, 29, 0.15);
        margin-bottom: 1rem;
    }}
    
    /* File Uploader */
    .stFileUploader {{
        background: linear-gradient(135deg, rgba(7, 20, 29, 0.05), rgba(74, 144, 226, 0.05)) !important;
        border: 2px dashed {COLOR_ACCENT} !important;
        border-radius: 12px !important;
        padding: 2rem !important;
    }}
    
    .stFileUploader label {{
        color: {COLOR_PRIMARY} !important;
        font-weight: 600 !important;
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        border: 2px solid {COLOR_ACCENT} !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: {COLOR_PRIMARY} !important;
        box-shadow: 0 0 0 2px rgba(7, 20, 29, 0.2) !important;
    }}
    
    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {{
        color: {COLOR_PRIMARY} !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_ACCENT} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(7, 20, 29, 0.4) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(7, 20, 29, 0.6) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Download Button */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLOR_BLUE} 0%, {COLOR_ACCENT} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {COLOR_PRIMARY} !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLOR_TEXT} !important;
        font-weight: 600 !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background: linear-gradient(90deg, rgba(7, 20, 29, 0.1), transparent) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: {COLOR_PRIMARY} !important;
    }}
    
    /* Progress Bar */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {COLOR_ACCENT}, {COLOR_BLUE}) !important;
    }}
    
    /* Divider */
    hr {{
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent, {COLOR_ACCENT}, transparent) !important;
        margin: 2.5rem 0 !important;
    }}
    
    /* Success/Error/Warning Messages */
    .stSuccess, .stError, .stWarning, .stInfo {{
        border-radius: 8px !important;
        padding: 1rem !important;
    }}
    
    /* Building Animation at Bottom */
    .construction-buildings {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 120px;
        pointer-events: none;
        z-index: 0;
        display: flex;
        align-items: flex-end;
        justify-content: space-around;
        padding: 0 5%;
        opacity: 0.08;
    }}
    
    .building {{
        width: 40px;
        background: linear-gradient(to top, rgba(42, 57, 50, 0.6), rgba(7, 20, 29, 0.8));
        border-radius: 3px 3px 0 0;
        animation: buildingRise 2.5s ease-out;
    }}
    
    .building:nth-child(1) {{ height: 80px; animation-delay: 0s; }}
    .building:nth-child(2) {{ height: 60px; animation-delay: 0.3s; }}
    .building:nth-child(3) {{ height: 100px; animation-delay: 0.6s; }}
    .building:nth-child(4) {{ height: 70px; animation-delay: 0.9s; }}
    .building:nth-child(5) {{ height: 90px; animation-delay: 1.2s; }}
    
    @keyframes buildingRise {{
        from {{
            transform: translateY(100%);
            opacity: 0;
        }}
        to {{
            transform: translateY(0);
            opacity: 1;
        }}
    }}
    
    /* Suggestion Box */
    .suggestion-box {{
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.1), rgba(7, 20, 29, 0.05));
        border: 2px solid {COLOR_ACCENT};
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }}
    
    .suggestion-item {{
        background: white;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        border-left: 3px solid {COLOR_BLUE};
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .suggestion-item:hover {{
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
</style>

<!-- Construction Buildings Animation -->
<div class="construction-buildings">
    <div class="building"></div>
    <div class="building"></div>
    <div class="building"></div>
    <div class="building"></div>
    <div class="building"></div>
</div>
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

def suggest_units_based_on_request(df, customer_request, max_suggestions=5):
    """
    AI-powered unit suggestions based on customer request.
    Analyzes the request and matches with inventory.
    """
    if not customer_request or df is None or df.empty:
        return []
    
    request_lower = customer_request.lower()
    suggestions = []
    
    # Extract keywords from request
    bedroom_match = re.search(r'(\d+)\s*bedroom', request_lower)
    bedrooms_needed = int(bedroom_match.group(1)) if bedroom_match else None
    
    # Keywords for features
    garden_keywords = ['garden', 'outdoor', 'green', 'terrace']
    view_keywords = ['view', 'sea', 'ocean', 'lagoon', 'golf', 'landscape']
    floor_keywords = ['ground', 'first', 'top', 'penthouse']
    
    has_garden_preference = any(kw in request_lower for kw in garden_keywords)
    has_view_preference = any(kw in request_lower for kw in view_keywords)
    
    # Score each unit
    for idx, row in df.iterrows():
        score = 0
        reasons = []
        
        # Bedroom match (highest priority)
        if bedrooms_needed and 'No.Bedrooms' in row:
            try:
                unit_bedrooms = int(row['No.Bedrooms'])
                if unit_bedrooms == bedrooms_needed:
                    score += 50
                    reasons.append(f"{bedrooms_needed} bedrooms")
                elif abs(unit_bedrooms - bedrooms_needed) == 1:
                    score += 25
            except:
                pass
        
        # Garden preference
        if has_garden_preference and 'Garden' in row:
            try:
                garden_area = float(str(row['Garden']).replace('m²', '').strip())
                if garden_area > 0:
                    score += 30
                    reasons.append(f"Garden {garden_area}m²")
            except:
                pass
        
        # View/location preference
        if has_view_preference:
            dev_name = str(row.get('Dev Name', '')).lower()
            type_info = str(row.get('Type', '')).lower()
            if any(kw in dev_name or kw in type_info for kw in view_keywords):
                score += 20
                reasons.append("Premium location")
        
        # Status - Available units priority
        if 'Status' in row and str(row['Status']).lower() in ['available', 'ready']:
            score += 15
            reasons.append("Available now")
        
        # Add to suggestions if score is good
        if score > 0:
            suggestions.append({
                'unit_number': row.get('Unit Number', 'N/A'),
                'dev_name': row.get('Dev Name', 'N/A'),
                'bedrooms': row.get('No.Bedrooms', 'N/A'),
                'area': row.get('BUA with Terraces', 'N/A'),
                'price': row.get('Final Price', 'N/A'),
                'score': score,
                'reasons': ', '.join(reasons)
            })
    
    # Sort by score and return top suggestions
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions[:max_suggestions]

def extract_unit_types_from_pdf(pdf_bytes):
    """Auto-detect unit/villa types from PDF brochure."""
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
                        for keyword in keywords:
                            if keyword in line_lower:
                                cleaned = re.sub(r'[^\w\s]', '', line).strip()
                                if 10 < len(cleaned) < 80:
                                    unit_types.add(line.strip())
                                    break
    except Exception as e:
        st.error(f"Error extracting unit types: {e}")
    
    return sorted(list(unit_types))[:20]

def extract_images_from_pdf_pages(pdf_bytes, page_indices, max_images=4):
    """Extract images from specific PDF pages."""
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
                    
                    pil_image = PILImage.open(BytesIO(image_bytes))
                    
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

class ProfessionalLetterhead(canvas.Canvas):
    """Custom canvas for professional letterhead template"""
    
    def __init__(self, *args, logo_bytes=None, customer_data=None, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.logo_bytes = logo_bytes
        self.customer_data = customer_data or {}
        self.pages = 0
        
    def showPage(self):
        self.pages += 1
        self._add_letterhead()
        canvas.Canvas.showPage(self)
        
    def save(self):
        self._add_letterhead()
        canvas.Canvas.save(self)
        
    def _add_letterhead(self):
        """Add header and footer to each page"""
        page_width, page_height = A4
        
        # --- HEADER ---
        # Decorative top line
        self.setStrokeColor(colors.HexColor("#07141D"))
        self.setLineWidth(3)
        self.line(30, page_height - 30, page_width - 30, page_height - 30)
        
        # Sales Director Info (LEFT side - swapped with logo)
        self.setFont("Helvetica-Bold", 11)
        self.setFillColor(colors.HexColor("#2A3932"))
        self.drawString(50, page_height - 55, "Karim Khaled")
        
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#07141D"))
        self.drawString(50, page_height - 70, "Sales Director")
        
        # Date
        current_date = datetime.now().strftime("%B %d, %Y")
        self.setFont("Helvetica", 9)
        self.drawString(50, page_height - 85, current_date)
        
        # Logo (RIGHT side - swapped with name)
        if self.logo_bytes:
            try:
                self.logo_bytes.seek(0)
                img_reader = ImageReader(self.logo_bytes)
                self.drawImage(img_reader, page_width - 200, page_height - 100, 
                             width=1.5*inch, height=0.5*inch, 
                             preserveAspectRatio=True, mask='auto')
            except:
                pass
        
        # Subtle header border
        self.setStrokeColor(colors.HexColor("#E5E5E5"))
        self.setLineWidth(0.5)
        self.line(30, page_height - 110, page_width - 30, page_height - 110)
        
        # --- FOOTER ---
        footer_y = 80
        
        # Decorative bottom line
        self.setStrokeColor(colors.HexColor("#07141D"))
        self.setLineWidth(2)
        self.line(30, footer_y + 45, page_width - 30, footer_y + 45)
        
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#2A3932"))
        
        # Website
        self.drawCentredString(page_width/2, footer_y + 30, "inertiaegypt.com")
        
        # Address
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#07141D"))
        address = "Building 06, Cairo West Business Park, KM 22, Cairo-Alexandria Desert Road, Giza"
        self.drawCentredString(page_width/2, footer_y + 18, address)
        
        # Hotline
        self.setFont("Helvetica-Bold", 7)
        self.drawCentredString(page_width/2, footer_y + 8, "Customer Service & Hotline: 19655")
        
        # Contact Numbers
        self.setFont("Helvetica", 6.5)
        contacts = "Sales: +20 120 014 0100  |  +20 107 039 9500  |  inquiries@inertiaegypt.com"
        self.drawCentredString(page_width/2, footer_y - 2, contacts)
        
        # Page number
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#07141D"))
        self.drawCentredString(page_width/2, 35, f"Page {self.pages}")

def generate_professional_offer_letter(unit_data, images, logo_bytes, customer_data):
    """Generate professional offer letter with enhanced letterhead template"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=130,
        bottomMargin=100
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- CUSTOM STYLES ---
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#2A3932"),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=28
    )
    
    style_subtitle = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#07141D"),
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=20,
        fontName='Helvetica',
        leading=16
    )
    
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2A3932"),
        spaceBefore=18,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor("#07141D"),
        borderPadding=5,
        backColor=colors.HexColor("#F5F7F5")
    )
    
    style_body = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        spaceAfter=8,
        textColor=colors.HexColor("#07141D"),
        fontName='Helvetica',
        alignment=TA_JUSTIFY
    )
    
    # ==================== PAGE 1: COVER & CUSTOMER INFO ====================
    
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("PROPERTY RESERVATION", style_title))
    elements.append(Paragraph("Exclusive Investment Opportunity", style_subtitle))
    
    elements.append(Spacer(1, 0.4*inch))
    
    # Customer Information Box
    if any(customer_data.values()):
        customer_box_data = []
        
        if customer_data.get('name'):
            customer_box_data.append(['Prepared For:', customer_data['name']])
        if customer_data.get('mobile'):
            customer_box_data.append(['Mobile:', customer_data['mobile']])
        if customer_data.get('email'):
            customer_box_data.append(['Email:', customer_data['email']])
        if customer_data.get('request'):
            customer_box_data.append(['Initial Request:', customer_data['request']])
        
        if customer_box_data:
            customer_table = Table(customer_box_data, colWidths=[1.8*inch, 4*inch])
            customer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FCFA')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2A3932')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#07141D')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#07141D')),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E5E5E5')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(customer_table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Property Highlight
    highlight_data = [
        ['Unit Reference', unit_data.get('Unit Number', 'N/A')],
        ['Development', unit_data.get('Dev Name', 'N/A')],
        ['Configuration', f"{unit_data.get('No.Bedrooms', 'N/A')} Bedrooms"],
        ['Total Area', f"{unit_data.get('BUA with Terraces', 'N/A')} m²"]
    ]
    
    highlight_table = Table(highlight_data, colWidths=[2*inch, 3.8*inch])
    highlight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2A3932')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#07141D')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2A3932')),
        ('LINEBELOW', (0, 0), (-1, -2), 1, colors.HexColor('#E5E5E5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(highlight_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Personalized Introduction with customer's first name
    customer_first_name = "Valued Client"
    if customer_data.get('name'):
        name_parts = customer_data['name'].strip().split()
        if name_parts:
            customer_first_name = name_parts[0]
    
    intro_text = f"""
    Dear {customer_first_name},<br/><br/>
    We are pleased to present this exclusive reservation offer for a premium property 
    at <b>{unit_data.get('Dev Name', 'N/A')}</b>. This document outlines the complete 
    specifications, pricing, and terms for your consideration.<br/><br/>
    Inertia Egypt continues to redefine luxury living through thoughtfully designed 
    communities that blend natural beauty with modern convenience.
    """
    elements.append(Paragraph(intro_text, style_body))
    
    elements.append(PageBreak())
    
    # ==================== PAGE 2: DETAILED SPECIFICATIONS ====================
    
    elements.append(Paragraph("UNIT SPECIFICATIONS", style_section))
    elements.append(Spacer(1, 0.2*inch))
    
    specs_data = [
        ['Unit Number', unit_data.get('Unit Number', 'N/A')],
        ['Development Name', unit_data.get('Dev Name', 'N/A')],
        ['Property Type', f"{unit_data.get('Type', 'N/A')} - {unit_data.get('Type 4', 'N/A')}"],
        ['Floor Level', unit_data.get('Floor', 'N/A')],
        ['Number of Bedrooms', str(unit_data.get('No.Bedrooms', 'N/A'))],
        ['Built-Up Area (BUA)', f"{unit_data.get('BUA with Terraces', 'N/A')} m²"],
        ['Garden Area', f"{unit_data.get('Garden', 'N/A')} m²"],
        ['Maid Room', unit_data.get('Maid Room', 'N/A')],
        ['Expected Delivery', unit_data.get('Delivery Date', 'N/A')],
        ['Current Status', unit_data.get('Status', 'N/A')],
    ]
    
    specs_table = Table(specs_data, colWidths=[2.5*inch, 3.3*inch])
    specs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F7F5')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2A3932')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#07141D')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E5E5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(specs_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Pricing Section
    elements.append(Paragraph("FINANCIAL DETAILS", style_section))
    elements.append(Spacer(1, 0.15*inch))
    
    price_data = [
        ['Total Price', f"{unit_data.get('Final Price', 'N/A')} EGP"],
    ]
    
    price_table = Table(price_data, colWidths=[2.5*inch, 3.3*inch])
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2A3932')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    
    elements.append(price_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment Terms
    elements.append(Paragraph("PAYMENT STRUCTURE", style_section))
    payment_terms = """
    <b>• Down Payment:</b> 5% of total unit price due upon reservation<br/>
    <b>• Installment Plans:</b> Flexible payment schedules available<br/>
    <b>• Delivery Schedule:</b> As per contract ({delivery})<br/>
    <b>• Maintenance Fees:</b> Applied as per community guidelines<br/>
    <b>• Additional Costs:</b> Registration fees and applicable taxes apply
    """.format(delivery=unit_data.get('Delivery Date', 'TBD'))
    
    elements.append(Paragraph(payment_terms, style_body))
    elements.append(Spacer(1, 0.2*inch))
    
    # Validity Notice
    validity_box = Paragraph(
        "<i>This offer remains valid for 14 calendar days from the date of issue. "
        "Unit availability is subject to confirmation at time of reservation.</i>",
        style_body
    )
    elements.append(validity_box)
    
    # ==================== PAGE 3: PROPERTY VISUALS (only if images exist) ====================
    if images and len(images) > 0:
        elements.append(PageBreak())
        elements.append(Paragraph("PROPERTY GALLERY", style_section))
        elements.append(Spacer(1, 0.3*inch))
        
        # Display images in 2-column grid
        for i in range(0, len(images), 2):
            row_images = images[i:i+2]
            image_elements = []
            
            for img in row_images:
                max_width = 3*inch
                max_height = 2.2*inch
                
                aspect = img.width / img.height
                if aspect > (max_width / max_height):
                    img_width = max_width
                    img_height = max_width / aspect
                else:
                    img_height = max_height
                    img_width = max_height * aspect
                
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                image_elements.append(Image(img_buffer, width=img_width, height=img_height))
            
            if len(image_elements) == 2:
                img_table = Table([image_elements], colWidths=[3.2*inch, 3.2*inch])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(img_table)
            else:
                for img_elem in image_elements:
                    elements.append(img_elem)
            
            elements.append(Spacer(1, 0.25*inch))
    
    # Build PDF with custom canvas
    def create_canvas(*args, **kwargs):
        return ProfessionalLetterhead(*args, logo_bytes=logo_bytes, 
                                     customer_data=customer_data, **kwargs)
    
    doc.build(elements, canvasmaker=create_canvas)
    buffer.seek(0)
    return buffer.getvalue()

def load_inventory_data(file):
    """Load inventory data from CSV or Excel file."""
    try:
        file_name = file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        file.seek(0)
        
        if file_ext in ['.xlsx', '.xls']:
            try:
                df = pd.read_excel(file, engine='openpyxl' if file_ext == '.xlsx' else None)
                df.columns = df.columns.str.strip()
                return df
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                return None
        
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
            st.error(f"Unsupported file format: {file_ext}")
            return None
        
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# --- MAIN APPLICATION ---

def main():
    # Initialize session state for inventory
    if 'inventory_df' not in st.session_state:
        st.session_state.inventory_df = None
    if 'selected_unit' not in st.session_state:
        st.session_state.selected_unit = ""
    
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <h1>🏗️ Inertia Offer Letter Generator</h1>
        <p class='subtitle'>Professional Property Proposals</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === STEP 1: INVENTORY UPLOAD (Persistent) ===
    st.markdown("### 📊 Upload Master Inventory")
    st.info("📌 Upload your complete inventory file once. It will remain loaded for the entire session.")
    
    inventory_file = st.file_uploader(
        "Master Inventory (CSV/Excel)", 
        type=['csv', 'xlsx', 'xls'], 
        help="Upload complete inventory with all projects",
        key="inventory_upload"
    )
    
    # Load inventory into session state
    if inventory_file and st.session_state.inventory_df is None:
        with st.spinner("📥 Loading inventory..."):
            st.session_state.inventory_df = load_inventory_data(inventory_file)
            if st.session_state.inventory_df is not None:
                st.success(f"✅ Loaded {len(st.session_state.inventory_df)} units from inventory!")
    
    # Show inventory status
    if st.session_state.inventory_df is not None:
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Total Units", len(st.session_state.inventory_df))
        with col_info2:
            projects = st.session_state.inventory_df['Dev Name'].nunique() if 'Dev Name' in st.session_state.inventory_df.columns else 0
            st.metric("Projects", projects)
        with col_info3:
            available = len(st.session_state.inventory_df[st.session_state.inventory_df['Status'].str.lower() == 'available']) if 'Status' in st.session_state.inventory_df.columns else 0
            st.metric("Available Units", available)
    
    st.markdown("---")
    
    # === STEP 2: CUSTOMER INFORMATION ===
    st.markdown("### 👤 Customer Information")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        customer_name = st.text_input(
            "Customer Name",
            placeholder="e.g., Ahmed Mohamed",
            help="Full name - First name will be used in greeting"
        )
        customer_mobile = st.text_input(
            "Mobile Number",
            placeholder="e.g., +20 100 123 4567",
            help="Primary contact number"
        )
    
    with col_b:
        customer_email = st.text_input(
            "Email Address",
            placeholder="e.g., ahmed@example.com",
            help="Customer's email address"
        )
        customer_request = st.text_area(
            "Customer Requirements",
            placeholder="e.g., Looking for 3-bedroom villa with garden view and sea access",
            help="Detailed description - AI will suggest matching units",
            height=100
        )
    
    # === AI-POWERED SUGGESTIONS ===
    if customer_request and st.session_state.inventory_df is not None:
        st.markdown("---")
        st.markdown("### 🤖 AI-Recommended Units")
        
        with st.spinner("🔍 Analyzing requirements and finding best matches..."):
            suggestions = suggest_units_based_on_request(
                st.session_state.inventory_df, 
                customer_request
            )
        
        if suggestions:
            st.success(f"✨ Found {len(suggestions)} matching units based on requirements!")
            
            for idx, suggestion in enumerate(suggestions, 1):
                with st.expander(f"🏘️ Option {idx}: {suggestion['unit_number']} - {suggestion['dev_name']}", expanded=(idx==1)):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Bedrooms", suggestion['bedrooms'])
                    with col2:
                        st.metric("Area", f"{suggestion['area']} m²")
                    with col3:
                        st.metric("Price", suggestion['price'])
                    with col4:
                        if st.button(f"Select Unit", key=f"select_{idx}"):
                            st.session_state.selected_unit = suggestion['unit_number']
                            st.success(f"✅ Selected: {suggestion['unit_number']}")
                    
                    st.info(f"**Match Reasons:** {suggestion['reasons']}")
        else:
            st.warning("No specific matches found. You can manually enter unit details below.")
    
    st.markdown("---")
    
    # === STEP 3: PROJECT BROCHURE ===
    st.markdown("### 📄 Project Brochure")
    
    pdf_file = st.file_uploader(
        "Upload Project E-Brochure (PDF)", 
        type=['pdf'], 
        help="Upload the PDF brochure for the selected project",
        key="brochure_upload"
    )
    
    st.markdown("---")
    
    # === STEP 4: UNIT SELECTION ===
    st.markdown("### 🏘️ Final Unit Selection")
    
    # Use session state selected unit or manual input
    unit_input = st.text_input(
        "Unit Number",
        value=st.session_state.selected_unit,
        placeholder="e.g., JF11-VSV-001",
        help="Select from suggestions above or enter manually"
    )
    
    # Auto-detect unit type from brochure
    available_unit_types = []
    search_term = ""
    
    if pdf_file:
        with st.spinner("🔍 Analyzing brochure..."):
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            available_unit_types = extract_unit_types_from_pdf(pdf_bytes)
            
            if available_unit_types:
                with st.expander("📋 Detected Unit Types from Brochure", expanded=False):
                    cols = st.columns(2)
                    for idx, unit_type in enumerate(available_unit_types[:10]):
                        with cols[idx % 2]:
                            st.write(f"• {unit_type}")
        
        if available_unit_types:
            search_term = st.selectbox(
                "Unit Type (for image extraction)",
                options=[""] + available_unit_types,
                help="Select unit type to extract relevant images from brochure"
            )
        else:
            search_term = st.text_input(
                "Unit Type (for image extraction)",
                placeholder="e.g., The Una Villa",
                help="Enter unit type to find in brochure"
            )
    
    # === PREVIEW UNIT DATA ===
    if st.session_state.inventory_df is not None and unit_input:
        unit_row = st.session_state.inventory_df[
            st.session_state.inventory_df['Unit Number'].astype(str).str.strip() == unit_input.strip()
        ]
        
        if not unit_row.empty:
            unit_data = unit_row.iloc[0].to_dict()
            
            with st.expander("✅ Selected Unit Details", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Development", unit_data.get('Dev Name', 'N/A'))
                with col2:
                    st.metric("Bedrooms", unit_data.get('No.Bedrooms', 'N/A'))
                with col3:
                    st.metric("Area (m²)", unit_data.get('BUA with Terraces', 'N/A'))
                with col4:
                    st.metric("Price", unit_data.get('Final Price', 'N/A'))
        else:
            st.error(f"❌ Unit '{unit_input}' not found in inventory.")
    
    st.markdown("---")
    
    # === GENERATE BUTTON ===
    if st.button("🚀 GENERATE PROFESSIONAL OFFER LETTER", type="primary", use_container_width=True):
        # Validation
        if st.session_state.inventory_df is None:
            st.error("⚠️ Please upload inventory file first.")
            st.stop()
        
        if not pdf_file:
            st.error("⚠️ Please upload project brochure (PDF).")
            st.stop()
        
        if not unit_input:
            st.error("⚠️ Please enter or select a unit number.")
            st.stop()
        
        # === PROCESSING ===
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 1. Logo
        status.text("📥 Loading company branding...")
        progress_bar.progress(10)
        logo_bytes = download_logo(LOGO_URL)
        
        # 2. Unit Data
        status.text("📊 Processing unit data...")
        progress_bar.progress(25)
        
        unit_row = st.session_state.inventory_df[
            st.session_state.inventory_df['Unit Number'].astype(str).str.strip() == unit_input.strip()
        ]
        
        if unit_row.empty:
            st.error(f"Unit '{unit_input}' not found in inventory.")
            st.stop()
        
        unit_data = unit_row.iloc[0].to_dict()
        
        # 3. Customer Data
        customer_data = {
            'name': customer_name,
            'mobile': customer_mobile,
            'email': customer_email,
            'request': customer_request
        }
        
        # 4. Find Pages & Extract Images
        images = []
        if search_term:
            status.text(f"🔍 Locating '{search_term}' in brochure...")
            progress_bar.progress(40)
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            found_pages = find_pages_in_pdf(pdf_bytes, search_term, limit=4)
            
            if found_pages:
                st.success(f"✅ Found {len(found_pages)} relevant pages")
                
                status.text("🖼️ Extracting property visuals...")
                progress_bar.progress(60)
                images = extract_images_from_pdf_pages(pdf_bytes, found_pages, max_images=4)
                if images:
                    st.info(f"📸 Extracted {len(images)} professional images")
        
        # 5. Generate PDF
        status.text("📝 Generating professional offer letter...")
        progress_bar.progress(80)
        
        try:
            final_pdf = generate_professional_offer_letter(
                unit_data, images, logo_bytes, customer_data
            )
            
            progress_bar.progress(100)
            status.text("✅ Complete!")
            
            st.success("🎉 Professional Offer Letter Generated!")
            
            # Download Button
            st.download_button(
                label="📥 DOWNLOAD OFFER LETTER",
                data=final_pdf,
                file_name=f"Inertia_Offer_{unit_input}_{datetime.now().strftime('%Y%m%d')}.pdf",
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
