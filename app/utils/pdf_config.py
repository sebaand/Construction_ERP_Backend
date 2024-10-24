# app/utils/pdf_generator.py

from app.config import settings
from app.utils.file_handler import get_file
from app.utils.pdf_style import PDF_STYLE
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
from reportlab.lib.colors import black, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
import base64
import logging
from datetime import datetime, timedelta
from io import BytesIO
from botocore.exceptions import ClientError
import boto3

# Register fonts
pdfmetrics.registerFont(TTFont('Cursive', 'DancingScript-VariableFont_wght.ttf'))

# Define styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

# Define page configuration
PAGE_WIDTH, PAGE_HEIGHT = 210*mm, 297*mm  # A4 size
MARGIN = 15*mm

# Define colors
HEADER_COLOR = colors.HexColor("#CCCCCC")
BODY_COLOR = colors.HexColor("#FFFFFF")
TEXT_COLOR = colors.black

# Define table styles
HEADER_STYLE = [
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
    ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_COLOR),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
]

BODY_STYLE = [
    ('BACKGROUND', (0, 1), (-1, -1), BODY_COLOR),
    ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),
    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('TOPPADDING', (0, 1), (-1, -1), 6),
    ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
]

TABLE_STYLE = HEADER_STYLE + BODY_STYLE + [
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
]

class CustomCheckbox(Flowable):
    def __init__(self, checked=False):
        Flowable.__init__(self)
        self.checked = checked
        self.size = 4*mm

    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(0.5)
        self.canv.rect(0, 0, self.size, self.size)
        if self.checked:
            self.canv.line(1, 1, self.size-1, self.size-1)
            self.canv.line(1, self.size-1, self.size-1, 1)
        self.canv.restoreState()

class HorizontalLine(Flowable):
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width

    def draw(self):
        self.canv.setStrokeColor(black)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.width, 0)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# function that formats RYG cell to fill the cell with the corresponding colour
def color_name_to_hex(color_name):
    color_map = {
        'red': '#FF0000',
        'green': '#008000',
        'yellow': '#FFFF00'
    }
    return color_map.get(color_name.lower(), '#FFFFFF')  # Default to white if color not found

