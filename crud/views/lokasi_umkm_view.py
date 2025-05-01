from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from ..models import LokasiUMKM
from ..serializers.lokasi_umkm_serializer import LokasiUMKMSerializer, LokasiUMKMListSerializer
from ..filters import LokasiUMKMFilter
from ..pagination import LaravelStylePagination


class LokasiUMKMViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Lokasi UMKM untuk dilihat atau diedit.
    """
    queryset = LokasiUMKM.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LokasiUMKMFilter
    search_fields = ['alamat_lengkap', 'kode_pos', 'pengguna__username', 'pengguna__profil_umkm__nm_bisnis']
    ordering_fields = ['tgl_update', 'pengguna__username', 'kecamatan__nm_kecamatan']
    ordering = ['-tgl_update']

    def get_serializer_class(self):
        if self.action == 'list':
            return LokasiUMKMListSerializer
        return LokasiUMKMSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['my_locations', 'create_my_location', 'update_my_location']:
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
                'message': 'Berhasil mendapatkan daftar lokasi UMKM',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar lokasi UMKM',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail lokasi UMKM',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        # Tambahkan pengguna dari request data jika tidak ada
        if 'pengguna' not in request.data and request.user.is_authenticated:
            request.data['pengguna'] = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return complete representation
        result_serializer = LokasiUMKMSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat lokasi UMKM baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return complete representation
        result_serializer = LokasiUMKMSerializer(instance)

        message = 'Berhasil memperbarui lokasi UMKM'
        if partial:
            message = 'Berhasil memperbarui sebagian lokasi UMKM'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        nm_bisnis = getattr(getattr(instance.pengguna, 'profil_umkm', None), 'nm_bisnis', instance.pengguna.username)
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus lokasi UMKM: {nm_bisnis}'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_locations(self, request):
        """
        Mendapatkan daftar lokasi UMKM milik pengguna yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat melihat lokasi UMKM mereka'
            }, status=status.HTTP_400_BAD_REQUEST)

        locations = LokasiUMKM.objects.filter(pengguna=request.user)
        serializer = LokasiUMKMSerializer(locations, many=True)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar lokasi UMKM',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def create_my_location(self, request):
        """
        Membuat lokasi UMKM baru untuk pengguna yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang dapat membuat lokasi UMKM'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set pengguna ke user yang sedang login
        request.data['pengguna'] = request.user.id

        serializer = LokasiUMKMSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat lokasi UMKM baru',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch'])
    def update_my_location(self, request, pk=None):
        """
        Update lokasi UMKM milik pengguna yang sedang login
        """
        try:
            location = LokasiUMKM.objects.get(pk=pk, pengguna=request.user)
        except LokasiUMKM.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Lokasi UMKM tidak ditemukan atau bukan milik Anda'
            }, status=status.HTTP_404_NOT_FOUND)

        partial = request.method == 'PATCH'
        serializer = LokasiUMKMSerializer(location, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui lokasi UMKM',
            'data': serializer.data
        })