# views/profile_umkm_view
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ProfilUMKM
from ..serializers.profil_umkm_serializer import ProfilUMKMSerializer, ProfilUMKMListSerializer
from ..pagination import LaravelStylePagination


class ProfilUMKMViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan Profil UMKM untuk dilihat atau diedit.
    """
    queryset = ProfilUMKM.objects.all()
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user']
    search_fields = ['nm_bisnis', 'alamat', 'tlp', 'user__username', 'user__email', 'user__first_name',
                     'user__last_name']
    ordering_fields = ['nm_bisnis', 'tgl_bergabung', 'user__username']
    ordering = ['-tgl_bergabung']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProfilUMKMListSerializer
        return ProfilUMKMSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['my_profile', 'update_my_profile']:
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
                'message': 'Berhasil mendapatkan daftar profil UMKM',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar profil UMKM',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail profil UMKM',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        # Tambahkan user dari request data jika tidak ada
        if 'user' not in request.data and request.user.is_authenticated:
            request.data['user'] = request.user.id

        serializer = self.get_serializer(data=request.data)

        # Handle validation error secara manual
        if not serializer.is_valid():
            # Ekstrak error messages
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                else:
                    error_messages.append(f"{field}: {errors}")

            return Response({
                'status': 'error',
                'message': '; '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        # Return complete representation
        result_serializer = ProfilUMKMSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'status': 'success',
            'message': 'Berhasil membuat profil UMKM baru',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        # Handle validation error secara manual
        if not serializer.is_valid():
            # Ekstrak error messages
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                else:
                    error_messages.append(f"{field}: {errors}")

            return Response({
                'status': 'error',
                'message': '; '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        # Return complete representation
        result_serializer = ProfilUMKMSerializer(instance)

        message = 'Berhasil memperbarui profil UMKM'
        if partial:
            message = 'Berhasil memperbarui sebagian profil UMKM'

        return Response({
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        bisnis_name = instance.nm_bisnis or instance.user.username
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus profil UMKM: {bisnis_name}'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Mendapatkan profil UMKM pengguna yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang memiliki profil UMKM'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = request.user.profil_umkm
        except ProfilUMKM.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Profil UMKM tidak ditemukan'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfilUMKMSerializer(profile)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan profil UMKM',
            'data': serializer.data
        })

    @action(detail=False, methods=['put', 'patch'])
    def update_my_profile(self, request):
        """
        Update profil UMKM pengguna yang sedang login
        """
        if request.user.role != 'umkm':
            return Response({
                'status': 'error',
                'message': 'Hanya pengguna dengan role UMKM yang memiliki profil UMKM'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = request.user.profil_umkm
        except ProfilUMKM.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Profil UMKM tidak ditemukan'
            }, status=status.HTTP_404_NOT_FOUND)

        partial = request.method == 'PATCH'
        serializer = ProfilUMKMSerializer(profile, data=request.data, partial=partial)

        # Handle validation error secara manual
        if not serializer.is_valid():
            # Ekstrak error messages
            error_messages = []
            for field, errors in serializer.errors.items():
                if isinstance(errors, list):
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                else:
                    error_messages.append(f"{field}: {errors}")

            return Response({
                'status': 'error',
                'message': '; '.join(error_messages)
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            'status': 'success',
            'message': 'Berhasil memperbarui profil UMKM',
            'data': serializer.data
        })