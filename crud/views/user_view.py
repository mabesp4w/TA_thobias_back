from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

# Import langsung dari model authentication.models
from authentication.models import User

from authentication.permissions import IsAdmin
from ..serializers.user_serializer import UserSerializer, UserListSerializer
from ..serializers.profil_umkm_serializer import ProfilUMKMSerializer
from ..models import ProfilUMKM
from ..pagination import LaravelStylePagination


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan User untuk dilihat atau diedit.
    Hanya menampilkan user dengan role bukan admin.
    Dapat menangani role 'umkm' dan secara otomatis membuat profil UMKM.
    """
    queryset = User.objects.exclude(role='admin')  # Filter untuk exclude admin
    pagination_class = LaravelStylePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'role']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
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
                'message': 'Berhasil mendapatkan daftar pengguna',
                'data': result.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar pengguna',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan detail pengguna',
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

        # Extract profile data if exists
        profile_data = None
        if 'profile' in request.data:
            profile_data = request.data.pop('profile')

        # Set default role ke 'umkm' jika tidak disediakan
        if 'role' not in request.data:
            request.data['role'] = 'umkm'

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Simpan show_password jika ada
        if 'password' in request.data:
            instance.show_password = request.data.get('password')
            instance.save()

        # Buat profil UMKM jika role adalah 'umkm' dan profile data tersedia
        profile_response = None
        if instance.role == 'umkm' and profile_data:
            try:
                # Create a new ProfilUMKM instance directly to avoid serializer issues
                profile = ProfilUMKM(
                    user=instance,
                    nm_bisnis=profile_data.get('nm_bisnis', ''),
                    alamat=profile_data.get('alamat', ''),
                    tlp=profile_data.get('tlp', ''),
                    desc_bisnis=profile_data.get('desc_bisnis', '')
                )
                # Save the profile to the database
                profile.save()

                # Get the serialized profile data for the response
                profile_response = ProfilUMKMSerializer(profile).data
            except Exception as e:
                # Log the error for debugging
                print(f"Error creating profile: {str(e)}")

                # If there's an exception, return with error details
                return Response({
                    'status': 'partial_success',
                    'message': f'Berhasil membuat pengguna baru, tetapi gagal membuat profil UMKM: {str(e)}',
                    'data': UserSerializer(instance).data
                }, status=status.HTTP_201_CREATED)

        # Return complete representation
        result_serializer = UserSerializer(instance)
        headers = self.get_success_headers(serializer.data)

        response_data = {
            'status': 'success',
            'message': 'Berhasil membuat pengguna baru',
            'data': result_serializer.data
        }

        # Tambahkan informasi profil jika profil berhasil dibuat
        if profile_response:
            response_data['profile'] = profile_response

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Extract profile data if exists
        profile_data = None
        if 'profile' in request.data:
            profile_data = request.data.pop('profile')

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Update show_password jika password diubah
        if 'password' in request.data:
            instance.show_password = request.data.get('password')
            instance.save()

        # Update profil UMKM jika role adalah 'umkm' dan profile data tersedia
        profile_response = None
        if instance.role == 'umkm' and profile_data:
            try:
                # Check if profile exists
                try:
                    profile = ProfilUMKM.objects.get(user=instance)
                    # Update existing profile fields
                    if 'nm_bisnis' in profile_data:
                        profile.nm_bisnis = profile_data['nm_bisnis']
                    if 'alamat' in profile_data:
                        profile.alamat = profile_data['alamat']
                    if 'tlp' in profile_data:
                        profile.tlp = profile_data['tlp']
                    if 'desc_bisnis' in profile_data:
                        profile.desc_bisnis = profile_data['desc_bisnis']
                    profile.save()
                except ProfilUMKM.DoesNotExist:
                    # Create new profile if doesn't exist
                    profile = ProfilUMKM(
                        user=instance,
                        nm_bisnis=profile_data.get('nm_bisnis', ''),
                        alamat=profile_data.get('alamat', ''),
                        tlp=profile_data.get('tlp', ''),
                        desc_bisnis=profile_data.get('desc_bisnis', '')
                    )
                    profile.save()

                # Get serialized profile data for the response
                profile_response = ProfilUMKMSerializer(profile).data
            except Exception as e:
                # Log the error for debugging
                print(f"Error updating profile: {str(e)}")
                # If there's an error, continue but include error message
                pass

        # Return complete representation
        result_serializer = UserSerializer(instance)

        message = 'Berhasil memperbarui pengguna'
        if partial:
            message = 'Berhasil memperbarui sebagian data pengguna'

        response_data = {
            'status': 'success',
            'message': message,
            'data': result_serializer.data
        }

        # Include profile information if profile was updated
        if profile_response:
            response_data['profile'] = profile_response

        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_name = instance.username
        self.perform_destroy(instance)

        return Response({
            'status': 'success',
            'message': f'Berhasil menghapus pengguna: {user_name}'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Mendapatkan informasi pengguna yang sedang login
        """
        serializer = UserSerializer(request.user)
        response_data = {
            'status': 'success',
            'message': 'Berhasil mendapatkan data profil',
            'data': serializer.data
        }

        # Jika pengguna memiliki role 'umkm', sertakan data profil UMKM
        if request.user.role == 'umkm':
            try:
                profile = ProfilUMKM.objects.get(user=request.user)
                profile_serializer = ProfilUMKMSerializer(profile)
                response_data['profile'] = profile_serializer.data
            except ProfilUMKM.DoesNotExist:
                pass

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def get_umkm_users(self, request):
        """
        Mendapatkan daftar pengguna dengan role UMKM
        """
        queryset = User.objects.filter(role='umkm')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = UserListSerializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'message': 'Berhasil mendapatkan daftar pengguna UMKM',
                'data': result.data
            })

        serializer = UserListSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Berhasil mendapatkan daftar pengguna UMKM',
            'data': serializer.data
        })