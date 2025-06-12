import sqlite3
from typing import Dict, Any, Optional, List

# from setup_logs import setup_logger

DATABASE_NAME = "src/data/warung.db"

# logger = setup_logger("transaction_database", log_filename="warung.log")

# logger.info("========================== Transaction Database Starting ==============================")

def init_db():
    # logger.info("init_db called")
    """Initialize the database and create transaction and detail_transaction tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS detail_transactions")

    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal_transaksi TEXT NOT NULL,
            total_harga_transaksi INTEGER NOT NULL,
            status TEXT,
            metode_pembayaran TEXT,
            catatan TEXT
        )
    """)
    
    # Create detail_transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detail_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            produk_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            harga_per_produk INTEGER NOT NULL,
            total_harga_produk INTEGER NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (produk_id) REFERENCES produk (id) 
        )
    """)
    conn.commit()
    conn.close()
    # logger.info("init_db finished")

# Transaction CRUD operations
def create_transaction_in_db(transaction_data: Dict[str, Any]) -> int:
    # logger.info(f"create_transaction_in_db called with transaction_data={transaction_data}")
    """Create a new transaction in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    transaction_id = None
    try:
        cursor.execute("""
            INSERT INTO transactions (tanggal_transaksi, total_harga_transaksi, status, metode_pembayaran, catatan)
            VALUES (:tanggal_transaksi, :total_harga_transaksi, :status, :metode_pembayaran, :catatan)
        """, transaction_data)
        transaction_id = cursor.lastrowid
        conn.commit()
        # logger.info(f"create_transaction_in_db returning transaction_id={transaction_id}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during create_transaction_in_db: {e}")
        raise
    finally:
        conn.close()
    return transaction_id

def get_transaction_from_db(transaction_id: int) -> Optional[Dict[str, Any]]:
    # logger.info(f"get_transaction_from_db called with transaction_id={transaction_id}")
    """Retrieve a transaction by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # logger.info(f"get_transaction_from_db returning row={dict(row)}")
        return dict(row)
    # logger.info("get_transaction_from_db returning None")
    return None

def get_all_transactions_from_db() -> List[Dict[str, Any]]:
    # logger.info("get_all_transactions_from_db called")
    """Retrieve all transactions from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    # logger.info(f"get_all_transactions_from_db returning {len(rows)} rows")
    return [dict(row) for row in rows]

