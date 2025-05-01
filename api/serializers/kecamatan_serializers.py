from rest_framework import serializers

from crud.models import Kecamatan
from .kabupaten_serializers import KabupatenSerializer


class KecamatanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Kecamatan (read-only)
    """
    kabupaten = KabupatenSerializer(read_only=True)
    nama_lengkap = serializers.SerializerMethodField()

    def get_nama_lengkap(self, obj):
        return f"{obj.nm_kecamatan}, {obj.kabupaten.nm_kabupaten}"

    class Meta:
        model = Kecamatan
        fields = ['id', 'kabupaten', 'nm_kecamatan', 'kode', 'nama_lengkap']
        read_only_fields = fields