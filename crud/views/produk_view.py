from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Produk
from ..serializers.produk_serializer import ProdukSerializer, ProdukListSerializer
from ..filters import ProdukFilter
from ..pagination import LaravelStylePagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class ProdukViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Produk untuk dilihat atau diedit.
    """
    queryset = Produk.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProdukFilter
    search_fields = ['nm_produk', 'desc', 'bahan_baku', 'umkm__username', 'umkm__profil_umkm__nm_bisnis',
                     'kategori__nm_kategori']
    ordering_fields = ['nm_produk', 'harga', 'stok', 'tgl_dibuat', 'tgl_update']
    ordering = ['-tgl_dibuat']

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProdukListSerializer
        return ProdukSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['my_products', 'create_my_product', 'update_my_product','destroy_my_product']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'list' or self.action == 'retrieve':
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
                'message': 'Berhasil mendapatkan daftar produk',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar produk',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail produk',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        # Tambahkan umkm dari request data jika tidak ada
        if 'umkm' not in request.data and request.user.is_authenticated:
            request.data['umkm'] = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = ProdukSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat produk baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = ProdukSerializer(instance)

        message = 'Berhasil memperbarui produk'
        if partial:
            message = 'Berhasil memperbarui sebagian produk'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        produk_name = instance.nm_produk
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus produk: {produk_name}'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """
        Mendapatkan daftar produk milik UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat melihat produk mereka'
            }, status=status.HTTP_400_BAD_REQUEST)

        produk = Produk.objects.filter(umkm=request.user)
        serializer = ProdukSerializer(produk, many=True)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar produk',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def create_my_product(self, request):
        """
        Membuat produk baru untuk UMKM yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat membuat produk'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set umkm ke user yang sedang login
        request.data['umkm'] = request.user.id

        serializer = ProdukSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat produk baru',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch'])
    def update_my_product(self, request, pk=None):
        """
        Update produk milik UMKM yang sedang login
        """
        try:
            produk = Produk.objects.get(pk=pk, umkm=request.user)
        except Produk.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Produk tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        # Tambahkan user id sebagai umkm ke request data
        data = request.data.copy()  # Buat copy dari request.data karena QueryDict mungkin immutable
        data['umkm'] = request.user.id

        partial = request.method == 'PATCH'
        serializer = ProdukSerializer(produk, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui produk',
            'data': serializer.data
        })

    @action(detail=True, methods=['delete'])
    def destroy_my_product(self, request, pk=None, *args, **kwargs):
        """
            Menghapus produk milik UMKM yang sedang login
            """
        try:
            produk = Produk.objects.get(pk=pk, umkm=request.user)
        except Produk.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Produk tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        produk_name = produk.nm_produk
        produk.delete()

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus produk: {produk_name}'
        }, status=status.HTTP_200_OK)