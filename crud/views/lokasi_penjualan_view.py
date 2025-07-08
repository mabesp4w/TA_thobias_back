from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

from ..models import LokasiPenjualan
from ..serializers.lokasi_penjualan_serializer import LokasiPenjualanSerializer, LokasiPenjualanListSerializer
from ..pagination import LaravelStylePagination

# views/lokasi_penjualan_view.py
class LokasiPenjualanViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Lokasi Penjualan untuk dilihat atau diedit.
    """
    queryset = LokasiPenjualan.objects.select_related('kecamatan__kabupaten__provinsi', 'kategori_lokasi', 'umkm')
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['kategori_lokasi', 'kecamatan', 'kecamatan__kabupaten', 'kecamatan__kabupaten__provinsi',
                        'aktif']
    search_fields = ['nm_lokasi', 'alamat', 'tlp_pengelola']
    ordering_fields = ['nm_lokasi', 'kategori_lokasi', 'tgl_dibuat']
    ordering = ['nm_lokasi']

    def get_serializer_class(self):
        if self.action == 'list':
            return LokasiPenjualanListSerializer
        return LokasiPenjualanSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['my_locations', 'create_my_location', 'update_my_location', 'destroy_my_location']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset berdasarkan user role
        """
        queryset = super().get_queryset()

        # Jika bukan admin, hanya tampilkan lokasi aktif
        if not self.request.user.is_staff:
            queryset = queryset.filter(aktif=True)

        return queryset

    def perform_create(self, serializer):
        """
        Set UMKM otomatis saat membuat lokasi penjualan
        """
        serializer.save(umkm=self.request.user)

    # Method untuk UMKM mengelola lokasi mereka sendiri
    @action(detail=False, methods=['get'])
    def my_locations(self, request):
        """
        Mendapatkan daftar lokasi penjualan milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat melihat lokasi mereka'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = LokasiPenjualan.objects.filter(umkm=request.user).select_related(
            'kecamatan__kabupaten__provinsi', 'kategori_lokasi'
        )

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar lokasi penjualan',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar lokasi penjualan',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def create_my_location(self, request):
        """
        Membuat lokasi penjualan baru untuk UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat membuat lokasi penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = LokasiPenjualanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(umkm=request.user)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat lokasi penjualan baru',
            'data': LokasiPenjualanSerializer(instance).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch'])
    def update_my_location(self, request, pk=None):
        """
        Update lokasi penjualan milik UMKM yang sedang login
        """
        try:
            location = LokasiPenjualan.objects.get(pk=pk, umkm=request.user)
        except LokasiPenjualan.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Lokasi penjualan tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        partial = request.method == 'PATCH'
        serializer = LokasiPenjualanSerializer(location, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui lokasi penjualan',
            'data': serializer.data
        })

    @action(detail=True, methods=['delete'])
    def destroy_my_location(self, request, pk=None):
        """
        Menghapus lokasi penjualan milik UMKM yang sedang login
        """
        try:
            location = LokasiPenjualan.objects.get(pk=pk, umkm=request.user)
        except LokasiPenjualan.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Lokasi penjualan tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        location_name = location.nm_lokasi
        location.delete()

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus lokasi penjualan: {location_name}'
        }, status=status.HTTP_200_OK)