# function that formats the data of the slate in order to print it out on an A4 pdf
def generate_slate_pdf(slate):
    buffer = BytesIO()
    page_width, page_height = A4
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=12.7*mm, rightMargin=12.7*mm,
                            topMargin=12.7*mm, bottomMargin=12.7*mm)
    
    available_width = doc.width
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        alignment=1,  # Center alignment
        spaceAfter=7.62*mm
    )
    description_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['BodyText'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=7.62*mm
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=5.08*mm,
        spaceAfter=2.54*mm
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceBefore=2.54*mm,
        spaceAfter=2.54*mm
    )
    cursive_style = ParagraphStyle(
        'Cursive',
        parent=styles['BodyText'],
        fontName='Cursive',
        fontSize=12
    )
    
    # Add header information
    elements.append(Paragraph(f"<b>Assignee:</b> {slate['assignee']}", body_style))
    elements.append(Paragraph(f"<b>Project:</b> {slate['projectId']}", body_style))
    
    # Handle last_updated date
    try:
        last_updated = datetime.strptime(slate['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_date = last_updated.strftime('%d/%m/%Y')
    except ValueError:
        formatted_date = slate['last_updated']  # Use as-is if it's not in the expected format
    elements.append(Paragraph(f"<b>Completion Date:</b> {formatted_date}", body_style))
    
     # Add horizontal line
    elements.append(Spacer(1, 5.08*mm))
    elements.append(HorizontalLine(available_width))
    elements.append(Spacer(1, 5.08*mm))

    # Add title
    elements.append(Paragraph(slate['title'], title_style))

    # Add description if available
    if slate.get('description'):
        elements.append(Paragraph(slate['description'], description_style))
        elements.append(Spacer(1, 5.08*mm))
    
    # Process fields and data
    for field in slate['fields']:
        elements.append(Paragraph(field['label'], heading_style))
        
        if field['field_type'] == 'table':
            table_data = [[col['label'] for col in field['columns']]]
            raw_data = slate['data'].get(field['name'], [[]])
            print('raw_data', raw_data)
            print(len(raw_data[0]))
            
            # if len(raw_data) > 0 and len(raw_data[0]) > 1:
            #     data_row = raw_data[0][1:]  # Skip the first entry as a null entry is created in cases wehre a length of greate than 1.
            # elif len(raw_data[0]) == 1:
            #     data_row = raw_data[0]
            if len(raw_data) > 0:
                if len(raw_data[0]) > 1:
                    data_row = raw_data[0][1:]  # Skip the first entry
                else:
                    data_row = raw_data[0]

                # Calculate cell width
                num_columns = len(field['columns'])
                cell_width = (available_width / num_columns) - 2*mm  # Subtracting 2mm for padding

                print('data_row', data_row)
                processed_row = []
                for value, col in zip(data_row, field['columns']):
                    print('col', col)
                    print('value', value)
                    print('picture id', data_row[value])
                    if col['dataType'] == 'picture':
                        try:
                        #     file_obj = spaces_client.get_object(Bucket=DO_SPACE_NAME, Key=data_row[value])
                        #     file_content = file_obj['Body'].read()
                        #     img = Image(BytesIO(file_content), width=15*mm, height=15*mm)  # Reduced size
                        #     processed_row.append(img)
                        # except ClientError as e:
                        #     logger.error(f"Error fetching image {value}: {str(e)}")
                        #     processed_row.append('Image not found')
                            file_content = get_file(data_row[value])
                            img_reader = ImageReader(BytesIO(file_content))
                            img_width, img_height = img_reader.getSize()
                            aspect = img_height / float(img_width)
                            
                            # Scale image to fit cell width
                            new_width = cell_width
                            new_height = cell_width * aspect
                            
                            img = Image(BytesIO(file_content), width=new_width, height=new_height)
                            processed_row.append(img)
                        except ClientError as e:
                            logger.error(f"Error fetching image {value}: {str(e)}")
                            processed_row.append('Image not found')
                    elif col['dataType'] == 'colour':
                        processed_row.append(value)
                    elif col['dataType'] == 'signature':
                        if isinstance(value, str) and value.startswith('data:image'):
                            image_data = base64.b64decode(value.split(',')[1])
                            img = Image(BytesIO(image_data), width=15*mm, height=7.5*mm)  # Reduced size
                            processed_row.append(img)
                        else:
                            processed_row.append(Paragraph(str(value), cursive_style))
                    else:
                        processed_row.append(Paragraph(str(value), ParagraphStyle('Wrapped', wordWrap='CJK', fontSize=8)))
                
                table_data.append(processed_row)
            
            # Calculate column widths
            num_columns = len(field['columns'])
            col_widths = [available_width / num_columns] * num_columns
            
            # Create table with auto word wrap
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#000000')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduced font size
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FFFFFF')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#000000')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Reduced font size
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5*mm, HexColor('#000000')),
                ('WORDWRAP', (0, 0), (-1, -1)),
            ])

            # Add color-specific styles
            for i, col in enumerate(field['columns']):
                if col['dataType'] == 'colour' and len(table_data) > 1:
                    color_value = str(table_data[1][i]).lower()
                    hex_color = color_name_to_hex(color_value)
                    table_style.add('BACKGROUND', (i, 1), (i, 1), HexColor(hex_color))

            t.setStyle(table_style)
            elements.append(t)
        elif field['field_type'] == 'signature':
            value = slate['data'].get(field['name'], '')
            if value.startswith('data:image'):  # It's a base64 encoded image
                image_data = base64.b64decode(value.split(',')[1])
                img = Image(BytesIO(image_data), width=100*mm, height=50*mm)
                elements.append(img)
            else:  # It's a typed signature
                elements.append(Paragraph(value, cursive_style))
        elif field['field_type'] == 'checkbox':
            options = field.get('options', [])
            value = slate['data'].get(field['name'], [])
            checkbox_text = " ".join([f"[{'X' if opt in value else ' '}] {opt}" for opt in options])
            elements.append(Paragraph(checkbox_text, body_style))
    try:
        doc.build(elements)
    except Exception as e:
        # logger.error(f"Error building PDF: {str(e)}")
        raise

    buffer.seek(0)
    return buffer


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