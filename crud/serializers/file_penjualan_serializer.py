# serializers/file_penjualan_serializer.py

from rest_framework import serializers
from ..models import FilePenjualan
from django.contrib.auth import get_user_model

User = get_user_model()


class FilePenjualanSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model FilePenjualan
    """
    umkm_detail = serializers.SerializerMethodField()
    ukuran_file_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = FilePenjualan
        fields = ['id', 'umkm', 'umkm_detail', 'file', 'file_url', 'nama_file',
                  'deskripsi', 'tgl_upload', 'tgl_update', 'ukuran_file', 'ukuran_file_display']
        read_only_fields = ['id', 'tgl_upload', 'tgl_update', 'ukuran_file']

    def get_umkm_detail(self, obj):
        """
        Menampilkan detail UMKM
        """
        try:
            profil = obj.umkm.profil_umkm
            return {
                'id': obj.umkm.id,
                'username': obj.umkm.username,
                'nama_bisnis': profil.nm_bisnis,
                'nama_pemilik': f"{obj.umkm.first_name} {obj.umkm.last_name}".strip()
            }
        except:
            return {
                'id': obj.umkm.id,
                'username': obj.umkm.username,
                'nama_bisnis': None,
                'nama_pemilik': f"{obj.umkm.first_name} {obj.umkm.last_name}".strip()
            }

    def get_ukuran_file_display(self, obj):
        """
        Menampilkan ukuran file dalam format yang mudah dibaca
        """
        return obj.get_file_size_display()

    def get_file_url(self, obj):
        """
        Menampilkan URL file
        """
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate_file(self, value):
        """
        Validasi file upload
        """
        if not value:
            raise serializers.ValidationError("File tidak boleh kosong")
        return value

    def validate(self, data):
        """
        Validasi data secara keseluruhan
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Set umkm dari user yang login jika tidak ada
            if 'umkm' not in data:
                data['umkm'] = request.user

            # Pastikan user adalah UMKM
            if data['umkm'].role != 'umkm':
                raise serializers.ValidationError("Hanya pengguna UMKM yang dapat mengupload file penjualan")

        return data


class FilePenjualanListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list FilePenjualan (lightweight)
    """
    ukuran_file_display = serializers.SerializerMethodField()
    nama_umkm = serializers.CharField(source='umkm.username', read_only=True)

    class Meta:
        model = FilePenjualan
        fields = ['id', 'nama_file', 'deskripsi', 'tgl_upload', 'tgl_update',
                  'ukuran_file_display', 'nama_umkm']

    def get_ukuran_file_display(self, obj):
        return obj.get_file_size_display()