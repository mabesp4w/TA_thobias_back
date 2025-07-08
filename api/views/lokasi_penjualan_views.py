from rest_framework import viewsets, permissions
from api.serializers import LokasiPenjualanSerializer
from crud.models import LokasiPenjualan


class LokasiPenjualanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint untuk melihat data lokasi penjualan.
    Read-only: Hanya mengizinkan operasi GET.
    """
    queryset = LokasiPenjualan.objects.all()
    serializer_class = LokasiPenjualanSerializer
    filterset_fields = ['nm_lokasi',  'kecamatan']
    search_fields = ['nm_lokasi', 'alamat',
                     'kecamatan__nm_kecamatan', 'kecamatan__kabupaten__nm_kabupaten']
    ordering_fields = ['nm_lokasi']
    ordering = ['nm_lokasi']

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

        return queryset