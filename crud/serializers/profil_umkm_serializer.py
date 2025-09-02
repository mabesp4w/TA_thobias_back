# serializers/profile_umkm_serializer

from rest_framework import serializers
from ..models import ProfilUMKM
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfilUMKMSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model ProfilUMKM
    """
    user_detail = serializers.SerializerMethodField()
    nama_pemilik = serializers.SerializerMethodField()

    # Direct access fields
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = ProfilUMKM
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name',
                  'user_detail', 'nama_pemilik', 'nm_bisnis', 'alamat',
                  'tlp', 'desc_bisnis', 'tgl_bergabung','total_laki','total_perempuan']
        read_only_fields = ['id', 'user', 'tgl_bergabung']

    def get_user_detail(self, obj):
        """
        Menampilkan detail user
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'role': obj.user.role,
            'is_active': obj.user.is_active,
            'date_joined': obj.user.date_joined
        }

    def get_nama_pemilik(self, obj):
        """
        Mendapatkan nama lengkap pemilik UMKM
        """
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def validate_nm_bisnis(self, value):
        """
        Validasi nama bisnis
        """
        if value and len(value) < 3:
            raise serializers.ValidationError("Nama bisnis terlalu pendek, minimal 3 karakter.")
        return value

    def validate_tlp(self, value):
        """
        Validasi nomor telepon
        """
        if value and not value.isdigit():
            raise serializers.ValidationError("Nomor telepon hanya boleh berisi angka.")
        return value


class ProfilUMKMListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list ProfilUMKM (lightweight)
    """
    nama_pemilik = serializers.SerializerMethodField()
    email_pemilik = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_detail = serializers.SerializerMethodField()

    class Meta:
        model = ProfilUMKM
        fields = ['id', 'user', 'username', 'nama_pemilik', 'email_pemilik', 'alamat',
                  'user_detail', 'nm_bisnis', 'tlp', 'tgl_bergabung', 'total_laki', 'total_perempuan']

    def get_nama_pemilik(self, obj):
        """
        Mendapatkan nama lengkap pemilik UMKM
        """
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def get_user_detail(self, obj):
        """
        Menampilkan detail user (versi ringkas)
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'nama_lengkap': f"{obj.user.first_name} {obj.user.last_name}".strip(),
            'role': obj.user.role
        }