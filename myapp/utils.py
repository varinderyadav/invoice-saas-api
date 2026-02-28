import io

from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_invoice_pdf(invoice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(f"Invoice: {invoice.invoice_no}", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Company: {invoice.company.business_name}", styles["Normal"]))
    elements.append(Paragraph(f"Client: {invoice.client.business_name}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Item", "Qty", "Price", "GST", "Total"]]
    for item in invoice.invoice_items.all():
        data.append(
            [
                item.item.item_name,
                item.quantity,
                str(item.price),
                str(item.gst_amount()),
                str(item.total_amount()),
            ]
        )

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Subtotal: {invoice.item_subtotal_amount}", styles["Normal"]))
    elements.append(Paragraph(f"GST: {invoice.item_subtotal_gst}", styles["Normal"]))
    elements.append(Paragraph(f"Grand Total: {invoice.item_total}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_invoice_email(invoice):
    client_email = getattr(invoice.client, "email", None)
    if not client_email:
        raise ValueError("Client email is missing for this invoice.")

    pdf_buffer = generate_invoice_pdf(invoice)

    subject = f"Invoice {invoice.invoice_no}"
    message = (
        f"Hello {invoice.client.business_name},\n\n"
        "Please find attached your invoice.\n\n"
        f"Invoice No: {invoice.invoice_no}\n"
        f"Total: {invoice.item_total}\n\n"
        "Thank you."
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[client_email],
    )
    email.attach(
        f"invoice_{invoice.invoice_no}.pdf",
        pdf_buffer.getvalue(),
        "application/pdf",
    )
    email.send(fail_silently=False)
