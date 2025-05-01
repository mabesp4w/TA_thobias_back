from rest_framework import viewsets, permissions
from api.serializers import KecamatanSerializer
from crud.models import Kecamatan


class KecamatanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data kecamatan.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = Kecamatan.objects.all()
    serializer_class = KecamatanSerializer
    filterset_fields = ['nm_kecamatan', 'kabupaten']
    search_fields = ['nm_kecamatan', 'kabupaten__nm_kabupaten', 'kabupaten__provinsi__nm_provinsi']
    ordering_fields = ['nm_kecamatan', 'kabupaten__nm_kabupaten']
    ordering = ['kabupaten__nm_kabupaten', 'nm_kecamatan']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()
        kabupaten_id = self.request.query_params.get('kabupaten_id')
        provinsi_id = self.request.query_params.get('provinsi_id')

        if kabupaten_id:
            queryset = queryset.filter(kabupaten__id=kabupaten_id)

        if provinsi_id:
            queryset = queryset.filter(kabupaten__provinsi__id=provinsi_id)

        return queryset