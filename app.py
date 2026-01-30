import streamlit as st
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.utils import ImageReader

# Define color constants (adjust these to match your app's colors)
COLOR_PRIMARY = '#2C3E50'
COLOR_ACCENT = '#3498DB'


def draw_footer(canvas, doc):
    """
    Draw footer on each page with company information and line.
    """
    try:
        canvas.saveState()
        
        # Draw a line above the footer
        canvas.setStrokeColor(colors.HexColor('#CCCCCC'))
        canvas.setLineWidth(0.5)
        canvas.line(0.5 * inch, 0.85 * inch, 7.5 * inch, 0.85 * inch)
        
        # Set font and color
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.black)
        
        # Draw footer text
        footer_text = "INERTIA HEADQUARTERS, Building 06. Cairo West Business Park. KM 22, Cairo-Alexandria, Desert Road, Giza | Hot Line 19655"
        
        # Draw text centered at bottom
        canvas.drawCentredString(4 * inch, 0.7 * inch, footer_text)
        
        canvas.restoreState()
    except Exception as e:
        st.error(f"Footer drawing error: {str(e)}")
        canvas.restoreState()


def generate_compact_offer_pdf(unit_data, images, logo_bytes):
    """
    Generate a compact, professional 2-page offer letter.
    Page 1: Logo, Details, Table, Terms.
    Page 2: Images.
    Includes Footer on all pages.
    """
    try:
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=50, 
            leftMargin=50, 
            topMargin=40,
            bottomMargin=60
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # --- CUSTOM STYLES ---
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(COLOR_PRIMARY),
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        style_subtitle = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(COLOR_PRIMARY),
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=15
        )
        
        style_section = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor(COLOR_PRIMARY),
            spaceBefore=10,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        )
        
        style_body = ParagraphStyle(
            'Body',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
        
        style_highlight = ParagraphStyle(
            'Highlight',
            parent=styles['BodyText'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor(COLOR_PRIMARY),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=10,
            borderColor=colors.HexColor(COLOR_ACCENT),
            borderWidth=1,
            borderPadding=10,
            backColor=colors.HexColor('#FDFDFD')
        )
        
        # ==================== PAGE 1: COVER & FULL DETAILS ====================
        
        if logo_bytes:
            try:
                img_reader = ImageReader(logo_bytes)
                img_width = 2.5 * inch
                img_height = (img_reader.getSize()[1] / img_reader.getSize()[0]) * img_width
                elements.append(Image(logo_bytes, width=img_width, height=img_height, hAlign='CENTER'))
                elements.append(Spacer(1, 0.2*inch))
            except Exception as e:
                st.warning(f"Logo loading error: {str(e)}")
        
        elements.append(Paragraph("RESERVATION & OFFER LETTER", style_title))
        elements.append(Paragraph("Exclusive Property Offer", style_subtitle))
        
        # Date
        current_date = datetime.now().strftime("%B %d, %Y")
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Date: <b>{current_date}</b>", date_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Unit highlight box
        highlight_text = f"""
        <font name="Helvetica" size="12" color="{COLOR_PRIMARY}">Unit Reference: {unit_data.get('Unit Number', 'N/A')}</font><br/>
        <font name="Helvetica" size="10" color="#555555">{unit_data.get('Dev Name', 'N/A')}</font>
        """
        elements.append(Paragraph(highlight_text, style_highlight))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # ==================== DETAILS TABLE ====================
        elements.append(Paragraph("UNIT SPECIFICATIONS", style_section))
        elements.append(HRFlowable(width="80%", thickness=1, color=colors.HexColor(COLOR_ACCENT), spaceAfter=10))
        
        # Details table - Compact version
        table_data = [
            ['Unit Number', str(unit_data.get('Unit Number', 'N/A'))],
            ['Development', str(unit_data.get('Dev Name', 'N/A'))],
            ['Type', f"{unit_data.get('Type', 'N/A')} - {unit_data.get('Type 4', 'N/A')}"],
            ['Floor', str(unit_data.get('Floor', 'N/A'))],
            ['Bedrooms', str(unit_data.get('No.Bedrooms', 'N/A'))],
            ['BUA with Terraces', f"{unit_data.get('BUA with Terraces', 'N/A')} m²"],
            ['Garden Area', f"{unit_data.get('Garden', 'N/A')} m²"],
            ['Final Price', f"{unit_data.get('Final Price', 'N/A')} EGP"],
            ['Maid Room', str(unit_data.get('Maid Room', 'N/A'))],
            ['Delivery Date', str(unit_data.get('Delivery Date', 'N/A'))],
            ['Status', str(unit_data.get('Status', 'N/A'))],
        ]
        
        # Compact table styles
        t = Table(table_data, colWidths=[2.2*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EEEEEE')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COLOR_PRIMARY)),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 0.2*inch))
        
        # Payment terms
        elements.append(Paragraph("PAYMENT TERMS", style_section))
        terms_text = """
        • <b>5% Down Payment</b> required at reservation.<br/>
        • Delivery as per schedule: {delivery}<br/>
        • Prices subject to maintenance charges and applicable taxes.<br/>
        • This offer is valid for 14 days from date of issue.
        """.format(delivery=unit_data.get('Delivery Date', 'TBD'))
        
        elements.append(Paragraph(terms_text, style_body))
        elements.append(Spacer(1, 0.1*inch))
        
        # Company Info on Page 1 bottom
        elements.append(HRFlowable(width="80%", thickness=1, color=colors.lightgrey))
        elements.append(Spacer(1, 0.1*inch))
        
        company_style = ParagraphStyle(
            'Company',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        web_style = ParagraphStyle(
            'Web',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph("<b>Inertia Properties</b>", company_style))
        elements.append(Paragraph("www.inertiaegypt.com", web_style))
        
        elements.append(PageBreak())
        
        # ==================== PAGE 2: PROPERTY IMAGES ====================
        if images and len(images) > 0:
            elements.append(Paragraph("PROPERTY VISUALS", style_section))
            elements.append(Spacer(1, 0.2*inch))
            
            # Arrange images in a grid (2 per row)
            for i in range(0, len(images), 2):
                row_images = images[i:i+2]
                image_elements = []
                
                for img in row_images:
                    try:
                        # Resize image to fit nicely
                        max_width = 3.2 * inch
                        max_height = 2.3 * inch
                        
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
                    except Exception as e:
                        st.warning(f"Error processing image: {str(e)}")
                        continue
                
                # Create table for side-by-side layout
                if len(image_elements) == 2:
                    img_table = Table([image_elements], colWidths=[3.5*inch, 3.5*inch])
                    img_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(img_table)
                elif len(image_elements) == 1:
                    elements.append(image_elements[0])
                
                elements.append(Spacer(1, 0.2*inch))
        
        # Build PDF with Footer on all pages
        doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
        buffer.seek(0)
        return buffer.getvalue()
    
    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        raise


# Example usage in Streamlit
if __name__ == "__main__":
    st.title("PDF Generator Test")
    
    # Sample unit data
    sample_unit_data = {
        'Unit Number': 'A-101',
        'Dev Name': 'Sample Development',
        'Type': 'Apartment',
        'Type 4': '2BR',
        'Floor': '1st',
        'No.Bedrooms': 2,
        'BUA with Terraces': 120,
        'Garden': 50,
        'Final Price': '5,000,000',
        'Maid Room': 'Yes',
        'Delivery Date': 'Dec 2025',
        'Status': 'Available'
    }
    
    if st.button("Generate Test PDF"):
        try:
            pdf_bytes = generate_compact_offer_pdf(sample_unit_data, [], None)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="test_offer.pdf",
                mime="application/pdf"
            )
            st.success("PDF generated successfully!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
