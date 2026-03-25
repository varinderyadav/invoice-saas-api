from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0002_client_company_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="payment_status",
            field=models.CharField(choices=[("pending", "Pending"), ("partially_paid", "Partially Paid"), ("paid", "Paid")], default="pending", max_length=20),
        ),
        migrations.AddField(
            model_name="invoice",
            name="remaining_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="invoice",
            name="total_paid_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("payment_method", models.CharField(choices=[("cash", "Cash"), ("online", "Online")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="myapp.invoice")),
            ],
        ),
    ]
