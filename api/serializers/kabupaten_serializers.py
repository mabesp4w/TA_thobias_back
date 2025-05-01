from rest_framework import serializers

from crud.models import Kabupaten
from .provinsi_serializers import ProvinsiSerializer


class KabupatenSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Kabupaten (read-only)
    """
    provinsi = ProvinsiSerializer(read_only=True)
    nama_lengkap = serializers.SerializerMethodField()

    def get_nama_lengkap(self, obj):
        prefix = "Kota" if obj.is_kota else "Kabupaten"
        return f"{prefix} {obj.nm_kabupaten}"

    class Meta:
        model = Kabupaten
        fields = ['id', 'provinsi', 'nm_kabupaten', 'kode', 'is_kota', 'nama_lengkap']
        read_only_fields = fields