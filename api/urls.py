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
    ProdukTerjualViewSet, KategoriLokasiPenjualanViewSet, SalesViewSet,
)
from api.views.grafik_view import grafik_penjualan_view, grafik_penjualan_per_umkm_view, list_umkm_view, \
    ringkasan_penjualan_view
from api.views.statistik_view import StatistikViewSet

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
router.register(r'kategori-lokasi-penjualan', KategoriLokasiPenjualanViewSet)
router.register(r'export-excel', SalesViewSet, basename='export-excel')
router.register(r'statistik', StatistikViewSet, basename='statistik')


urlpatterns = [
    path('', include(router.urls)),
    path('grafik-penjualan/', grafik_penjualan_view, name='grafik-penjualan'),
    path('grafik-penjualan-per-umkm/', grafik_penjualan_per_umkm_view, name='   grafik-penjualan-per-umkm'),
    path('list-umkm/', list_umkm_view, name='list-umkm'),
    path('ringkasan-penjualan/', ringkasan_penjualan_view, name='ringkasan-penjualan'),

    path('promosi/', include('api.promosi_urls')),

]