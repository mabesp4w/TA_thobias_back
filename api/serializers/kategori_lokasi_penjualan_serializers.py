from rest_framework import serializers

from crud.models import KategoriLokasi
from .kabupaten_serializers import KabupatenSerializer


class KategoriLokasiPenjualanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model KategoriLokasiPenjualan (read-only)
    """

    class Meta:
        model = KategoriLokasi
        fields = ['id', 'nm_kategori_lokasi', 'desc']
        read_only_fields = fields