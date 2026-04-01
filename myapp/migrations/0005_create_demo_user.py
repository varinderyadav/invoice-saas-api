from django.conf import settings
from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_demo_user(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    UserModel = apps.get_model(app_label, model_name)

    email = "demo@invoicesaas.com"
    username = email

    if UserModel.objects.filter(username=username).exists() or UserModel.objects.filter(email=email).exists():
        return

    user = UserModel(username=username, email=email, is_staff=False, is_superuser=False)
    user.password = make_password("Csk007@vy")
    user.save()


def reverse_demo_user(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    UserModel = apps.get_model(app_label, model_name)
    UserModel.objects.filter(username="demo@invoicesaas.com").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0004_backfill_payment_fields"),
    ]

    operations = [
        migrations.RunPython(create_demo_user, reverse_demo_user),
    ]
