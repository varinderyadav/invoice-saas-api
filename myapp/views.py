import logging
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

from decimal import Decimal
from .models import Client, Company, Invoice, InvoiceItem, Item, Payment
from .permissions import IsAuthenticatedUser, OwnerOrAdminPermission
from .serializers import (
    ClientSerializer,
    CompanySerializer,
    InvoiceItemSerializer,
    InvoiceSerializer,
    ItemSerializer,
    PaymentSerializer,
    RegisterSerializer,
)
from .utils import generate_invoice_pdf, send_invoice_email

logger = logging.getLogger(__name__)

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

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_buffer = generate_invoice_pdf(invoice)
        filename = f"invoice-{invoice.invoice_no}.pdf"

        return HttpResponse(
            pdf_buffer.getvalue(),
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    @action(detail=True, methods=["post"], url_path="send-email")
    def send_email(self, request, pk=None):
        invoice = self.get_object()

        try:
            send_invoice_email(invoice)
            return Response(
                {"message": "Invoice email sent successfully"},
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
        except Exception as exc:
            logger.exception("Failed to send invoice email for invoice_id=%s", invoice.id)
            return Response(
                {"detail": f"Failed to send invoice email: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get", "post"], url_path="payments")
    def payments(self, request, pk=None):
        invoice = self.get_object()

        if request.method == "GET":
            payments = invoice.payments.order_by("-created_at")
            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data.get("amount")
        payment_method = serializer.validated_data.get("payment_method")

        if amount is None or amount <= 0:
            raise ValidationError("Payment amount must be greater than 0.")

        remaining = invoice.remaining_amount if invoice.remaining_amount is not None else invoice.item_total
        if amount > remaining:
            raise ValidationError("Payment amount cannot exceed the remaining amount.")

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
        )

        invoice.total_paid_amount = (invoice.total_paid_amount or Decimal("0")) + amount
        invoice.remaining_amount = invoice.item_total - invoice.total_paid_amount
        if invoice.total_paid_amount == 0:
            invoice.payment_status = "pending"
        elif invoice.total_paid_amount < invoice.item_total:
            invoice.payment_status = "partially_paid"
        else:
            invoice.payment_status = "paid"

        invoice.save(update_fields=["total_paid_amount", "remaining_amount", "payment_status"])

        return Response(
            {
                "message": "Payment recorded successfully.",
                "total_paid_amount": invoice.total_paid_amount,
                "remaining_amount": invoice.remaining_amount,
                "payment_status": invoice.payment_status,
            },
            status=status.HTTP_201_CREATED,
        )


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticatedUser, OwnerOrAdminPermission]

    def get_permissions(self):
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
        invoice = serializer.validated_data["invoice"]
        item = serializer.validated_data["item"]

        if invoice.is_locked:
            raise ValidationError("Cannot add items to a locked invoice.")
        if invoice.user != self.request.user or item.user != self.request.user:
            raise ValidationError("You can only add your own items to your own invoices.")

        serializer.save()
