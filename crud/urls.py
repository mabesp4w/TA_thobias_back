from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from crud.views import UserViewSet, LokasiPenjualanViewSet, ProdukTerjualViewSet, ProfilUMKMViewSet

from crud.views.provinsi_view import ProvinsiViewSet
from crud.views.kabupaten_view import KabupatenViewSet
from crud.views.kecamatan_view import KecamatanViewSet
from crud.views.lokasi_umkm_view import LokasiUMKMViewSet
from crud.views.kategori_produk_view import KategoriProdukViewSet
from crud.views.produk_view import ProdukViewSet

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
router.register(r'user', UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # API Endpoints
]
