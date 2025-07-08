from rest_framework import viewsets, permissions
from api.serializers import KategoriLokasiPenjualanSerializer
from crud.models import KategoriLokasi


class KategoriLokasiPenjualanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data kategori produk.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = KategoriLokasi.objects.all()
    serializer_class = KategoriLokasiPenjualanSerializer
    filterset_fields = ['nm_kategori_lokasi']
    search_fields = ['nm_kategori_lokasi', 'desc']
    ordering_fields = ['nm_kategori_lokasi']
    ordering = ['nm_kategori_lokasi']