from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from api.serializers import ProfilUMKMSerializer
from crud.models import ProfilUMKM


class ProfilUMKMViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data profil UMKM.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = ProfilUMKM.objects.all()
    serializer_class = ProfilUMKMSerializer
    filterset_fields = ['nm_bisnis', 'user__username']
    search_fields = ['nm_bisnis', 'user__username', 'user__first_name', 'user__last_name', 'alamat']
    ordering_fields = ['nm_bisnis', 'tgl_bergabung', 'user__username']
    ordering = ['-tgl_bergabung']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()

        # Filter hanya menampilkan profil sendiri jika bukan admin
        user = self.request.user
        if user.role != 'admin':
            queryset = queryset.filter(user=user)

        return queryset