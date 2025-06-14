import json
import os
from barcode import Code128
from barcode.writer import ImageWriter

# Path file JSON
json_file_path = '../../produk.json'

# Folder output barcode
output_folder = 'barcodes'
os.makedirs(output_folder, exist_ok=True)

# Baca file JSON
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    barcode_data = json.dumps({
        "id": item["id"],
        # "nama_barang": item["nama_barang"],
        # "harga": item["harga"],
        # "deskripsi_suara_lokasi": item["deskripsi_suara_lokasi"],
        # "lokasi": item["lokasi"]
    })

    filename = os.path.join(output_folder, f"{item['id']:03}-{item['nama_barang'].replace(' ', '_')}")
    barcode = Code128(barcode_data, writer=ImageWriter())
    barcode.save(filename, options={"write_text": False})  # ← ini penting

