from rest_framework import viewsets, permissions
from api.serializers import LokasiUMKMSerializer
from crud.models import LokasiUMKM


class LokasiUMKMViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data lokasi UMKM.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = LokasiUMKM.objects.all()
    serializer_class = LokasiUMKMSerializer
    filterset_fields = ['pengguna', 'kecamatan']
    search_fields = ['alamat_lengkap', 'kode_pos', 'pengguna__username',
                     'kecamatan__nm_kecamatan', 'kecamatan__kabupaten__nm_kabupaten']
    ordering_fields = ['pengguna__username', 'tgl_update']
    ordering = ['-tgl_update']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()

        # Filter berdasarkan parameter
        kecamatan_id = self.request.query_params.get('kecamatan_id')
        kabupaten_id = self.request.query_params.get('kabupaten_id')
        provinsi_id = self.request.query_params.get('provinsi_id')

        if kecamatan_id:
            queryset = queryset.filter(kecamatan__id=kecamatan_id)

        if kabupaten_id:
            queryset = queryset.filter(kecamatan__kabupaten__id=kabupaten_id)

        if provinsi_id:
            queryset = queryset.filter(kecamatan__kabupaten__provinsi__id=provinsi_id)

        # Filter hanya menampilkan lokasi milik sendiri jika bukan admin
        user = self.request.user
        if user.role != 'admin':
            queryset = queryset.filter(pengguna=user)

        return queryset