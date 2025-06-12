from mcp.server.fastmcp import FastMCP
from produk import ProdukService, Produk, ProdukCreationRequest # Import ProdukCreationRequest
from typing import List, Optional
from setup_logs import setup_logger
# logger = setup_logger("produk_server", log_filename="warung.log")
# logger.info("========================== produk_server Starting ==============================")
# Initialize ProdukService to ensure db is set up if not already
# (Assuming init_db() in produk_database.py is called upon import of produk.py or ProdukService instantiation)

mcp = FastMCP("produk_server")

# @mcp.tool()
# async def get_produk(produk_id: int) -> Optional[str]:
#     """Get a product by its ID.

#     Args:
#         produk_id: The ID of the product to retrieve.
#     """
#     # logger.info("get_produk called with produk_id=%s", produk_id)
#     produk = ProdukService.get_produk(produk_id)
#     if produk:
#         result = ProdukService.to_json_report(produk)
#         # logger.info("get_produk success: %s", result)
#         return result
#     # logger.info("get_produk success: None")
#     return None

@mcp.tool()
async def list_all_produk() -> List[str]:
    """List all available products."""
    # logger.info("list_all_produk called")
    produk_list = ProdukService.get_all_produk()
    result = [ProdukService.to_json_report(p) for p in produk_list]
    # logger.info("list_all_produk success: %s", result)
    return result

# @mcp.tool()
async def get_produk_by_name(produk_name: str) -> Optional[str]:
    """Get a product by its name."""
    # logger.info("get_produk_by_name called with produk_name=%s", produk_name)
    produk = ProdukService.get_produk_by_name(produk_name)
    if produk:
        result = ProdukService.to_json_report(produk)
        # logger.info("get_produk_by_name success: %s", result)
        return result
    # logger.info("get_produk_by_name success: None")
    return None

# @mcp.tool()
# async def delete_produk(produk_id: int) -> bool:
#     """Delete a product by its ID.

#     Args:
#         produk_id: The ID of the product to delete.
#     """
#     # logger.info("delete_produk called with produk_id=%s", produk_id)
#     result = ProdukService.delete_produk(produk_id)
#     # logger.info("delete_produk success: %s", result)
#     return result

# @mcp.tool()
# async def create_produk(
#     nama_barang: str,
#     harga: int,
#     stok: int,
#     lokasi: Optional[str] = None,
#     deskripsi_suara_lokasi: Optional[str] = None,
#     path_qris: Optional[str] = None
# ) -> str:
#     """Create a new product.

#     Args:
#         nama_barang: Nama barang yang dijual.
#         harga: Harga barang dalam mata uang lokal (misal: Rupiah).
#         stok: Jumlah stok barang yang tersedia.
#         lokasi: Lokasi fisik barang di warung (opsional).
#         deskripsi_suara_lokasi: Deskripsi lokasi barang untuk panduan suara (opsional).
#         path_qris: Path ke gambar QRIS untuk pembayaran (opsional).
#     """
#     # logger.info("create_produk called with nama_barang=%s, harga=%s, stok=%s, lokasi=%s, deskripsi_suara_lokasi=%s, path_qris=%s", nama_barang, harga, stok, lokasi, deskripsi_suara_lokasi, path_qris)
#     produk_data = ProdukCreationRequest(
#         nama_barang=nama_barang,
#         harga=harga,
#         stok=stok,
#         lokasi=lokasi,
#         deskripsi_suara_lokasi=deskripsi_suara_lokasi,
#         path_qris=path_qris
#     )
#     new_produk = ProdukService.create_produk(produk_data)
#     result = ProdukService.to_json_report(new_produk)
#     # logger.info("create_produk success: %s", result)
#     return result

# @mcp.tool()
# async def update_produk(
#     produk_id: int,
#     nama_barang: str,
#     harga: int,
#     stok: int,
#     lokasi: Optional[str] = None,
#     deskripsi_suara_lokasi: Optional[str] = None,
#     path_qris: Optional[str] = None
# ) -> Optional[str]:
#     """Update an existing product.

#     Args:
#         produk_id: The ID of the product to update.
#         nama_barang: Nama barang yang dijual.
#         harga: Harga barang dalam mata uang lokal (misal: Rupiah).
#         stok: Jumlah stok barang yang tersedia.
#         lokasi: Lokasi fisik barang di warung (opsional).
#         deskripsi_suara_lokasi: Deskripsi lokasi barang untuk panduan suara (opsional).
#         path_qris: Path ke gambar QRIS untuk pembayaran (opsional).
#     """
#     # logger.info("update_produk called with produk_id=%s, nama_barang=%s, harga=%s, stok=%s, lokasi=%s, deskripsi_suara_lokasi=%s, path_qris=%s", produk_id, nama_barang, harga, stok, lokasi, deskripsi_suara_lokasi, path_qris)
#     produk_data = ProdukCreationRequest(
#         nama_barang=nama_barang,
#         harga=harga,
#         stok=stok,
#         lokasi=lokasi,
#         deskripsi_suara_lokasi=deskripsi_suara_lokasi,
#         path_qris=path_qris
#     )
#     updated_produk = ProdukService.update_produk(produk_id, produk_data)
#     if updated_produk:
#         result = ProdukService.to_json_report(updated_produk)
#         # logger.info("update_produk success: %s", result)
#         return result
#     # logger.info("update_produk success: None")
#     return None

@mcp.resource("produk://produk_server/item/{produk_id}")
async def read_produk_resource(produk_id: int) -> Optional[str]:
    # logger.info("read_produk_resource called with produk_id=%s", produk_id)
    produk = ProdukService.get_produk(produk_id)
    if produk:
        result = ProdukService.to_json_report(produk)
        # logger.info("read_produk_resource success: %s", result)
        return result
    # logger.info("read_produk_resource success: None")
    return None # Or raise a resource not found error

@mcp.resource("produk://produk_server/all_items")
async def read_all_produk_resource() -> List[str]:
    # logger.info("read_all_produk_resource called")
    produk_list = ProdukService.get_all_produk()
    result = [ProdukService.to_json_report(p) for p in produk_list]
    # logger.info("read_all_produk_resource success: %s", result)
    return result


if __name__ == "__main__":
    mcp.run(transport='stdio')