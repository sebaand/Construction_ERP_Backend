from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from .pdf_config import styles, PAGE_WIDTH, PAGE_HEIGHT, MARGIN, TABLE_STYLE

# function for generating an invoice pdf
def generate_invoice_pdf(invoice_data, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    
    # Content
    elements = []
    
    # Header
    header_data = [
        [Paragraph(f"INVOICE #{invoice_data['invoice_number']}", styles['Heading1'])],
        [Paragraph("BREAKDOWN", styles['Heading2'])]
    ]
    header = Table(header_data, colWidths=[doc.width])
    header.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 10*mm))
    
    # Customer and Company Info
    info_data = [
        [Paragraph(f"<b>Customer:</b><br/>{invoice_data['customer_name']}<br/>{invoice_data['customer_address']}", styles['Normal']),
         Paragraph(f"<b>Company:</b><br/>{invoice_data['company_name']}<br/>{invoice_data['company_address']}", styles['Normal'])],
    ]
    info_table = Table(info_data, colWidths=[doc.width/2]*2)
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # Invoice Details
    details_data = [
        ['HOURS', 'PRICE', 'TOTAL'],
    ]
    for item in invoice_data['items']:
        details_data.append([str(item['hours']), f"${item['price']}", f"${item['total']}"])
    
    details_table = Table(details_data, colWidths=[doc.width/3]*3)
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(details_table)
    
    # Total
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Total: ${invoice_data['total']}", styles['Right']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# # Function for generating a downloadable quote
# def generate_quote_pdf(quote_data):
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4, 
#                             leftMargin=MARGIN, rightMargin=MARGIN,
#                             topMargin=MARGIN, bottomMargin=MARGIN)
    
#     elements = []
    
#     # Header
#     elements.append(Paragraph(f"Project: {quote_data.projectName}", styles['Heading1']))
#     elements.append(Paragraph(f"Quote #{quote_data.quote_number} - {quote_data.name}", styles['Heading2']))
#     elements.append(Spacer(1, 10*mm))
    
#     # Customer and Company Info
#     info_data = [
#         [Paragraph(f"<b>Customer:</b><br/>{quote_data.companyName}<br/>{quote_data.site_address}", styles['Normal']),
#          Paragraph(f"<b>Company:</b><br/>{quote_data.companyName}<br/>{quote_data.company_address}<br/>Telephone: {quote_data.telephone}<br/>VAT: {quote_data.vat_number}<br/>Company Number: {quote_data.company_number}", styles['Normal'])],
#     ]
#     info_table = Table(info_data, colWidths=[(PAGE_WIDTH - 2*MARGIN)/2]*2)
#     info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
#     elements.append(info_table)
#     elements.append(Spacer(1, 10*mm))
    
#     # Quote Details
#     details_data = [
#         ['Item', 'Quantity', 'Units', 'Price', 'Total'],
#     ]
#     for item in quote_data.lineItems:
#         details_data.append([
#             item.lineItem,
#             f"{int(item.quantity)}",  # Format quantity as whole number
#             item.units,
#             f"£{'{:,.2f}'.format(item.pricePerUnit)}",  # Add thousands separator
#             f"£{'{:,.2f}'.format(item.quantity * item.pricePerUnit)}"  # Add thousands separator
#         ])
    
#     details_table = Table(details_data, colWidths=[(PAGE_WIDTH - 2*MARGIN)/5]*5)
#     details_table.setStyle(TableStyle(TABLE_STYLE))
#     elements.append(details_table)
    
#     # Total
#     elements.append(Spacer(1, 10*mm))
#     elements.append(Paragraph(f"Total: £{'{:,.2f}'.format(quote_data.quoteTotal)}", styles['Right']))  # Add thousands separator
    
#     # Terms
#     if quote_data.terms:
#         elements.append(Spacer(1, 10*mm))
#         elements.append(Paragraph("Terms and Conditions:", styles['Heading3']))
#         elements.append(Paragraph(quote_data.terms, styles['Normal']))
    
