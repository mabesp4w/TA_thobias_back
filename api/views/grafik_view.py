# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, DecimalField, IntegerField, Case, When, Window
from django.db.models.functions import Extract, Coalesce
from django.contrib.auth import get_user_model
from datetime import datetime
from crud.models import ProdukTerjual, ProfilUMKM, LokasiPenjualan, Produk
from api.serializers.grafik_serializers import (
    GrafikPenjualanSerializer,
    GrafikPenjualanUMKMSerializer,
    LokasiPenjualanDetailSerializer,
    RingkasanLokasiSerializer,
    UMKMListSerializer,
    LokasiPenjualanListSerializer,
    FilterGrafikSerializer,
    RingkasanPenjualanSerializer,
    AnalisisProdukTerlaris,
    PerbandinganUMKMSerializer,
    BreakdownLokasiSerializer
)

User = get_user_model()

# Mapping nama bulan
NAMA_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}


def get_breakdown_lokasi(base_queryset, total_penjualan_global=None):
    """
    Helper function untuk mendapatkan breakdown penjualan per lokasi
    """
    breakdown_data = (
        base_queryset
        .filter(lokasi_penjualan__isnull=False)
        .annotate(
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'lokasi_penjualan_id',
            'lokasi_penjualan__nm_lokasi',
            'lokasi_penjualan__alamat'
        )
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            total_produk_terjual=Sum('jumlah_terjual')
        )
        .order_by('-total_penjualan')
    )

    result = []
    for item in breakdown_data:
        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran

        # Hitung persentase kontribusi
        persentase_kontribusi = 0
        if total_penjualan_global and total_penjualan_global > 0:
            persentase_kontribusi = (total_penjualan / total_penjualan_global) * 100

        result.append({
            'lokasi_id': str(item['lokasi_penjualan_id']) if item['lokasi_penjualan_id'] else None,
            'nama_lokasi': item['lokasi_penjualan__nm_lokasi'] or 'Tidak diketahui',
            'alamat_lokasi': item['lokasi_penjualan__alamat'] or 'Tidak diketahui',
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': item['jumlah_transaksi'],
            'total_produk_terjual': item['total_produk_terjual'] or 0,
            'persentase_kontribusi': round(persentase_kontribusi, 2)
        })

    return result


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grafik_penjualan_view(request):
    """
    Endpoint untuk mendapatkan data grafik penjualan dengan pengeluaran
    Support filter: umkm_id, lokasi_id, tahun, bulan_start, bulan_end
    """
    # Validasi parameter
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset dengan join ke produk untuk mendapatkan biaya
    queryset = ProdukTerjual.objects.select_related('produk', 'lokasi_penjualan')

    # Apply filters
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('lokasi_id'):
        queryset = queryset.filter(lokasi_penjualan_id=filters['lokasi_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )
    elif filters.get('bulan_start'):
        queryset = queryset.filter(tgl_penjualan__month__gte=filters['bulan_start'])
    elif filters.get('bulan_end'):
        queryset = queryset.filter(tgl_penjualan__month__lte=filters['bulan_end'])

    # Agregasi data dengan perhitungan pengeluaran
    data_penjualan = (
        queryset
        .annotate(
            bulan=Extract('tgl_penjualan', 'month'),
            tahun=Extract('tgl_penjualan', 'year'),
            # Hitung pengeluaran per item
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values('bulan', 'tahun')
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            total_produk_terjual=Sum('jumlah_terjual')
        )
        .order_by('tahun', 'bulan')
    )

    # Format data dengan perhitungan tambahan
    result_data = []
    for item in data_penjualan:
        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        jumlah_transaksi = item['jumlah_transaksi']

        # Buat queryset untuk periode bulan ini untuk breakdown lokasi
        bulan_queryset = queryset.filter(
            tgl_penjualan__year=item['tahun'],
            tgl_penjualan__month=item['bulan']
        )
        breakdown_lokasi = get_breakdown_lokasi(bulan_queryset, total_penjualan)

        result_data.append({
            'bulan': item['bulan'],
            'tahun': item['tahun'],
            'nama_bulan': NAMA_BULAN.get(item['bulan'], f"Bulan {item['bulan']}"),
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': jumlah_transaksi,
            'total_produk_terjual': item['total_produk_terjual'] or 0,
            'rata_rata_penjualan_per_transaksi': total_penjualan / jumlah_transaksi if jumlah_transaksi > 0 else 0,
            'breakdown_lokasi': breakdown_lokasi
        })

    serializer = GrafikPenjualanSerializer(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grafik_penjualan_per_umkm_view(request):
    """
    Endpoint untuk mendapatkan data grafik penjualan semua UMKM dengan pengeluaran
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related(
        'produk__umkm__profil_umkm', 'produk'
    )

    # Apply filters
    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )

    # Agregasi data per UMKM dan bulan
    data_penjualan = (
        queryset
        .annotate(
            bulan=Extract('tgl_penjualan', 'month'),
            tahun=Extract('tgl_penjualan', 'year'),
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'produk__umkm_id',
            'produk__umkm__username',
            'produk__umkm__profil_umkm__nm_bisnis',
            'bulan',
            'tahun'
        )
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            total_produk_terjual=Sum('jumlah_terjual')
        )
        .order_by('produk__umkm__username', 'tahun', 'bulan')
    )

    # Format data
    result_data = []
    for item in data_penjualan:
        nama_umkm = (
                item['produk__umkm__profil_umkm__nm_bisnis'] or
                item['produk__umkm__username']
        )

        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        margin_keuntungan = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0

        # Buat queryset untuk UMKM dan bulan ini untuk breakdown lokasi
        umkm_bulan_queryset = queryset.filter(
            produk__umkm_id=item['produk__umkm_id'],
            tgl_penjualan__year=item['tahun'],
            tgl_penjualan__month=item['bulan']
        )
        breakdown_lokasi = get_breakdown_lokasi(umkm_bulan_queryset, total_penjualan)

        result_data.append({
            'umkm_id': str(item['produk__umkm_id']),
            'nama_umkm': nama_umkm,
            'bulan': item['bulan'],
            'tahun': item['tahun'],
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': item['jumlah_transaksi'],
            'total_produk_terjual': item['total_produk_terjual'] or 0,
            'nama_bulan': NAMA_BULAN.get(item['bulan'], f"Bulan {item['bulan']}"),
            'margin_keuntungan': round(margin_keuntungan, 2),
            'breakdown_lokasi': breakdown_lokasi
        })

    serializer = GrafikPenjualanUMKMSerializer(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def penjualan_per_lokasi_view(request):
    """
    Endpoint untuk mendapatkan data penjualan per lokasi dengan detail pengeluaran
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related(
        'lokasi_penjualan', 'produk__umkm__profil_umkm', 'produk'
    ).filter(lokasi_penjualan__isnull=False)

    # Apply filters
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('lokasi_id'):
        queryset = queryset.filter(lokasi_penjualan_id=filters['lokasi_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )

    # Agregasi data per lokasi dan bulan
    data_lokasi = (
        queryset
        .annotate(
            bulan=Extract('tgl_penjualan', 'month'),
            tahun=Extract('tgl_penjualan', 'year'),
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'lokasi_penjualan_id',
            'lokasi_penjualan__nm_lokasi',
            'lokasi_penjualan__alamat',
            'produk__umkm_id',
            'produk__umkm__username',
            'produk__umkm__profil_umkm__nm_bisnis',
            'bulan',
            'tahun'
        )
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            total_produk_terjual=Sum('jumlah_terjual')
        )
        .order_by('lokasi_penjualan__nm_lokasi', 'tahun', 'bulan')
    )

    # Format data
    result_data = []
    for item in data_lokasi:
        nama_umkm = (
                item['produk__umkm__profil_umkm__nm_bisnis'] or
                item['produk__umkm__username']
        )

        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        jumlah_transaksi = item['jumlah_transaksi']

        result_data.append({
            'lokasi_id': str(item['lokasi_penjualan_id']),
            'nama_lokasi': item['lokasi_penjualan__nm_lokasi'],
            'alamat_lokasi': item['lokasi_penjualan__alamat'],
            'umkm_id': str(item['produk__umkm_id']),
            'nama_umkm': nama_umkm,
            'bulan': item['bulan'],
            'tahun': item['tahun'],
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': jumlah_transaksi,
            'total_produk_terjual': item['total_produk_terjual'] or 0,
            'nama_bulan': NAMA_BULAN.get(item['bulan'], f"Bulan {item['bulan']}"),
            'rata_rata_per_transaksi': total_penjualan / jumlah_transaksi if jumlah_transaksi > 0 else 0
        })

    serializer = LokasiPenjualanDetailSerializer(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ringkasan_lokasi_view(request):
    """
    Endpoint untuk ringkasan penjualan per lokasi (total, tidak per bulan)
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related(
        'lokasi_penjualan', 'produk__umkm__profil_umkm', 'produk'
    ).filter(lokasi_penjualan__isnull=False)

    # Apply filters (tanpa filter bulan untuk ringkasan total)
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])

    # Agregasi data per lokasi
    data_lokasi = (
        queryset
        .annotate(
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'lokasi_penjualan_id',
            'lokasi_penjualan__nm_lokasi',
            'lokasi_penjualan__alamat',
            'produk__umkm_id',
            'produk__umkm__username',
            'produk__umkm__profil_umkm__nm_bisnis'
        )
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            total_produk_terjual=Sum('jumlah_terjual'),
            jumlah_produk_berbeda=Count('produk', distinct=True)
        )
        .order_by('-total_penjualan')
    )

    # Format data
    result_data = []
    for item in data_lokasi:
        nama_umkm = (
                item['produk__umkm__profil_umkm__nm_bisnis'] or
                item['produk__umkm__username']
        )

        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        jumlah_transaksi = item['jumlah_transaksi']
        margin_keuntungan = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0

        result_data.append({
            'lokasi_id': str(item['lokasi_penjualan_id']),
            'nama_lokasi': item['lokasi_penjualan__nm_lokasi'],
            'alamat_lokasi': item['lokasi_penjualan__alamat'],
            'umkm_id': str(item['produk__umkm_id']),
            'nama_umkm': nama_umkm,
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': jumlah_transaksi,
            'total_produk_terjual': item['total_produk_terjual'] or 0,
            'rata_rata_per_transaksi': total_penjualan / jumlah_transaksi if jumlah_transaksi > 0 else 0,
            'margin_keuntungan': round(margin_keuntungan, 2),
            'jumlah_produk_berbeda': item['jumlah_produk_berbeda']
        })

    serializer = RingkasanLokasiSerializer(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_umkm_view(request):
    """
    Endpoint untuk mendapatkan list UMKM untuk dropdown dengan statistik
    """
    # Filter user berdasarkan role jika field tersebut ada
    try:
        umkm_users = User.objects.filter(
            role='umkm'
        ).select_related('profil_umkm').annotate(
            jumlah_lokasi=Count('lokasi_penjualan', distinct=True),
            jumlah_produk=Count('produk', distinct=True)
        ).order_by('username')
    except:
        umkm_users = User.objects.filter(
            profil_umkm__isnull=False
        ).select_related('profil_umkm').annotate(
            jumlah_lokasi=Count('lokasi_penjualan', distinct=True),
            jumlah_produk=Count('produk', distinct=True)
        ).order_by('username')

    serializer = UMKMListSerializer(umkm_users, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lokasi_penjualan_view(request):
    """
    Endpoint untuk mendapatkan list lokasi penjualan untuk dropdown
    """
    umkm_id = request.query_params.get('umkm_id')

    queryset = LokasiPenjualan.objects.select_related(
        'umkm__profil_umkm', 'kecamatan__kabupaten'
    ).filter(aktif=True)

    if umkm_id:
        queryset = queryset.filter(umkm_id=umkm_id)

    queryset = queryset.order_by('nm_lokasi')

    serializer = LokasiPenjualanListSerializer(queryset, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ringkasan_penjualan_view(request):
    """
    Endpoint untuk mendapatkan ringkasan data penjualan dengan pengeluaran
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related('produk')

    # Apply filters
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('lokasi_id'):
        queryset = queryset.filter(lokasi_penjualan_id=filters['lokasi_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )

    # Hitung ringkasan dengan pengeluaran
    summary = queryset.annotate(
        pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
    ).aggregate(
        total_penjualan=Sum('total_penjualan'),
        total_pengeluaran=Sum('pengeluaran_per_item'),
        total_transaksi=Count('id'),
        total_produk_terjual=Sum('jumlah_terjual'),
        jumlah_produk_berbeda=Count('produk', distinct=True)
    )

    # Hitung statistik lainnya
    jumlah_umkm = queryset.values('produk__umkm').distinct().count()
    jumlah_lokasi = queryset.filter(
        lokasi_penjualan__isnull=False
    ).values('lokasi_penjualan').distinct().count()

    # Perhitungan laba dan margin
    total_penjualan = summary['total_penjualan'] or 0
    total_pengeluaran = summary['total_pengeluaran'] or 0
    laba_kotor = total_penjualan - total_pengeluaran
    total_transaksi = summary['total_transaksi']
    margin_keuntungan = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0

    # Dapatkan breakdown lokasi untuk ringkasan
    breakdown_lokasi = get_breakdown_lokasi(queryset, total_penjualan)

    result_data = {
        'total_penjualan': total_penjualan,
        'total_pengeluaran': total_pengeluaran,
        'laba_kotor': laba_kotor,
        'total_transaksi': total_transaksi,
        'total_produk_terjual': summary['total_produk_terjual'] or 0,
        'jumlah_umkm_aktif': jumlah_umkm,
        'jumlah_lokasi_aktif': jumlah_lokasi,
        'rata_rata_per_transaksi': total_penjualan / total_transaksi if total_transaksi > 0 else 0,
        'margin_keuntungan': round(margin_keuntungan, 2),
        'jumlah_produk_berbeda': summary['jumlah_produk_berbeda'] or 0,
        'breakdown_lokasi': breakdown_lokasi
    }

    serializer = RingkasanPenjualanSerializer(result_data)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analisis_produk_terlaris_view(request):
    """
    Endpoint untuk analisis produk terlaris dengan profit
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data
    limit = int(request.query_params.get('limit', 10))

    # Base queryset
    queryset = ProdukTerjual.objects.select_related(
        'produk__umkm__profil_umkm', 'produk__kategori'
    )

    # Apply filters
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])

    # Agregasi per produk
    produk_terlaris = (
        queryset
        .annotate(
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'produk_id',
            'produk__nm_produk',
            'produk__umkm__username',
            'produk__umkm__profil_umkm__nm_bisnis',
            'produk__kategori__nm_kategori'
        )
        .annotate(
            total_terjual=Sum('jumlah_terjual'),
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            harga_rata_rata=Sum('total_penjualan') / Sum('jumlah_terjual')
        )
        .order_by('-total_terjual')[:limit]
    )

    # Format data
    result_data = []
    for item in produk_terlaris:
        nama_umkm = (
                item['produk__umkm__profil_umkm__nm_bisnis'] or
                item['produk__umkm__username']
        )

        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        margin_keuntungan = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0

        result_data.append({
            'produk_id': str(item['produk_id']),
            'nama_produk': item['produk__nm_produk'],
            'nama_umkm': nama_umkm,
            'kategori': item['produk__kategori__nm_kategori'],
            'total_terjual': item['total_terjual'],
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': item['jumlah_transaksi'],
            'harga_rata_rata': item['harga_rata_rata'] or 0,
            'margin_keuntungan': round(margin_keuntungan, 2)
        })

    serializer = AnalisisProdukTerlaris(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perbandingan_umkm_view(request):
    """
    Endpoint untuk perbandingan performa antar UMKM
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related(
        'produk__umkm__profil_umkm', 'produk'
    )

    # Apply filters
    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])

    # Agregasi per UMKM
    umkm_comparison = (
        queryset
        .annotate(
            pengeluaran_per_item=F('jumlah_terjual') * (F('produk__biaya_upah') + F('produk__biaya_produksi'))
        )
        .values(
            'produk__umkm_id',
            'produk__umkm__username',
            'produk__umkm__profil_umkm__nm_bisnis'
        )
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            total_pengeluaran=Sum('pengeluaran_per_item'),
            jumlah_transaksi=Count('id'),
            jumlah_produk_berbeda=Count('produk', distinct=True),
            jumlah_lokasi=Count('lokasi_penjualan', distinct=True)
        )
        .order_by('-total_penjualan')
    )

    # Format data dengan ranking
    result_data = []
    penjualan_list = [(item['total_penjualan'] or 0) for item in umkm_comparison]
    keuntungan_list = [
        (item['total_penjualan'] or 0) - (item['total_pengeluaran'] or 0)
        for item in umkm_comparison
    ]

    for idx, item in enumerate(umkm_comparison):
        nama_umkm = (
                item['produk__umkm__profil_umkm__nm_bisnis'] or
                item['produk__umkm__username']
        )

        total_penjualan = item['total_penjualan'] or 0
        total_pengeluaran = item['total_pengeluaran'] or 0
        laba_kotor = total_penjualan - total_pengeluaran
        jumlah_transaksi = item['jumlah_transaksi']
        margin_keuntungan = (laba_kotor / total_penjualan * 100) if total_penjualan > 0 else 0

        # Buat queryset untuk UMKM ini untuk breakdown lokasi
        umkm_queryset = queryset.filter(produk__umkm_id=item['produk__umkm_id'])
        breakdown_lokasi = get_breakdown_lokasi(umkm_queryset, total_penjualan)

        result_data.append({
            'umkm_id': str(item['produk__umkm_id']),
            'nama_umkm': nama_umkm,
            'total_penjualan': total_penjualan,
            'total_pengeluaran': total_pengeluaran,
            'laba_kotor': laba_kotor,
            'jumlah_transaksi': jumlah_transaksi,
            'jumlah_produk_berbeda': item['jumlah_produk_berbeda'],
            'jumlah_lokasi': item['jumlah_lokasi'],
            'rata_rata_per_transaksi': total_penjualan / jumlah_transaksi if jumlah_transaksi > 0 else 0,
            'margin_keuntungan': round(margin_keuntungan, 2),
            'ranking_penjualan': idx + 1,
            'ranking_keuntungan': sorted(keuntungan_list, reverse=True).index(laba_kotor) + 1,
            'breakdown_lokasi': breakdown_lokasi
        })

    serializer = PerbandinganUMKMSerializer(result_data, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
        'filters_applied': filters
    })