def update_transaction_in_db(transaction_id: int, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # logger.info(f"update_transaction_in_db called with transaction_id={transaction_id}, transaction_data={transaction_data}")
    """Update an existing transaction in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    updated_row = None
    try:
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        if not cursor.fetchone():
            # logger.info("update_transaction_in_db: transaction not found, returning None")
            return None 

        cursor.execute("""
            UPDATE transactions
            SET tanggal_transaksi = :tanggal_transaksi,
                total_harga_transaksi = :total_harga_transaksi,
                status = :status,
                metode_pembayaran = :metode_pembayaran,
                catatan = :catatan
            WHERE id = :id
        """, {**transaction_data, "id": transaction_id})
        conn.commit()
        
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        updated_row = cursor.fetchone()
        # logger.info(f"update_transaction_in_db returning updated_row={dict(updated_row)}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during update_transaction_in_db: {e}")
        raise
    finally:
        conn.close()
    if updated_row:
        return dict(updated_row)
    # logger.info("update_transaction_in_db returning None")
    return None

def delete_transaction_from_db(transaction_id: int) -> bool:
    # logger.info(f"delete_transaction_from_db called with transaction_id={transaction_id}")
    """Delete a transaction by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    deleted_rows = 0
    try:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        deleted_rows = cursor.rowcount
        # logger.info(f"delete_transaction_from_db returning {deleted_rows > 0}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during delete_transaction_from_db: {e}")
        raise
    finally:
        conn.close()
    return deleted_rows > 0

# DetailTransaction CRUD operations
def create_detail_transaction_in_db(detail_transaction_data: Dict[str, Any]) -> int:
    # logger.info(f"create_detail_transaction_in_db called with detail_transaction_data={detail_transaction_data}")
    """Create a new detail_transaction in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    detail_transaction_id = None
    try:
        cursor.execute("""
            INSERT INTO detail_transactions (transaction_id, produk_id, qty, harga_per_produk, total_harga_produk)
            VALUES (:transaction_id, :produk_id, :qty, :harga_per_produk, :total_harga_produk)
        """, detail_transaction_data)
        detail_transaction_id = cursor.lastrowid
        conn.commit()
        # logger.info(f"create_detail_transaction_in_db returning detail_transaction_id={detail_transaction_id}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during create_detail_transaction_in_db: {e}")
        raise
    finally:
        conn.close()
    return detail_transaction_id

def get_detail_transaction_from_db(detail_transaction_id: int) -> Optional[Dict[str, Any]]:
    # logger.info(f"get_detail_transaction_from_db called with detail_transaction_id={detail_transaction_id}")
    """Retrieve a detail_transaction by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail_transactions WHERE id = ?", (detail_transaction_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # logger.info(f"get_detail_transaction_from_db returning row={dict(row)}")
        return dict(row)
    # logger.info("get_detail_transaction_from_db returning None")
    return None

def get_all_detail_transactions_from_db() -> List[Dict[str, Any]]:
    # logger.info("get_all_detail_transactions_from_db called")
    """Retrieve all detail_transactions from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail_transactions")
    rows = cursor.fetchall()
    conn.close()
    # logger.info(f"get_all_detail_transactions_from_db returning {len(rows)} rows")
    return [dict(row) for row in rows]

def update_detail_transaction_in_db(detail_transaction_id: int, detail_transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # logger.info(f"update_detail_transaction_in_db called with detail_transaction_id={detail_transaction_id}, detail_transaction_data={detail_transaction_data}")
    """Update an existing detail_transaction in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    updated_row = None
    try:
        cursor.execute("SELECT * FROM detail_transactions WHERE id = ?", (detail_transaction_id,))
        if not cursor.fetchone():
            # logger.info("update_detail_transaction_in_db: detail_transaction not found, returning None")
            return None

        cursor.execute("""
            UPDATE detail_transactions
            SET transaction_id = :transaction_id,
                produk_id = :produk_id,
                qty = :qty,
                harga_per_produk = :harga_per_produk,
                total_harga_produk = :total_harga_produk
            WHERE id = :id
        """, {**detail_transaction_data, "id": detail_transaction_id})
        conn.commit()

        cursor.execute("SELECT * FROM detail_transactions WHERE id = ?", (detail_transaction_id,))
        updated_row = cursor.fetchone()
        # logger.info(f"update_detail_transaction_in_db returning updated_row={dict(updated_row)}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during update_detail_transaction_in_db: {e}")
        raise
    finally:
        conn.close()
    if updated_row:
        return dict(updated_row)
    # logger.info("update_detail_transaction_in_db returning None")
    return None

def delete_detail_transaction_from_db(detail_transaction_id: int) -> bool:
    # logger.info(f"delete_detail_transaction_from_db called with detail_transaction_id={detail_transaction_id}")
    """Delete a detail_transaction by its ID from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    deleted_rows = 0
    try:
        cursor.execute("DELETE FROM detail_transactions WHERE id = ?", (detail_transaction_id,))
        conn.commit()
        deleted_rows = cursor.rowcount
        # logger.info(f"delete_detail_transaction_from_db returning {deleted_rows > 0}")
    except sqlite3.Error as e:
        conn.rollback()
        # logger.error(f"Database error during delete_detail_transaction_from_db: {e}")
        raise
    finally:
        conn.close()
    return deleted_rows > 0

def get_detail_transactions_by_transaction_id(transaction_id: int) -> List[Dict[str, Any]]:
    # logger.info(f"get_detail_transactions_by_transaction_id called with transaction_id={transaction_id}")
    """Retrieve all detail_transactions by transaction_id from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail_transactions WHERE transaction_id = ?", (transaction_id,))
    rows = cursor.fetchall()
    conn.close()
    # logger.info(f"get_detail_transactions_by_transaction_id returning {len(rows)} rows")
    return [dict(row) for row in rows]

if __name__ == '__main__':
    init_db() # Ensure tables are created

    # Example Usage for Transaction
    sample_transaction_data = {
        "tanggal_transaksi": "2024-07-27",
        "total_harga_transaksi": 10000,
        "status": "pending",
        "metode_pembayaran": "cash",
        "catatan": "Test transaction"
    }
    created_transaction_id = create_transaction_in_db(sample_transaction_data)
    print(f"Created transaction with ID: {created_transaction_id}")

    retrieved_transaction = get_transaction_from_db(created_transaction_id)
    print(f"Retrieved transaction: {retrieved_transaction}")

    all_transactions = get_all_transactions_from_db()
    print(f"All transactions: {all_transactions}")
    
    update_transaction_data = {
        "tanggal_transaksi": "2024-07-28",
        "total_harga_transaksi": 12000,
        "status": "success",
        "metode_pembayaran": "qris",
        "catatan": "Updated test transaction"
    }
    updated_transaction = update_transaction_in_db(created_transaction_id, update_transaction_data)
    print(f"Updated transaction: {updated_transaction}")

    # Example Usage for DetailTransaction
    # Assuming a product with ID 1 exists for FK constraint
    sample_detail_transaction_data = {
        "transaction_id": created_transaction_id, # Use the ID from the transaction created above
        "produk_id": 1, 
        "qty": 2,
        "harga_per_produk": 5000,
        "total_harga_produk": 10000
    }
    created_detail_id = create_detail_transaction_in_db(sample_detail_transaction_data)
    print(f"Created detail transaction with ID: {created_detail_id}")

    retrieved_detail = get_detail_transaction_from_db(created_detail_id)
    print(f"Retrieved detail transaction: {retrieved_detail}")

    all_details = get_all_detail_transactions_from_db()
    print(f"All detail transactions: {all_details}")

    update_detail_data = {
        "transaction_id": created_transaction_id,
        "produk_id": 1,
        "qty": 3,
        "harga_per_produk": 6000,
        "total_harga_produk": 18000
    }
    updated_detail = update_detail_transaction_in_db(created_detail_id, update_detail_data)
    print(f"Updated detail transaction: {updated_detail}")

    print("get_detail_transactions_by_transaction_id")
    
    print(get_detail_transactions_by_transaction_id(created_transaction_id))

    # Delete (optional, uncomment to test)
    # delete_detail_status = delete_detail_transaction_from_db(created_detail_id)
    # print(f"Delete detail status for ID {created_detail_id}: {delete_detail_status}")
    
    # delete_transaction_status = delete_transaction_from_db(created_transaction_id)
    # print(f"Delete transaction status for ID {created_transaction_id}: {delete_transaction_status}") 