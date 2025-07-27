# utils/statistik_utils.py
from django.db.models import Q, Sum, Count, Avg, F, Case, When, DecimalField, Value, IntegerField
from django.db.models.functions import Coalesce, Cast
from decimal import Decimal
from datetime import datetime, date
from calendar import monthrange
import calendar

from crud.models import ProdukTerjual, Produk, LokasiPenjualan


class StatistikCalculator:
    """
    Utility class untuk menghitung statistik pemasukan dan pengeluaran UMKM
    Pengeluaran dihitung dari biaya_upah + biaya_produksi * jumlah_terjual
    """

    def __init__(self, user):
        self.user = user
        self.base_queryset = ProdukTerjual.objects.filter(
            produk__umkm=user
        ).select_related('produk', 'lokasi_penjualan')

    def get_periode_filter(self, params):
        """
        Membuat filter berdasarkan periode
        """
        tipe_periode = params.get('tipe_periode', 'bulanan')

        if tipe_periode == 'custom':
            tanggal_awal = params.get('tanggal_awal')
            tanggal_akhir = params.get('tanggal_akhir')
            return Q(tgl_penjualan__range=[tanggal_awal, tanggal_akhir])

        elif tipe_periode == 'bulanan':
            tahun = params.get('tahun')
            bulan = params.get('bulan')

            if bulan:
                return Q(tgl_penjualan__year=tahun, tgl_penjualan__month=bulan)
            else:
                return Q(tgl_penjualan__year=tahun)

        elif tipe_periode == 'tahunan':
            tahun = params.get('tahun')
            return Q(tgl_penjualan__year=tahun)

        return Q()

    def get_additional_filters(self, params):
        """
        Filter tambahan berdasarkan lokasi atau produk
        """
        filters = Q()

        if params.get('lokasi_id'):
            filters &= Q(lokasi_penjualan_id=params['lokasi_id'])

        if params.get('produk_id'):
            filters &= Q(produk_id=params['produk_id'])

        return filters

    def calculate_base_stats(self, queryset):
        """
        Menghitung statistik dasar dengan semua field sebagai DecimalField
        """
        # Konversi semua field ke DecimalField untuk menghindari mixed types
        aggregates = queryset.aggregate(
            total_transaksi=Cast(Count('id'), DecimalField(max_digits=15, decimal_places=2)),
            total_produk_terjual=Cast(
                Coalesce(Sum('jumlah_terjual'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            total_pemasukan=Cast(
                Coalesce(Sum('total_penjualan'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            )
        )

        # Hitung pengeluaran menggunakan annotation untuk menghindari mixed types
        pengeluaran_aggregate = queryset.aggregate(
            total_pengeluaran=Cast(
                Coalesce(
                    Sum(
                        Cast('jumlah_terjual', DecimalField(max_digits=15, decimal_places=2)) *
                        (Cast(Coalesce('produk__biaya_upah', 0), DecimalField(max_digits=15, decimal_places=2)) +
                         Cast(Coalesce('produk__biaya_produksi', 0), DecimalField(max_digits=15, decimal_places=2))),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=15, decimal_places=2))
                ),
                DecimalField(max_digits=15, decimal_places=2)
            )
        )

        # Konversi ke Decimal
        total_transaksi = Decimal(str(aggregates['total_transaksi']))
        total_produk_terjual = Decimal(str(aggregates['total_produk_terjual']))
        total_pemasukan = Decimal(str(aggregates['total_pemasukan']))
        total_pengeluaran = Decimal(str(pengeluaran_aggregate['total_pengeluaran']))

        keuntungan_bersih = total_pemasukan - total_pengeluaran

        margin_keuntungan = None
        if total_pemasukan > 0:
            margin_keuntungan = (keuntungan_bersih / total_pemasukan * 100).quantize(Decimal('0.01'))

        return {
            'total_transaksi': int(total_transaksi),
            'total_produk_terjual': int(total_produk_terjual),
            'total_pemasukan': total_pemasukan,
            'total_pengeluaran': total_pengeluaran,
            'keuntungan_bersih': keuntungan_bersih,
            'margin_keuntungan': margin_keuntungan
        }

    def get_statistik_per_lokasi(self, queryset):
        """
        Menghitung statistik per lokasi penjualan dengan semua field sebagai DecimalField
        """
        # Ambil statistik dasar per lokasi dengan konversi ke DecimalField
        lokasi_stats = queryset.values(
            'lokasi_penjualan__id',
            'lokasi_penjualan__nm_lokasi',
            'lokasi_penjualan__alamat',
            'lokasi_penjualan__kategori_lokasi__nm_kategori_lokasi',
            'lokasi_penjualan__kecamatan__nm_kecamatan',
            'lokasi_penjualan__kecamatan__kabupaten__nm_kabupaten',
            'lokasi_penjualan__kecamatan__kabupaten__provinsi__nm_provinsi'
        ).annotate(
            total_transaksi=Cast(Count('id'), DecimalField(max_digits=15, decimal_places=2)),
            total_produk_terjual=Cast(
                Coalesce(Sum('jumlah_terjual'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            total_pemasukan=Cast(
                Coalesce(Sum('total_penjualan'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            total_pengeluaran=Cast(
                Coalesce(
                    Sum(
                        Cast('jumlah_terjual', DecimalField(max_digits=15, decimal_places=2)) *
                        (Cast(Coalesce('produk__biaya_upah', 0), DecimalField(max_digits=15, decimal_places=2)) +
                         Cast(Coalesce('produk__biaya_produksi', 0), DecimalField(max_digits=15, decimal_places=2))),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=15, decimal_places=2))
                ),
                DecimalField(max_digits=15, decimal_places=2)
            )
        ).order_by('-total_pemasukan')

        result = []
        for stat in lokasi_stats:
            lokasi_id = stat['lokasi_penjualan__id']

            # Konversi ke Decimal
            total_transaksi = Decimal(str(stat['total_transaksi']))
            total_produk_terjual = Decimal(str(stat['total_produk_terjual']))
            total_pemasukan = Decimal(str(stat['total_pemasukan']))
            total_pengeluaran = Decimal(str(stat['total_pengeluaran']))

            keuntungan_bersih = total_pemasukan - total_pengeluaran

            margin_keuntungan = None
            if total_pemasukan > 0:
                margin_keuntungan = (keuntungan_bersih / total_pemasukan * 100).quantize(Decimal('0.01'))

            # Cari produk terlaris di lokasi ini
            lokasi_queryset = queryset.filter(lokasi_penjualan_id=lokasi_id)
            produk_terlaris = lokasi_queryset.values('produk__nm_produk').annotate(
                jumlah_terjual_total=Cast(
                    Sum('jumlah_terjual'),
                    DecimalField(max_digits=15, decimal_places=2)
                )
            ).order_by('-jumlah_terjual_total').first()

            result.append({
                'lokasi_id': stat['lokasi_penjualan__id'],
                'nama_lokasi': stat['lokasi_penjualan__nm_lokasi'],
                'alamat': stat['lokasi_penjualan__alamat'],
                'kategori_lokasi': stat['lokasi_penjualan__kategori_lokasi__nm_kategori_lokasi'],
                'kecamatan': stat['lokasi_penjualan__kecamatan__nm_kecamatan'],
                'kabupaten': stat['lokasi_penjualan__kecamatan__kabupaten__nm_kabupaten'],
                'provinsi': stat['lokasi_penjualan__kecamatan__kabupaten__provinsi__nm_provinsi'],
                'total_transaksi': int(total_transaksi),
                'total_produk_terjual': int(total_produk_terjual),
                'total_pemasukan': total_pemasukan,
                'total_pengeluaran': total_pengeluaran,
                'keuntungan_bersih': keuntungan_bersih,
                'margin_keuntungan': margin_keuntungan,
                'produk_terlaris': produk_terlaris['produk__nm_produk'] if produk_terlaris else None,
                'jumlah_produk_terlaris': int(
                    Decimal(str(produk_terlaris['jumlah_terjual_total']))) if produk_terlaris else 0
            })

        return result

    def get_statistik_per_produk(self, queryset):
        """
        Menghitung statistik per produk dengan semua field sebagai DecimalField
        """
        # Ambil statistik dasar per produk dengan konversi ke DecimalField
        produk_stats = queryset.values(
            'produk__id',
            'produk__nm_produk',
            'produk__kategori__nm_kategori',
            'produk__satuan'
        ).annotate(
            total_terjual=Cast(
                Coalesce(Sum('jumlah_terjual'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            total_pemasukan=Cast(
                Coalesce(Sum('total_penjualan'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            harga_jual_rata_rata=Cast(
                Coalesce(Avg('harga_jual'), 0),
                DecimalField(max_digits=15, decimal_places=2)
            ),
            total_pengeluaran=Cast(
                Coalesce(
                    Sum(
                        Cast('jumlah_terjual', DecimalField(max_digits=15, decimal_places=2)) *
                        (Cast(Coalesce('produk__biaya_upah', 0), DecimalField(max_digits=15, decimal_places=2)) +
                         Cast(Coalesce('produk__biaya_produksi', 0), DecimalField(max_digits=15, decimal_places=2))),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    ),
                    Value(0, output_field=DecimalField(max_digits=15, decimal_places=2))
                ),
                DecimalField(max_digits=15, decimal_places=2)
            )
        ).order_by('-total_terjual')

        result = []
        for stat in produk_stats:
            # Konversi ke Decimal
            total_terjual = Decimal(str(stat['total_terjual']))
            total_pemasukan = Decimal(str(stat['total_pemasukan']))
            total_pengeluaran = Decimal(str(stat['total_pengeluaran']))
            harga_jual_rata_rata = Decimal(str(stat['harga_jual_rata_rata']))

            keuntungan_per_produk = total_pemasukan - total_pengeluaran

            result.append({
                'produk_id': stat['produk__id'],
                'nama_produk': stat['produk__nm_produk'],
                'kategori': stat['produk__kategori__nm_kategori'],
                'satuan': stat['produk__satuan'],
                'harga_jual_rata_rata': harga_jual_rata_rata,
                'total_terjual': int(total_terjual),
                'total_pemasukan': total_pemasukan,
                'total_pengeluaran': total_pengeluaran,
                'keuntungan_per_produk': keuntungan_per_produk
            })

        return result

    def get_statistik_per_periode(self, queryset, tipe_periode):
        """
        Menghitung statistik per periode (bulanan/tahunan) dengan semua field sebagai DecimalField
        """
        if tipe_periode == 'bulanan':
            # Group by tahun dan bulan
            periode_stats = queryset.extra(
                select={'periode': "DATE_FORMAT(tgl_penjualan, '%%Y-%%m')"}
            ).values('periode').annotate(
                total_transaksi=Cast(Count('id'), DecimalField(max_digits=15, decimal_places=2)),
                total_produk_terjual=Cast(
                    Coalesce(Sum('jumlah_terjual'), 0),
                    DecimalField(max_digits=15, decimal_places=2)
                ),
                total_pemasukan=Cast(
                    Coalesce(Sum('total_penjualan'), 0),
                    DecimalField(max_digits=15, decimal_places=2)
                ),
                total_pengeluaran=Cast(
                    Coalesce(
                        Sum(
                            Cast('jumlah_terjual', DecimalField(max_digits=15, decimal_places=2)) *
                            (Cast(Coalesce('produk__biaya_upah', 0), DecimalField(max_digits=15, decimal_places=2)) +
                             Cast(Coalesce('produk__biaya_produksi', 0),
                                  DecimalField(max_digits=15, decimal_places=2))),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        ),
                        Value(0, output_field=DecimalField(max_digits=15, decimal_places=2))
                    ),
                    DecimalField(max_digits=15, decimal_places=2)
                )
            ).order_by('periode')

            result = []
            for stat in periode_stats:
                # Konversi ke Decimal
                total_transaksi = Decimal(str(stat['total_transaksi']))
                total_produk_terjual = Decimal(str(stat['total_produk_terjual']))
                total_pemasukan = Decimal(str(stat['total_pemasukan']))
                total_pengeluaran = Decimal(str(stat['total_pengeluaran']))

                keuntungan_bersih = total_pemasukan - total_pengeluaran

                margin_keuntungan = None
                if total_pemasukan > 0:
                    margin_keuntungan = (keuntungan_bersih / total_pemasukan * 100).quantize(Decimal('0.01'))

                tahun, bulan = stat['periode'].split('-')
                nama_bulan = calendar.month_name[int(bulan)]
                label_periode = f"{nama_bulan} {tahun}"

                result.append({
                    'periode': stat['periode'],
                    'label_periode': label_periode,
                    'total_transaksi': int(total_transaksi),
                    'total_produk_terjual': int(total_produk_terjual),
                    'total_pemasukan': total_pemasukan,
                    'total_pengeluaran': total_pengeluaran,
                    'keuntungan_bersih': keuntungan_bersih,
                    'margin_keuntungan': margin_keuntungan
                })

        else:  # tahunan
            periode_stats = queryset.extra(
                select={'periode': "DATE_FORMAT(tgl_penjualan, '%%Y')"}
            ).values('periode').annotate(
                total_transaksi=Cast(Count('id'), DecimalField(max_digits=15, decimal_places=2)),
                total_produk_terjual=Cast(
                    Coalesce(Sum('jumlah_terjual'), 0),
                    DecimalField(max_digits=15, decimal_places=2)
                ),
                total_pemasukan=Cast(
                    Coalesce(Sum('total_penjualan'), 0),
                    DecimalField(max_digits=15, decimal_places=2)
                ),
                total_pengeluaran=Cast(
                    Coalesce(
                        Sum(
                            Cast('jumlah_terjual', DecimalField(max_digits=15, decimal_places=2)) *
                            (Cast(Coalesce('produk__biaya_upah', 0), DecimalField(max_digits=15, decimal_places=2)) +
                             Cast(Coalesce('produk__biaya_produksi', 0),
                                  DecimalField(max_digits=15, decimal_places=2))),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        ),
                        Value(0, output_field=DecimalField(max_digits=15, decimal_places=2))
                    ),
                    DecimalField(max_digits=15, decimal_places=2)
                )
            ).order_by('periode')

            result = []
            for stat in periode_stats:
                # Konversi ke Decimal
                total_transaksi = Decimal(str(stat['total_transaksi']))
                total_produk_terjual = Decimal(str(stat['total_produk_terjual']))
                total_pemasukan = Decimal(str(stat['total_pemasukan']))
                total_pengeluaran = Decimal(str(stat['total_pengeluaran']))

                keuntungan_bersih = total_pemasukan - total_pengeluaran

                margin_keuntungan = None
                if total_pemasukan > 0:
                    margin_keuntungan = (keuntungan_bersih / total_pemasukan * 100).quantize(Decimal('0.01'))

                result.append({
                    'periode': stat['periode'],
                    'label_periode': stat['periode'],
                    'total_transaksi': int(total_transaksi),
                    'total_produk_terjual': int(total_produk_terjual),
                    'total_pemasukan': total_pemasukan,
                    'total_pengeluaran': total_pengeluaran,
                    'keuntungan_bersih': keuntungan_bersih,
                    'margin_keuntungan': margin_keuntungan
                })

        return result

    def calculate_full_statistics(self, params):
        """
        Menghitung statistik lengkap berdasarkan parameter
        """
        # Buat filter berdasarkan periode
        periode_filter = self.get_periode_filter(params)
        additional_filter = self.get_additional_filters(params)

        # Gabungkan filter
        queryset = self.base_queryset.filter(periode_filter & additional_filter)

        # Hitung statistik dasar
        base_stats = self.calculate_base_stats(queryset)

        # Tentukan periode awal dan akhir
        if params.get('tipe_periode') == 'custom':
            periode_awal = params.get('tanggal_awal')
            periode_akhir = params.get('tanggal_akhir')
        else:
            tahun = params.get('tahun')
            bulan = params.get('bulan')

            if bulan:
                periode_awal = date(tahun, bulan, 1)
                last_day = monthrange(tahun, bulan)[1]
                periode_akhir = date(tahun, bulan, last_day)
            else:
                periode_awal = date(tahun, 1, 1)
                periode_akhir = date(tahun, 12, 31)

        # Hitung rata-rata per hari
        total_hari = (periode_akhir - periode_awal).days + 1
        rata_rata_transaksi_per_hari = Decimal(str(base_stats['total_transaksi'])) / total_hari
        rata_rata_pemasukan_per_hari = base_stats['total_pemasukan'] / total_hari

        # Hitung breakdown
        statistik_per_lokasi = self.get_statistik_per_lokasi(queryset)
        statistik_per_produk = self.get_statistik_per_produk(queryset)
        statistik_per_periode = self.get_statistik_per_periode(
            queryset,
            params.get('tipe_periode', 'bulanan')
        )

        return {
            'periode_awal': periode_awal,
            'periode_akhir': periode_akhir,
            'total_transaksi': base_stats['total_transaksi'],
            'total_produk_terjual': base_stats['total_produk_terjual'],
            'total_pemasukan': base_stats['total_pemasukan'],
            'total_pengeluaran': base_stats['total_pengeluaran'],
            'keuntungan_bersih': base_stats['keuntungan_bersih'],
            'margin_keuntungan': base_stats['margin_keuntungan'],
            'rata_rata_transaksi_per_hari': rata_rata_transaksi_per_hari.quantize(Decimal('0.01')),
            'rata_rata_pemasukan_per_hari': rata_rata_pemasukan_per_hari.quantize(Decimal('0.01')),
            'statistik_per_lokasi': statistik_per_lokasi,
            'statistik_per_produk': statistik_per_produk,
            'statistik_per_periode': statistik_per_periode
        }