from rest_framework import serializers
from django.contrib.auth.models import User

from crud.models import ProfilUMKM


class UserLiteSerializer(serializers.ModelSerializer):
    """
    Serializer sederhana untuk data User (read-only)
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']
        read_only_fields = fields


class ProfilUMKMSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model ProfilUMKM (read-only)
    """
    user = UserLiteSerializer(read_only=True)
    tgl_bergabung_formatted = serializers.SerializerMethodField()

    def get_tgl_bergabung_formatted(self, obj):
        return obj.tgl_bergabung.strftime("%d %b %Y, %H:%M")

    class Meta:
        model = ProfilUMKM
        fields = ['id', 'user', 'nm_bisnis', 'alamat', 'tlp', 'desc_bisnis',
                  'tgl_bergabung', 'tgl_bergabung_formatted']
        read_only_fields = fields