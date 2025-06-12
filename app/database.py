import sqlite3
import csv
import os

DB_NAME = 'src/data/warung.db'
CSV_NAME = 'src/data/data.csv'

def create_database():
    """
    Membuat tabel produk dalam database SQLite jika belum ada.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produk (
        id INTEGER PRIMARY KEY,
        nama_barang TEXT NOT NULL,
        harga INTEGER NOT NULL,
        lokasi TEXT,
        deskripsi_suara_lokasi TEXT,
        path_qris TEXT,
        stok INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' dan tabel 'produk' berhasil disiapkan.")

def populate_data_from_csv():
    """
    Mengisi data ke tabel produk dari file CSV.
    Data lama akan dihapus terlebih dahulu (jika ada) untuk menghindari duplikasi
    jika skrip dijalankan berkali-kali.
    """
    if not os.path.exists(CSV_NAME):
        print(f"Error: File '{CSV_NAME}' tidak ditemukan. Pastikan file ada di direktori yang sama.")
        # Membuat file CSV dummy jika tidak ada untuk pengujian dasar
        print(f"Membuat file '{CSV_NAME}' dummy untuk pengujian...")
        with open(CSV_NAME, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'nama_barang', 'harga', 'lokasi', 'deskripsi_suara_lokasi', 'path_qris', 'stok']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'id': 1, 'nama_barang': 'Contoh Barang', 'harga': 10000, 
                'lokasi': 'Rak Contoh', 
                'deskripsi_suara_lokasi': 'Barang contoh ada di rak contoh.', 
                'path_qris': 'qris_images/contoh.png',
                'stok': 10
            })
        print(f"File '{CSV_NAME}' dummy berhasil dibuat. Silakan isi dengan data yang benar dan jalankan lagi.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Hapus data lama untuk menghindari duplikasi jika skrip dijalankan ulang
    # cursor.execute("DELETE FROM produk") 
    # Sebaiknya, kita cek apakah data sudah ada berdasarkan ID agar lebih aman
    # Atau, kita bisa menggunakan INSERT OR IGNORE atau INSERT OR REPLACE

    with open(CSV_NAME, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        products_to_insert = []
        for row in reader:
            try:
                products_to_insert.append((
                    int(row['id']),
                    row['nama_barang'],
                    int(row['harga']),
                    row['lokasi'],
                    row['deskripsi_suara_lokasi'],
                    row['path_qris'],
                    row['stok']
                ))
            except ValueError as e:
                print(f"Skipping row due to data error: {row} - {e}")
            except KeyError as e:
                print(f"Skipping row due to missing column: {e} in {row}")


    # Menggunakan INSERT OR IGNORE agar tidak error jika ID sudah ada
    # Jika ingin update jika ID sudah ada, gunakan INSERT OR REPLACE
    cursor.executemany('''
    INSERT OR IGNORE INTO produk (id, nama_barang, harga, lokasi, deskripsi_suara_lokasi, path_qris, stok)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', products_to_insert)

    conn.commit()
    conn.close()
    print(f"Data dari '{CSV_NAME}' berhasil dimasukkan ke tabel 'produk'.")

if __name__ == '__main__':
    create_database()
    populate_data_from_csv()
    
    # Contoh query untuk verifikasi
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print("\nData produk saat ini di database:")
    for row in cursor.execute("SELECT * FROM produk"):
        print(row)
    conn.close()
