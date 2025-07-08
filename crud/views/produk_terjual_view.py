# views/produk_terjual_view.py

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ProdukTerjual, Produk, LokasiPenjualan
from ..serializers.produk_terjual_serializer import ProdukTerjualSerializer, ProdukTerjualListSerializer
from ..filters import ProdukTerjualFilter
from ..pagination import LaravelStylePagination


class ProdukTerjualViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan data Produk Terjual untuk dilihat atau diedit.
    """
    queryset = ProdukTerjual.objects.select_related(
        'produk__umkm__profil_umkm',
        'produk__kategori',
        'lokasi_penjualan__kecamatan__kabupaten__provinsi'
    )
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProdukTerjualFilter
    search_fields = ['produk__nm_produk', 'lokasi_penjualan__nm_lokasi', 'catatan']
    ordering_fields = ['tgl_penjualan', 'jumlah_terjual', 'harga_jual', 'total_penjualan', 'tgl_pelaporan']
    ordering = ['-tgl_penjualan']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProdukTerjualListSerializer
        return ProdukTerjualSerializer

    def get_permissions(self):
        if self.action in ['my_sales', 'create_my_sale', 'update_my_sale', 'destroy_my_sale']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Customize queryset berdasarkan user role
        """
        queryset = super().get_queryset()

        # Jika bukan admin/staff, filter hanya produk aktif
        if not self.request.user.is_staff:
            queryset = queryset.filter(produk__aktif=True)

        return queryset

    # Methods yang sudah ada tetap sama, tapi dengan perbaikan kecil...

    @action(detail=False, methods=['get'])
    def my_sales(self, request):
        """
        Mendapatkan daftar penjualan produk milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat melihat data penjualan mereka'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Optimized query
        penjualan = ProdukTerjual.objects.filter(
            produk__umkm=request.user
        ).select_related(
            'produk__kategori',
            'lokasi_penjualan__kecamatan__kabupaten__provinsi'
        )

        penjualan = self.filter_queryset(penjualan)
        page = self.paginate_queryset(penjualan)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar penjualan',
                'data': result.data
            })

        serializer = self.get_serializer(penjualan, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar penjualan',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def create_my_sale(self, request):
        """
        Membuat data penjualan baru untuk produk milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat membuat data penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validasi produk
        produk_id = request.data.get('produk')
        if not produk_id:
            return Response({
                'status': 'error',
                'message': 'ID produk diperlukan',
                'errors': {'produk': ['Field ini diperlukan.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            produk = Produk.objects.get(pk=produk_id, umkm=request.user)
        except Produk.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Produk tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validasi lokasi penjualan (jika ada)
        lokasi_id = request.data.get('lokasi_penjualan')
        if lokasi_id:
            try:
                lokasi = LokasiPenjualan.objects.get(pk=lokasi_id, umkm=request.user)
            except LokasiPenjualan.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Lokasi penjualan tidak ditemukan atau bukan milik Anda'
                }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProdukTerjualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat data penjualan baru',
            'data': ProdukTerjualSerializer(instance).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch'])
    def update_my_sale(self, request, pk=None):
        """
        Update data penjualan produk milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat mengupdate data penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Dapatkan instance penjualan
        try:
            instance = ProdukTerjual.objects.select_related(
                'produk__umkm'
            ).get(pk=pk, produk__umkm=request.user)
        except ProdukTerjual.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Data penjualan tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validasi produk jika diubah
        produk_id = request.data.get('produk')
        if produk_id:
            try:
                produk = Produk.objects.get(pk=produk_id, umkm=request.user)
            except Produk.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Produk tidak ditemukan atau bukan milik Anda'
                }, status=status.HTTP_404_NOT_FOUND)

        # Validasi lokasi penjualan jika diubah
        lokasi_id = request.data.get('lokasi_penjualan')
        if lokasi_id:
            try:
                lokasi = LokasiPenjualan.objects.get(pk=lokasi_id, umkm=request.user)
            except LokasiPenjualan.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Lokasi penjualan tidak ditemukan atau bukan milik Anda'
                }, status=status.HTTP_404_NOT_FOUND)

        # Update data
        partial = request.method == 'PATCH'
        serializer = ProdukTerjualSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil mengupdate data penjualan',
            'data': ProdukTerjualSerializer(updated_instance).data
        })

    @action(detail=True, methods=['delete'])
    def destroy_my_sale(self, request, pk=None):
        """
        Hapus data penjualan produk milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat menghapus data penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Dapatkan instance penjualan
        try:
            instance = ProdukTerjual.objects.select_related(
                'produk__umkm'
            ).get(pk=pk, produk__umkm=request.user)
        except ProdukTerjual.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Data penjualan tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        # Simpan data untuk response (opsional)
        deleted_data = {
            'id': instance.id,
            'produk': instance.produk.nm_produk,
            'tgl_penjualan': instance.tgl_penjualan,
            'jumlah_terjual': instance.jumlah_terjual,
            'total_penjualan': instance.total_penjualan
        }

        # Hapus data
        instance.delete()

        return Response({
            'status': 'success',
            'message': 'Berhasil menghapus data penjualan',
            'data': deleted_data
        })

    