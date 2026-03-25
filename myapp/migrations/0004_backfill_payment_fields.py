from decimal import Decimal
from django.db import migrations


def backfill_payment_fields(apps, schema_editor):
    Invoice = apps.get_model("myapp", "Invoice")
    for invoice in Invoice.objects.all():
        total = invoice.item_total or Decimal("0")
        paid = invoice.total_paid_amount or Decimal("0")
        remaining = total - paid
        if paid == 0:
            status = "pending"
        elif paid < total:
            status = "partially_paid"
        else:
            status = "paid"
        invoice.remaining_amount = remaining
        invoice.payment_status = status
        invoice.save(update_fields=["remaining_amount", "payment_status"])


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0003_payment_and_invoice_payment_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_payment_fields, migrations.RunPython.noop),
    ]
