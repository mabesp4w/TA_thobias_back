from rest_framework import viewsets, permissions
from django.db.models import Sum
from api.serializers import ProdukTerjualSerializer
from crud.models import ProdukTerjual


class ProdukTerjualViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data produk terjual.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = ProdukTerjual.objects.all()
    serializer_class = ProdukTerjualSerializer
    filterset_fields = ['produk', 'lokasi_penjualan', 'tgl_penjualan']
    search_fields = ['produk__nm_produk', 'lokasi_penjualan__nm_lokasi', 'catatan']
    ordering_fields = ['tgl_penjualan', 'jumlah_terjual', 'total_penjualan']
    ordering = ['-tgl_penjualan']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()

        # Filter berdasarkan parameter
        produk_id = self.request.query_params.get('produk_id')
        kategori_id = self.request.query_params.get('kategori_id')
        lokasi_penjualan_id = self.request.query_params.get('lokasi_penjualan_id')
        tanggal_awal = self.request.query_params.get('tanggal_awal')
        tanggal_akhir = self.request.query_params.get('tanggal_akhir')

        if produk_id:
            queryset = queryset.filter(produk__id=produk_id)

        if kategori_id:
            queryset = queryset.filter(produk__kategori__id=kategori_id)

        if lokasi_penjualan_id:
            queryset = queryset.filter(lokasi_penjualan__id=lokasi_penjualan_id)

        if tanggal_awal:
            queryset = queryset.filter(tgl_penjualan__gte=tanggal_awal)

        if tanggal_akhir:
            queryset = queryset.filter(tgl_penjualan__lte=tanggal_akhir)

        # Filter hanya menampilkan penjualan produk milik sendiri jika bukan admin
        user = self.request.user
        if user.role != 'admin':
            queryset = queryset.filter(produk__umkm=user)

        return queryset