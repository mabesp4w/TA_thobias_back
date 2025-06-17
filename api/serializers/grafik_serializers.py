# serializers.py
from rest_framework import serializers
from django.db.models import Sum, Count
from django.db.models.functions import Extract
from django.contrib.auth import get_user_model
from crud.models import ProdukTerjual, ProfilUMKM

User = get_user_model()


class GrafikPenjualanSerializer(serializers.Serializer):
    """
    Serializer untuk data grafik penjualan
    """
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    nama_bulan = serializers.CharField()


class GrafikPenjualanUMKMSerializer(serializers.Serializer):
    """
    Serializer untuk data grafik penjualan per UMKM
    """
    umkm_id = serializers.CharField()
    nama_umkm = serializers.CharField()
    bulan = serializers.IntegerField()
    tahun = serializers.IntegerField()
    total_penjualan = serializers.DecimalField(max_digits=15, decimal_places=2)
    jumlah_transaksi = serializers.IntegerField()
    nama_bulan = serializers.CharField()


class UMKMListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk list UMKM untuk dropdown
    """
    nama_umkm = serializers.CharField(source='profil_umkm.nm_bisnis')

    class Meta:
        model = User
        fields = ['id', 'username', 'nama_umkm']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Jika nama_umkm kosong, gunakan username
        if not data['nama_umkm']:
            data['nama_umkm'] = data['username']
        return data


class FilterGrafikSerializer(serializers.Serializer):
    """
    Serializer untuk validasi filter grafik
    """
    umkm_id = serializers.UUIDField(required=False, allow_null=True)
    tahun = serializers.IntegerField(required=False)
    bulan_start = serializers.IntegerField(min_value=1, max_value=12, required=False)
    bulan_end = serializers.IntegerField(min_value=1, max_value=12, required=False)

    def validate(self, attrs):
        if 'bulan_start' in attrs and 'bulan_end' in attrs:
            if attrs['bulan_start'] > attrs['bulan_end']:
                raise serializers.ValidationError(
                    "Bulan mulai tidak boleh lebih besar dari bulan akhir"
                )
        return attrs