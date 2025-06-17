# management/commands/populate_papua_data.py

import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from crud.models import (
    Provinsi, Kabupaten, Kecamatan, KategoriProduk,
    LokasiPenjualan, ProfilUMKM, LokasiUMKM, Produk, ProdukTerjual
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with Papua-focused UMKM data'

    def handle(self, *args, **options):
        self.stdout.write('Starting data population for Papua...')

        # 1. Create Provinsi Papua
        papua, created = Provinsi.objects.get_or_create(
            nm_provinsi='Papua'
        )
        if created:
            self.stdout.write(f'Created: {papua}')

        # 2. Create Kabupaten/Kota di Papua
        kabupaten_data = [
            {'nm_kabupaten': 'Jayapura', 'kode': '9471', 'is_kota': True},
            {'nm_kabupaten': 'Biak Numfor', 'kode': '9403', 'is_kota': False},
            {'nm_kabupaten': 'Sarmi', 'kode': '9406', 'is_kota': False},
            {'nm_kabupaten': 'Keerom', 'kode': '9407', 'is_kota': False},
            {'nm_kabupaten': 'Tolikara', 'kode': '9417', 'is_kota': False},
            {'nm_kabupaten': 'Mimika', 'kode': '9410', 'is_kota': False},
            {'nm_kabupaten': 'Paniai', 'kode': '9415', 'is_kota': False},
            {'nm_kabupaten': 'Merauke', 'kode': '9401', 'is_kota': False},
            {'nm_kabupaten': 'Nabire', 'kode': '9408', 'is_kota': False},
            {'nm_kabupaten': 'Yahukimo', 'kode': '9459', 'is_kota': False},
        ]

        kabupaten_objects = []
        for kab_data in kabupaten_data:
            kabupaten, created = Kabupaten.objects.get_or_create(
                provinsi=papua,
                nm_kabupaten=kab_data['nm_kabupaten'],
                defaults={
                    'kode': kab_data['kode'],
                    'is_kota': kab_data['is_kota']
                }
            )
            kabupaten_objects.append(kabupaten)
            if created:
                self.stdout.write(f'Created: {kabupaten}')

        # 3. Create Kecamatan
        kecamatan_data = {
            'Jayapura': ['Abepura', 'Heram', 'Muara Tami', 'Sentani'],
            'Biak Numfor': ['Biak Kota', 'Numfor Barat', 'Biak Timur', 'Yendidori'],
            'Sarmi': ['Sarmi', 'Pantai Barat', 'Bonggo', 'Tor Atas'],
            'Keerom': ['Arso', 'Waris', 'Senggi', 'Skanto'],
            'Tolikara': ['Karubaga', 'Wouma', 'Kanggime', 'Bokondini'],
            'Mimika': ['Mimika Baru', 'Kuala Kencana', 'Tembagapura', 'Agimuga'],
            'Paniai': ['Paniai Timur', 'Paniai Barat', 'Aradide', 'Bogabaida'],
            'Merauke': ['Merauke', 'Muting', 'Kurik', 'Jagebob'],
            'Nabire': ['Nabire', 'Teluk Umar', 'Uwapa', 'Makimi'],
            'Yahukimo': ['Sumohai', 'Yahukimo', 'Kurulu', 'Anggruk'],
        }

        kecamatan_objects = []
        for kabupaten in kabupaten_objects:
            if kabupaten.nm_kabupaten in kecamatan_data:
                for kec_name in kecamatan_data[kabupaten.nm_kabupaten]:
                    kecamatan, created = Kecamatan.objects.get_or_create(
                        kabupaten=kabupaten,
                        nm_kecamatan=kec_name,
                        defaults={'kode': f'{kabupaten.kode[:2]}{random.randint(10, 99)}'}
                    )
                    kecamatan_objects.append(kecamatan)
                    if created:
                        self.stdout.write(f'Created: {kecamatan}')

        # 4. Create Kategori Produk
        kategori_data = [
            {'nm_kategori': 'Kerajinan Tangan', 'desc': 'Produk kerajinan tradisional Papua'},
            {'nm_kategori': 'Makanan Tradisional', 'desc': 'Makanan khas Papua'},
            {'nm_kategori': 'Minuman Tradisional', 'desc': 'Minuman khas daerah'},
            {'nm_kategori': 'Pakaian & Aksesoris', 'desc': 'Pakaian dan aksesoris tradisional'},
            {'nm_kategori': 'Produk Pertanian', 'desc': 'Hasil pertanian dan perkebunan'},
            {'nm_kategori': 'Produk Perikanan', 'desc': 'Hasil laut dan perikanan'},
            {'nm_kategori': 'Obat Tradisional', 'desc': 'Jamu dan obat herbal tradisional'},
            {'nm_kategori': 'Hasil Hutan', 'desc': 'Produk dari hasil hutan'},
        ]

        kategori_objects = []
        for kat_data in kategori_data:
            kategori, created = KategoriProduk.objects.get_or_create(
                nm_kategori=kat_data['nm_kategori'],
                defaults={'desc': kat_data['desc']}
            )
            kategori_objects.append(kategori)
            if created:
                self.stdout.write(f'Created: {kategori}')

        # 5. Create Lokasi Penjualan
        tipe_lokasi_choices = ['kios', 'pasar', 'supermarket', 'online', 'lainnya']
        lokasi_penjualan_data = [
            {'nm_lokasi': 'Pasar Sentani', 'tipe_lokasi': 'pasar', 'alamat': 'Jl. Raya Sentani, Jayapura'},
            {'nm_lokasi': 'Toko Oleh-oleh Papua', 'tipe_lokasi': 'kios', 'alamat': 'Jl. Ahmad Yani, Jayapura'},
            {'nm_lokasi': 'Pasar Yotefa', 'tipe_lokasi': 'pasar', 'alamat': 'Abepura, Jayapura'},
            {'nm_lokasi': 'Galeri Kerajinan Papua', 'tipe_lokasi': 'kios', 'alamat': 'Biak Kota, Biak Numfor'},
            {'nm_lokasi': 'Pasar Tradisional Biak', 'tipe_lokasi': 'pasar', 'alamat': 'Biak Kota, Biak Numfor'},
            {'nm_lokasi': 'Marketplace Online Papua', 'tipe_lokasi': 'online', 'alamat': 'Platform Digital'},
            {'nm_lokasi': 'Toko Suku Asmat', 'tipe_lokasi': 'kios', 'alamat': 'Agats, Asmat'},
            {'nm_lokasi': 'Koperasi Petani Merauke', 'tipe_lokasi': 'lainnya', 'alamat': 'Merauke'},
            {'nm_lokasi': 'Supermarket Mimika Mall', 'tipe_lokasi': 'supermarket', 'alamat': 'Timika, Mimika'},
            {'nm_lokasi': 'Pasar Nabire', 'tipe_lokasi': 'pasar', 'alamat': 'Nabire Kota'},
        ]

        lokasi_penjualan_objects = []
        for i, lok_data in enumerate(lokasi_penjualan_data):
            # Randomly assign kecamatan
            kecamatan = random.choice(kecamatan_objects) if kecamatan_objects else None

            lokasi, created = LokasiPenjualan.objects.get_or_create(
                nm_lokasi=lok_data['nm_lokasi'],
                defaults={
                    'tipe_lokasi': lok_data['tipe_lokasi'],
                    'alamat': lok_data['alamat'],
                    'latitude': -2.5 + random.uniform(-1, 1),  # Around Papua coordinates
                    'longitude': 140.7 + random.uniform(-2, 2),
                    'kecamatan': kecamatan,
                    'tlp_pengelola': f'0811{random.randint(1000000, 9999999)}'
                }
            )
            lokasi_penjualan_objects.append(lokasi)
            if created:
                self.stdout.write(f'Created: {lokasi}')

        # 6. Create Users (UMKM)
        umkm_users_data = [
            {'username': 'umkm_papua1', 'email': 'papua1@example.com', 'first_name': 'Maria', 'last_name': 'Kambu'},
            {'username': 'umkm_papua2', 'email': 'papua2@example.com', 'first_name': 'John', 'last_name': 'Wenda'},
            {'username': 'umkm_papua3', 'email': 'papua3@example.com', 'first_name': 'Sarah', 'last_name': 'Mandacan'},
            {'username': 'umkm_papua4', 'email': 'papua4@example.com', 'first_name': 'David', 'last_name': 'Yikwa'},
            {'username': 'umkm_papua5', 'email': 'papua5@example.com', 'first_name': 'Lisa', 'last_name': 'Tekege'},
            {'username': 'umkm_papua6', 'email': 'papua6@example.com', 'first_name': 'Michael', 'last_name': 'Numberi'},
            {'username': 'umkm_papua7', 'email': 'papua7@example.com', 'first_name': 'Anna', 'last_name': 'Womsiwor'},
            {'username': 'umkm_papua8', 'email': 'papua8@example.com', 'first_name': 'Robert', 'last_name': 'Ayomi'},
            {'username': 'umkm_papua9', 'email': 'papua9@example.com', 'first_name': 'Grace', 'last_name': 'Klembiap'},
            {'username': 'umkm_papua10', 'email': 'papua10@example.com', 'first_name': 'Peter', 'last_name': 'Mekere'},
            {'username': 'umkm_papua11', 'email': 'papua11@example.com', 'first_name': 'Diana', 'last_name': 'Warami'},
            {'username': 'umkm_papua12', 'email': 'papua12@example.com', 'first_name': 'James',
             'last_name': 'Yigibalom'},
            {'username': 'umkm_papua13', 'email': 'papua13@example.com', 'first_name': 'Ruth', 'last_name': 'Dimara'},
            {'username': 'umkm_papua14', 'email': 'papua14@example.com', 'first_name': 'Samuel', 'last_name': 'Pakage'},
            {'username': 'umkm_papua15', 'email': 'papua15@example.com', 'first_name': 'Helen', 'last_name': 'Wanma'},
        ]

        umkm_users = []
        for user_data in umkm_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': 'umkm',  # Assuming you have a role field
                    'is_active': True,
                    'show_password':'password123'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            umkm_users.append(user)
            if created:
                self.stdout.write(f'Created user: {user}')

        # 7. Update ProfilUMKM (akan dibuat otomatis oleh signal, tapi kita update)
        bisnis_names = [
            'Kerajinan Tangan Papua Asli',
            'Makanan Tradisional Sentani',
            'Batik Papua Modern',
            'Keripik Sagu Krispi',
            'Tas Noken Tradisional',
            'Kopi Arabica Baliem',
            'Madu Hutan Papua',
            'Kerajinan Kulit Kayu',
            'Teh Herbal Papua',
            'Souvenir Papua Authentic',
            'Makanan Ringan Ubi',
            'Kerajinan Batu Akik',
            'Sambal Roa Khas Papua',
            'Anyaman Pandan',
            'Minuman Tradisional Sagu',
        ]

        for i, user in enumerate(umkm_users):
            try:
                profil = user.profil_umkm
                profil.nm_bisnis = bisnis_names[i % len(bisnis_names)]
                profil.alamat = f'Alamat lengkap di {random.choice(kecamatan_objects).nm_kecamatan}'
                profil.tlp = f'081{random.randint(10000000, 99999999)}'
                profil.desc_bisnis = f'Usaha {profil.nm_bisnis} yang telah berjalan sejak beberapa tahun dengan produk berkualitas tinggi.'
                profil.save()
                self.stdout.write(f'Updated profil: {profil}')
            except ProfilUMKM.DoesNotExist:
                # Create manually if signal didn't work
                profil = ProfilUMKM.objects.create(
                    user=user,
                    nm_bisnis=bisnis_names[i % len(bisnis_names)],
                    alamat=f'Alamat lengkap di {random.choice(kecamatan_objects).nm_kecamatan}',
                    tlp=f'081{random.randint(10000000, 99999999)}',
                    desc_bisnis=f'Usaha {bisnis_names[i % len(bisnis_names)]} yang telah berjalan sejak beberapa tahun.'
                )
                self.stdout.write(f'Created profil: {profil}')

        # 8. Create LokasiUMKM
        for user in umkm_users:
            kecamatan = random.choice(kecamatan_objects)
            lokasi_umkm, created = LokasiUMKM.objects.get_or_create(
                pengguna=user,
                defaults={
                    'latitude': -2.5 + random.uniform(-1, 1),
                    'longitude': 140.7 + random.uniform(-2, 2),
                    'alamat_lengkap': f'Jl. {random.choice(["Raya", "Utama", "Merdeka", "Diponegoro"])} No.{random.randint(1, 100)}, {kecamatan.nm_kecamatan}',
                    'kecamatan': kecamatan,
                    'kode_pos': f'9{random.randint(1000, 9999)}'
                }
            )
            if created:
                self.stdout.write(f'Created lokasi UMKM: {lokasi_umkm}')

        # 9. Create Produk
        produk_data = [
            {'nm_produk': 'Tas Noken Asli', 'kategori': 'Kerajinan Tangan', 'satuan': 'buah',
             'harga_range': (150000, 500000)},
            {'nm_produk': 'Keripik Sagu Original', 'kategori': 'Makanan Tradisional', 'satuan': 'pack',
             'harga_range': (25000, 50000)},
            {'nm_produk': 'Topi Cendrawasih', 'kategori': 'Pakaian & Aksesoris', 'satuan': 'buah',
             'harga_range': (100000, 200000)},
            {'nm_produk': 'Kopi Arabica Baliem', 'kategori': 'Produk Pertanian', 'satuan': 'kg',
             'harga_range': (120000, 180000)},
            {'nm_produk': 'Madu Hutan Murni', 'kategori': 'Hasil Hutan', 'satuan': 'botol',
             'harga_range': (80000, 150000)},
            {'nm_produk': 'Sambal Roa Khas', 'kategori': 'Makanan Tradisional', 'satuan': 'botol',
             'harga_range': (35000, 60000)},
            {'nm_produk': 'Teh Herbal Daun Wati', 'kategori': 'Obat Tradisional', 'satuan': 'pack',
             'harga_range': (40000, 80000)},
            {'nm_produk': 'Kerajinan Kulit Kayu', 'kategori': 'Kerajinan Tangan', 'satuan': 'buah',
             'harga_range': (200000, 400000)},
            {'nm_produk': 'Ikan Asin Kering', 'kategori': 'Produk Perikanan', 'satuan': 'kg',
             'harga_range': (60000, 100000)},
            {'nm_produk': 'Batik Papua Motif Cendrawasih', 'kategori': 'Pakaian & Aksesoris', 'satuan': 'buah',
             'harga_range': (250000, 450000)},
            {'nm_produk': 'Anyaman Pandan Mini', 'kategori': 'Kerajinan Tangan', 'satuan': 'buah',
             'harga_range': (50000, 100000)},
            {'nm_produk': 'Dodol Sagu', 'kategori': 'Makanan Tradisional', 'satuan': 'pack',
             'harga_range': (30000, 50000)},
            {'nm_produk': 'Gelang Manik Tradisional', 'kategori': 'Pakaian & Aksesoris', 'satuan': 'buah',
             'harga_range': (75000, 150000)},
            {'nm_produk': 'Gula Aren Organik', 'kategori': 'Produk Pertanian', 'satuan': 'kg',
             'harga_range': (45000, 70000)},
            {'nm_produk': 'Kerupuk Ikan Mas', 'kategori': 'Makanan Tradisional', 'satuan': 'pack',
             'harga_range': (20000, 35000)},
            {'nm_produk': 'Kalung Kerang Laut', 'kategori': 'Kerajinan Tangan', 'satuan': 'buah',
             'harga_range': (80000, 120000)},
            {'nm_produk': 'Minuman Sagu Tradisional', 'kategori': 'Minuman Tradisional', 'satuan': 'botol',
             'harga_range': (15000, 25000)},
            {'nm_produk': 'Ukiran Kayu Ironwood', 'kategori': 'Kerajinan Tangan', 'satuan': 'buah',
             'harga_range': (300000, 800000)},
            {'nm_produk': 'Beras Merah Organik', 'kategori': 'Produk Pertanian', 'satuan': 'kg',
             'harga_range': (25000, 40000)},
            {'nm_produk': 'Jamu Tradisional Papua', 'kategori': 'Obat Tradisional', 'satuan': 'botol',
             'harga_range': (50000, 100000)},
        ]

        produk_objects = []
        for i, prod_data in enumerate(produk_data):
            umkm = umkm_users[i % len(umkm_users)]
            kategori = next((k for k in kategori_objects if k.nm_kategori == prod_data['kategori']),
                            random.choice(kategori_objects))

            harga = random.randint(prod_data['harga_range'][0], prod_data['harga_range'][1])
            produk, created = Produk.objects.get_or_create(
                umkm=umkm,
                nm_produk=prod_data['nm_produk'],
                defaults={
                    'kategori': kategori,
                    'desc': f'Produk {prod_data["nm_produk"]} berkualitas tinggi dengan cita rasa khas Papua. Dibuat dengan bahan alami pilihan.',
                    'harga': Decimal(str(harga)),
                    'stok': random.randint(10, 100),
                    'satuan': prod_data['satuan'],
                    'bahan_baku': f'Bahan alami khas Papua untuk {prod_data["nm_produk"]}',
                    'metode_produksi': 'Dibuat secara tradisional dengan resep turun temurun',
                    'aktif': True
                }
            )
            produk_objects.append(produk)
            if created:
                self.stdout.write(f'Created produk: {produk}')

        # 10. Create ProdukTerjual
        # Create sales records for the last 3 months
        start_date = date.today() - timedelta(days=90)
        for produk in produk_objects:
            # Create 3-8 sales records per product
            num_sales = random.randint(3, 8)
            for _ in range(num_sales):
                tgl_penjualan = start_date + timedelta(days=random.randint(0, 90))
                jumlah_terjual = random.randint(1, 10)
                harga_jual = int(produk.harga * random.uniform(0.9, 1.1))  # Price variation ±10%

                penjualan = ProdukTerjual.objects.create(
                    produk=produk,
                    lokasi_penjualan=random.choice(lokasi_penjualan_objects),
                    tgl_penjualan=tgl_penjualan,
                    jumlah_terjual=jumlah_terjual,
                    harga_jual=harga_jual,
                    catatan=f'Penjualan {produk.nm_produk} di {random.choice(lokasi_penjualan_objects).nm_lokasi}'
                )
                self.stdout.write(f'Created penjualan: {penjualan}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with Papua UMKM data:\n'
                f'- 1 Provinsi (Papua)\n'
                f'- {len(kabupaten_objects)} Kabupaten/Kota\n'
                f'- {len(kecamatan_objects)} Kecamatan\n'
                f'- {len(kategori_objects)} Kategori Produk\n'
                f'- {len(lokasi_penjualan_objects)} Lokasi Penjualan\n'
                f'- {len(umkm_users)} UMKM Users\n'
                f'- {len(produk_objects)} Produk\n'
                f'- {ProdukTerjual.objects.count()} Records Penjualan'
            )
        )