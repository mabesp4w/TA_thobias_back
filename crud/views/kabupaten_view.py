from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Kabupaten
from ..serializers.kabupaten_serializer import KabupatenSerializer, KabupatenListSerializer
from ..pagination import LaravelStylePagination

class KabupatenViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Kabupaten untuk dilihat atau diedit.
    """
    queryset = Kabupaten.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provinsi', 'is_kota']
    search_fields = ['nm_kabupaten', 'kode', 'provinsi__nm_provinsi']
    ordering_fields = ['nm_kabupaten', 'provinsi__nm_provinsi', 'is_kota']
    ordering = ['provinsi__nm_provinsi', 'nm_kabupaten']

    def get_serializer_class(self):
        if self.action == 'list':
            return KabupatenListSerializer
        return KabupatenSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar kabupaten/kota',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar kabupaten/kota',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail kabupaten/kota',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = KabupatenSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat kabupaten/kota baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = KabupatenSerializer(instance)

        message = 'Berhasil memperbarui kabupaten/kota'
        if partial:
            message = 'Berhasil memperbarui sebagian kabupaten/kota'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        tipe = "Kota" if instance.is_kota else "Kabupaten"
        kabupaten_name = f"{tipe} {instance.nm_kabupaten}"
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus {kabupaten_name}'
        }, status=status.HTTP_200_OK)