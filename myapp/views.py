from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import BadHeaderError
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Client, Company, Invoice, InvoiceItem, Item
from .permissions import (
    AdminFullAccessPermission,
    IsAuthenticatedUser,
    OwnerOrAdminPermission,
)
from .serializers import (
    ClientSerializer,
    CompanySerializer,
    InvoiceItemSerializer,
    InvoiceSerializer,
    ItemSerializer,
    RegisterSerializer,
)
from .utils import generate_invoice_pdf, send_invoice_email



# Create your views here.


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]


class RefreshAPIView(TokenRefreshView):
    permission_classes = [AllowAny]


class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticatedUser, OwnerOrAdminPermission]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticatedUser(), AdminFullAccessPermission()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Company.objects.all()
        return Company.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticatedUser, OwnerOrAdminPermission]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticatedUser(), AdminFullAccessPermission()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        invoice = self.get_object()

        if invoice.is_locked:
            raise ValidationError("This invoice is locked and cannot be edited.")

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        invoice = self.get_object()

        if invoice.is_locked:
            raise ValidationError("This invoice is locked and cannot be edited.")

        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_buffer = generate_invoice_pdf(invoice)

        return HttpResponse(
            pdf_buffer,
            content_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="invoice_{invoice.invoice_no}.pdf"'
            }
        )

    @action(detail=True, methods=["get", "post"])
    def send_email(self, request, pk=None):
        invoice = self.get_object()

        try:
            send_invoice_email(invoice)
            return Response(
                {"detail": "Invoice email sent successfully."},
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (BadHeaderError, ObjectDoesNotExist) as exc:
            return Response(
                {"detail": f"Failed to prepare email: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Failed to send invoice email due to a server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    

class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticatedUser, OwnerOrAdminPermission]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticatedUser(), AdminFullAccessPermission()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Client.objects.all()
        return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    

class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedUser, OwnerOrAdminPermission]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticatedUser(), AdminFullAccessPermission()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Item.objects.all()
        return Item.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class InvoiceItemViewSet(ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        return InvoiceItem.objects.filter(invoice__user=self.request.user)

    def perform_create(self, serializer):
        invoice = serializer.validated_data['invoice']
        item = serializer.validated_data['item']

        if invoice.is_locked:
            raise ValidationError("Cannot add items to a locked invoice.")
        if invoice.user != self.request.user or item.user != self.request.user:
            raise ValidationError("You can only add your own items to your own invoices.")

        serializer.save()
