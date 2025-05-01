from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ..models import KategoriProduk
from ..serializers.kategori_produk_serializer import KategoriProdukSerializer, KategoriProdukListSerializer
from ..pagination import LaravelStylePagination

class KategoriProdukViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Kategori Produk untuk dilihat atau diedit.
    """
    queryset = KategoriProduk.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nm_kategori', 'desc']
    ordering_fields = ['nm_kategori']
    ordering = ['nm_kategori']

    def get_serializer_class(self):
        if self.action == 'list':
            return KategoriProdukListSerializer
        return KategoriProdukSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar kategori produk',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar kategori produk',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail kategori produk',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = KategoriProdukSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat kategori produk baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = KategoriProdukSerializer(instance)

        message = 'Berhasil memperbarui kategori produk'
        if partial:
            message = 'Berhasil memperbarui sebagian kategori produk'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        kategori_name = instance.nm_kategori
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus kategori produk: {kategori_name}'
        }, status=status.HTTP_200_OK)