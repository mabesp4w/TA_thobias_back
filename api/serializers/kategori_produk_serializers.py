from rest_framework import serializers

from crud.models import KategoriProduk


class KategoriProdukSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model KategoriProduk (read-only)
    """
    jumlah_produk = serializers.SerializerMethodField()

    def get_jumlah_produk(self, obj):
        return obj.produk.count()

    class Meta:
        model = KategoriProduk
        fields = ['id', 'nm_kategori', 'desc', 'jumlah_produk']
        read_only_fields = fields