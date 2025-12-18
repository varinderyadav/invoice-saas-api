from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)

    def __str__(self):
        return self.name
    

class Invoice(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    issue_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Invoice {self.id} for {self.client_name}" 
      

class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    companies = models.ManyToManyField(
        Company,
        related_name='clients'
    )

    def __str__(self):
        return self.name