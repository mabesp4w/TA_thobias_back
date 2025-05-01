from rest_framework import serializers

from crud.models import LokasiUMKM
from .kecamatan_serializers import KecamatanSerializer
from .profil_umkm_serializers import UserLiteSerializer


class LokasiUMKMSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model LokasiUMKM (read-only)
    """
    pengguna = UserLiteSerializer(read_only=True)
    kecamatan = KecamatanSerializer(read_only=True)
    tgl_update_formatted = serializers.SerializerMethodField()

    def get_tgl_update_formatted(self, obj):
        return obj.tgl_update.strftime("%d %b %Y, %H:%M")

    class Meta:
        model = LokasiUMKM
        fields = ['id', 'pengguna', 'latitude', 'longitude', 'alamat_lengkap',
                  'kecamatan', 'kode_pos', 'tgl_update', 'tgl_update_formatted']
        read_only_fields = fields