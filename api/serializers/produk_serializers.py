from rest_framework import serializers

from crud.models import Produk
from .profil_umkm_serializers import UserLiteSerializer
from .kategori_produk_serializers import KategoriProdukSerializer


class ProdukSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Produk (read-only)
    """
    umkm = UserLiteSerializer(read_only=True)
    kategori = KategoriProdukSerializer(read_only=True)
    nama_bisnis = serializers.SerializerMethodField()
    tgl_dibuat_formatted = serializers.SerializerMethodField()
    tgl_update_formatted = serializers.SerializerMethodField()

    def get_nama_bisnis(self, obj):
        return getattr(getattr(obj.umkm, 'profil_umkm', None), 'nm_bisnis', obj.umkm.username)

    def get_tgl_dibuat_formatted(self, obj):
        return obj.tgl_dibuat.strftime("%d %b %Y, %H:%M")

    def get_tgl_update_formatted(self, obj):
        return obj.tgl_update.strftime("%d %b %Y, %H:%M")

    class Meta:
        model = Produk
        fields = ['id', 'umkm', 'kategori', 'nm_produk', 'desc', 'harga', 'stok',
                  'satuan', 'bahan_baku', 'metode_produksi', 'aktif', 'tgl_dibuat',
                  'tgl_update', 'nama_bisnis', 'tgl_dibuat_formatted', 'tgl_update_formatted']
        read_only_fields = fields