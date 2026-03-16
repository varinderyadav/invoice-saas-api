import io
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def format_money(value):
    try:
        decimal_value = Decimal(value)
    except Exception:
        decimal_value = Decimal("0")
    return f"{decimal_value:.2f}"


def build_client_address(client):
    parts = [
        getattr(client, "address", "") or "",
        getattr(client, "city", "") or "",
        getattr(client, "state", "") or "",
        getattr(client, "pincode", "") or "",
    ]
    return ", ".join([part for part in parts if part]) or "-"


def generate_invoice_pdf(invoice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Company Name: {invoice.company.business_name}", styles["Title"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Invoice Title: {invoice.invoice_title}", styles["Normal"]))
    elements.append(Paragraph(f"Invoice Number: {invoice.invoice_no}", styles["Normal"]))
    elements.append(Paragraph(f"Invoice Date: {invoice.invoice_date}", styles["Normal"]))
    elements.append(Paragraph(f"Status: {invoice.status}", styles["Normal"]))

    elements.append(Spacer(1, 14))
    elements.append(Paragraph("Client Details", styles["Heading3"]))
    elements.append(Paragraph(f"Client Name: {invoice.client.business_name}", styles["Normal"]))
    elements.append(Paragraph(f"Client Email: {invoice.client.email or '-'}", styles["Normal"]))
    elements.append(Paragraph(f"Client Address: {build_client_address(invoice.client)}", styles["Normal"]))

    elements.append(Spacer(1, 14))
    data = [["Item Name", "Quantity", "Unit Price", "GST", "Total"]]
    for invoice_item in invoice.invoice_items.all():
        data.append(
            [
                invoice_item.item.item_name,
                str(invoice_item.quantity),
                format_money(invoice_item.price),
                f"{format_money(invoice_item.gst_amount())} ({format_money(invoice_item.gst_rate)}%)",
                format_money(invoice_item.total_amount()),
            ]
        )

    item_table = Table(data, repeatRows=1)
    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )

    elements.append(item_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph(f"Subtotal: {format_money(invoice.item_subtotal_amount)}", styles["Normal"]))
    elements.append(Paragraph(f"GST: {format_money(invoice.item_subtotal_gst)}", styles["Normal"]))
    elements.append(Paragraph(f"Grand Total: {format_money(invoice.item_total)}", styles["Heading3"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_invoice_email(invoice):
    client_email = getattr(invoice.client, "email", None)
    if not client_email:
        raise ValueError("Client email is missing for this invoice.")

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        raise ValueError("Email credentials are not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.")

    if not settings.DEFAULT_FROM_EMAIL:
        raise ValueError("DEFAULT_FROM_EMAIL is not configured.")

    pdf_buffer = generate_invoice_pdf(invoice)

    client_name = getattr(invoice.client, "name", None) or getattr(invoice.client, "business_name", "Client")

    subject = f"Invoice {invoice.invoice_no}"
    message = (
        f"Hello {client_name},\n\n"
        "Please find your invoice attached.\n\n"
        f"Invoice Number: {invoice.invoice_no}\n"
        f"Invoice Date: {invoice.invoice_date}\n"
        f"Total Amount: {format_money(invoice.item_total)}\n\n"
        "Thank you."
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_email],
    )
    email.attach(
        f"invoice-{invoice.invoice_no}.pdf",
        pdf_buffer.getvalue(),
        "application/pdf",
    )
    email.send(fail_silently=False)
