# serialisers/produk_terjual_serializer.py

from rest_framework import serializers
from ..models import ProdukTerjual
from decimal import Decimal


class ProdukTerjualSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model ProdukTerjual
    """
    produk_detail = serializers.SerializerMethodField()
    lokasi_penjualan_detail = serializers.SerializerMethodField()
    umkm_detail = serializers.SerializerMethodField()
    kategori_detail = serializers.SerializerMethodField()

    # Direct access fields
    produk_nama = serializers.CharField(source='produk.nm_produk', read_only=True)
    satuan = serializers.CharField(source='produk.satuan', read_only=True)
    kategori_nama = serializers.CharField(source='produk.kategori.nm_kategori', read_only=True)
    lokasi_nama = serializers.SerializerMethodField()
    umkm_nama = serializers.SerializerMethodField()
    nm_bisnis = serializers.SerializerMethodField()

    class Meta:
        model = ProdukTerjual
        fields = ['id', 'produk', 'produk_nama', 'satuan', 'produk_detail',
                  'kategori_nama', 'kategori_detail',
                  'lokasi_penjualan', 'lokasi_nama', 'lokasi_penjualan_detail',
                  'umkm_detail', 'umkm_nama', 'nm_bisnis',
                  'tgl_penjualan', 'jumlah_terjual', 'harga_jual',
                  'total_penjualan', 'catatan', 'tgl_pelaporan']
        read_only_fields = ['id', 'total_penjualan', 'tgl_pelaporan']

    def get_produk_detail(self, obj):
        """
        Menampilkan detail produk
        """
        return {
            'id': obj.produk.id,
            'nm_produk': obj.produk.nm_produk,
            'kategori': obj.produk.kategori.nm_kategori,
            'satuan': obj.produk.satuan,
            'harga': obj.produk.harga,
            'stok': obj.produk.stok
        }

    def get_kategori_detail(self, obj):
        """
        Menampilkan detail kategori produk
        """
        kategori = obj.produk.kategori
        return {
            'id': kategori.id,
            'nm_kategori': kategori.nm_kategori,
            'desc': kategori.desc
        }

    def get_lokasi_penjualan_detail(self, obj):
        """
        Menampilkan detail lokasi penjualan
        """
        if not obj.lokasi_penjualan:
            return None

        lokasi = obj.lokasi_penjualan
        result = {
            'id': lokasi.id,
            'nm_lokasi': lokasi.nm_lokasi,
            'tipe_lokasi': lokasi.tipe_lokasi,
            'alamat': lokasi.alamat
        }

        if lokasi.kecamatan:
            result['kecamatan'] = lokasi.kecamatan.nm_kecamatan

            if lokasi.kecamatan.kabupaten:
                kab = lokasi.kecamatan.kabupaten
                prefix = "Kota" if kab.is_kota else "Kabupaten"
                result['kabupaten'] = f"{prefix} {kab.nm_kabupaten}"

                if kab.provinsi:
                    result['provinsi'] = kab.provinsi.nm_provinsi

        return result

    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM
        """
        umkm = obj.produk.umkm
        result = {
            'id': umkm.id,
            'username': umkm.username,
            'email': umkm.email,
            'nama_lengkap': f"{umkm.first_name} {umkm.last_name}".strip()
        }

        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            result['nm_bisnis'] = umkm.profil_umkm.nm_bisnis

        return result

    def get_lokasi_nama(self, obj):
        """
        Mendapatkan nama lokasi penjualan
        """
        if obj.lokasi_penjualan:
            return obj.lokasi_penjualan.nm_lokasi
        return None

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama UMKM
        """
        umkm = obj.produk.umkm
        return f"{umkm.first_name} {umkm.last_name}".strip() or umkm.username

    def get_nm_bisnis(self, obj):
        """
        Mendapatkan nama bisnis UMKM
        """
        umkm = obj.produk.umkm
        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            return umkm.profil_umkm.nm_bisnis
        return None

    def validate_jumlah_terjual(self, value):
        """
        Validasi jumlah terjual
        """
        if value <= 0:
            raise serializers.ValidationError("Jumlah terjual harus lebih dari 0.")
        return value

    def validate_harga_jual(self, value):
        """
        Validasi harga jual
        """
        if value <= Decimal('0'):
            raise serializers.ValidationError("Harga jual harus lebih dari 0.")
        return value

    def validate(self, data):
        """
        Validasi data penjualan
        """
        produk = data.get('produk')
        jumlah_terjual = data.get('jumlah_terjual')

        # Jika create atau update jumlah terjual
        if jumlah_terjual and produk:
            # Periksa apakah update (instance ada) atau create
            if not self.instance or self.instance.produk != produk:
                # Harga jual default ke harga produk saat ini jika tidak disediakan
                if 'harga_jual' not in data:
                    data['harga_jual'] = produk.harga

        return data


class ProdukTerjualListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list ProdukTerjual (lightweight)
    """
    produk_nama = serializers.CharField(source='produk.nm_produk', read_only=True)
    umkm_nama = serializers.SerializerMethodField()
    lokasi_nama = serializers.SerializerMethodField()
    satuan = serializers.CharField(source='produk.satuan', read_only=True)
    kategori_nama = serializers.CharField(source='produk.kategori.nm_kategori', read_only=True)

    produk_detail = serializers.SerializerMethodField()
    lokasi_penjualan_detail = serializers.SerializerMethodField()
    umkm_detail = serializers.SerializerMethodField()
    kategori_detail = serializers.SerializerMethodField()

    class Meta:
        model = ProdukTerjual
        fields = ['id', 'produk', 'produk_nama', 'produk_detail',
                  'umkm_nama', 'umkm_detail',
                  'lokasi_penjualan', 'lokasi_nama', 'lokasi_penjualan_detail',
                  'kategori_nama', 'kategori_detail',
                  'tgl_penjualan', 'jumlah_terjual', 'satuan', 'harga_jual',
                  'total_penjualan', 'tgl_pelaporan']

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama UMKM
        """
        umkm = obj.produk.umkm
        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            return umkm.profil_umkm.nm_bisnis
        return f"{umkm.first_name} {umkm.last_name}".strip() or umkm.username

    def get_lokasi_nama(self, obj):
        """
        Mendapatkan nama lokasi penjualan
        """
        if obj.lokasi_penjualan:
            return obj.lokasi_penjualan.nm_lokasi
        return None

    def get_produk_detail(self, obj):
        """
        Menampilkan detail produk (versi ringkas)
        """
        return {
            'id': obj.produk.id,
            'nm_produk': obj.produk.nm_produk,
            'satuan': obj.produk.satuan,
            'harga': obj.produk.harga
        }

    def get_kategori_detail(self, obj):
        """
        Menampilkan detail kategori produk (versi ringkas)
        """
        kategori = obj.produk.kategori
        return {
            'id': kategori.id,
            'nm_kategori': kategori.nm_kategori
        }

    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM (versi ringkas)
        """
        umkm = obj.produk.umkm
        result = {
            'id': umkm.id,
            'username': umkm.username,
            'nama_lengkap': f"{umkm.first_name} {umkm.last_name}".strip()
        }

        if hasattr(umkm, 'profil_umkm') and umkm.profil_umkm.nm_bisnis:
            result['nm_bisnis'] = umkm.profil_umkm.nm_bisnis

        return result

    def get_lokasi_penjualan_detail(self, obj):
        """
        Menampilkan detail lokasi penjualan (versi ringkas)
        """
        if not obj.lokasi_penjualan:
            return None

        return {
            'id': obj.lokasi_penjualan.id,
            'nm_lokasi': obj.lokasi_penjualan.nm_lokasi,
            'tipe_lokasi': obj.lokasi_penjualan.tipe_lokasi
        }