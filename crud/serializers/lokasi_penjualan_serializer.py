from rest_framework import serializers
from ..models import LokasiPenjualan


class LokasiPenjualanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model LokasiPenjualan
    """
    kecamatan_detail = serializers.SerializerMethodField()
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()
    total_penjualan = serializers.SerializerMethodField()

    # Direct access fields
    kecamatan_nama = serializers.CharField(source='kecamatan.nm_kecamatan', read_only=True, allow_null=True)
    kabupaten_nama = serializers.SerializerMethodField()
    provinsi_nama = serializers.SerializerMethodField()

    class Meta:
        model = LokasiPenjualan
        fields = ['id', 'nm_lokasi', 'tipe_lokasi', 'alamat', 'latitude', 'longitude',
                  'kecamatan', 'kecamatan_nama', 'kabupaten_nama', 'provinsi_nama',
                  'kecamatan_detail', 'kabupaten_detail', 'provinsi_detail',
                  'tlp_pengelola', 'total_penjualan']
        read_only_fields = ['id', 'total_penjualan']

    def get_kecamatan_detail(self, obj):
        """
        Menampilkan detail kecamatan
        """
        if not obj.kecamatan:
            return None

        return {
            'id': obj.kecamatan.id,
            'nm_kecamatan': obj.kecamatan.nm_kecamatan,
            'kode': obj.kecamatan.kode
        }

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten
        """
        if not obj.kecamatan or not obj.kecamatan.kabupaten:
            return None

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
        if not obj.kecamatan or not obj.kecamatan.kabupaten or not obj.kecamatan.kabupaten.provinsi:
            return None

        prov = obj.kecamatan.kabupaten.provinsi
        return {
            'id': prov.id,
            'nm_provinsi': prov.nm_provinsi
        }

    def get_total_penjualan(self, obj):
        """
        Menghitung total penjualan di lokasi ini
        """
        return obj.penjualan.count()

    def get_kabupaten_nama(self, obj):
        """
        Mendapatkan nama kabupaten
        """
        if obj.kecamatan and obj.kecamatan.kabupaten:
            kab = obj.kecamatan.kabupaten
            prefix = "Kota" if kab.is_kota else "Kabupaten"
            return f"{prefix} {kab.nm_kabupaten}"
        return None

    def get_provinsi_nama(self, obj):
        """
        Mendapatkan nama provinsi
        """
        if obj.kecamatan and obj.kecamatan.kabupaten and obj.kecamatan.kabupaten.provinsi:
            return obj.kecamatan.kabupaten.provinsi.nm_provinsi
        return None

    def validate(self, data):
        """
        Validasi data lokasi penjualan
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

        # Validasi nomor telepon
        tlp = data.get('tlp_pengelola')
        if tlp and not tlp.isdigit():
            raise serializers.ValidationError({
                'tlp_pengelola': 'Nomor telepon hanya boleh berisi angka.'
            })

        return data


class LokasiPenjualanListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list LokasiPenjualan (lightweight)
    """
    kecamatan_nama = serializers.SerializerMethodField()
    kabupaten_nama = serializers.SerializerMethodField()
    provinsi_nama = serializers.SerializerMethodField()
    total_penjualan = serializers.SerializerMethodField()

    kecamatan_detail = serializers.SerializerMethodField()
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()

    class Meta:
        model = LokasiPenjualan
        fields = ['id', 'nm_lokasi', 'tipe_lokasi', 'alamat', 'kecamatan_nama',
                  'kabupaten_nama', 'provinsi_nama', 'kecamatan_detail',
                  'kabupaten_detail', 'provinsi_detail', 'total_penjualan']

    def get_kecamatan_nama(self, obj):
        """
        Mendapatkan nama kecamatan
        """
        if obj.kecamatan:
            return obj.kecamatan.nm_kecamatan
        return None

    def get_kabupaten_nama(self, obj):
        """
        Mendapatkan nama kabupaten
        """
        if obj.kecamatan and obj.kecamatan.kabupaten:
            kab = obj.kecamatan.kabupaten
            prefix = "Kota" if kab.is_kota else "Kabupaten"
            return f"{prefix} {kab.nm_kabupaten}"
        return None

    def get_provinsi_nama(self, obj):
        """
        Mendapatkan nama provinsi
        """
        if obj.kecamatan and obj.kecamatan.kabupaten and obj.kecamatan.kabupaten.provinsi:
            return obj.kecamatan.kabupaten.provinsi.nm_provinsi
        return None

    def get_total_penjualan(self, obj):
        """
        Menghitung total penjualan di lokasi ini
        """
        return obj.penjualan.count()

    def get_kecamatan_detail(self, obj):
        """
        Menampilkan detail kecamatan (versi ringkas)
        """
        if not obj.kecamatan:
            return None

        return {
            'id': obj.kecamatan.id,
            'nm_kecamatan': obj.kecamatan.nm_kecamatan
        }

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten (versi ringkas)
        """
        if not obj.kecamatan or not obj.kecamatan.kabupaten:
            return None

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
        if not obj.kecamatan or not obj.kecamatan.kabupaten or not obj.kecamatan.kabupaten.provinsi:
            return None

        prov = obj.kecamatan.kabupaten.provinsi
        return {
            'id': prov.id,
            'nm_provinsi': prov.nm_provinsi
        }