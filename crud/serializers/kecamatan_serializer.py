from rest_framework import serializers
from ..models import Kecamatan, Kabupaten


class KecamatanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Kecamatan
    """
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()
    kabupaten_nama = serializers.CharField(source='kabupaten.nm_kabupaten', read_only=True)
    provinsi_nama = serializers.CharField(source='kabupaten.provinsi.nm_provinsi', read_only=True)
    tipe_kabupaten = serializers.SerializerMethodField()

    class Meta:
        model = Kecamatan
        fields = ['id', 'nm_kecamatan', 'kode', 'kabupaten', 'kabupaten_nama', 'provinsi_nama',
                  'kabupaten_detail', 'provinsi_detail', 'tipe_kabupaten']

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten
        """
        return {
            'id': obj.kabupaten.id,
            'nm_kabupaten': obj.kabupaten.nm_kabupaten,
            'is_kota': obj.kabupaten.is_kota,
            'kode': obj.kabupaten.kode
        }

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi
        """
        return {
            'id': obj.kabupaten.provinsi.id,
            'nm_provinsi': obj.kabupaten.provinsi.nm_provinsi
        }

    def get_tipe_kabupaten(self, obj):
        """
        Mengembalikan tipe kabupaten atau kota
        """
        return "Kota" if obj.kabupaten.is_kota else "Kabupaten"

    def validate(self, data):
        """
        Validasi data kecamatan
        """
        # Cek duplikasi nama kecamatan dalam kabupaten yang sama
        nm_kecamatan = data.get('nm_kecamatan')
        kabupaten = data.get('kabupaten')

        if not kabupaten:
            kabupaten = getattr(self.instance, 'kabupaten', None)

        if nm_kecamatan and kabupaten:
            query = Kecamatan.objects.filter(
                nm_kecamatan__iexact=nm_kecamatan,
                kabupaten=kabupaten
            )

            if self.instance:
                query = query.exclude(id=self.instance.id)

            if query.exists():
                raise serializers.ValidationError({
                    'nm_kecamatan': f"Kecamatan dengan nama '{nm_kecamatan}' sudah ada di kabupaten/kota ini."
                })

        return data


class KecamatanListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list Kecamatan (lightweight)
    """
    kabupaten_nama = serializers.CharField(source='kabupaten.nm_kabupaten', read_only=True)
    provinsi_nama = serializers.CharField(source='kabupaten.provinsi.nm_provinsi', read_only=True)
    kabupaten_detail = serializers.SerializerMethodField()
    provinsi_detail = serializers.SerializerMethodField()
    tipe_kabupaten = serializers.SerializerMethodField()

    class Meta:
        model = Kecamatan
        fields = ['id', 'nm_kecamatan', 'kode', 'kabupaten', 'kabupaten_nama', 'provinsi_nama',
                  'kabupaten_detail', 'provinsi_detail', 'tipe_kabupaten']

    def get_kabupaten_detail(self, obj):
        """
        Menampilkan detail kabupaten
        """
        return {
            'id': obj.kabupaten.id,
            'nm_kabupaten': obj.kabupaten.nm_kabupaten,
            'is_kota': obj.kabupaten.is_kota,
            'kode': obj.kabupaten.kode
        }

    def get_provinsi_detail(self, obj):
        """
        Menampilkan detail provinsi
        """
        return {
            'id': obj.kabupaten.provinsi.id,
            'nm_provinsi': obj.kabupaten.provinsi.nm_provinsi
        }

    def get_tipe_kabupaten(self, obj):
        """
        Mengembalikan tipe kabupaten atau kota
        """
        return "Kota" if obj.kabupaten.is_kota else "Kabupaten"