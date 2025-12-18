from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, InvoiceViewSet, ClientViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'clients', ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
