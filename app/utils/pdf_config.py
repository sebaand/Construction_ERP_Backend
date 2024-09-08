PDF_STYLE = {
    "page": {
        "size": "A4",
        "margins": {"top": 72, "bottom": 72, "left": 72, "right": 72}
    },
    "fonts": {
        "title": {"name": "Helvetica-Bold", "size": 20},
        "description": {"name": "Helvetica", "size": 14},
        "heading": {"name": "Helvetica-Bold", "size": 16},
        "body": {"name": "Helvetica", "size": 12},
        "signature": {"name": "Helvetica", "size": 12} 
    },
    "colors": {
        "title": "#000000",
        "description": "#333333",
        "heading": "#000000",
        "body": "#000000",
        "separator": "#CCCCCC"
    },
    "spacing": {
        "before_title": 12,
        "after_title": 6,
        "before_description": 6,
        "after_description": 12,
        "before_section": 12,
        "after_section": 6,
        "before_table": 12,
        "after_table": 12
    },
    "alignment": {
        "title": "CENTER",
        "description": "CENTER",
        "heading": "LEFT",
        "body": "LEFT"
    },
    "table": {
        "style": [
            ("BACKGROUND", (0, 0), (-1, 0), "#EEEEEE"),
            ("TEXTCOLOR", (0, 0), (-1, 0), "#000000"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), "#FFFFFF"),
            ("TEXTCOLOR", (0, 1), (-1, -1), "#000000"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 1, "#000000")
        ],
        "picture_column_width": 200  # in points
    },
    "separator": {
        "width": 1,
        "color": "#CCCCCC"
    }
}