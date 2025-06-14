import cv2
from pyzbar.pyzbar import decode

# Path ke gambar barcode
image_path = 'barcodes/001-Indomie_Goreng.png'

# Baca gambar
image = cv2.imread(image_path)

# Deteksi dan decode barcode
barcodes = decode(image)

# Tampilkan hasil
if not barcodes:
    print("❌ Tidak ada barcode ditemukan.")
else:
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        print(f"✅ Ditemukan barcode:")
        print(f"   Tipe: {barcode_type}")
        print(f"   Data: {barcode_data}")
