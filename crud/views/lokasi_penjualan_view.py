from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from ..models import LokasiPenjualan
from ..serializers.lokasi_penjualan_serializer import LokasiPenjualanSerializer, LokasiPenjualanListSerializer
from ..pagination import LaravelStylePagination


class LokasiPenjualanViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Lokasi Penjualan untuk dilihat atau diedit.
    """
    queryset = LokasiPenjualan.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipe_lokasi', 'kecamatan', 'kecamatan__kabupaten', 'kecamatan__kabupaten__provinsi']
    search_fields = ['nm_lokasi', 'alamat', 'tlp_pengelola']
    ordering_fields = ['nm_lokasi', 'tipe_lokasi']
    ordering = ['nm_lokasi']

    def get_serializer_class(self):
        if self.action == 'list':
            return LokasiPenjualanListSerializer
        return LokasiPenjualanSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail lokasi penjualan',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = LokasiPenjualanSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat lokasi penjualan baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = LokasiPenjualanSerializer(instance)

        message = 'Berhasil memperbarui lokasi penjualan'
        if partial:
            message = 'Berhasil memperbarui sebagian lokasi penjualan'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        lokasi_name = instance.nm_lokasi
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus lokasi penjualan: {lokasi_name}'
        }, status=status.HTTP_200_OK)