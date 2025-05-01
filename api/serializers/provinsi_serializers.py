from rest_framework import serializers
from crud.models import Provinsi


class ProvinsiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Provinsi (read-only)
    """
    class Meta:
        model = Provinsi
        fields = ['id', 'nm_provinsi']
        read_only_fields = fields  # Membuat semua field menjadi read-only