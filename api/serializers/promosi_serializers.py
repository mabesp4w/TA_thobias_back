# api/serializers/promosi_serializers.py

from rest_framework import serializers
from crud.models import Produk, KategoriProduk, ProfilUMKM
from django.contrib.auth.models import User


class KategoriPromosiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk kategori produk khusus promosi
    """

    class Meta:
        model = KategoriProduk
        fields = ['id', 'nm_kategori', 'desc']


class ProfilUMKMPromosiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk profil UMKM khusus promosi
    """

    class Meta:
        model = ProfilUMKM
        fields = ['nm_bisnis', 'alamat', 'tlp', 'desc_bisnis']


class UserUMKMPromosiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk user UMKM khusus promosi
    """
    profil_umkm = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'profil_umkm']

    def get_profil_umkm(self, obj):
        """
        Safely get profil_umkm data
        """
        try:
            if hasattr(obj, 'profil_umkm') and obj.profil_umkm:
                return {
                    'nm_bisnis': obj.profil_umkm.nm_bisnis or '',
                    'alamat': obj.profil_umkm.alamat or '',
                    'tlp': obj.profil_umkm.tlp or '',
                    'desc_bisnis': obj.profil_umkm.desc_bisnis or ''
                }
            else:
                return {
                    'nm_bisnis': obj.username,
                    'alamat': '',
                    'tlp': '',
                    'desc_bisnis': ''
                }
        except Exception as e:
            return {
                'nm_bisnis': obj.username,
                'alamat': '',
                'tlp': '',
                'desc_bisnis': ''
            }


class ProdukPromosiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk produk khusus halaman promosi
    Optimized untuk performance dan menampilkan data yang diperlukan
    """
    kategori_detail = serializers.SerializerMethodField()
    umkm_detail = serializers.SerializerMethodField()
    gambar_utama_url = serializers.SerializerMethodField()

    class Meta:
        model = Produk
        fields = [
            'id',
            'nm_produk',
            'desc',
            'harga',
            'stok',
            'satuan',
            'gambar_utama',
            'gambar_utama_url',
            'aktif',
            'tgl_dibuat',
            'tgl_update',
            'kategori_detail',
            'umkm_detail'
        ]

    def get_kategori_detail(self, obj):
        """
        Safely get kategori data
        """
        try:
            if obj.kategori:
                return {
                    'id': str(obj.kategori.id),
                    'nm_kategori': obj.kategori.nm_kategori,
                    'desc': obj.kategori.desc or ''
                }
            else:
                return {
                    'id': '',
                    'nm_kategori': 'Tidak Dikategorikan',
                    'desc': ''
                }
        except Exception as e:
            return {
                'id': '',
                'nm_kategori': 'Tidak Dikategorikan',
                'desc': ''
            }

    def get_umkm_detail(self, obj):
        """
        Safely get UMKM data
        """
        try:
            if obj.umkm:
                # Get profil_umkm data safely
                profil_data = {
                    'nm_bisnis': obj.umkm.username,
                    'alamat': '',
                    'tlp': '',
                    'desc_bisnis': ''
                }

                try:
                    if hasattr(obj.umkm, 'profil_umkm') and obj.umkm.profil_umkm:
                        profil_data.update({
                            'nm_bisnis': obj.umkm.profil_umkm.nm_bisnis or obj.umkm.username,
                            'alamat': obj.umkm.profil_umkm.alamat or '',
                            'tlp': obj.umkm.profil_umkm.tlp or '',
                            'desc_bisnis': obj.umkm.profil_umkm.desc_bisnis or ''
                        })
                except:
                    pass  # Use default values

                return {
                    'id': obj.umkm.id,
                    'username': obj.umkm.username,
                    'profil_umkm': profil_data
                }
            else:
                return {
                    'id': '',
                    'username': 'Unknown',
                    'profil_umkm': {
                        'nm_bisnis': 'Unknown',
                        'alamat': '',
                        'tlp': '',
                        'desc_bisnis': ''
                    }
                }
        except Exception as e:
            return {
                'id': '',
                'username': 'Unknown',
                'profil_umkm': {
                    'nm_bisnis': 'Unknown',
                    'alamat': '',
                    'tlp': '',
                    'desc_bisnis': ''
                }
            }

    def get_gambar_utama_url(self, obj):
        """
        Method untuk mendapatkan URL lengkap gambar
        """
        try:
            if obj.gambar_utama:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.gambar_utama.url)
                return obj.gambar_utama.url
            return None
        except Exception as e:
            return None


class KategoriStatistikSerializer(serializers.ModelSerializer):
    """
    Serializer untuk kategori dengan statistik produk
    """
    jumlah_produk = serializers.SerializerMethodField()

    class Meta:
        model = KategoriProduk
        fields = ['id', 'nm_kategori', 'desc', 'jumlah_produk']

    def get_jumlah_produk(self, obj):
        """
        Menghitung jumlah produk aktif per kategori
        """
        try:
            return obj.produk.filter(aktif=True).count()
        except Exception as e:
            return 0


class PromosiStatsSerializer(serializers.Serializer):
    """
    Serializer untuk statistik promosi
    """
    total_produk = serializers.IntegerField()
    total_umkm = serializers.IntegerField()
    total_kategori = serializers.IntegerField()
    produk_terbaru = serializers.IntegerField()
    umkm_aktif = serializers.IntegerField()