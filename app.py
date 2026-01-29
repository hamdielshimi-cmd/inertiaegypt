import streamlit as st
import pandas as pd
import io
import re
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from fpdf import FPDF
import pdfplumber
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="Vaya Offer Letter Generator",
    page_icon="🏠",
    layout="centered"
)

# Define colors matching the Vaya/Inertia theme (Soft Earthy Tones)
COLOR_PRIMARY = "#2C3E50"  # Dark Blue/Grey
COLOR_ACCENT = "#D4A373"   # Sand/Gold
COLOR_BG = "#F9F7F2"       # Off-white

# Custom CSS for Streamlit UI
st.markdown(f"""
<style>
    .stApp {{
        background-color: {COLOR_BG};
    }}
    h1 {{
        color: {COLOR_PRIMARY};
        font-family: 'Helvetica', sans-serif;
    }}
    .stButton>button {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_PRIMARY};
    }}
    .upload-file {{
        border: 2px dashed {COLOR_ACCENT};
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: white;
    }}
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def normalize_text(text):
    """Removes special characters and accents to help match Unit Types in PDF."""
    if not text:
        return ""
    # Remove accents
    text = text.replace('ū', 'u').replace('ō', 'o').replace('ē', 'e').replace('ī', 'i').replace('ā', 'a')
    # Remove non-alphanumeric (keep spaces)
    text = re.sub(r'[^\w\s]', '', text).lower()
    return text.strip()

def find_pages_in_pdf(pdf_bytes, search_term):
    """
    Scans PDF for pages containing the search term.
    Returns a list of page indices (0-based).
    """
    found_pages = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            search_clean = normalize_text(search_term)
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    page_clean = normalize_text(text)
                    if search_clean in page_clean:
                        found_pages.append(i)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return found_pages

def generate_offer_pdf(unit_data, logo_path=None):
    """
    Generates the specific Offer Letter pages using ReportLab.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    # Container for the 'Flowable' objects
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=COLOR_PRIMARY,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        spaceAfter=12,
        alignment=TA_LEFT
    )
    style_highlight = ParagraphStyle(
        'Highlight',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=COLOR_ACCENT,
        spaceBefore=20,
        spaceAfter=10
    )

    # --- PAGE 1: COVER ---
    # Ideally, we would place the Inertia Logo here.
    # Since we don't have the file, we add a placeholder.
    # if logo_path:
    #     elements.append(Image(logo_path, 2*inch, 1*inch, hAlign='CENTER'))
    
    elements.append(Paragraph("JEFaira - Vaya", style_title))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("RESERVATION & OFFER LETTER", style_title))
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Prepared for:", style_body))
    elements.append(Paragraph(f"Unit Reference: <b>{unit_data['Unit Number']}</b>", style_highlight))
    
    # Decorative line
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Inertia Properties", style_body))
    elements.append(Paragraph("www.inertiaegypt.com", style_body))
    
    elements.append(PageBreak())

    # --- PAGE 2: UNIT DETAILS (The Core Requirement) ---
    elements.append(Paragraph("UNIT DETAILS & SPECIFICATIONS", style_title))
    elements.append(Spacer(1, 0.3*inch))

    # The specific paragraph requested
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

    # Additional details from CSV for completeness
    elements.append(Paragraph("SPECIFICATION SUMMARY", style_highlight))
    details_table = f"""
    <b>Development:</b> {unit_data['Dev Name']}<br/>
    <b>Type:</b> {unit_data['Type']} - {unit_data['Type 4']}<br/>
    <b>Floor:</b> {unit_data['Floor']}<br/>
    <b>Bedrooms:</b> {unit_data['No.Bedrooms']}<br/>
    <b>BUA with Terraces:</b> {unit_data['BUA with Terraces']} m²<br/>
    <b>Garden Area:</b> {unit_data['Garden']} m²<br/>
    <b>Roof Area:</b> {unit_data['Roof Area']} m²<br/>
    <b>Maid Room:</b> {'Yes' if unit_data['Maid Room'] == 'Yes' else 'No'}<br/>
    <b>Touristic Licensed:</b> {'Yes' if unit_data['Touristic Status'] == 'Yes' else 'No'}
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

    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- MAIN STREAMLIT APP ---

def main():
    st.title("Vaya Offer Letter Generator")
    st.markdown("---")

    # Sidebar or Main Area for Inputs? Main area is simpler for this request.
    
    # 1. Upload CSV
    st.subheader("1. Upload Inventory CSV")
    csv_file = st.file_uploader("Select the Inertia Inventory CSV file", type=['csv'])
    
    # 2. Upload PDF Brochure
    st.subheader("2. Upload E-Brochure PDF")
    pdf_file = st.file_uploader("Select the Vaya E-Brochure PDF file", type=['pdf'])

    # 3. Input Unit Number
    st.subheader("3. Unit Details")
    col1, col2 = st.columns([3, 1])
    with col1:
        unit_input = st.text_input("Enter Unit Number (e.g., JF11-VSV-001)", "")
    with col2:
        st.write("") # Spacer
        generate_btn = st.button("Generate Offer Letter", type="primary")

    # --- LOGIC SECTION ---

    if generate_btn:
        if not csv_file or not pdf_file or not unit_input:
            st.error("Please upload both the CSV and PDF Brochure, and enter a Unit Number.")
            st.stop()

        # Step A: Process CSV
        try:
            df = pd.read_csv(csv_file)
            # Normalize column names just in case of spaces
            df.columns = df.columns.str.strip()
            
            # Find the unit
            unit_row = df[df['Unit Number'].astype(str).str.strip() == unit_input.strip()]
            
            if unit_row.empty:
                st.error(f"Unit Number '{unit_input}' not found in the CSV.")
                st.stop()
            
            unit_data = unit_row.iloc[0].to_dict()
            st.success(f"Unit Found: {unit_data['Dev Name']}")

        except Exception as e:
            st.error(f"Error processing CSV: {e}")
            st.stop()

        # Step B: Process PDF Brochure
        try:
            pdf_bytes = pdf_file.read()
            
            # Search for the Unit Type in the PDF (e.g., "The Una Villa")
            # We search for "Dev Name" column from CSV
            unit_type_name = unit_data['Dev Name']
            st.info(f"Searching brochure for: {unit_type_name}...")
            
            relevant_pages = find_pages_in_pdf(pdf_bytes, unit_type_name)
            
            # Also try to find "Master Plan" and "Introduction" pages based on keywords
            intro_pages = find_pages_in_pdf(pdf_bytes, "Introduction") or find_pages_in_pdf(pdf_bytes, "In the heart")
            masterplan_pages = find_pages_in_pdf(pdf_bytes, "Master Plan") or find_pages_in_pdf(pdf_bytes, "DESTINATION MASTER PLAN")
            
            if not relevant_pages:
                st.warning(f"Could not find specific unit pages for '{unit_type_name}' in the brochure. Using brochure as is.")

        except Exception as e:
            st.error(f"Error processing PDF Brochure: {e}")
            st.stop()

        # Step C: Generate Dynamic Offer Letter (Pages 1-2)
        with st.spinner("Generating Offer Letter..."):
            try:
                generated_pdf_bytes = generate_offer_pdf(unit_data)
            except Exception as e:
                st.error(f"Error generating dynamic PDF: {e}")
                st.stop()

        # Step D: Merge PDFs
        try:
            final_pdf_writer = PdfWriter()
            
            # 1. Add the Generated Cover & Details
            reader_generated = PdfReader(io.BytesIO(generated_pdf_bytes))
            for page in reader_generated.pages:
                final_pdf_writer.add_page(page)
                
            # 2. Add Static Pages from Brochure (Strategy: Extract relevant ones)
            # We add Intro and Masterplan first (if found and not duplicates)
            reader_brochure = PdfReader(io.BytesIO(pdf_bytes))
            added_indices = set()
            
            # Helper to add page if exists and unique
            def add_page_indices(indices, label):
                if indices:
                    for idx in indices:
                        if idx not in added_indices and idx < len(reader_brochure.pages):
                            final_pdf_writer.add_page(reader_brochure.pages[idx])
                            added_indices.add(idx)
                            st.toast(f"Added {label} page {idx+1}")

            add_page_indices(intro_pages, "Introduction")
            add_page_indices(masterplan_pages, "Master Plan")
            add_page_indices(relevant_pages, "Unit Specifics")
            
            # If we missed specific pages, just append the rest or specific generic ones?
            # For now, we ensure the generated parts + the found specific parts are there.
            # To fill the 13 pages or make it look like the sample, we might need more logic.
            # But strictly following the prompt: "Insert specific unit details... others static extracted"
            
            # Save final output
            output_buffer = io.BytesIO()
            final_pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            # Step E: Provide Download
            st.success("Offer Letter Generated Successfully!")
            
            st.download_button(
                label="📥 Download Complete Offer Letter PDF",
                data=output_buffer,
                file_name=f"Offer_Letter_{unit_input}.pdf",
                mime="application/pdf"
            )
            
            # Show a preview of what was found
            with st.expander("See Extracted Data"):
                st.json(unit_data)
                
        except Exception as e:
            st.error(f"Error merging PDFs: {e}")
            st.stop()

if __name__ == "__main__":
    main()
