# api/urls/promosi_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.promosi_views import PromosiViewSet, PromosiKategoriViewSet

# Jika masih error, uncomment baris di bawah ini dan comment yang atas
# from api.views.simple_promosi_views import SimplePromosiViewSet

# Router untuk API promosi
promosi_router = DefaultRouter()

# Gunakan ViewSet utama (jika masih error, ganti dengan SimplePromosiViewSet)
promosi_router.register(r'products', PromosiViewSet, basename='promosi-products')

# Jika error, comment baris di atas dan uncomment baris di bawah:
# promosi_router.register(r'products', SimplePromosiViewSet, basename='promosi-products')

promosi_router.register(r'categories', PromosiKategoriViewSet, basename='promosi-categories')

urlpatterns = [
    path('', include(promosi_router.urls)),
]

# URL patterns yang akan tersedia:
# GET /api/promosi/products/                     - List produk dengan pagination dan filter
# GET /api/promosi/products/{id}/                - Detail produk
# GET /api/promosi/products/categories/          - Kategori dengan statistik
# GET /api/promosi/products/stats/               - Statistik promosi
# GET /api/promosi/categories/                   - List kategori dengan statistik
# GET /api/promosi/categories/{id}/              - Detail kategori