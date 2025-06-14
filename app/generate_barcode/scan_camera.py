import cv2
from pyzbar.pyzbar import decode
import json

def scan_barcode_from_webcam():
    cap = cv2.VideoCapture(-1)

    print("Tekan 'q' untuk keluar...\n")

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Deteksi barcode di frame
        barcodes = decode(frame)

        for barcode in barcodes:
            # Gambar kotak di sekeliling barcode
            x, y, w, h = barcode.rect
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            try:
                data = barcode.data.decode('utf-8')
                tipe = barcode.type

                # Coba ubah ke JSON jika bisa
                try:
                    obj = json.loads(data)
                    tampil = json.dumps(obj, indent=2, ensure_ascii=False)
                except:
                    tampil = data

                text = f"{tipe}: {tampil}"
            except:
                text = "Gagal membaca data"

            # Tampilkan di atas kotak
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 0, 0), 2)

        cv2.imshow('Scan Barcode - Tekan q untuk keluar', frame)

        # Keluar kalau pencet q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

scan_barcode_from_webcam()
