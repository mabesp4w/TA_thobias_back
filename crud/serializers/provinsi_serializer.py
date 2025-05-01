from rest_framework import serializers
from ..models import Provinsi


class ProvinsiSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Provinsi
    """

    class Meta:
        model = Provinsi
        fields = ['id', 'nm_provinsi']

    def validate_nm_provinsi(self, value):
        """
        Validasi nama provinsi
        """
        # Cek duplikasi nama provinsi (case insensitive)
        if Provinsi.objects.filter(nm_provinsi__iexact=value).exists():
            if self.instance and self.instance.nm_provinsi.lower() == value.lower():
                return value
            raise serializers.ValidationError("Provinsi dengan nama ini sudah ada.")
        return value


class ProvinsiListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list Provinsi (lightweight)
    """
    kabupaten_count = serializers.SerializerMethodField()

    class Meta:
        model = Provinsi
        fields = ['id', 'nm_provinsi', 'kabupaten_count']

    def get_kabupaten_count(self, obj):
        """
        Menghitung jumlah kabupaten dalam provinsi
        """
        return obj.kabupaten.count()