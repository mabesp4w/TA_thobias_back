from rest_framework import viewsets, permissions
from api.serializers import KategoriProdukSerializer
from crud.models import KategoriProduk


class KategoriProdukViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data kategori produk.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = KategoriProduk.objects.all()
    serializer_class = KategoriProdukSerializer
    filterset_fields = ['nm_kategori']
    search_fields = ['nm_kategori', 'desc']
    ordering_fields = ['nm_kategori']
    ordering = ['nm_kategori']