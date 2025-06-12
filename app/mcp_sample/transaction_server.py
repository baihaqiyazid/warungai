import os

from mcp.server.fastmcp import FastMCP
# from setup_logs import setup_logger
from setup_logs import setup_logger
from transaction import (
    DetailTransactionCreationRequest,
    TransactionCreationRequest,
    TransactionService,
    TransactionWithDetailsCreationRequest
)
import json
from typing import List, Optional
import logging
from pathlib import Path
print(os.getcwd())
mcp = FastMCP("transaction_server")

# logger = setup_logger("transaction_server", log_filename="warung.log")

# logger.info("========================== Transaction Server Starting ==========================")

@mcp.tool()
async def create_transaction(
    tanggal_transaksi: str,
    total_harga_transaksi: int,
    status: str,
    metode_pembayaran: str,
    detail_transactions: List[DetailTransactionCreationRequest],
    catatan: Optional[str] = None
) -> str:
    """Create a new transaction with its detail transactions.

    Args:
        tanggal_transaksi (str): The date of the transaction in YYYY-MM-DD format.
        total_harga_transaksi (int): The total amount of the transaction.
        status (str): The current status of the transaction (e.g., "pending", "success", "failed").
        metode_pembayaran (str): The payment method used for the transaction.
        detail_transactions (List[DetailTransactionCreationRequest]): A list of dictionaries, where each dictionary represents a detail transaction.
            Example: '''
            [
                {"produk_name": "Sari Roti", "qty": 2, "harga_per_produk": 15000, "total_harga_produk": 30000},
                {"produk_name": "Teh Kotak", "qty": 1, "harga_per_produk": 25000, "total_harga_produk": 25000}
            ]
            '''
        catatan (Optional[str]): Optional notes or remarks for the transaction.

    Returns:
        str: A JSON string representing the created transaction with its details, or an error message if the creation fails.

    Example Usage:
        '''python
        transaction_data = {
            "tanggal_transaksi": "2023-10-26",
            "total_harga_transaksi": 75000,
            "status": "success",
            "metode_pembayaran": "Cash",
            "detail_transactions": [
                {"produk_name": "Sari Roti", "qty": 2, "harga_per_produk": 15000, "total_harga_produk": 30000},
                {"produk_name": "Teh Kotak", "harga_per_produk": 45000, "total_harga_produk": 45000}
            ],
            "catatan": "Pembelian lancar"
        }
        result = await create_transaction(**transaction_data)
        '''
    """
    try:
        # Parse detail transactions
        detail_transactions_data = detail_transactions
        
        # Create transaction with details request
        transaction_with_details_data = TransactionWithDetailsCreationRequest(
            tanggal_transaksi=tanggal_transaksi,
            total_harga_transaksi=total_harga_transaksi,
            status=status,
            metode_pembayaran=metode_pembayaran,
            catatan=catatan,
            detail_transactions=detail_transactions_data
        )
        
        # Create transaction with details
        result = TransactionService.create_transaction_with_details(transaction_with_details_data)
        
        # Convert result to JSON
        return TransactionService.to_json_report_with_details(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to create transaction with details: {str(e)}"})

@mcp.tool()
async def get_transaction(transaction_id: int) -> Optional[str]:
    """Get a transaction by its ID, including its detail transactions.

    Args:
        transaction_id (int): The unique identifier of the transaction.

    Returns:
        Optional[str]: A JSON string representing the transaction with its details if found, otherwise None.

    Example Usage:
        '''python
        transaction_id = 123
        result = await get_transaction(transaction_id)
        '''
    """
    # logger.info(f"get_transaction called with transaction_id={transaction_id}")
    transaction_with_details = TransactionService.get_transaction_with_details(transaction_id)
    # logger.info(f"get_transaction SUCCESS for transaction_id={transaction_id}")
    return TransactionService.to_json_report_with_details(transaction_with_details)

@mcp.tool()
async def get_all_transactions() -> List[str]:
    """Get all transactions, including their detail transactions.

    Returns:
        List[str]: A list of JSON strings, where each string represents a transaction with its details.

    Example Usage:
        '''python
        all_transactions = await get_all_transactions()
        '''
    """
    # logger.info("get_all_transactions called")
    transactions_with_details = TransactionService.get_all_transactions_with_details()
    # logger.info("get_all_transactions SUCCESS")
    return [TransactionService.to_json_report_with_details(t) for t in transactions_with_details]

@mcp.tool()
async def update_transaction(
    tanggal_transaksi: str,
    total_harga_transaksi: int,
    status: str,
    metode_pembayaran: str,
    detail_transactions: List[DetailTransactionCreationRequest], # JSON array of DetailTransactionCreationRequest
    catatan: Optional[str] = None
) -> Optional[str]:
    """Update the last transaction, including its detail transactions.

    Args:
        tanggal_transaksi (str): The new date of the transaction in YYYY-MM-DD format.
        total_harga_transaksi (int): The new total amount of the transaction.
        status (str): The new status of the transaction (e.g., "pending", "success", "failed").
        metode_pembayaran (str): The new payment method used for the transaction.
        detail_transactions (List[DetailTransactionCreationRequest]): A list of dictionaries, where each dictionary represents an updated or new detail transaction.
            Example: '''
            [
                {"produk_name": "Sari Roti", "qty": 3, "harga_per_produk": 15000, "total_harga_produk": 45000},
                {"produk_name": "Teh Kotak", "qty": 1, "harga_per_produk": 10000, "total_harga_produk": 10000}
            ]
            '''
        catatan (Optional[str]): Optional new notes or remarks for the transaction.

    Returns:
        Optional[str]: A JSON string representing the updated transaction with its details, or None if no transaction is found.

    Example Usage:
        '''python
        updated_data = {
            "tanggal_transaksi": "2023-10-27",
            "total_harga_transaksi": 80000,
            "status": "completed",
            "metode_pembayaran": "Credit Card",
            "detail_transactions": [
                {"produk_name": "Sari Roti", "qty": 2, "harga_per_produk": 20000, "total_harga_produk": 40000},
                {"produk_name": "Teh Kotak", "qty": 1, "harga_per_produk": 40000, "total_harga_produk": 40000}
            ],
            "catatan": "Pembelian diperbarui"
        }
        result = await update_transaction(**updated_data)
        '''
    """
    # logger.info(f"update_transaction called with transaction_id={transaction_id}, tanggal_transaksi={tanggal_transaksi}, total_harga_transaksi={total_harga_transaksi}, status={status}, metode_pembayaran={metode_pembayaran}, catatan={catatan}")
    last_transaction = TransactionService.get_last_transaction()
    if last_transaction is None:
        return json.dumps({"error": "No transaction found to update."})

    transaction_id = last_transaction.id
    transaction_data = TransactionCreationRequest(
        tanggal_transaksi=tanggal_transaksi,
        total_harga_transaksi=total_harga_transaksi,
        status=status,
        metode_pembayaran=metode_pembayaran,
        catatan=catatan
    )
    detail_transactions_data = detail_transactions

    transaction_with_details = TransactionService.update_transaction_with_details(transaction_id, transaction_data, detail_transactions_data)
    # logger.info(f"update_transaction SUCCESS for transaction_id={transaction_id}")
    return TransactionService.to_json_report_with_details(transaction_with_details)

@mcp.tool()
async def delete_transaction() -> bool:
    """Delete the last transaction, including all associated detail transactions.

    Returns:
        bool: True if the transaction and its details were successfully deleted, False otherwise.

    Example Usage:
        '''python
        success = await delete_transaction()
        '''
    """
    # logger.info(f"delete_transaction called with transaction_id={transaction_id}")
    last_transaction = TransactionService.get_last_transaction()
    if last_transaction is None:
        print("No transaction found to delete.")
        return False
    
    result = TransactionService.delete_transaction_with_details(last_transaction.id)
    # logger.info(f"delete_transaction SUCCESS for transaction_id={transaction_id}, result={result}")
    return result

@mcp.resource("transaction://transaction_server/transaction/{transaction_id}")
async def read_transaction_resource(transaction_id: int) -> Optional[str]:
    """Read a transaction by its ID.

    Args:
        transaction_id (int): The unique identifier of the transaction to read.

    Returns:
        Optional[str]: A JSON string representing the transaction with its details if found, otherwise None.

    Example Usage:
        '''python
        transaction_id_to_read = 123
        result = await read_transaction_resource(transaction_id_to_read)
        '''
    """
    # logger.info(f"read_transaction_resource called with transaction_id={transaction_id}")
    transaction_with_details = TransactionService.get_transaction_with_details(transaction_id)
    # logger.info(f"read_transaction_resource SUCCESS for transaction_id={transaction_id}")
    return TransactionService.to_json_report_with_details(transaction_with_details)

@mcp.resource("transaction://transaction_server/all_transactions")
async def read_all_transactions_resource() -> List[str]:
    """Read all transactions.

    Returns:
        List[str]: A list of JSON strings, where each string represents a transaction with its details.

    Example Usage:
        '''python
        all_transactions_resource = await read_all_transactions_resource())
        '''
    """
    # logger.info("read_all_transactions_resource called")
    transactions_with_details = TransactionService.get_all_transactions_with_details()
    # logger.info("read_all_transactions_resource SUCCESS")
    return [TransactionService.to_json_report_with_details(t) for t in transactions_with_details]

if __name__ == "__main__":
    mcp.run()