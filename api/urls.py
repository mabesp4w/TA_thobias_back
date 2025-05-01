from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    ProvinsiViewSet,
    KabupatenViewSet,
    KecamatanViewSet,
    ProfilUMKMViewSet,
    LokasiUMKMViewSet,
    KategoriProdukViewSet,
    ProdukViewSet,
    LokasiPenjualanViewSet,
    ProdukTerjualViewSet,
)

# Buat router untuk API
router = DefaultRouter()
router.register(r'provinsi', ProvinsiViewSet)
router.register(r'kabupaten', KabupatenViewSet)
router.register(r'kecamatan', KecamatanViewSet)
router.register(r'profil-umkm', ProfilUMKMViewSet)
router.register(r'lokasi-umkm', LokasiUMKMViewSet)
router.register(r'kategori-produk', KategoriProdukViewSet)
router.register(r'produk', ProdukViewSet)
router.register(r'lokasi-penjualan', LokasiPenjualanViewSet)
router.register(r'produk-terjual', ProdukTerjualViewSet)

urlpatterns = [
    path('', include(router.urls)),
]