#     # Build PDF
#     doc.build(elements)
#     buffer.seek(0)
#     return buffer
def generate_quote_pdf(quote_data):
    # Create a buffer to hold the PDF data
    buffer = BytesIO()
    
    # Define page size and margins
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 20 * mm  # 20mm margins on all sides
    
    # Initialize the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2 * mm,
        bottomMargin=MARGIN
    )
    
    # Initialize the list to hold flowable elements
    elements = []
    
    # Get predefined styles and add custom styles if necessary
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    
    # ---------------------------
    # Header Section with Logo
    # ---------------------------
    
    # Path to the logo image
    logo_path = 'app/utils/logo_nobackground_withname.png'
    
    try:
        # Load the logo image
        logo = Image(logo_path)
        
        # Desired logo height in millimeters
        desired_logo_height = 20 * mm  # 20mm high
        
        # Calculate aspect ratio to maintain it
        logo_aspect = logo.imageWidth / logo.imageHeight
        
        # Set the desired height and calculate corresponding width
        logo.drawHeight = desired_logo_height
        logo.drawWidth = desired_logo_height * logo_aspect
        
    except IOError:
        # If the logo image is not found, use a placeholder text
        logo = Paragraph("Logo Not Found", styles['Normal'])
    
    # Create a two-column table for the header
    # Left column can hold additional header info or remain empty
    # Right column holds the logo
    header_data = [
        ['', logo]  # Empty string for left cell, logo for right cell
    ]
    
    # Define column widths
    # Left column takes up remaining space after accounting for the logo width and some padding
    padding = 10 * mm  # Padding between columns
    logo_width_with_padding = logo.drawWidth + padding
    available_width = PAGE_WIDTH - 2 * MARGIN  # Total available width within margins
    left_col_width = available_width - logo_width_with_padding
    
    header_table = Table(
        header_data,
        colWidths=[left_col_width, logo_width_with_padding]
    )
    
    # Style the header table
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Align logo to the right in the right cell
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Vertically align content to the top
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # Add padding below the header
        ('TOPPADDING', (0, 0), (-1, -1), 0),  # No padding above the header
    ]))
    
    # Add the header table to elements
    elements.append(header_table)
    
    # # Spacer after header
    # elements.append(Spacer(1, 5 * mm))  # 5mm space
    
    # ---------------------------
    # Project and Quote Information
    # ---------------------------
    
    # Add project name as Heading1
    project_para = Paragraph(f"<b>Project:</b> {quote_data.projectName}", styles['Heading1'])
    elements.append(project_para)
    
    # Add quote number and name as Heading2
    quote_para = Paragraph(f"<b>Quote #{quote_data.quote_number} - {quote_data.name}</b>", styles['Heading2'])
    elements.append(quote_para)
    
    # Spacer after project info
    elements.append(Spacer(1, 10 * mm))  # 10mm space
    
    # ---------------------------
    # Customer and Company Information
    # ---------------------------
    
    # Prepare customer information
    customer_info = f"""
        <b>Customer:</b><br/>
        {quote_data.companyName}<br/>
        {quote_data.site_address}
    """
    
    # Prepare company information
    company_info = f"""
        <b>Company:</b><br/>
        {quote_data.companyName}<br/>
        {quote_data.company_address}<br/>
        Telephone: {quote_data.telephone}<br/>
        VAT: {quote_data.vat_number}<br/>
        Company Number: {quote_data.company_number}
    """
    
    # Create a table with two columns: Customer and Company Info
    info_data = [
        [
            Paragraph(customer_info, styles['Normal']),
            Paragraph(company_info, styles['Normal'])
        ]
    ]
    
    # Define column widths (half of the available width each, minus some padding)
    info_table = Table(
        info_data,
        colWidths=[(available_width / 2) - 5 * mm, (available_width / 2) - 5 * mm]
    )
    
    # Style the info table
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Remove left padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Remove right padding
    ]))
    
    # Add the info table to elements
    elements.append(info_table)
    
    # Spacer after info
    elements.append(Spacer(1, 10 * mm))  # 10mm space
    
    # ---------------------------
    # Quote Details Table
    # ---------------------------
    
    # Define the table style for quote details
    TABLE_STYLE = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Add grid lines
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row background
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align Quantity, Units, Price
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Right align Total
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for headers
    ])
    
    # Initialize details data with header row
    details_data = [
        ['Item', 'Quantity', 'Units', 'Price', 'Total']
    ]
    
    # Add each line item to the details data
    for item in quote_data.lineItems:
        total_price = item.quantity * item.pricePerUnit
        details_data.append([
            item.lineItem,
            f"{int(item.quantity)}",
            item.units,
            f"£{'{:,.2f}'.format(item.pricePerUnit)}",
            f"£{'{:,.2f}'.format(total_price)}"
        ])
    
    # Create the details table
    details_table = Table(
        details_data,
        colWidths=[
            (available_width) * 0.4,  # Item - 40%
            (available_width) * 0.15, # Quantity - 15%
            (available_width) * 0.15, # Units - 15%
            (available_width) * 0.15, # Price - 15%
            (available_width) * 0.15  # Total - 15%
        ]
    )
    
    # Apply the table style
    details_table.setStyle(TABLE_STYLE)
    
    # Add the details table to elements
    elements.append(details_table)
    
    # ---------------------------
    # Total Amount Section
    # ---------------------------
    
    # Spacer before total
    elements.append(Spacer(1, 10 * mm))  # 10mm space
    
    # Create a table for the total amount, aligned to the right
    total_data = [
        ['', '', '', 'Total:', f"£{'{:,.2f}'.format(quote_data.quoteTotal)}"]
    ]
    
    total_table = Table(
        total_data,
        colWidths=[
            (available_width) * 0.4,  # Empty - 40%
            (available_width) * 0.15, # Empty - 15%
            (available_width) * 0.15, # Empty - 15%
            (available_width) * 0.15, # Label - 15%
            (available_width) * 0.15  # Amount - 15%
        ]
    )
    
    # Style the total table
    total_table.setStyle(TableStyle([
        ('ALIGN', (4, 0), (4, 0), 'RIGHT'),  # Right align the total amount
        ('FONTNAME', (3, 0), (4, 0), 'Helvetica-Bold'),  # Bold font for label and amount
        ('LINEABOVE', (3, 0), (4, 0), 1, colors.black),  # Line above the total
    ]))
    
    # Add the total table to elements
    elements.append(total_table)
    
    # ---------------------------
    # Terms and Conditions Section
    # ---------------------------
    
    if quote_data.terms:
        # Spacer before terms
        elements.append(Spacer(1, 10 * mm))  # 10mm space
        
        # Add Terms and Conditions heading
        elements.append(Paragraph("Terms and Conditions:", styles['Heading3']))
        
        # Add Terms and Conditions text
        elements.append(Paragraph(quote_data.terms, styles['Normal']))
    
    # ---------------------------
    # Build the PDF
    # ---------------------------
    
    # Generate the PDF
    doc.build(elements)
    
    # Move the buffer's cursor to the beginning
    buffer.seek(0)
    
    return buffer