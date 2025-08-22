# crud/views/admin_view.py

from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

# Import langsung dari model authentication.models
from authentication.models import User

from authentication.permissions import IsAdmin
from crud.serializers.admin_serializer import AdminSerializer, AdminListSerializer
from crud.pagination import LaravelStylePagination


class AdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk mengelola User dengan role admin.
    Username tidak ditampilkan di response untuk keamanan.
    Tidak ada handling profil seperti di UMKM.
    """
    queryset = User.objects.filter(role='admin').exclude(username='admin')
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['email', 'first_name', 'last_name']  # Exclude username dari search
    ordering_fields = ['email', 'date_joined', 'last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminListSerializer
        return AdminSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar admin',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar admin',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail admin',
            'data': serializer.data
        })

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Pastikan password dan password_confirmation ada dalam request
        if 'password' not in request.data:
            return Response({
                'status': 'error',
                'message': 'Password diperlukan',
                'errors': {'password': ['Field ini diperlukan.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        if 'password_confirmation' not in request.data:
            return Response({
                'status': 'error',
                'message': 'Password confirmation diperlukan',
                'errors': {'password_confirmation': ['Field ini diperlukan.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Force role ke 'admin'
        request.data['role'] = 'admin'

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Simpan show_password jika ada
        if 'password' in request.data:
            instance.show_password = request.data.get('password')
            instance.save()

        result_serializer = AdminSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        response_data = {
            'status': 'success',
            'message': 'Berhasil membuat admin baru',
            'data': result_serializer.data
        }

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Force role tetap 'admin' jika ada upaya ubah
        if 'role' in request.data:
            request.data['role'] = 'admin'

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Update show_password jika password diubah
        if 'password' in request.data:
            instance.show_password = request.data.get('password')
            instance.save()

        # Return complete representation (tanpa username)
        result_serializer = AdminSerializer(instance)

        message = 'Berhasil memperbarui admin'
        if partial:
            message = 'Berhasil memperbarui sebagian data admin'

        response_data = {
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        }

        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Hindari menampilkan username di message
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil menghapus admin'
        }, status=status.HTTP_200_OK)