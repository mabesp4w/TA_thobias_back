# filters.py
import django_filters
from .models import Produk, ProdukTerjual, LokasiUMKM


class ProdukFilter(django_filters.FilterSet):
    """Filter untuk model Produk"""
    harga_min = django_filters.NumberFilter(field_name='harga', lookup_expr='gte')
    harga_max = django_filters.NumberFilter(field_name='harga', lookup_expr='lte')
    stok_min = django_filters.NumberFilter(field_name='stok', lookup_expr='gte')
    stok_max = django_filters.NumberFilter(field_name='stok', lookup_expr='lte')

    class Meta:
        model = Produk
        fields = {
            'kategori': ['exact'],
            'aktif': ['exact'],
            'umkm': ['exact'],
            'tgl_dibuat': ['gte', 'lte'],
        }


class ProdukTerjualFilter(django_filters.FilterSet):
    """Filter untuk model ProdukTerjual"""
    tgl_penjualan_start = django_filters.DateFilter(field_name='tgl_penjualan', lookup_expr='gte')
    tgl_penjualan_end = django_filters.DateFilter(field_name='tgl_penjualan', lookup_expr='lte')
    total_penjualan_min = django_filters.NumberFilter(field_name='total_penjualan', lookup_expr='gte')
    total_penjualan_max = django_filters.NumberFilter(field_name='total_penjualan', lookup_expr='lte')

    class Meta:
        model = ProdukTerjual
        fields = {
            'produk': ['exact'],
            'lokasi_penjualan': ['exact'],
            # Hapus 'gte' dan 'lte' di sini karena Anda sudah punya custom filter
            'tgl_penjualan': ['exact'],
        }


class LokasiUMKMFilter(django_filters.FilterSet):
    """Filter untuk model LokasiUMKM"""
    provinsi = django_filters.UUIDFilter(field_name='kecamatan__kabupaten__provinsi')
    kabupaten = django_filters.UUIDFilter(field_name='kecamatan__kabupaten')

    class Meta:
        model = LokasiUMKM
        fields = {
            'pengguna': ['exact'],
            'kecamatan': ['exact'],
            'kode_pos': ['exact'],
        }