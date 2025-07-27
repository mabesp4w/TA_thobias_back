from rest_framework import serializers
from ..models import KategoriProduk


class KategoriProdukSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model KategoriProduk
    """
    produk_count = serializers.SerializerMethodField()

    class Meta:
        model = KategoriProduk
        fields = ['id', 'nm_kategori', 'jasa', 'desc', 'produk_count']
        read_only_fields = ['id']

    def get_produk_count(self, obj):
        """
        Menghitung jumlah produk dalam kategori ini
        """
        return obj.produk.count()

    def validate_nm_kategori(self, value):
        """
        Validasi nama kategori
        """
        # Cek duplikasi nama kategori
        if KategoriProduk.objects.filter(nm_kategori__iexact=value).exists():
            if self.instance and self.instance.nm_kategori.lower() == value.lower():
                return value
            raise serializers.ValidationError("Kategori dengan nama ini sudah ada.")
        return value


class KategoriProdukListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list KategoriProduk (lightweight)
    """
    produk_count = serializers.SerializerMethodField()

    class Meta:
        model = KategoriProduk
        fields = ['id', 'nm_kategori', 'jasa', 'produk_count']

    def get_produk_count(self, obj):
        """
        Menghitung jumlah produk dalam kategori ini
        """
        return obj.produk.count()