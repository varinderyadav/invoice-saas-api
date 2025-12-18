from django.contrib import admin
from .models import Company, Invoice, Client
# Register your models here.

admin.site.register(Company)
admin.site.register(Invoice)    
admin.site.register(Client)