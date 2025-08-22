from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from crud.views import UserViewSet, LokasiPenjualanViewSet, ProdukTerjualViewSet, ProfilUMKMViewSet, \
    KategoriLokasiPenjualanViewSet, AdminViewSet
from crud.views.file_penjualan_view import FilePenjualanViewSet

from crud.views.provinsi_view import ProvinsiViewSet
from crud.views.kabupaten_view import KabupatenViewSet
from crud.views.kecamatan_view import KecamatanViewSet
from crud.views.lokasi_umkm_view import LokasiUMKMViewSet
from crud.views.kategori_produk_view import KategoriProdukViewSet
from crud.views.produk_view import ProdukViewSet
from django.conf import settings
from django.conf.urls.static import static

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
router.register(r'file-penjualan', FilePenjualanViewSet)
router.register(r'kategori-lokasi-penjualan', KategoriLokasiPenjualanViewSet)

router.register(r'administrator', AdminViewSet, basename='admin')


urlpatterns = [
    path('', include(router.urls)),
    # API Endpoints
]

# Add media URLs for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)