from rest_framework import serializers

from crud.models import LokasiPenjualan
from .kecamatan_serializers import KecamatanSerializer


class LokasiPenjualanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model LokasiPenjualan (read-only)
    """
    kecamatan = KecamatanSerializer(read_only=True)
    nama_lengkap = serializers.SerializerMethodField()

    def get_nama_lengkap(self, obj):
        kab_name = obj.kecamatan.kabupaten.nm_kabupaten if obj.kecamatan else "Tidak diketahui"
        return f"{obj.nm_lokasi} - ({kab_name})"

    class Meta:
        model = LokasiPenjualan
        fields = ['id', 'nm_lokasi', 'alamat', 'latitude', 'longitude',
                  'kecamatan', 'tlp_pengelola', 'nama_lengkap']
        read_only_fields = fields