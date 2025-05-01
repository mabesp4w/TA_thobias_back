# models.py
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone

from thobias import settings


class Provinsi(models.Model):
    """
    Model untuk data provinsi
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nm_provinsi = models.CharField(max_length=100)
    def __str__(self):
        return self.nm_provinsi

    class Meta:
        db_table="provinsi"
        verbose_name_plural = "Provinsi"
        ordering = ['nm_provinsi']


class Kabupaten(models.Model):
    """
    Model untuk data kabupaten/kota
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provinsi = models.ForeignKey(Provinsi, on_delete=models.CASCADE, related_name='kabupaten')
    nm_kabupaten = models.CharField(max_length=100)
    kode = models.CharField(max_length=10, blank=True, null=True)
    is_kota = models.BooleanField(default=False)  # True jika kota, False jika kabupaten

    def __str__(self):
        prefix = "Kota" if self.is_kota else "Kabupaten"
        return f"{prefix} {self.nm_kabupaten}, {self.provinsi.nm_provinsi}"

    class Meta:
        db_table = "kabupaten"
        verbose_name_plural = "Kabupaten"
        ordering = ['provinsi', 'nm_kabupaten']


class Kecamatan(models.Model):
    """
    Model untuk data kecamatan
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kabupaten = models.ForeignKey(Kabupaten, on_delete=models.CASCADE, related_name='kecamatan')
    nm_kecamatan = models.CharField(max_length=100)
    kode = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.nm_kecamatan}, {self.kabupaten.nm_kabupaten}"

    class Meta:
        db_table = "kecamatan"
        verbose_name_plural = "Kecamatan"
        ordering = ['kabupaten', 'nm_kecamatan']


class ProfilUMKM(models.Model):
    """
    Model untuk profil UMKM yang terhubung dengan User model Django
    Hanya dibuat untuk user dengan role='umkm'
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_umkm')
    nm_bisnis = models.CharField(max_length=255, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    tlp = models.CharField(max_length=20, blank=True, null=True)
    desc_bisnis = models.TextField(blank=True, null=True)
    tgl_bergabung = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.nm_bisnis}"
    class Meta:
        db_table = "profil_umkm"
        verbose_name_plural = "Profil UMKM"
        ordering = ['user', 'nm_bisnis']


# Signal untuk membuat profil UMKM otomatis saat user dengan role='umkm' dibuat
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Hanya buat profil jika user adalah UMKM
    if instance.role == 'umkm':
        if created:
            ProfilUMKM.objects.create(user=instance)
        else:
            # Jika user sudah ada, pastikan profil juga ada
            try:
                instance.profil_umkm.save()
            except ProfilUMKM.DoesNotExist:
                ProfilUMKM.objects.create(user=instance)


class LokasiUMKM(models.Model):
    """
    Model untuk menyimpan data lokasi UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pengguna = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lokasi_umkm')
    latitude = models.FloatField()
    longitude = models.FloatField()
    alamat_lengkap = models.TextField()
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.PROTECT, related_name='lokasi_umkm')
    kode_pos = models.CharField(max_length=10, blank=True, null=True)
    tgl_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        nm_bisnis = getattr(getattr(self.pengguna, 'profil_umkm', None), 'nm_bisnis', self.pengguna.username)
        return f"Lokasi {nm_bisnis} - {self.alamat_lengkap}"

    class Meta:
        db_table = "lokasi_umkm"
        verbose_name_plural = "Lokasi UMKM"
        ordering = ['pengguna']


class KategoriProduk(models.Model):
    """
    Model untuk kategori produk
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nm_kategori = models.CharField(max_length=100)
    desc = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nm_kategori

    class Meta:
        db_table = "kategori_produk"
        verbose_name_plural = "Kategori Produk"
        ordering = ['nm_kategori']


class Produk(models.Model):
    """
    Model untuk produk yang dijual oleh UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    umkm = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='produk')
    kategori = models.ForeignKey(KategoriProduk, on_delete=models.PROTECT, related_name='produk')
    nm_produk = models.CharField(max_length=255)
    desc = models.TextField()
    harga = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    stok = models.PositiveIntegerField(default=0)
    satuan = models.CharField(max_length=50)
    bahan_baku = models.TextField(blank=True, null=True)
    metode_produksi = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)
    tgl_dibuat = models.DateTimeField(auto_now_add=True)
    tgl_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        nm_bisnis = getattr(getattr(self.umkm, 'profil_umkm', None), 'nm_bisnis', self.umkm.username)
        return f"{self.nm_produk} - {nm_bisnis}"

    class Meta:
        db_table = "produk"
        verbose_name_plural = "Produk"
        ordering = ['nm_produk']


class LokasiPenjualan(models.Model):
    """
    Model untuk menyimpan informasi lokasi penjualan produk UMKM
    """
    # TIPE_LOKASI_CHOICES = (
    #     ('kios', 'Kios/Toko'),
    #     ('pasar', 'Pasar Tradisional'),
    #     ('supermarket', 'Supermarket'),
    #     ('online', 'Marketplace Online'),
    #     ('lainnya', 'Lainnya'),
    # )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nm_lokasi = models.CharField(max_length=255)
    tipe_lokasi = models.CharField(max_length=20)
    alamat = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    kecamatan = models.ForeignKey(Kecamatan, on_delete=models.PROTECT, related_name='lokasi_penjualan', null=True,
                                  blank=True)
    tlp_pengelola = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        kab_name = self.kecamatan.kabupaten.nama if self.kecamatan else "Tidak diketahui"
        return f"{self.nm_lokasi} - {self.tipe_lokasi} ({kab_name})"

    class Meta:
        db_table = "lokasi_penjualan"
        verbose_name_plural = "Lokasi Penjualan"
        ordering = ['nm_lokasi']


class ProdukTerjual(models.Model):
    """
    Model untuk mencatat produk yang terjual oleh UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='penjualan')
    lokasi_penjualan = models.ForeignKey(LokasiPenjualan, on_delete=models.SET_NULL, null=True,
                                         related_name='penjualan')
    tgl_penjualan = models.DateField()
    jumlah_terjual = models.PositiveIntegerField()
    harga_jual = models.DecimalField(max_digits=12, decimal_places=2)
    total_penjualan = models.DecimalField(max_digits=15, decimal_places=2)
    catatan = models.TextField(blank=True, null=True)
    tgl_pelaporan = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Hitung total penjualan
        self.total_penjualan = self.jumlah_terjual * self.harga_jual
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produk.nm_produk} - {self.tgl_penjualan} - {self.jumlah_terjual} {self.produk.satuan}"

    class Meta:
        db_table = "produk_terjual"
        verbose_name_plural = "Produk Terjual"
        ordering = ['tgl_penjualan']