from rest_framework import serializers
from .models import Invoice, Company ,Client 

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all()
    )

    class Meta:
        model = Invoice
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    companies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Company.objects.all()
    )

    class Meta:
        model = Client
        fields = '__all__'
