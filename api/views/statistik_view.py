# views/statistik_viewset.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from datetime import datetime, date
import hashlib

from ..serializers.statistik_serializer import (
    ParameterStatistikSerializer,
    StatistikUmumSerializer,
    LokasiStatistikSerializer,
    ProdukStatistikSerializer,
    PeriodeStatistikSerializer
)
from ..utils.statistik_utils import StatistikCalculator
from crud.models import LokasiPenjualan, Produk


class StatistikViewSet(viewsets.ViewSet):
    """
    API ViewSet untuk statistik pemasukan dan pengeluaran UMKM

    Endpoint yang tersedia:
    - GET /statistik/ringkasan/ - Statistik umum dengan parameter fleksibel
    - GET /statistik/lokasi/ - Statistik per lokasi penjualan
    - GET /statistik/produk/ - Statistik per produk
    - GET /statistik/periode/ - Statistik per periode (bulanan/tahunan)
    - GET /statistik/dashboard/ - Ringkasan untuk dashboard
    """

    permission_classes = [IsAuthenticated]

    def get_cache_key(self, user_id, action_name, params):
        """
        Generate cache key berdasarkan user, action, dan parameter
        """
        params_str = str(sorted(params.items()))
        key_string = f"statistik:{user_id}:{action_name}:{params_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def validate_umkm_access(self, request):
        """
        Validasi akses untuk user dengan role UMKM
        """
        if request.user.role not in ['umkm', 'admin']:
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna UMKM atau Admin yang dapat mengakses statistik'
            }, status=status.HTTP_403_FORBIDDEN)
        return None

    @action(detail=False, methods=['get'])
    def ringkasan(self, request):
        """
        Endpoint untuk mendapatkan statistik lengkap

        Query Parameters:
        - tipe_periode: bulanan|tahunan|custom (default: bulanan)
        - tahun: 2024 (required untuk bulanan/tahunan)
        - bulan: 1-12 (optional untuk bulanan)
        - tanggal_awal: YYYY-MM-DD (required untuk custom)
        - tanggal_akhir: YYYY-MM-DD (required untuk custom)
        - lokasi_id: UUID (optional)
        - produk_id: UUID (optional)
        """
        # Validasi akses
        access_error = self.validate_umkm_access(request)
        if access_error:
            return access_error

        # Validasi parameter
        param_serializer = ParameterStatistikSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Parameter tidak valid',
                'errors': param_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = param_serializer.validated_data

        # Check cache
        cache_key = self.get_cache_key(request.user.id, 'ringkasan', params)
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik (cached)',
                'data': cached_result
            })

        try:
            # Hitung statistik
            calculator = StatistikCalculator(user=request.user)
            statistics = calculator.calculate_full_statistics(params)

            # Serialize hasil
            serializer = StatistikUmumSerializer(statistics)

            # Cache hasil selama 5 menit
            cache.set(cache_key, serializer.data, 300)

            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik lengkap',
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Terjadi kesalahan saat menghitung statistik: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def lokasi(self, request):
        """
        Endpoint untuk statistik per lokasi penjualan
        """
        access_error = self.validate_umkm_access(request)
        if access_error:
            return access_error

        param_serializer = ParameterStatistikSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Parameter tidak valid',
                'errors': param_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = param_serializer.validated_data

        try:
            calculator = StatistikCalculator(user=request.user)

            # Buat filter berdasarkan periode
            periode_filter = calculator.get_periode_filter(params)
            additional_filter = calculator.get_additional_filters(params)

            # Gabungkan filter
            queryset = calculator.base_queryset.filter(periode_filter & additional_filter)

            # Hitung statistik per lokasi
            stats_lokasi = calculator.get_statistik_per_lokasi(queryset)

            serializer = LokasiStatistikSerializer(stats_lokasi, many=True)

            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik per lokasi',
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def produk(self, request):
        """
        Endpoint untuk statistik per produk
        """
        access_error = self.validate_umkm_access(request)
        if access_error:
            return access_error

        param_serializer = ParameterStatistikSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Parameter tidak valid',
                'errors': param_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = param_serializer.validated_data

        try:
            calculator = StatistikCalculator(user=request.user)

            # Buat filter berdasarkan periode
            periode_filter = calculator.get_periode_filter(params)
            additional_filter = calculator.get_additional_filters(params)

            # Gabungkan filter
            queryset = calculator.base_queryset.filter(periode_filter & additional_filter)

            # Hitung statistik per produk
            stats_produk = calculator.get_statistik_per_produk(queryset)

            serializer = ProdukStatistikSerializer(stats_produk, many=True)

            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik per produk',
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def periode(self, request):
        """
        Endpoint untuk statistik per periode (bulanan/tahunan)
        """
        access_error = self.validate_umkm_access(request)
        if access_error:
            return access_error

        param_serializer = ParameterStatistikSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Parameter tidak valid',
                'errors': param_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = param_serializer.validated_data

        try:
            calculator = StatistikCalculator(user=request.user)

            # Buat filter berdasarkan periode
            periode_filter = calculator.get_periode_filter(params)
            additional_filter = calculator.get_additional_filters(params)

            # Gabungkan filter
            queryset = calculator.base_queryset.filter(periode_filter & additional_filter)

            # Hitung statistik per periode
            stats_periode = calculator.get_statistik_per_periode(
                queryset,
                params.get('tipe_periode', 'bulanan')
            )

            serializer = PeriodeStatistikSerializer(stats_periode, many=True)

            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik per periode',
                'data': serializer.data
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Endpoint untuk dashboard - ringkasan singkat statistik bulan ini
        """
        access_error = self.validate_umkm_access(request)
        if access_error:
            return access_error

        try:
            # Parameter default untuk bulan ini
            today = date.today()
            params = {
                'tipe_periode': 'bulanan',
                'tahun': today.year,
                'bulan': today.month
            }

            calculator = StatistikCalculator(user=request.user)

            # Hitung statistik bulan ini
            periode_filter = calculator.get_periode_filter(params)
            queryset = calculator.base_queryset.filter(periode_filter)
            base_stats = calculator.calculate_base_stats(queryset)

            # Hitung statistik bulan lalu untuk perbandingan
            if today.month == 1:
                bulan_lalu = {'tahun': today.year - 1, 'bulan': 12}
            else:
                bulan_lalu = {'tahun': today.year, 'bulan': today.month - 1}

            params_bulan_lalu = {
                'tipe_periode': 'bulanan',
                'tahun': bulan_lalu['tahun'],
                'bulan': bulan_lalu['bulan']
            }

            periode_filter_lalu = calculator.get_periode_filter(params_bulan_lalu)
            queryset_lalu = calculator.base_queryset.filter(periode_filter_lalu)
            stats_bulan_lalu = calculator.calculate_base_stats(queryset_lalu)

            # Hitung persentase perubahan
            def hitung_perubahan(nilai_sekarang, nilai_lalu):
                if nilai_lalu == 0:
                    return 100 if nilai_sekarang > 0 else 0
                return ((nilai_sekarang - nilai_lalu) / nilai_lalu * 100)

            perubahan_pemasukan = hitung_perubahan(
                base_stats['total_pemasukan'],
                stats_bulan_lalu['total_pemasukan']
            )

            perubahan_transaksi = hitung_perubahan(
                base_stats['total_transaksi'],
                stats_bulan_lalu['total_transaksi']
            )

            # Top 3 produk terlaris bulan ini
            top_produk = calculator.get_statistik_per_produk(queryset)[:3]

            # Top 3 lokasi terlaris bulan ini
            top_lokasi = calculator.get_statistik_per_lokasi(queryset)[:3]

            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik dashboard',
                'data': {
                    'periode': f"{today.strftime('%B %Y')}",
                    'ringkasan': {
                        'total_pemasukan_bulan_ini': base_stats['total_pemasukan'],
                        'total_transaksi_bulan_ini': base_stats['total_transaksi'],
                        'keuntungan_bersih': base_stats['keuntungan_bersih'],
                        'margin_keuntungan': base_stats['margin_keuntungan'],
                        'perubahan_pemasukan': round(perubahan_pemasukan, 2),
                        'perubahan_transaksi': round(perubahan_transaksi, 2)
                    },
                    'top_produk': ProdukStatistikSerializer(top_produk, many=True).data,
                    'top_lokasi': LokasiStatistikSerializer(top_lokasi, many=True).data
                }
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
