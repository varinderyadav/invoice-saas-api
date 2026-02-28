from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Invoice, Company, Client , Item , InvoiceItem


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('user',)




class ClientSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['company'].queryset = Company.objects.filter(user=request.user)

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ('user',)



class ItemSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    gst_amount = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'user',
            'item_code',
            'item_name',
            'price',
            'quantity',
            'gst_rate',
            'amount',
            'gst_amount',
            'total_amount',
        ]
        read_only_fields = ('user',)

    def get_amount(self, obj):
        return obj.amount()

    def get_gst_amount(self, obj):
        return obj.gst_amount()

    def get_total_amount(self, obj):
        return obj.total_amount()
    


class InvoiceItemSerializer(serializers.ModelSerializer):
    invoice = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.all()
    )
    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all()
    )
    item_name = serializers.CharField(source='item.item_name', read_only=True)

    amount = serializers.SerializerMethodField()
    gst_amount = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'invoice',
            'item',
            'item_name',    
            'quantity',
            'price',
            'gst_rate',
            'amount',
            'gst_amount',
            'total_amount',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['invoice'].queryset = Invoice.objects.filter(user=request.user)
            self.fields['item'].queryset = Item.objects.filter(user=request.user)

    def get_amount(self, obj):
        return obj.amount()

    def get_gst_amount(self, obj):
        return obj.gst_amount()

    def get_total_amount(self, obj):
        return obj.total_amount()



class InvoiceSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemSerializer(many=True, read_only=True)

    company_name = serializers.CharField(
        source='company.business_name',
        read_only=True
    )
    client_name = serializers.CharField(
        source='client.business_name',
        read_only=True
    )

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = (
            'user',
            'invoice_no',
            'item_subtotal_amount',
            'item_subtotal_gst',
            'item_total',
            'is_locked',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['company'].queryset = Company.objects.filter(user=request.user)
            self.fields['client'].queryset = Client.objects.filter(user=request.user)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
        )
        read_only_fields = ("id",)

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
