from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from setup_logs import setup_logger

from produk_database import (
    create_product_in_db,
    get_product_from_db,
    get_all_products_from_db,
    update_product_in_db,
    delete_product_from_db,
    init_db,
    get_product_by_name
)

# Initialize the database and table
# init_db()

logger = setup_logger("produk", log_filename="warung.log")
# logger.info("========================== produk Starting ==============================")

class Produk(BaseModel):
    """
    Model Pydantic untuk merepresentasikan entitas produk.
    """
    id: Optional[int] = None
    nama_barang: str = Field(..., description="Nama barang yang dijual")
    harga: int = Field(..., description="Harga barang dalam mata uang lokal (misal: Rupiah)")
    lokasi: Optional[str] = Field(None, description="Lokasi fisik barang di warung")
    deskripsi_suara_lokasi: Optional[str] = Field(None, description="Deskripsi lokasi barang untuk panduan suara")
    path_qris: Optional[str] = Field(None, description="Path ke gambar QRIS untuk pembayaran")
    stok: int = Field(..., description="Jumlah stok barang yang tersedia")

class ProdukCreationRequest(BaseModel):
    """
    Model for creating a new product, id is not required.
    """
    nama_barang: str = Field(..., description="Nama barang yang dijual")
    harga: int = Field(..., description="Harga barang dalam mata uang lokal (misal: Rupiah)")
    lokasi: Optional[str] = Field(None, description="Lokasi fisik barang di warung")
    deskripsi_suara_lokasi: Optional[str] = Field(None, description="Deskripsi lokasi barang untuk panduan suara")
    path_qris: Optional[str] = Field(None, description="Path ke gambar QRIS untuk pembayaran")
    stok: int = Field(..., description="Jumlah stok barang yang tersedia")


class ProdukService:
    @staticmethod
    def create_produk(produk_data: ProdukCreationRequest) -> Produk:
        """Create a new product."""
        logger.info("create_produk called with produk_data=%s", produk_data)
        product_id = create_product_in_db(produk_data.model_dump())
        result = Produk(id=product_id, **produk_data.model_dump())
        logger.info("create_produk success: %s", result)
        return result

    @staticmethod
    def get_produk(produk_id: int) -> Optional[Produk]:
        """Get a product by its ID."""
        logger.info("get_produk called with produk_id=%s", produk_id)
        data = get_product_from_db(produk_id)
        if data:
            result = Produk(**data)
            logger.info("get_produk success: %s", result)
            return result
        logger.info("get_produk success: None")
        return None

    @staticmethod
    def get_all_produk() -> List[Produk]:
        """Get all products."""
        logger.info("get_all_produk called")
        all_data = get_all_products_from_db()
        result = [Produk(**data) for data in all_data]
        logger.info("get_all_produk success: %s", result)
        return result

    @staticmethod
    def update_produk(produk_id: int, produk_data: ProdukCreationRequest) -> Optional[Produk]:
        """Update an existing product."""
        logger.info("update_produk called with produk_id=%s, produk_data=%s", produk_id, produk_data)
        updated_data = update_product_in_db(produk_id, produk_data.model_dump())
        if updated_data:
            result = Produk(**updated_data)
            logger.info("update_produk success: %s", result)
            return result
        logger.info("update_produk success: None")
        return None

    @staticmethod
    def delete_produk(produk_id: int) -> bool:
        """Delete a product by its ID."""
        logger.info("delete_produk called with produk_id=%s", produk_id)
        result = delete_product_from_db(produk_id)
        logger.info("delete_produk success: %s", result)
        return result
    
    @staticmethod
    def get_produk_by_name(produk_name: str) -> Optional[Produk]:
        """Get a product by its name."""
        logger.info("get_produk_by_name called with produk_name=%s", produk_name)
        data = get_product_by_name(produk_name)
        if data:
            result = Produk(**data)
            logger.info("get_produk_by_name success: %s", result)
            return result
        logger.info("get_produk_by_name success: None")
        return None

    @staticmethod
    def to_json_report(produk: Produk) -> str:
        """Return a JSON string representing the product."""
        # logger.info("to_json_report called with produk=%s", produk)
        result = produk.model_dump_json()
        # logger.info("to_json_report success: %s", result)
        return result
    
    @staticmethod
    def from_json_report(json_str: str) -> Produk:
        """Return a Produk object from a JSON string."""
        # logger.info("from_json_report called with json_str=%s", json_str)
        produk = Produk.model_validate_json(json_str)
        logger.info("from_json_report success: %s", produk)
        return produk


# Example of usage:
if __name__ == "__main__":
    # Ensure the database and table are created
    init_db()

    # Create a new product
    new_produk_data = ProdukCreationRequest(
        nama_barang="Kopi ABC",
        harga=2500,
        lokasi="Rak Kopi",
        deskripsi_suara_lokasi="Rak Kopi ada di sebelah kanan kasir",
        path_qris="/qris/kopi_abc.png",
        stok=100
    )
    created_produk = ProdukService.create_produk(new_produk_data)
    if created_produk:
        print(f"Created Produk: {created_produk}")
        produk_id = created_produk.id

        # Get the product
        retrieved_produk = ProdukService.get_produk(produk_id)
        print(f"Retrieved Produk: {retrieved_produk}")

        # Update the product
        update_data = ProdukCreationRequest(
            nama_barang="Kopi ABC Susu",
            harga=3000,
            lokasi="Rak Kopi",
            deskripsi_suara_lokasi="Rak Kopi ada di sebelah kanan kasir, dekat susu",
            path_qris="/qris/kopi_abc_susu.png",
            stok=90
        )
        updated_produk = ProdukService.update_produk(produk_id, update_data)
        print(f"Updated Produk: {updated_produk}")

        # Get all products
        all_produk = ProdukService.get_all_produk()
        print(f"All Produk: {all_produk}")
        
        # Report one product
        if updated_produk:
            print(f"Report for updated product: {ProdukService.to_json_report(updated_produk)}")


        # Delete the product
        # deletion_result = ProdukService.delete_produk(produk_id)
        # print(f"Deletion Result: {deletion_result}")

        # Verify deletion
        # verify_deleted_produk = ProdukService.get_produk(produk_id)
        # print(f"Retrieved Produk after deletion: {verify_deleted_produk}")
    else:
        print("Failed to create product.")

    # Example of getting all products if some exist
    all_produk_after_ops = ProdukService.get_all_produk()
    print(f"All Produk after operations: {all_produk_after_ops}")
