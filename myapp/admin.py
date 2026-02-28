from django.contrib import admin
from .models import Company, Invoice, Client , Activity , Item , InvoiceItem
# Register your models here.

admin.site.register(Company)
admin.site.register(Invoice)    
admin.site.register(Client)
admin.site.register(Activity)
admin.site.register(Item)
admin.site.register(InvoiceItem)