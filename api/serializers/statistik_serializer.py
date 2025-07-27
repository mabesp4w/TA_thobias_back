# serializers/statistik_serializer.py
from rest_framework import serializers
from decimal import Decimal


class LokasiStatistikSerializer(serializers.Serializer):
    """
    Serializer untuk statistik per lokasi penjualan
    """
    lokasi_id = serializers.UUIDField()
    nama_lokasi = serializers.CharField()
    alamat = serializers.CharField()
    kategori_lokasi = serializers.CharField(allow_null=True)
    kecamatan = serializers.CharField(allow_null=True)
    kabupaten = serializers.CharField(allow_null=True)
    provinsi = serializers.CharField(allow_null=True)

    # Statistik Penjualan
    total_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    total_pemasukan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    keuntungan_bersih = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

    # Produk Terlaris
    produk_terlaris = serializers.CharField(allow_null=True)
    jumlah_produk_terlaris = serializers.IntegerField(default=0)


class ProdukStatistikSerializer(serializers.Serializer):
    """
    Serializer untuk statistik per produk
    """
    produk_id = serializers.UUIDField()
    nama_produk = serializers.CharField()
    kategori = serializers.CharField()
    satuan = serializers.CharField()
    harga_jual_rata_rata = serializers.DecimalField(max_digits=15, decimal_places=2)

    total_terjual = serializers.IntegerField()
    total_pemasukan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    keuntungan_per_produk = serializers.DecimalField(max_digits=15, decimal_places=2)


class PeriodeStatistikSerializer(serializers.Serializer):
    """
    Serializer untuk statistik berdasarkan periode
    """
    periode = serializers.CharField()  # '2024-01' untuk bulanan, '2024' untuk tahunan
    label_periode = serializers.CharField()  # 'Januari 2024' atau '2024'

    total_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    total_pemasukan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    keuntungan_bersih = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)


class StatistikUmumSerializer(serializers.Serializer):
    """
    Serializer untuk statistik umum
    """
    periode_awal = serializers.DateField()
    periode_akhir = serializers.DateField()

    # Ringkasan Umum
    total_transaksi = serializers.IntegerField()
    total_produk_terjual = serializers.IntegerField()
    total_pemasukan = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pengeluaran = serializers.DecimalField(max_digits=15, decimal_places=2)
    keuntungan_bersih = serializers.DecimalField(max_digits=15, decimal_places=2)
    margin_keuntungan = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

    # Rata-rata per hari
    rata_rata_transaksi_per_hari = serializers.DecimalField(max_digits=10, decimal_places=2)
    rata_rata_pemasukan_per_hari = serializers.DecimalField(max_digits=15, decimal_places=2)

    # Breakdown
    statistik_per_lokasi = LokasiStatistikSerializer(many=True)
    statistik_per_produk = ProdukStatistikSerializer(many=True)
    statistik_per_periode = PeriodeStatistikSerializer(many=True)


class StatistikResponseSerializer(serializers.Serializer):
    """
    Serializer untuk response API statistik
    """
    status = serializers.CharField()
    message = serializers.CharField()
    data = StatistikUmumSerializer()


class ParameterStatistikSerializer(serializers.Serializer):
    """
    Serializer untuk validasi parameter input
    """
    TIPE_PERIODE_CHOICES = [
        ('bulanan', 'Bulanan'),
        ('tahunan', 'Tahunan'),
        ('custom', 'Periode Custom'),
    ]

    tipe_periode = serializers.ChoiceField(
        choices=TIPE_PERIODE_CHOICES,
        default='bulanan',
        help_text="Tipe periode: bulanan, tahunan, atau custom"
    )

    tahun = serializers.IntegerField(
        required=False,
        min_value=2020,
        max_value=2030,
        help_text="Tahun untuk filter (required jika tipe_periode bukan custom)"
    )

    bulan = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=12,
        help_text="Bulan untuk filter (optional, hanya untuk tipe bulanan)"
    )

    tanggal_awal = serializers.DateField(
        required=False,
        help_text="Tanggal awal (required jika tipe_periode = custom)"
    )

    tanggal_akhir = serializers.DateField(
        required=False,
        help_text="Tanggal akhir (required jika tipe_periode = custom)"
    )

    lokasi_id = serializers.UUIDField(
        required=False,
        help_text="Filter berdasarkan lokasi tertentu (optional)"
    )

    produk_id = serializers.UUIDField(
        required=False,
        help_text="Filter berdasarkan produk tertentu (optional)"
    )

    def validate(self, data):
        tipe_periode = data.get('tipe_periode')

        if tipe_periode == 'custom':
            if not data.get('tanggal_awal') or not data.get('tanggal_akhir'):
                raise serializers.ValidationError(
                    "tanggal_awal dan tanggal_akhir harus diisi untuk periode custom"
                )

            if data['tanggal_awal'] > data['tanggal_akhir']:
                raise serializers.ValidationError(
                    "tanggal_awal tidak boleh lebih besar dari tanggal_akhir"
                )

        elif tipe_periode in ['bulanan', 'tahunan']:
            if not data.get('tahun'):
                raise serializers.ValidationError(
                    "tahun harus diisi untuk periode bulanan atau tahunan"
                )

        return data