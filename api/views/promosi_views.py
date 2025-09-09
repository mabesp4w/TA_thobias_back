# api/views/promosi_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination

from crud.models import Produk, KategoriProduk, ProfilUMKM
from authentication.models import User
from api.serializers.promosi_serializers import (
    ProdukPromosiSerializer,
    KategoriStatistikSerializer,
    PromosiStatsSerializer
)

# Import LaravelStylePagination dari kategori_produk_view.py
# Asumsi ini didefinisikan di crud/pagination.py atau serupa, jadi import sesuai
from crud.pagination import LaravelStylePagination  # Sesuaikan path import jika diperlukan
import uuid

class PromosePagination(PageNumberPagination):
    """
    Custom pagination untuk halaman promosi
    """
    page_size = 12
    page_size_query_param = 'limit'
    max_page_size = 48
    page_query_param = 'page'


class PromosiViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet khusus untuk halaman promosi produk UMKM
    Read-only karena ini untuk public display
    """
    queryset = Produk.objects.all()
    serializer_class = ProdukPromosiSerializer
    # Ganti ke LaravelStylePagination seperti di kategori_produk_view.py
    pagination_class = LaravelStylePagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Filter queryset untuk halaman promosi
        """
        queryset = super().get_queryset()

        # Filter produk aktif
        queryset = queryset.filter(aktif=True)

        # Optimasi query dengan select_related
        queryset = queryset.select_related('kategori', 'umkm')

        # Filter berdasarkan parameter query
        kategori = self.request.query_params.get('kategori')
        umkm_id = self.request.query_params.get('umkm_id')
        min_harga = self.request.query_params.get('min_harga')
        max_harga = self.request.query_params.get('max_harga')
        stok_tersedia = self.request.query_params.get('stok_tersedia')
        search = self.request.query_params.get('search')

        if kategori:
            try:
                # Konversi ke UUID untuk menghindari masalah filter pada UUIDField
                kategori_uuid = uuid.UUID(kategori)
                queryset = queryset.filter(kategori__id=kategori_uuid)
            except (ValueError, TypeError):
                # Jika bukan UUID valid, skip filter atau bisa raise error jika diinginkan
                pass

        if umkm_id:
            try:
                umkm_uuid = uuid.UUID(umkm_id)
                queryset = queryset.filter(umkm__id=umkm_uuid)
            except (ValueError, TypeError):
                pass

        if min_harga:
            try:
                queryset = queryset.filter(harga__gte=float(min_harga))
            except ValueError:
                pass

        if max_harga:
            try:
                queryset = queryset.filter(harga__lte=float(max_harga))
            except ValueError:
                pass

        if stok_tersedia and stok_tersedia.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(stok__gt=0)

        # Search functionality
        if search:
            queryset = queryset.filter(
                Q(nm_produk__icontains=search) |
                Q(desc__icontains=search) |
                Q(umkm__username__icontains=search) |
                Q(kategori__nm_kategori__icontains=search)
            )

        # Filter user aktif jika field exists
        try:
            queryset = queryset.filter(umkm__is_active=True)
        except Exception:
            pass

        # Ordering
        ordering = self.request.query_params.get('ordering', '-tgl_update')
        valid_orderings = ['nm_produk', '-nm_produk', 'harga', '-harga',
                           'tgl_dibuat', '-tgl_dibuat', 'tgl_update', '-tgl_update',
                           'stok', '-stok']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-tgl_update', '-tgl_dibuat')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list untuk format response seperti di kategori_produk_view.py
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar produk promosi',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar produk promosi',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve untuk format response konsisten
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail produk promosi',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Endpoint untuk mendapatkan daftar kategori dengan statistik
        GET /api/promosi/categories/
        """
        try:
            categories = KategoriProduk.objects.annotate(
                jumlah_produk=Count(
                    'produk',
                    filter=Q(produk__aktif=True)
                )
            ).filter(jumlah_produk__gt=0).order_by('nm_kategori')

            serializer = KategoriStatistikSerializer(categories, many=True)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar kategori',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat kategori: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Endpoint untuk produk unggulan/featured
        GET /api/promosi/featured/
        """
        try:
            featured_products = self.get_queryset().filter(
                stok__gt=0,
                tgl_dibuat__gte=timezone.now() - timedelta(days=30)
            ).order_by('-tgl_dibuat')[:8]

            serializer = self.get_serializer(featured_products, many=True)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan produk unggulan',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat produk unggulan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint untuk statistik promosi
        GET /api/promosi/stats/
        """
        try:
            total_produk = Produk.objects.filter(aktif=True).count()

            try:
                total_umkm = User.objects.filter(
                    is_active=True,
                    produk__aktif=True
                ).distinct().count()
            except:
                total_umkm = User.objects.filter(
                    produk__aktif=True
                ).distinct().count()

            total_kategori = KategoriProduk.objects.annotate(
                produk_count=Count(
                    'produk',
                    filter=Q(produk__aktif=True)
                )
            ).filter(produk_count__gt=0).count()

            produk_terbaru = Produk.objects.filter(
                aktif=True,
                tgl_dibuat__gte=timezone.now() - timedelta(days=30)
            ).count()

            stats_data = {
                'total_produk': total_produk,
                'total_umkm': total_umkm,
                'total_kategori': total_kategori,
                'produk_terbaru': produk_terbaru,
            }

            serializer = PromosiStatsSerializer(stats_data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan statistik promosi',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat statistik: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Endpoint untuk produk populer
        GET /api/promosi/popular/
        """
        try:
            popular_products = self.get_queryset().filter(
                stok__gte=5
            ).order_by('-stok', '-tgl_update')[:12]

            serializer = self.get_serializer(popular_products, many=True)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan produk populer',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat produk populer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_umkm(self, request):
        """
        Endpoint untuk mendapatkan produk berdasarkan UMKM
        GET /api/promosi/by_umkm/?umkm_id=xxx
        """
        umkm_id = request.query_params.get('umkm_id')
        if not umkm_id:
            return Response(
                {'error': 'Parameter umkm_id diperlukan'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            products = self.get_queryset().filter(umkm_id=umkm_id)

            page = self.paginate_queryset(products)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                result = self.get_paginated_response(serializer.data)
                return Response({
                    'status': 'success',
                    'message': 'Berhasil mendapatkan produk UMKM',
                    'data': result.data
                })

            serializer = self.get_serializer(products, many=True)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan produk UMKM',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat produk UMKM: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """
        Endpoint untuk produk terkait berdasarkan kategori
        GET /api/promosi/{id}/related/
        """
        try:
            product = self.get_object()
            related_products = self.get_queryset().filter(
                kategori=product.kategori
            ).exclude(id=product.id)[:6]

            serializer = self.get_serializer(related_products, many=True)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan produk terkait',
                'data': serializer.data
            })

        except Produk.DoesNotExist:
            return Response(
                {'error': 'Produk tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Gagal memuat produk terkait: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromosiKategoriViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet untuk kategori produk dalam promosi
    """
    queryset = KategoriProduk.objects.all()
    serializer_class = KategoriStatistikSerializer
    permission_classes = [AllowAny]
    # Tambahkan pagination seperti di kategori_produk_view.py
    pagination_class = LaravelStylePagination

    def get_queryset(self):
        """
        Hanya tampilkan kategori yang memiliki produk aktif
        """
        queryset = super().get_queryset()

        queryset = queryset.annotate(
            jumlah_produk=Count(
                'produk',
                filter=Q(produk__aktif=True)
            )
        ).filter(jumlah_produk__gt=0)

        # Manual search implementation
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nm_kategori__icontains=search) |
                Q(desc__icontains=search)
            )

        # Manual ordering
        ordering = self.request.query_params.get('ordering', 'nm_kategori')
        if ordering in ['nm_kategori', '-nm_kategori', 'jumlah_produk', '-jumlah_produk']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('nm_kategori')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list untuk format response konsisten
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar kategori promosi',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar kategori promosi',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve untuk format response konsisten
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail kategori promosi',
            'data': serializer.data
        })