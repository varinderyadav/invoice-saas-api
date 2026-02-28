from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User




class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=100)
    business_name = models.CharField(max_length=150 ,null=True, blank=True)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=15)
    website = models.URLField(blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)

    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    address = models.TextField(blank=True, null=True)

    stamp = models.ImageField(upload_to='stamps/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    def __str__(self):
        return self.business_name


class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='clients'
    )

    business_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15)
    gst_number = models.CharField(max_length=20, blank=True, null=True)

    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.business_name




class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_code = models.CharField(max_length=50)
    item_name = models.CharField(max_length=150)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def amount(self):
        return self.quantity * self.price

    def gst_amount(self):
        return (self.amount() * self.gst_rate) / 100

    def total_amount(self):
        return self.amount() + self.gst_amount()

    def __str__(self):
        return self.item_name




class Invoice(models.Model):
    STATUS_CHOICES = (
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    selected_template = models.CharField(max_length=50)
    invoice_title = models.CharField(max_length=100, default='Invoice')

    invoice_no = models.CharField(max_length=50, unique=True , blank=True)
    invoice_date = models.DateField()
    is_locked = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    item_subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    item_subtotal_gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    item_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Auto generate invoice number
        if not self.invoice_no:
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_no__startswith=f"INV-{year}"
            ).order_by('id').last()

            if last_invoice:
                last_number = int(last_invoice.invoice_no.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.invoice_no = f"INV-{year}-{str(new_number).zfill(4)}"

        # Lock invoice if paid or cancelled
        if self.status in ['paid', 'cancelled']:
            self.is_locked = True

        super().save(*args, **kwargs)

    def calculate_totals(self):
        subtotal = 0
        gst = 0

        for item in self.invoice_items.all():
            subtotal += item.amount()
            gst += item.gst_amount()

        self.item_subtotal_amount = subtotal
        self.item_subtotal_gst = gst
        self.item_total = subtotal + gst

        super().save(
            update_fields=[
                'item_subtotal_amount',
                'item_subtotal_gst',
                'item_total'
            ]
        )
    def __str__(self):
        return self.invoice_no




class Activity(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    event = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice.invoice_no} - {self.event}"



class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='invoice_items'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def amount(self):
        return self.quantity * self.price

    def gst_amount(self):
        return (self.amount() * self.gst_rate) / 100

    def total_amount(self):
        return self.amount() + self.gst_amount()

    def __str__(self):
        return f"{self.invoice.invoice_no} - {self.item.item_name}"
    
