from rest_framework import serializers
from ..models import Produk, KategoriProduk
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class ProdukSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Produk
    """
    umkm_detail = serializers.SerializerMethodField()
    kategori_detail = serializers.SerializerMethodField()
    nm_bisnis = serializers.SerializerMethodField()

    # Direct access fields
    kategori_nama = serializers.CharField(source='kategori.nm_kategori', read_only=True)
    umkm_nama = serializers.SerializerMethodField()

    class Meta:
        model = Produk
        fields = ['id', 'umkm', 'umkm_nama', 'umkm_detail', 'nm_bisnis', 'kategori',
                  'kategori_nama', 'kategori_detail', 'nm_produk', 'desc', 'harga',
                  'stok', 'satuan', 'bahan_baku', 'metode_produksi', 'aktif',
                  'tgl_dibuat', 'tgl_update']
        read_only_fields = ['id', 'tgl_dibuat', 'tgl_update']

    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM
        """
        return {
            'id': obj.umkm.id,
            'username': obj.umkm.username,
            'email': obj.umkm.email,
            'nama_lengkap': f"{obj.umkm.first_name} {obj.umkm.last_name}".strip(),
            'role': obj.umkm.role
        }

    def get_kategori_detail(self, obj):
        """
        Menampilkan detail kategori
        """
        return {
            'id': obj.kategori.id,
            'nm_kategori': obj.kategori.nm_kategori,
            'desc': obj.kategori.desc
        }

    def get_nm_bisnis(self, obj):
        """
        Mendapatkan nama bisnis UMKM
        """
        if hasattr(obj.umkm, 'profil_umkm') and obj.umkm.profil_umkm.nm_bisnis:
            return obj.umkm.profil_umkm.nm_bisnis
        return obj.umkm.username

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama lengkap UMKM
        """
        return f"{obj.umkm.first_name} {obj.umkm.last_name}".strip()

    def validate_harga(self, value):
        """
        Validasi harga produk
        """
        if value < Decimal('0'):
            raise serializers.ValidationError("Harga tidak boleh bernilai negatif.")
        return value

    def validate_stok(self, value):
        """
        Validasi stok produk
        """
        if value < 0:
            raise serializers.ValidationError("Stok tidak boleh bernilai negatif.")
        return value

    def validate(self, data):
        """
        Validasi data produk
        """
        # Cek duplikasi nama produk untuk UMKM yang sama
        nm_produk = data.get('nm_produk')
        umkm = data.get('umkm')

        if not umkm:
            umkm = getattr(self.instance, 'umkm', None)

        if nm_produk and umkm:
            query = Produk.objects.filter(
                nm_produk__iexact=nm_produk,
                umkm=umkm
            )

            if self.instance:
                query = query.exclude(id=self.instance.id)

            if query.exists():
                raise serializers.ValidationError({
                    'nm_produk': f"Produk dengan nama '{nm_produk}' sudah ada untuk UMKM ini."
                })

        return data


class ProdukListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list Produk (lightweight)
    """
    umkm_nama = serializers.SerializerMethodField()
    nm_bisnis = serializers.SerializerMethodField()
    kategori_nama = serializers.CharField(source='kategori.nm_kategori', read_only=True)
    umkm_detail = serializers.SerializerMethodField()
    kategori_detail = serializers.SerializerMethodField()

    class Meta:
        model = Produk
        fields = ['id', 'nm_produk', 'harga', 'stok', 'satuan', 'umkm', 'umkm_nama',
                  'nm_bisnis', 'umkm_detail', 'kategori', 'kategori_nama',
                  'kategori_detail', 'aktif', 'tgl_dibuat']

    def get_umkm_nama(self, obj):
        """
        Mendapatkan nama lengkap UMKM
        """
        return f"{obj.umkm.first_name} {obj.umkm.last_name}".strip()

    def get_nm_bisnis(self, obj):
        """
        Mendapatkan nama bisnis UMKM
        """
        if hasattr(obj.umkm, 'profil_umkm') and obj.umkm.profil_umkm.nm_bisnis:
            return obj.umkm.profil_umkm.nm_bisnis
        return obj.umkm.username

    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM (versi ringkas)
        """
        return {
            'id': obj.umkm.id,
            'username': obj.umkm.username,
            'nama_lengkap': f"{obj.umkm.first_name} {obj.umkm.last_name}".strip()
        }

    def get_kategori_detail(self, obj):
        """
        Menampilkan detail kategori (versi ringkas)
        """
        return {
            'id': obj.kategori.id,
            'nm_kategori': obj.kategori.nm_kategori
        }