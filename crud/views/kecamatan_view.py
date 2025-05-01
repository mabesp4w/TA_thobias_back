from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Kecamatan
from ..serializers.kecamatan_serializer import KecamatanSerializer, KecamatanListSerializer
from ..pagination import LaravelStylePagination

class KecamatanViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Kecamatan untuk dilihat atau diedit.
    """
    queryset = Kecamatan.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['kabupaten', 'kabupaten__provinsi', 'kabupaten__is_kota']
    search_fields = ['nm_kecamatan', 'kode', 'kabupaten__nm_kabupaten', 'kabupaten__provinsi__nm_provinsi']
    ordering_fields = ['nm_kecamatan', 'kabupaten__nm_kabupaten', 'kabupaten__provinsi__nm_provinsi']
    ordering = ['kabupaten__provinsi__nm_provinsi', 'kabupaten__nm_kabupaten', 'nm_kecamatan']

    def get_serializer_class(self):
        if self.action == 'list':
            return KecamatanListSerializer
        return KecamatanSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar kecamatan',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar kecamatan',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail kecamatan',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = KecamatanSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat kecamatan baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = KecamatanSerializer(instance)

        message = 'Berhasil memperbarui kecamatan'
        if partial:
            message = 'Berhasil memperbarui sebagian kecamatan'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        kecamatan_name = instance.nm_kecamatan
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus kecamatan: {kecamatan_name}'
        }, status=status.HTTP_200_OK)