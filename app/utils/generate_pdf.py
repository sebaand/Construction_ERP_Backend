from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

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


def generate_quote_pdf(invoice_data, buffer):
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