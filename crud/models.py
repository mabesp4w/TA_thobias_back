# models.py
import os
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from jsonschema.exceptions import ValidationError
from PIL import Image  # Tambahkan ini di bagian import


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


# Fungsi untuk path upload gambar produk
def produk_image_upload_path(instance, filename):
    """
    Path untuk upload gambar produk
    Format: produk/{username}/{produk_id}/{filename}
    """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'produk/{instance.umkm.username}/{instance.id}/{filename}'


def validate_image_file(value):
    """
    Validator untuk memastikan file yang diupload adalah gambar
    """
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    ext = value.name.split('.')[-1].lower()

    if ext not in valid_extensions:
        raise ValidationError(f'Format file tidak didukung. Format yang diperbolehkan: {", ".join(valid_extensions)}')

    # Limit ukuran file (5MB)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Ukuran file tidak boleh lebih dari 5MB')


# UPDATE MODEL PRODUK - Tambahkan field gambar
class Produk(models.Model):
    """
    Model untuk produk yang dijual oleh UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    umkm = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='produk')
    kategori = models.ForeignKey(KategoriProduk, on_delete=models.PROTECT, related_name='produk')
    nm_produk = models.CharField(max_length=255)
    desc = models.TextField()
    harga = models.IntegerField()
    stok = models.PositiveIntegerField(default=0)
    satuan = models.CharField(max_length=50)
    bahan_baku = models.TextField(blank=True, null=True)
    metode_produksi = models.TextField(blank=True, null=True)
    # FIELD GAMBAR BARU
    gambar_utama = models.ImageField(
        upload_to=produk_image_upload_path,
        validators=[validate_image_file],
        blank=True,
        null=True,
        help_text="Gambar utama produk"
    )
    aktif = models.BooleanField(default=True)
    tgl_dibuat = models.DateTimeField(auto_now_add=True)
    tgl_update = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Override save untuk optimasi gambar"""
        super().save(*args, **kwargs)

        # Optimasi ukuran gambar jika ada
        if self.gambar_utama:
            img_path = self.gambar_utama.path
            if os.path.exists(img_path):
                img = Image.open(img_path)

                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img

                # Resize jika terlalu besar
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Simpan dengan kualitas optimal
                img.save(img_path, quality=85, optimize=True)

    def delete(self, *args, **kwargs):
        """Hapus file gambar saat produk dihapus"""
        if self.gambar_utama and os.path.isfile(self.gambar_utama.path):
            os.remove(self.gambar_utama.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        nm_bisnis = getattr(getattr(self.umkm, 'profil_umkm', None), 'nm_bisnis', self.umkm.username)
        return f"{self.nm_produk} - {nm_bisnis}"

    class Meta:
        db_table = "produk"
        verbose_name_plural = "Produk"
        ordering = ['nm_produk']


class KategoriLokasi(models.Model):
    """
    Model untuk kategori lokasi
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nm_kategori_lokasi = models.CharField(max_length=100)
    desc = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nm_kategori_lokasi

    class Meta:
        db_table = "kategori_lokasi"
        verbose_name_plural = "Kategori lokasi"
        ordering = ['nm_kategori_lokasi']

class LokasiPenjualan(models.Model):
    """
    Model untuk menyimpan informasi lokasi penjualan produk UMKM
    Setiap UMKM dapat menentukan lokasi penjualan mereka sendiri
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    umkm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lokasi_penjualan',
        help_text="UMKM pemilik lokasi penjualan",
        null=True,
        blank=True,
    )
    nm_lokasi = models.CharField(max_length=255)
    alamat = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    tlp_pengelola = models.CharField(max_length=20, blank=True, null=True)
    kecamatan = models.ForeignKey(
        Kecamatan,
        on_delete=models.PROTECT,
        related_name='lokasi_penjualan',
        null=True,
        blank=True
    )
    kategori_lokasi = models.ForeignKey(
        KategoriLokasi,
        on_delete=models.PROTECT,
        related_name='lokasi_penjualan',
        null=True,
        blank=True
    )
    aktif = models.BooleanField(default=True, help_text="Status aktif lokasi penjualan")
    tgl_dibuat = models.DateTimeField(auto_now_add=True)
    tgl_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        kab_name = self.kecamatan.kabupaten.nm_kabupaten if self.kecamatan else "Tidak diketahui"
        umkm_name = getattr(getattr(self.umkm, 'profil_umkm', None), 'nm_bisnis', self.umkm.username)
        return f"{self.nm_lokasi} - {umkm_name} ({kab_name})"

    class Meta:
        db_table = "lokasi_penjualan"
        verbose_name_plural = "Lokasi Penjualan"
        ordering = ['umkm', 'nm_lokasi']
        # Constraint untuk memastikan UMKM tidak membuat lokasi dengan nama sama
        constraints = [
            models.UniqueConstraint(
                fields=['umkm', 'nm_lokasi'],
                name='unique_lokasi_per_umkm'
            )
        ]


