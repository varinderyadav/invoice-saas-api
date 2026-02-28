from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet,
    CompanyViewSet,
    InvoiceItemViewSet,
    InvoiceViewSet,
    ItemViewSet,
    LoginAPIView,
    RefreshAPIView,
    RegisterAPIView,
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'items', ItemViewSet)
router.register(r'invoice-items', InvoiceItemViewSet)



urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshAPIView.as_view(), name="auth-refresh"),
    path('', include(router.urls)),
]
