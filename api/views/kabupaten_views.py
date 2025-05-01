from rest_framework import viewsets, permissions, filters
from api.serializers import KabupatenSerializer
from crud.models import Kabupaten


class KabupatenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data kabupaten.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = Kabupaten.objects.all()
    serializer_class = KabupatenSerializer
    filterset_fields = ['nm_kabupaten', 'provinsi', 'is_kota']
    search_fields = ['nm_kabupaten', 'provinsi__nm_provinsi']
    ordering_fields = ['nm_kabupaten', 'provinsi__nm_provinsi']
    ordering = ['provinsi__nm_provinsi', 'nm_kabupaten']

    def get_queryset(self):
        """
        Filter tambahan berdasarkan parameter query
        """
        queryset = super().get_queryset()
        provinsi_id = self.request.query_params.get('provinsi_id')

        if provinsi_id:
            queryset = queryset.filter(provinsi__id=provinsi_id)

        return queryset