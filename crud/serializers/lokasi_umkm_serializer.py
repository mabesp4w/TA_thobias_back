from rest_framework import serializers
from ..models import LokasiUMKM
from django.contrib.auth import get_user_model

User = get_user_model()


class LokasiUMKMSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model LokasiUMKM
    """
    pengguna_detail = serializers.SerializerMethodField()
    kecamatan_detail = serializers.SerializerMethodField()
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()
    nm_bisnis = serializers.SerializerMethodField()

    # Direct access fields
    kecamatan_nama = serializers.CharField(source='kecamatan.nm_kecamatan', read_only=True)
    kabupaten_nama = serializers.CharField(source='kecamatan.kabupaten.nm_kabupaten', read_only=True)
    provinsi_nama = serializers.CharField(source='kecamatan.kabupaten.provinsi.nm_provinsi', read_only=True)
    pengguna_nama = serializers.SerializerMethodField()
    tipe_kabupaten = serializers.SerializerMethodField()

    class Meta:
        model = LokasiUMKM
        fields = ['id', 'pengguna', 'pengguna_nama', 'pengguna_detail', 'nm_bisnis',
                  'latitude', 'longitude', 'alamat_lengkap',
                  'kecamatan', 'kecamatan_nama', 'kecamatan_detail',
                  'kabupaten_nama', 'kabupaten_detail',
                  'provinsi_nama', 'provinsi_detail',
                  'tipe_kabupaten', 'kode_pos', 'tgl_update']
        read_only_fields = ['id', 'tgl_update']

    def get_pengguna_detail(self, obj):
        """
        Menampilkan detail pengguna
        """
        return {
            'id': obj.pengguna.id,
            'username': obj.pengguna.username,
            'email': obj.pengguna.email,
            'nama_lengkap': f"{obj.pengguna.first_name} {obj.pengguna.last_name}".strip(),
            'role': obj.pengguna.role
        }

    def get_pengguna_nama(self, obj):
        """
        Mendapatkan nama lengkap pengguna
        """
        return f"{obj.pengguna.first_name} {obj.pengguna.last_name}".strip()

    def get_nm_bisnis(self, obj):
        """
        Mendapatkan nama bisnis UMKM
        """
        if hasattr(obj.pengguna, 'profil_umkm') and obj.pengguna.profil_umkm.nm_bisnis:
            return obj.pengguna.profil_umkm.nm_bisnis
        return obj.pengguna.username

    def get_kecamatan_detail(self, obj):
        """
        Menampilkan detail kecamatan
        """
        return {
            'id': obj.kecamatan.id,
            'nm_kecamatan': obj.kecamatan.nm_kecamatan,
            'kode': obj.kecamatan.kode
        }

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten
        """
        kab = obj.kecamatan.kabupaten
        return {
            'id': kab.id,
            'nm_kabupaten': kab.nm_kabupaten,
            'is_kota': kab.is_kota,
            'tipe': "Kota" if kab.is_kota else "Kabupaten",
            'kode': kab.kode
        }

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi
        """
        prov = obj.kecamatan.kabupaten.provinsi
        return {
            'id': prov.id,
            'nm_provinsi': prov.nm_provinsi
        }

    def get_tipe_kabupaten(self, obj):
        """
        Mengembalikan tipe kabupaten atau kota
        """
        return "Kota" if obj.kecamatan.kabupaten.is_kota else "Kabupaten"

    def validate(self, data):
        """
        Validasi data lokasi
        """
        # Validasi koordinat
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is not None and (latitude < -90 or latitude > 90):
            raise serializers.ValidationError({
                'latitude': 'Nilai latitude harus berada antara -90 dan 90.'
            })

        if longitude is not None and (longitude < -180 or longitude > 180):
            raise serializers.ValidationError({
                'longitude': 'Nilai longitude harus berada antara -180 dan 180.'
            })

        # Validasi kode pos
        kode_pos = data.get('kode_pos')
        if kode_pos and not kode_pos.isdigit():
            raise serializers.ValidationError({
                'kode_pos': 'Kode pos hanya boleh berisi angka.'
            })

        return data


class LokasiUMKMListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list LokasiUMKM (lightweight)
    """
    nm_bisnis = serializers.SerializerMethodField()
    pengguna_nama = serializers.SerializerMethodField()
    kecamatan_nama = serializers.CharField(source='kecamatan.nm_kecamatan', read_only=True)
    kabupaten_nama = serializers.CharField(source='kecamatan.kabupaten.nm_kabupaten', read_only=True)
    provinsi_nama = serializers.CharField(source='kecamatan.kabupaten.provinsi.nm_provinsi', read_only=True)

    pengguna_detail = serializers.SerializerMethodField()
    kecamatan_detail = serializers.SerializerMethodField()
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()

    class Meta:
        model = LokasiUMKM
        fields = ['id', 'pengguna', 'pengguna_nama', 'pengguna_detail', 'nm_bisnis',
                  'alamat_lengkap', 'kecamatan_nama', 'kabupaten_nama', 'provinsi_nama',
                  'kecamatan_detail', 'kabupaten_detail', 'provinsi_detail',
                  'kode_pos', 'tgl_update']

    def get_nm_bisnis(self, obj):
        """
        Mendapatkan nama bisnis UMKM
        """
        if hasattr(obj.pengguna, 'profil_umkm') and obj.pengguna.profil_umkm.nm_bisnis:
            return obj.pengguna.profil_umkm.nm_bisnis
        return obj.pengguna.username

    def get_pengguna_nama(self, obj):
        """
        Mendapatkan nama lengkap pengguna
        """
        return f"{obj.pengguna.first_name} {obj.pengguna.last_name}".strip()

    def get_pengguna_detail(self, obj):
        """
        Menampilkan detail pengguna (versi ringkas)
        """
        return {
            'id': obj.pengguna.id,
            'username': obj.pengguna.username,
            'nama_lengkap': f"{obj.pengguna.first_name} {obj.pengguna.last_name}".strip()
        }

    def get_kecamatan_detail(self, obj):
        """
        Menampilkan detail kecamatan (versi ringkas)
        """
        return {
            'id': obj.kecamatan.id,
            'nm_kecamatan': obj.kecamatan.nm_kecamatan
        }

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten (versi ringkas)
        """
        kab = obj.kecamatan.kabupaten
        return {
            'id': kab.id,
            'nm_kabupaten': kab.nm_kabupaten,
            'is_kota': kab.is_kota
        }

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi (versi ringkas)
        """
        prov = obj.kecamatan.kabupaten.provinsi
        return {
            'id': prov.id,
            'nm_provinsi': prov.nm_provinsi
        }