from typing import Optional
from pydantic import BaseModel, Field

class Produk(BaseModel):
    """
    Model Pydantic untuk merepresentasikan entitas produk.
    """
    id: int
    nama_barang: str = Field(..., description="Nama barang yang dijual")
    harga: int = Field(..., description="Harga barang dalam mata uang lokal (misal: Rupiah)")
    lokasi: Optional[str] = Field(None, description="Lokasi fisik barang di warung")
    deskripsi_suara_lokasi: Optional[str] = Field(None, description="Deskripsi lokasi barang untuk panduan suara")
    path_qris: Optional[str] = Field(None, description="Path ke gambar QRIS untuk pembayaran")
    stok: int = Field(..., description="Jumlah stok barang yang tersedia")