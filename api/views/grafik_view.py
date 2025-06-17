# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.db.models.functions import Extract
from django.contrib.auth import get_user_model
from datetime import datetime
from crud.models import ProdukTerjual, ProfilUMKM
from api.serializers.grafik_serializers import (
    GrafikPenjualanSerializer,
    UMKMListSerializer,
    FilterGrafikSerializer
)

User = get_user_model()

# Mapping nama bulan
NAMA_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grafik_penjualan_view(request):
    """
    Endpoint untuk mendapatkan data grafik penjualan
    Support filter: umkm_id, tahun, bulan_start, bulan_end
    """
    # Validasi parameter
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.all()

    # Filter berdasarkan UMKM jika ada
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    # Filter berdasarkan tahun jika ada
    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        # Default tahun sekarang jika tidak ada filter
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    # Filter berdasarkan periode bulan jika ada
    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )
    elif filters.get('bulan_start'):
        queryset = queryset.filter(tgl_penjualan__month__gte=filters['bulan_start'])
    elif filters.get('bulan_end'):
        queryset = queryset.filter(tgl_penjualan__month__lte=filters['bulan_end'])

    # Agregasi data per bulan
    data_penjualan = (
        queryset
        .annotate(
            bulan=Extract('tgl_penjualan', 'month'),
            tahun=Extract('tgl_penjualan', 'year')
        )
        .values('bulan', 'tahun')
        .annotate(
            total_penjualan=Sum('total_penjualan'),
            jumlah_transaksi=Count('id')
        )
        .order_by('tahun', 'bulan')
    )

    # Tambahkan nama bulan
    result_data = []
    for item in data_penjualan:
        item['nama_bulan'] = NAMA_BULAN.get(item['bulan'], f"Bulan {item['bulan']}")
        result_data.append(item)

    # Serialize data
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
    Endpoint untuk mendapatkan data grafik penjualan semua UMKM
    Untuk membandingkan performa antar UMKM
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.select_related('produk__umkm__profil_umkm')

    # Filter berdasarkan tahun
    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    # Filter berdasarkan periode bulan jika ada
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
            tahun=Extract('tgl_penjualan', 'year')
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
            jumlah_transaksi=Count('id')
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

        result_data.append({
            'umkm_id': str(item['produk__umkm_id']),
            'nama_umkm': nama_umkm,
            'bulan': item['bulan'],
            'tahun': item['tahun'],
            'total_penjualan': item['total_penjualan'] or 0,
            'jumlah_transaksi': item['jumlah_transaksi'],
            'nama_bulan': NAMA_BULAN.get(item['bulan'], f"Bulan {item['bulan']}")
        })

    return Response({
        'status': 'success',
        'data': result_data,
        'filters_applied': filters
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_umkm_view(request):
    """
    Endpoint untuk mendapatkan list UMKM untuk dropdown
    """
    # Filter user berdasarkan role jika field tersebut ada
    try:
        # Coba filter berdasarkan role
        umkm_users = User.objects.filter(
            role='umkm'
        ).select_related('profil_umkm').order_by('username')
    except:
        # Jika field role tidak ada, ambil user yang memiliki profil_umkm
        umkm_users = User.objects.filter(
            profil_umkm__isnull=False
        ).select_related('profil_umkm').order_by('username')

    serializer = UMKMListSerializer(umkm_users, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ringkasan_penjualan_view(request):
    """
    Endpoint untuk mendapatkan ringkasan data penjualan
    """
    filter_serializer = FilterGrafikSerializer(data=request.query_params)
    if not filter_serializer.is_valid():
        return Response(
            {'error': filter_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    filters = filter_serializer.validated_data

    # Base queryset
    queryset = ProdukTerjual.objects.all()

    # Apply filters
    if filters.get('umkm_id'):
        queryset = queryset.filter(produk__umkm_id=filters['umkm_id'])

    if filters.get('tahun'):
        queryset = queryset.filter(tgl_penjualan__year=filters['tahun'])
    else:
        queryset = queryset.filter(tgl_penjualan__year=datetime.now().year)

    if filters.get('bulan_start') and filters.get('bulan_end'):
        queryset = queryset.filter(
            tgl_penjualan__month__gte=filters['bulan_start'],
            tgl_penjualan__month__lte=filters['bulan_end']
        )

    # Hitung ringkasan
    summary = queryset.aggregate(
        total_penjualan=Sum('total_penjualan'),
        total_transaksi=Count('id'),
        total_produk_terjual=Sum('jumlah_terjual')
    )

    # Hitung jumlah UMKM aktif
    jumlah_umkm = queryset.values('produk__umkm').distinct().count()

    return Response({
        'status': 'success',
        'data': {
            'total_penjualan': summary['total_penjualan'] or 0,
            'total_transaksi': summary['total_transaksi'],
            'total_produk_terjual': summary['total_produk_terjual'] or 0,
            'jumlah_umkm_aktif': jumlah_umkm
        },
        'filters_applied': filters
    })