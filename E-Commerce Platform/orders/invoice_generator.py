import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.http import HttpResponse

def render_to_pdf(order):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Title & Order Header
    title_style = ParagraphStyle('InvTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor("#1A365D"))
    story.append(Paragraph("ShopEase Tax Invoice", title_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [f"Order ID: #{order.id}", f"Date: {order.created.strftime('%d-%b-%Y') if hasattr(order, 'created') else (order.created_at.strftime('%d-%b-%Y') if hasattr(order, 'created_at') else 'N/A')}"],
        [f"Customer: {order.user.get_full_name() or order.user.username if order.user else 'Guest'}", f"Payment Mode: {order.payment_method} ({'Paid' if getattr(order, 'paid', False) else 'Unpaid'})"],
    ]
    t_meta = Table(meta_data, colWidths=[260, 260])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#334155")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # Order Items Table
    items_data = [["Item", "Price", "Qty", "Total"]]
    for item in order.items.all():
        items_data.append([
            item.product.name if item.product else "Item",
            f"Rs. {item.price}",
            str(item.quantity),
            f"Rs. {item.price * item.quantity}"
        ])

    items_data.append(["", "", "Total Amount:", f"Rs. {order.total_amount}"])
    if getattr(order, 'wallet_discount', 0) > 0:
        items_data.append(["", "", "Wallet Applied:", f"-Rs. {order.wallet_discount}"])

    t_items = Table(items_data, colWidths=[240, 90, 60, 130])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_items)

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{order.id}.pdf"'
    return response
