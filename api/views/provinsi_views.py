from rest_framework import viewsets
from api.serializers import ProvinsiSerializer
from crud.models import Provinsi


class ProvinsiViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data provinsi.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = Provinsi.objects.all()
    serializer_class = ProvinsiSerializer
    filterset_fields = ['nm_provinsi']
    search_fields = ['nm_provinsi']
    ordering_fields = ['nm_provinsi']
    ordering = ['nm_provinsi']