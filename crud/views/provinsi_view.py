from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from authentication.permissions import IsAdmin
from ..models import Provinsi
from ..serializers.provinsi_serializer import ProvinsiSerializer, ProvinsiListSerializer
from ..pagination import LaravelStylePagination

class ProvinsiViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Provinsi untuk dilihat atau diedit.
    """
    queryset = Provinsi.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nm_provinsi']
    ordering_fields = ['nm_provinsi']
    ordering = ['nm_provinsi']
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProvinsiListSerializer
        return ProvinsiSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar provinsi',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar provinsi',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail provinsi',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = ProvinsiSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat provinsi baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = ProvinsiSerializer(instance)

        message = 'Berhasil memperbarui provinsi'
        if partial:
            message = 'Berhasil memperbarui sebagian provinsi'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        provinsi_name = instance.nm_provinsi
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus provinsi: {provinsi_name}'
        }, status=status.HTTP_200_OK)