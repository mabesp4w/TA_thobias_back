from rest_framework import serializers
from ..models import Kabupaten, Provinsi


class KabupatenSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Kabupaten
    """
    provinsi_detail = serializers.SerializerMethodField()
    provinsi_nama = serializers.CharField(source='provinsi.nm_provinsi', read_only=True)
    kecamatan_count = serializers.SerializerMethodField()
    tipe = serializers.SerializerMethodField()

    class Meta:
        model = Kabupaten
        fields = ['id', 'nm_kabupaten', 'kode', 'is_kota', 'provinsi', 'provinsi_nama',
                  'provinsi_detail', 'kecamatan_count', 'tipe']

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi
        """
        return {
            'id': obj.provinsi.id,
            'nm_provinsi': obj.provinsi.nm_provinsi
        }

    def get_kecamatan_count(self, obj):
        """
        Menghitung jumlah kecamatan dalam kabupaten
        """
        return obj.kecamatan.count()

    def get_tipe(self, obj):
        """
        Mengembalikan tipe kabupaten atau kota
        """
        return "Kota" if obj.is_kota else "Kabupaten"

    def validate(self, data):
        """
        Validasi data kabupaten
        """
        # Cek duplikasi nama kabupaten dalam provinsi yang sama
        nm_kabupaten = data.get('nm_kabupaten')
        provinsi = data.get('provinsi')

        if not provinsi:
            provinsi = getattr(self.instance, 'provinsi', None)

        if nm_kabupaten and provinsi:
            query = Kabupaten.objects.filter(
                nm_kabupaten__iexact=nm_kabupaten,
                provinsi=provinsi
            )

            if self.instance:
                query = query.exclude(id=self.instance.id)

            if query.exists():
                raise serializers.ValidationError({
                    'nm_kabupaten': f"Kabupaten/Kota dengan nama '{nm_kabupaten}' sudah ada di provinsi ini."
                })

        return data


class KabupatenListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list Kabupaten (lightweight)
    """
    provinsi_nama = serializers.CharField(source='provinsi.nm_provinsi', read_only=True)
    provinsi_detail = serializers.SerializerMethodField()
    tipe = serializers.SerializerMethodField()
    kecamatan_count = serializers.SerializerMethodField()

    class Meta:
        model = Kabupaten
        fields = ['id', 'nm_kabupaten', 'kode', 'is_kota', 'provinsi', 'provinsi_nama',
                  'provinsi_detail', 'tipe', 'kecamatan_count']

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi
        """
        return {
            'id': obj.provinsi.id,
            'nm_provinsi': obj.provinsi.nm_provinsi
        }

    def get_tipe(self, obj):
        """
        Mengembalikan tipe kabupaten atau kota
        """
        return "Kota" if obj.is_kota else "Kabupaten"

    def get_kecamatan_count(self, obj):
        """
        Menghitung jumlah kecamatan dalam kabupaten
        """
        return obj.kecamatan.count()