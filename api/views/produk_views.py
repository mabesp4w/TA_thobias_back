from rest_framework import viewsets, permissions
from api.serializers import ProdukSerializer
from crud.models import Produk


class ProdukViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data produk.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    filterset_fields = ['umkm', 'kategori', 'nm_produk', 'aktif']
    search_fields = ['nm_produk', 'desc', 'bahan_baku', 'metode_produksi',
                     'umkm__username', 'kategori__nm_kategori']
    ordering_fields = ['nm_produk', 'harga', 'tgl_dibuat', 'tgl_update']
    ordering = ['-tgl_update']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()

        # Filter produk berdasarkan parameter
        kategori_id = self.request.query_params.get('kategori_id')
        min_harga = self.request.query_params.get('min_harga')
        max_harga = self.request.query_params.get('max_harga')

        if kategori_id:
            queryset = queryset.filter(kategori__id=kategori_id)

        if min_harga:
            queryset = queryset.filter(harga__gte=min_harga)

        if max_harga:
            queryset = queryset.filter(harga__lte=max_harga)

        # Hanya tampilkan produk aktif
        aktif = self.request.query_params.get('aktif')
        if aktif is None:  # jika parameter tidak disertakan, default true
            queryset = queryset.filter(aktif=True)
        elif aktif.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(aktif=True)

        # Filter hanya menampilkan produk milik sendiri jika bukan admin
        user = self.request.user
        if user.role != 'admin':
            queryset = queryset.filter(umkm=user)

        return queryset