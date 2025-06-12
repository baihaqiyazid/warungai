import sqlite3
from typing import Dict, Any, Optional, List
# from setup_logs import setup_logger

DATABASE_NAME = "src/data/warung.db"
# logger = setup_logger("produk_database", log_filename="warung.log")
# logger.info("========================== Produk Database Starting ==============================")

def init_db():
    """Drop and recreate the produk table."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Drop the table if it exists
    cursor.execute("DROP TABLE IF EXISTS produk")
    
    # Recreate the table
    cursor.execute("""
        CREATE TABLE produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_barang TEXT NOT NULL,
            harga INTEGER NOT NULL,
            lokasi TEXT,
            deskripsi_suara_lokasi TEXT,
            path_qris TEXT,
            stok INTEGER NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    # logger.info("init_db success - dropped and recreated table")


def create_product_in_db(produk_data: Dict[str, Any]) -> int:
    """Create a new product in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO produk (nama_barang, harga, lokasi, deskripsi_suara_lokasi, path_qris, stok)
        VALUES (:nama_barang, :harga, :lokasi, :deskripsi_suara_lokasi, :path_qris, :stok)
    """, produk_data)
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    # logger.info(f"create_product_in_db success, product_id={product_id}")
    return product_id

def get_product_from_db(produk_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a product by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produk WHERE id = ?", (produk_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # logger.info(f"get_product_from_db success, data={dict(row)}")
        return dict(row)
    # logger.info(f"get_product_from_db success, data=None")
    return None

def get_all_products_from_db() -> List[Dict[str, Any]]:
    """Retrieve all products from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produk")
    rows = cursor.fetchall()
    conn.close()
    # logger.info(f"get_all_products_from_db success, count={len(rows)}")
    return [dict(row) for row in rows]

def update_product_in_db(produk_id: int, produk_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing product in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Check if product exists
    cursor.execute("SELECT * FROM produk WHERE id = ?", (produk_id,))
    if not cursor.fetchone():
        conn.close()
        # logger.info(f"update_product_in_db success, data=None (not found)")
        return None # Product not found

    cursor.execute("""
        UPDATE produk
        SET nama_barang = :nama_barang,
            harga = :harga,
            lokasi = :lokasi,
            deskripsi_suara_lokasi = :deskripsi_suara_lokasi,
            path_qris = :path_qris,
            stok = :stok
        WHERE id = :id
    """, {**produk_data, "id": produk_id})
    conn.commit()
    # Fetch the updated row
    cursor.execute("SELECT * FROM produk WHERE id = ?", (produk_id,))
    updated_row = cursor.fetchone()
    conn.close()
    if updated_row:
        # logger.info(f"update_product_in_db success, data={dict(updated_row)}")
        return dict(updated_row)
    # logger.info(f"update_product_in_db success, data=None (after update)")
    return None

def get_product_by_name(produk_name: str) -> Optional[Dict[str, Any]]:
    """Get a product by name (case-insensitive, partial match) from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM produk WHERE LOWER(nama_barang) LIKE ?"
    like_pattern = f"%{produk_name.lower()}%"
    cursor.execute(query, (like_pattern,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # logger.info(f"get_product_by_name success, data={dict(row)}")
        return dict(row)
    # logger.info(f"get_product_by_name success, data=None")
    return None

def delete_product_from_db(produk_id: int) -> bool:
    """Delete a product by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produk WHERE id = ?", (produk_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()
    # logger.info(f"delete_product_from_db success, deleted={deleted_rows > 0}")
    return deleted_rows > 0

if __name__ == '__main__':
    # Example Usage (for testing the database functions directly)
    init_db()

    # Create
    sample_product_data = {
        "nama_barang": "Indomie Goreng",
        "harga": 3000,
        "lokasi": "Rak Mie Instan",
        "deskripsi_suara_lokasi": "Ada di rak tengah, bagian mie instan.",
        "path_qris": "/qris/indomie.png",
        "stok": 50
    }
    created_id = create_product_in_db(sample_product_data)
    print(f"Created product with ID: {created_id}")

    # Read
    retrieved_product = get_product_from_db(created_id)
    print(f"Retrieved product: {retrieved_product}")

    # Update
    update_data = {
        "nama_barang": "Indomie Goreng Special",
        "harga": 3500,
        "lokasi": "Rak Mie Instan",
        "deskripsi_suara_lokasi": "Ada di rak tengah, bagian mie instan, promo!",
        "path_qris": "/qris/indomie_special.png",
        "stok": 45
    }
    updated_product = update_product_in_db(created_id, update_data)
    print(f"Updated product: {updated_product}")
    
    # Read All
    all_products = get_all_products_from_db()
    print(f"All products: {all_products}")

    # Delete
    # delete_status = delete_product_from_db(created_id)
    # print(f"Delete status for ID {created_id}: {delete_status}")

    # Verify Deletion
    # verify_deleted = get_product_from_db(created_id)
    # print(f"Product after deletion attempt: {verify_deleted}")