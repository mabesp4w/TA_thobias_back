# views/file_penjualan_view.py

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from django.contrib.auth import get_user_model

from ..models import FilePenjualan
from ..serializers.file_penjualan_serializer import FilePenjualanSerializer, FilePenjualanListSerializer
from ..pagination import LaravelStylePagination

User = get_user_model()


class FilePenjualanViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk mengelola file Excel detail penjualan UMKM.
    """
    queryset = FilePenjualan.objects.all()
    serializer_class = FilePenjualanSerializer
    pagination_class = LaravelStylePagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['umkm']
    search_fields = ['nama_file', 'deskripsi', 'umkm__username']
    ordering_fields = ['nama_file', 'tgl_upload', 'tgl_update']
    ordering = ['-tgl_upload']

    def get_serializer_class(self):
        if self.action == 'list':
            return FilePenjualanListSerializer
        return FilePenjualanSerializer

    def get_permissions(self):
        """
        Atur permission berdasarkan action
        """
        if self.action in ['my_files', 'upload_file', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset berdasarkan user
        """
        queryset = FilePenjualan.objects.all()

        # Jika bukan admin, hanya tampilkan file milik user sendiri
        if not self.request.user.is_staff and self.request.user.role == 'umkm':
            queryset = queryset.filter(umkm=self.request.user)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar file penjualan',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar file penjualan',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail file penjualan',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        # Set umkm dari user yang login
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna UMKM yang dapat mengupload file penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(umkm=request.user)

        return Response({
            'status': 'success',
            'message': 'Berhasil mengupload file penjualan',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Pastikan user hanya bisa update file miliknya sendiri
        if not request.user.is_staff and instance.umkm != request.user:
            return Response({
                'status': 'error',
                'message': 'Anda tidak memiliki permission untuk mengubah file ini'
            }, status=status.HTTP_403_FORBIDDEN)

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui file penjualan',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Pastikan user hanya bisa hapus file miliknya sendiri
        if not request.user.is_staff and instance.umkm != request.user:
            return Response({
                'status': 'error',
                'message': 'Anda tidak memiliki permission untuk menghapus file ini'
            }, status=status.HTTP_403_FORBIDDEN)

        file_name = instance.nama_file
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus file: {file_name}'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download file Excel
        """
        instance = self.get_object()

        # Pastikan user memiliki akses ke file
        if not request.user.is_staff and instance.umkm != request.user:
            return Response({
                'status': 'error',
                'message': 'Anda tidak memiliki permission untuk mendownload file ini'
            }, status=status.HTTP_403_FORBIDDEN)

        if not instance.file:
            raise Http404("File tidak ditemukan")

        try:
            response = HttpResponse(
                instance.file.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{instance.nama_file}"'
            return response
        except FileNotFoundError:
            raise Http404("File tidak ditemukan di server")

    @action(detail=False, methods=['get'])
    def my_files(self, request):
        """
        Mendapatkan daftar file penjualan milik user yang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna UMKM yang memiliki file penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = FilePenjualan.objects.filter(umkm=request.user)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar file penjualan Anda',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar file penjualan Anda',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        """
        Upload file Excel penjualan
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna UMKM yang dapat mengupload file penjualan'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(umkm=request.user)

        return Response({
            'status': 'success',
            'message': 'Berhasil mengupload file penjualan',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)