class ProdukTerjual(models.Model):
    """
    Model untuk mencatat produk yang terjual oleh UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='penjualan')
    lokasi_penjualan = models.ForeignKey(
        LokasiPenjualan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='penjualan'
    )
    tgl_penjualan = models.DateField()
    jumlah_terjual = models.PositiveIntegerField()
    harga_jual = models.IntegerField()
    total_penjualan = models.IntegerField()
    catatan = models.TextField(blank=True, null=True)
    tgl_pelaporan = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Validasi untuk memastikan lokasi penjualan milik UMKM yang sama dengan produk
        """
        from django.core.exceptions import ValidationError

        if self.lokasi_penjualan and self.produk:
            if self.lokasi_penjualan.umkm != self.produk.umkm:
                raise ValidationError(
                    "Lokasi penjualan harus milik UMKM yang sama dengan produk"
                )

    def save(self, *args, **kwargs):
        # Validasi sebelum save
        self.clean()
        # Hitung total penjualan
        self.total_penjualan = self.jumlah_terjual * self.harga_jual
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produk.nm_produk} - {self.tgl_penjualan} - {self.jumlah_terjual} {self.produk.satuan}"

    class Meta:
        db_table = "produk_terjual"
        verbose_name_plural = "Produk Terjual"
        ordering = ['-tgl_penjualan']


def validate_excel_file(value):
    """
    Validator untuk memastikan file yang diupload adalah Excel
    """

    # Limit ukuran file (5MB)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Ukuran file tidak boleh lebih dari 5MB')


def file_upload_path(instance, filename):
    """
    Path untuk upload file penjualan
    """
    return f'penjualan/{instance.umkm.username}/{filename}'


class FilePenjualan(models.Model):
    """
    Model untuk menyimpan file Excel detail penjualan UMKM
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    umkm = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='file_penjualan')
    file = models.FileField(upload_to=file_upload_path, validators=[validate_excel_file])
    nama_file = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)
    tgl_upload = models.DateTimeField(auto_now_add=True)
    tgl_update = models.DateTimeField(auto_now=True)
    ukuran_file = models.PositiveIntegerField(default=0)  # dalam bytes

    def save(self, *args, **kwargs):
        if self.file:
            self.ukuran_file = self.file.size
            if not self.nama_file:
                self.nama_file = self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Hapus file dari storage ketika record dihapus
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def get_file_size_display(self):
        """
        Menampilkan ukuran file dalam format yang mudah dibaca
        """
        if self.ukuran_file < 1024:
            return f"{self.ukuran_file} bytes"
        elif self.ukuran_file < 1024 * 1024:
            return f"{self.ukuran_file / 1024:.1f} KB"
        else:
            return f"{self.ukuran_file / (1024 * 1024):.1f} MB"

    def __str__(self):
        return f"{self.nama_file} - {self.umkm.username}"

    class Meta:
        db_table = "file_penjualan"
        verbose_name_plural = "File Penjualan"
        ordering = ['-tgl_upload']