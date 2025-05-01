from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ProdukTerjual, Produk
from ..serializers.produk_terjual_serializer import ProdukTerjualSerializer, ProdukTerjualListSerializer
from ..filters import ProdukTerjualFilter
from ..pagination import LaravelStylePagination


class ProdukTerjualViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan data Produk Terjual untuk dilihat atau diedit.
    """
    queryset = ProdukTerjual.objects.all()
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
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['my_sales', 'create_my_sale', 'update_my_sale']:
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
                'message': 'Berhasil mendapatkan daftar produk terjual',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar produk terjual',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail produk terjual',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = ProdukTerjualSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat data produk terjual baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = ProdukTerjualSerializer(instance)

        message = 'Berhasil memperbarui data produk terjual'
        if partial:
            message = 'Berhasil memperbarui sebagian data produk terjual'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        produk_name = instance.produk.nm_produk
        tgl_penjualan = instance.tgl_penjualan.strftime('%Y-%m-%d')
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus data penjualan {produk_name} pada {tgl_penjualan}'
        }, status=status.HTTP_200_OK)

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

        # Filter produk milik UMKM yang login
        produk_ids = Produk.objects.filter(umkm=request.user).values_list('id', flat=True)

        # Filter penjualan berdasarkan produk milik UMKM
        penjualan = ProdukTerjual.objects.filter(produk_id__in=produk_ids)

        # Terapkan filter dari query params
        penjualan = self.filter_queryset(penjualan)

        # Pagination
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

        # Pastikan produk milik UMKM yang login
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

        serializer = ProdukTerjualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat data penjualan baru',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch'])
    def update_my_sale(self, request, pk=None):
        """
        Update data penjualan produk milik UMKM yang sedang login
        """
        try:
            # Ambil penjualan berdasarkan ID
            penjualan = ProdukTerjual.objects.get(pk=pk)

            # Periksa apakah produk milik UMKM yang login
            if penjualan.produk.umkm.id != request.user.id:
                return Response({
                    'status': 'error',
                    'message': 'Data penjualan ini bukan milik produk Anda'
                }, status=status.HTTP_403_FORBIDDEN)

        except ProdukTerjual.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Data penjualan tidak ditemukan'
            }, status=status.HTTP_404_NOT_FOUND)

        # Jika request mengubah produk, pastikan produk baru juga milik UMKM yang login
        if 'produk' in request.data and request.data['produk'] != str(penjualan.produk.id):
            try:
                new_produk = Produk.objects.get(pk=request.data['produk'], umkm=request.user)
            except Produk.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Produk baru tidak ditemukan atau bukan milik Anda'
                }, status=status.HTTP_400_BAD_REQUEST)

        partial = request.method == 'PATCH'
        serializer = ProdukTerjualSerializer(penjualan, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui data penjualan',
            'data': serializer.data
        })