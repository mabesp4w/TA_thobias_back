from rest_framework import serializers
from ..models import KategoriLokasi


class KategoriLokasiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model KategoriLokasi
    """

    class Meta:
        model = KategoriLokasi
        fields = ['id', 'nm_kategori_lokasi', 'desc']
        read_only_fields = ['id']

    def validate_nm_kategori_lokasi(self, value):
        """
        Validasi nama kategori
        """
        # Cek duplikasi nama kategori
        if KategoriLokasi.objects.filter(nm_kategori_lokasi__iexact=value).exists():
            if self.instance and self.instance.nm_kategori_lokasi.lower() == value.lower():
                return value
            raise serializers.ValidationError("Kategori Lokasi Penjualan dengan nama ini sudah ada.")
        return value


class KategoriLokasiListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list KategoriLokasi (lightweight)
    """

    class Meta:
        model = KategoriLokasi
        fields = ['id', 'nm_kategori_lokasi', 'desc']