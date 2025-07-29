# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Extract
from django.contrib.auth import get_user_model
from crud.models import ProdukTerjual, ProfilUMKM, LokasiPenjualan

User = get_user_model()


class GrafikPenjualanSerializer(serializers.Serializer):
    """
    Serializer untuk data grafik penjualan dengan pengeluaran
    """
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    nama_bulan = serializers.CharField()
    rata_rata_penjualan_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)


class BreakdownLokasiSerializer(serializers.Serializer):
    """
    Serializer untuk breakdown penjualan per lokasi
    """
    lokasi_id = serializers.CharField()
    nama_lokasi = serializers.CharField()
    alamat_lokasi = serializers.CharField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    persentase_kontribusi = serializers.DecimalField(max_digits=5, decimal_places=2)


class GrafikPenjualanSerializer(serializers.Serializer):
    """
    Serializer untuk data grafik penjualan dengan pengeluaran
    """
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    nama_bulan = serializers.CharField()
    rata_rata_penjualan_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)
    breakdown_lokasi = BreakdownLokasiSerializer(many=True, read_only=True)  # Tambahan


class GrafikPenjualanUMKMSerializer(serializers.Serializer):
    """
    Serializer untuk data grafik penjualan per UMKM dengan pengeluaran
    """
    umkm_id = serializers.CharField()
    nama_umkm = serializers.CharField()
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    nama_bulan = serializers.CharField()
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2)  # dalam persen
    breakdown_lokasi = BreakdownLokasiSerializer(many=True, read_only=True)  # Tambahan


class LokasiPenjualanDetailSerializer(serializers.Serializer):
    """
    Serializer untuk detail penjualan per lokasi
    """
    lokasi_id = serializers.CharField()
    nama_lokasi = serializers.CharField()
    alamat_lokasi = serializers.CharField()
    umkm_id = serializers.CharField()
    nama_umkm = serializers.CharField()
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    nama_bulan = serializers.CharField()
    rata_rata_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)


class RingkasanLokasiSerializer(serializers.Serializer):
    """
    Serializer untuk ringkasan penjualan per lokasi (tidak berdasarkan bulan)
    """
    lokasi_id = serializers.CharField()
    nama_lokasi = serializers.CharField()
    alamat_lokasi = serializers.CharField()
    umkm_id = serializers.CharField()
    nama_umkm = serializers.CharField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    rata_rata_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2)
    jumlah_produk_berbeda = serializers.IntegerField()  # jumlah jenis produk yang dijual


class UMKMListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list UMKM untuk dropdown
    """
    nama_umkm = serializers.CharField(source='profil_umkm.nm_bisnis')
    jumlah_lokasi = serializers.IntegerField(read_only=True)
    jumlah_produk = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'nama_umkm', 'jumlah_lokasi', 'jumlah_produk']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Jika nama_umkm kosong, gunakan username
        if not data['nama_umkm']:
            data['nama_umkm'] = data['username']
        return data


class LokasiPenjualanListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list lokasi penjualan untuk dropdown
    """
    nama_umkm = serializers.CharField(source='umkm.profil_umkm.nm_bisnis')
    kecamatan_nama = serializers.CharField(source='kecamatan.nm_kecamatan')
    kabupaten_nama = serializers.CharField(source='kecamatan.kabupaten.nm_kabupaten')

    class Meta:
        model = LokasiPenjualan
        fields = [
            'id', 'nm_lokasi', 'alamat', 'nama_umkm',
            'kecamatan_nama', 'kabupaten_nama', 'aktif'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Jika nama_umkm kosong, gunakan username
        if not data['nama_umkm']:
            data['nama_umkm'] = instance.umkm.username if instance.umkm else 'Unknown'
        return data


class FilterGrafikSerializer(serializers.Serializer):
    """
    Serializer untuk validasi filter grafik
    """
    umkm_id = serializers.UUIDField(required=False, allow_null=True)
    lokasi_id = serializers.UUIDField(required=False, allow_null=True)  # Filter baru
    tahun = serializers.IntegerField(required=False)
    bulan_start = serializers.IntegerField(min_value=1, max_value=12, required=False)
    bulan_end = serializers.IntegerField(min_value=1, max_value=12, required=False)

    def validate(self, attrs):
        if 'bulan_start' in attrs and 'bulan_end' in attrs:
            if attrs['bulan_start'] > attrs['bulan_end']:
                raise serializers.ValidationError(
                    "Bulan mulai tidak boleh lebih besar dari bulan akhir"
                )
        return attrs


class RingkasanPenjualanSerializer(serializers.Serializer):
    """
    Serializer untuk ringkasan penjualan dengan pengeluaran dan profit
    """
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    jumlah_umkm_aktif = serializers.IntegerField()
    jumlah_lokasi_aktif = serializers.IntegerField()
    rata_rata_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2)
    jumlah_produk_berbeda = serializers.IntegerField()
    breakdown_lokasi = BreakdownLokasiSerializer(many=True, read_only=True)  # Tambahan


class AnalisisProdukTerlaris(serializers.Serializer):
    """
    Serializer untuk analisis produk terlaris dengan profit
    """
    produk_id = serializers.CharField()
    nama_produk = serializers.CharField()
    nama_umkm = serializers.CharField()
    kategori = serializers.CharField()
    total_terjual = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    harga_rata_rata = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2)


class PerbandinganUMKMSerializer(serializers.Serializer):
    """
    Serializer untuk perbandingan performa antar UMKM
    """
    umkm_id = serializers.CharField()
    nama_umkm = serializers.CharField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    laba_kotor = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    jumlah_produk_berbeda = serializers.IntegerField()
    jumlah_lokasi = serializers.IntegerField()
    rata_rata_per_transaksi = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2)
    ranking_penjualan = serializers.IntegerField()
    ranking_keuntungan = serializers.IntegerField()
    breakdown_lokasi = BreakdownLokasiSerializer(many=True, read_only=True)  # Tambahan