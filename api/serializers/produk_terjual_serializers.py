from rest_framework import serializers

from crud.models import ProdukTerjual
from .produk_serializers import ProdukSerializer
from .lokasi_penjualan_serializers import LokasiPenjualanSerializer


class ProdukTerjualSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model ProdukTerjual (read-only)
    """
    produk = ProdukSerializer(read_only=True)
    lokasi_penjualan = LokasiPenjualanSerializer(read_only=True)
    tgl_penjualan_formatted = serializers.SerializerMethodField()
    tgl_pelaporan_formatted = serializers.SerializerMethodField()

    def get_tgl_penjualan_formatted(self, obj):
        return obj.tgl_penjualan.strftime("%d %b %Y")

    def get_tgl_pelaporan_formatted(self, obj):
        return obj.tgl_pelaporan.strftime("%d %b %Y, %H:%M")

    class Meta:
        model = ProdukTerjual
        fields = ['id', 'produk', 'lokasi_penjualan', 'tgl_penjualan', 'jumlah_terjual',
                  'harga_jual', 'total_penjualan', 'catatan', 'tgl_pelaporan',
                  'tgl_penjualan_formatted', 'tgl_pelaporan_formatted']
        read_only_fields = fields