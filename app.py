import streamlit as st
import pandas as pd
import io
import re
import requests
from io import BytesIO
from PIL import Image as PILImage
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="Vaya Offer Letter Generator",
    page_icon="🏠",
    layout="centered"
)

# Colors
COLOR_PRIMARY = "#2C3E50"  # Dark Blue/Grey
COLOR_ACCENT = "#D4A373"   # Sand/Gold
COLOR_BG = "#F9F7F2"       # Off-white

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
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        st.error(f"Could not download logo: {e}")
        return None

def normalize_text(text):
    """Simple text normalization for searching."""
    if not text:
        return ""
    return text.lower().strip()

def find_limited_pages_in_pdf(pdf_bytes, search_term, limit=4):
    """
    Scans PDF for pages containing the search term.
    Returns a list of page indices (0-based), limited to 'limit'.
    """
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
        st.error(f"Error reading PDF: {e}")
    return found_pages

def generate_offer_pdf(unit_data, pdf_search_term, logo_bytes):
    """
    Generates the Cover and Details pages using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=COLOR_PRIMARY, spaceAfter=30, alignment=TA_CENTER)
    style_body = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontSize=11, leading=16, spaceAfter=12, alignment=TA_LEFT)
    style_highlight = ParagraphStyle('Highlight', parent=styles['Heading2'], fontSize=14, textColor=COLOR_ACCENT, spaceBefore=20, spaceAfter=10)

    # --- PAGE 1: COVER WITH LOGO ---
    if logo_bytes:
        try:
            img_reader = ImageReader(logo_bytes)
            # Calculate aspect ratio to fit width ~4 inches
            img_width = 4 * inch
            img_height = (img_reader.getSize()[1] / img_reader.getSize()[0]) * img_width
            
            elements.append(Image(logo_bytes, width=img_width, height=img_height, hAlign='CENTER'))
            elements.append(Spacer(1, 0.5*inch))
        except:
            st.warning("Logo file format not supported for PDF generation.")

    elements.append(Paragraph("JEFaira - Vaya", style_title))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("RESERVATION & OFFER LETTER", style_title))
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Prepared for:", style_body))
    elements.append(Paragraph(f"Unit Reference: <b>{unit_data['Unit Number']}</b>", style_highlight))
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Inertia Properties", style_body))
    elements.append(Paragraph("www.inertiaegypt.com", style_body))
    
    elements.append(PageBreak())

    # --- PAGE 2: UNIT DETAILS ---
    elements.append(Paragraph("UNIT DETAILS", style_title))
    elements.append(Spacer(1, 0.3*inch))

    details_text = (
        f"Vaya <b>{unit_data['Unit Number']}</b>. "
        f"{unit_data['Dev Name']}. "
        f"BUA {unit_data['BUA with Terraces']} sqm. "
        f"{unit_data['No.Bedrooms']} Bedrooms. "
        f"Price = {unit_data['Final Price']}. "
        f"5% Down Payment. Delivery {unit_data['Delivery Date']}."
    )
    elements.append(Paragraph(details_text, style_body))
    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph("SPECIFICATION SUMMARY", style_highlight))
    details_table = f"""
    <b>Development:</b> {unit_data['Dev Name']}<br/>
    <b>Type:</b> {unit_data['Type']} - {unit_data['Type 4']}<br/>
    <b>Floor:</b> {unit_data['Floor']}<br/>
    <b>Bedrooms:</b> {unit_data['No.Bedrooms']}<br/>
    <b>BUA with Terraces:</b> {unit_data['BUA with Terraces']} m²<br/>
    <b>Price:</b> {unit_data['Final Price']} EGP<br/>
    <b>Maid Room:</b> {unit_data['Maid Room']}<br/>
    <b>Status:</b> {unit_data['Status']}
    """
    elements.append(Paragraph(details_table, style_body))
    elements.append(Spacer(1, 0.5*inch))
    
    terms = """
    <i>TERMS & CONDITIONS:</i><br/>
    1. Prices are subject to maintenance charges and taxes.<br/>
    2. Delivery date is subject to developer schedule.<br/>
    3. This offer is valid for 14 days from date of issue.
    """
    elements.append(Paragraph(terms, style_body))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- MAIN APPLICATION ---

def main():
    st.title("Vaya Offer Letter Generator")
    st.markdown("---")

    # --- STEP 1: FILE UPLOADS ---
    col_csv, col_pdf = st.columns(2)
    
    with col_csv:
        csv_file = st.file_uploader("1. Upload Inventory CSV", type=['csv'])
    
    with col_pdf:
        pdf_file = st.file_uploader("2. Upload E-Brochure PDF", type=['pdf'])

    # --- STEP 2: UNIT INPUTS ---
    st.markdown("### 3. Select Unit & Brochure Images")
    st.info("Enter the Unit Number. The app will automatically try to match the Brochure Name from the CSV. You can edit it if needed.")

    # Session State to hold the PDF search term so it doesn't reset on rerun
    if 'pdf_search_term' not in st.session_state:
        st.session_state.pdf_search_term = ""

    col_unit, col_term = st.columns([2, 2])
    
    with col_unit:
        unit_input = st.text_input("Unit Number (e.g., JF11-VSV-001)", "")
    
    with col_term:
        # The user asked for a separate field to specify the PDF images
        pdf_input = st.text_input("Brochure Section Name (e.g., The Una Villa)", st.session_state.pdf_search_term)

    # --- SMART MAPPING LOGIC ---
    if csv_file and unit_input:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            # Find the unit
            unit_row = df[df['Unit Number'].astype(str).str.strip() == unit_input.strip()]
            
            if not unit_row.empty:
                unit_data = unit_row.iloc[0].to_dict()
                
                # If the user hasn't manually typed a search term yet, 
                # Auto-fill it with the 'Dev Name' from the CSV (The Smart Solution)
                if not pdf_input: 
                    st.session_state.pdf_search_term = unit_data.get('Dev Name', '')
                    pdf_input = st.session_state.pdf_search_term
                    # Rerun to update the text input value (streamlit quirk)
                    # st.rerun() # Optional: might flicker, so we let the user see the value in the logic below
                
            else:
                st.error("Unit number not found in CSV.")
                st.stop()
        except Exception as e:
            st.error(f"Error processing CSV: {e}")
            st.stop()

    # --- GENERATE BUTTON ---
    generate_btn = st.button("Generate Offer Letter", type="primary", use_container_width=True)

    if generate_btn:
        if not csv_file or not pdf_file:
            st.error("Please upload both the CSV and PDF files.")
            st.stop()
        
        if not unit_input or not pdf_input:
            st.error("Please enter both a Unit Number and a Brochure Section Name.")
            st.stop()

        # --- PROCESSING ---
        
        # 1. Get Logo
        st.toast("Fetching Logo...")
        logo_bytes = download_logo(LOGO_URL)

        # 2. Get CSV Data
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            unit_row = df[df['Unit Number'].astype(str).str.strip() == unit_input.strip()]
            unit_data = unit_row.iloc[0].to_dict()
        except Exception as e:
            st.error(f"CSV Error: {e}")
            st.stop()

        # 3. Search PDF (Limited to 4 pages)
        with st.spinner(f"Searching brochure for '{pdf_input}'..."):
            pdf_bytes = pdf_file.read()
            
            # STRICT LIMIT: 4 Pages max
            found_page_indices = find_limited_pages_in_pdf(pdf_bytes, pdf_input, limit=4)
            
            if not found_page_indices:
                st.warning(f"No pages found in PDF containing: '{pdf_input}'. Proceeding with text only.")
            else:
                st.success(f"Found {len(found_page_indices)} relevant pages in brochure.")

        # 4. Generate Main Document (Cover + Details)
        with st.spinner("Generating Offer Letter..."):
            main_pdf_bytes = generate_offer_pdf(unit_data, pdf_input, logo_bytes)

        # 5. Merge PDFs (Main + Extracted Brochure Pages)
        try:
            final_writer = PdfWriter()
            
            # Add Generated Pages
            reader_generated = PdfReader(BytesIO(main_pdf_bytes))
            for page in reader_generated.pages:
                final_writer.add_page(page)
            
            # Add Extracted Brochure Pages (Max 4)
            if found_page_indices:
                reader_brochure = PdfReader(BytesIO(pdf_bytes))
                for idx in found_page_indices:
                    if idx < len(reader_brochure.pages):
                        final_writer.add_page(reader_brochure.pages[idx])

            # Save Output
            output_buffer = BytesIO()
            final_writer.write(output_buffer)
            output_buffer.seek(0)

            # Download Button
            st.success("Offer Letter Generated!")
            
            st.download_button(
                label="📥 Download Offer Letter PDF",
                data=output_buffer,
                file_name=f"Offer_Letter_{unit_input}.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Error merging PDFs: {e}")

if __name__ == "__main__":
    main()

