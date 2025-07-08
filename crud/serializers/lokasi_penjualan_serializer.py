# Update untuk serializers/lokasi_penjualan_serializer.py

from rest_framework import serializers
from ..models import LokasiPenjualan


class LokasiPenjualanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model LokasiPenjualan
    """
    kecamatan_detail = serializers.SerializerMethodField()
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()
    kategori_lokasi_detail = serializers.SerializerMethodField()
    umkm_detail = serializers.SerializerMethodField()
    total_penjualan = serializers.SerializerMethodField()

    # Direct access fields
    kecamatan_nama = serializers.CharField(source='kecamatan.nm_kecamatan', read_only=True, allow_null=True)
    kabupaten_nama = serializers.SerializerMethodField()
    provinsi_nama = serializers.SerializerMethodField()
    kategori_lokasi_nama = serializers.CharField(source='kategori_lokasi.nm_kategori_lokasi', read_only=True,
                                                 allow_null=True)
    umkm_nama = serializers.SerializerMethodField()

    class Meta:
        model = LokasiPenjualan
        fields = ['id', 'nm_lokasi', 'alamat', 'latitude', 'longitude',
                  'kecamatan', 'kecamatan_nama', 'kabupaten_nama', 'provinsi_nama',
                  'kecamatan_detail', 'kabupaten_detail', 'provinsi_detail',
                  'kategori_lokasi', 'kategori_lokasi_nama', 'kategori_lokasi_detail',
                  'umkm', 'umkm_nama', 'umkm_detail',
                  'tlp_pengelola', 'aktif', 'total_penjualan', 'tgl_dibuat', 'tgl_update']
        read_only_fields = ['id', 'umkm', 'total_penjualan', 'tgl_dibuat', 'tgl_update']

    # Method implementations tetap sama...
    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM pemilik lokasi
        """
        umkm = obj.umkm
        result = {
            'id': umkm.id,
            'username': umkm.username,
            'nama_lengkap': f"{umkm.first_name} {umkm.last_name}".strip() or umkm.username
        }

        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            result['nm_bisnis'] = umkm.profil_umkm.nm_bisnis

        return result

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama UMKM
        """
        umkm = obj.umkm
        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            return umkm.profil_umkm.nm_bisnis
        return f"{umkm.first_name} {umkm.last_name}".strip() or umkm.username

    def get_kategori_lokasi_detail(self, obj):
        """
        Menampilkan detail kategori lokasi
        """
        if not obj.kategori_lokasi:
            return None

        return {
            'id': obj.kategori_lokasi.id,
            'nm_kategori_lokasi': obj.kategori_lokasi.nm_kategori_lokasi,
            'desc': obj.kategori_lokasi.desc
        }

    def validate(self, data):
        """
        Validasi tambahan untuk lokasi penjualan
        """
        data = super().validate(data)

        # Validasi nama lokasi unik per UMKM
        umkm = self.context['request'].user if self.context.get('request') else None
        nm_lokasi = data.get('nm_lokasi')

        if umkm and nm_lokasi:
            existing_query = LokasiPenjualan.objects.filter(umkm=umkm, nm_lokasi=nm_lokasi)

            # Jika update, exclude instance saat ini
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)

            if existing_query.exists():
                raise serializers.ValidationError({
                    'nm_lokasi': 'Anda sudah memiliki lokasi penjualan dengan nama ini.'
                })

        return data

    def get_kecamatan_detail(self, obj):
        if not obj.kecamatan:
            return None
        return {
            'id': obj.kecamatan.id,
            'nm_kecamatan': obj.kecamatan.nm_kecamatan,
            'kode': obj.kecamatan.kode
        }

    def get_kabupaten_detail(self, obj):
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
        if not obj.kecamatan or not obj.kecamatan.kabupaten or not obj.kecamatan.kabupaten.provinsi:
            return None
        prov = obj.kecamatan.kabupaten.provinsi
        return {
            'id': prov.id,
            'nm_provinsi': prov.nm_provinsi
        }

    def get_total_penjualan(self, obj):
        return obj.penjualan.count()

    def get_kabupaten_nama(self, obj):
        if obj.kecamatan and obj.kecamatan.kabupaten:
            kab = obj.kecamatan.kabupaten
            prefix = "Kota" if kab.is_kota else "Kabupaten"
            return f"{prefix} {kab.nm_kabupaten}"
        return None

    def get_provinsi_nama(self, obj):
        if obj.kecamatan and obj.kecamatan.kabupaten and obj.kecamatan.kabupaten.provinsi:
            return obj.kecamatan.kabupaten.provinsi.nm_provinsi
        return None


class LokasiPenjualanListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list LokasiPenjualan (lightweight)
    """
    kecamatan_nama = serializers.SerializerMethodField()
    kabupaten_nama = serializers.SerializerMethodField()
    provinsi_nama = serializers.SerializerMethodField()
    kategori_lokasi_nama = serializers.CharField(source='kategori_lokasi.nm_kategori_lokasi', read_only=True,
                                                 allow_null=True)
    umkm_nama = serializers.SerializerMethodField()
    total_penjualan = serializers.SerializerMethodField()

    class Meta:
        model = LokasiPenjualan
        fields = ['id', 'umkm_nama', 'nm_lokasi', 'kategori_lokasi_nama',
                  'alamat', 'tlp_pengelola', 'kecamatan_nama',
                  'kabupaten_nama', 'provinsi_nama', 'latitude', 'longitude',
                  'aktif', 'total_penjualan']

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

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama bisnis UMKM atau username
        """
        if hasattr(obj.umkm, 'profil_umkm') and obj.umkm.profil_umkm.nm_bisnis:
            return obj.umkm.profil_umkm.nm_bisnis
        return f"{obj.umkm.first_name} {obj.umkm.last_name}".strip() or obj.umkm.username

    def get_total_penjualan(self, obj):
        """
        Menghitung total penjualan di lokasi ini
        """
        return obj.penjualan.count()