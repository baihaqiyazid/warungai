from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from setup_logs import setup_logger
from transaction_database import (
    create_transaction_in_db,
    get_transaction_from_db,
    get_all_transactions_from_db,
    update_transaction_in_db,
    delete_transaction_from_db,
    create_detail_transaction_in_db,
    get_detail_transaction_from_db,
    get_all_detail_transactions_from_db,
    update_detail_transaction_in_db,
    delete_detail_transaction_from_db,
    get_detail_transactions_by_transaction_id
)
from produk import ProdukService, ProdukCreationRequest, Produk

logger = setup_logger("transaction", log_filename="warung.log")

# logger.info("========================== Transaction Starting ==============================")


class Transaction(BaseModel):
    """
    Model Pydantic untuk merepresentasikan entitas transaction.
    """
    id: Optional[int] = None
    tanggal_transaksi: str = Field(..., description="Tanggal transaksi (YYYY-MM-DD)")
    total_harga_transaksi: int = Field(..., description="Total Harga barang dalam mata uang lokal (misal: Rupiah)")
    status: str = Field(None, description="status transaksi (pending, success, failed)")
    metode_pembayaran: str = Field(None, description="Metode pembayaran yang digunakan untuk transaksi")
    catatan : Optional[str] = Field(None, description="Catatan transaksi (opsional) jika ada")

class TransactionCreationRequest(BaseModel):
    """
    Model for creating a new transaction, id is not required.
    """
    tanggal_transaksi: str = Field(..., description="Tanggal transaksi (YYYY-MM-DD)")
    total_harga_transaksi: int = Field(..., description="Total Harga barang dalam mata uang lokal (misal: Rupiah)")
    status: str = Field(None, description="status transaksi (pending, success, failed)")
    metode_pembayaran: str = Field(None, description="Metode pembayaran yang digunakan untuk transaksi")
    catatan : Optional[str] = Field(None, description="Catatan transaksi (opsional) jika ada")

class DetailTransaction(BaseModel):
    """
    Model Pydantic untuk merepresentasikan entitas detail transaction.
    """
    id: Optional[int] = None
    transaction_id: int = Field(..., description="ID transaksi")
    produk_id: int = Field(..., description="ID produk")
    produk: Optional[Produk] = Field(None, description="Detail produk terkait")
    qty: int = Field(..., description="Jumlah produk yang dibeli")
    harga_per_produk: int = Field(..., description="Harga per produk dalam mata uang lokal (misal: Rupiah)")
    total_harga_produk: int = Field(..., description="Total harga produk dalam mata uang lokal (misal: Rupiah)")

class DetailTransactionCreationRequest(BaseModel):
    """
    Model for creating a new detail transaction, id is not required.
    """
    transaction_id: int = Field(..., description="ID transaksi")
    produk_id: int = Field(..., description="ID produk")
    product_name: str = Field(..., description="Nama produk")
    qty: int = Field(..., description="Jumlah produk yang dibeli")
    harga_per_produk: int = Field(..., description="Harga per produk dalam mata uang lokal (misal: Rupiah)")
    total_harga_produk: int = Field(..., description="Total harga produk dalam mata uang lokal (misal: Rupiah)")

class TransactionWithDetails(BaseModel):
    """
    Model Pydantic untuk merepresentasikan entitas transaksi lengkap dengan detailnya.
    """
    transaction: Transaction
    detail_transactions: List[DetailTransaction]

class TransactionWithDetailsCreationRequest(BaseModel):
    """
    Model untuk membuat transaksi baru dengan detailnya, id tidak diperlukan.
    """
    tanggal_transaksi: str = Field(..., description="Tanggal transaksi (YYYY-MM-DD)")
    total_harga_transaksi: int = Field(..., description="Total Harga barang dalam mata uang lokal (misal: Rupiah)")
    status: str = Field(None, description="status transaksi (pending, success, failed)")
    metode_pembayaran: str = Field(None, description="Metode pembayaran yang digunakan untuk transaksi")
    catatan : Optional[str] = Field(None, description="Catatan transaksi (opsional) jika ada")
    detail_transactions: List[DetailTransactionCreationRequest] = Field(..., description="Daftar detail transaksi")


class TransactionService:
    @staticmethod
    def create_transaction(transaction_data: TransactionCreationRequest) -> Transaction:
        """Create a new transaction."""
        logger.info(f"create_transaction called with transaction_data={transaction_data}")
        transaction_id = create_transaction_in_db(transaction_data.model_dump())
        result = Transaction(id=transaction_id, **transaction_data.model_dump())
        logger.info(f"create_transaction returning {result}")
        return result
    
    @staticmethod
    def get_transaction(transaction_id: int) -> Transaction:
        """Get a transaction by its ID."""
        logger.info(f"get_transaction called with transaction_id={transaction_id}")
        transaction_data = get_transaction_from_db(transaction_id)
        if transaction_data is None:
            # Or raise an HTTPException(status_code=404, detail="Transaction not found") in a web context
            logger.info(f"get_transaction: Transaction with id {transaction_id} not found, raising ValueError")
            raise ValueError(f"Transaction with id {transaction_id} not found")
        result = Transaction(**transaction_data)
        logger.info(f"get_transaction returning {result}")
        return result
    
    @staticmethod
    def get_all_transactions() -> List[Transaction]:
        """Get all transactions."""
        logger.info("get_all_transactions called")
        transaction_data = get_all_transactions_from_db()
        result = [Transaction(**data) for data in transaction_data]
        logger.info(f"get_all_transactions returning {len(result)} transactions")
        return result
    
    @staticmethod
    def update_transaction(transaction_id: int, transaction_data: TransactionCreationRequest) -> Transaction:
        """Update a transaction by its ID."""
        logger.info(f"update_transaction called with transaction_id={transaction_id}, transaction_data={transaction_data}")
        updated_data = update_transaction_in_db(transaction_id, transaction_data.model_dump())
        if updated_data is None:
            logger.info(f"update_transaction: Transaction with id {transaction_id} not found for update, raising ValueError")
            raise ValueError(f"Transaction with id {transaction_id} not found for update")
        result = Transaction(**updated_data)
        logger.info(f"update_transaction returning {result}")
        return result
    
    @staticmethod
    def delete_transaction(transaction_id: int) -> bool:
        """Delete a transaction by its ID."""
        logger.info(f"delete_transaction called with transaction_id={transaction_id}")
        result = delete_transaction_from_db(transaction_id)
        logger.info(f"delete_transaction returning {result}")
        return result
    
    @staticmethod
    def to_json_report(transaction: Transaction) -> str:
        """Convert a transaction to a JSON string."""
        logger.info(f"to_json_report called with transaction={transaction}")
        result = json.dumps(transaction.model_dump())
        logger.info(f"to_json_report returning {result}")
        return result
    
    @staticmethod
    def get_last_transaction() -> Optional[Transaction]:
        """Get the last transaction based on the highest ID."""
        logger.info("get_last_transaction called")
        all_transactions = TransactionService.get_all_transactions()
        if not all_transactions:
            logger.info("get_last_transaction: No transactions found.")
            return None
        # Assuming higher ID means more recent transaction
        last_transaction = max(all_transactions, key=lambda t: t.id)
        logger.info(f"get_last_transaction returning {last_transaction}")
        return last_transaction

    @staticmethod
    def create_transaction_with_details(transaction_with_details_data: TransactionWithDetailsCreationRequest) -> TransactionWithDetails:
        """Create a new transaction along with its detail transactions and update product stock."""
        logger.info(f"create_transaction_with_details called with transaction_with_details_data={transaction_with_details_data}")

        # Create the main transaction
        transaction_data_for_db = transaction_with_details_data.model_dump(exclude={'detail_transactions'})
        transaction_id = create_transaction_in_db(transaction_data_for_db)
        new_transaction = Transaction(id=transaction_id, **transaction_data_for_db)

        # Create detail transactions and update product stock
        created_detail_transactions: List[DetailTransaction] = []
        for detail_req_data in transaction_with_details_data.detail_transactions:
            # Assign the newly created transaction_id to each detail transaction
            detail_req_data.transaction_id = new_transaction.id
            detail_req_data.produk_id = ProdukService.get_produk_by_name(detail_req_data.product_name).id

            detail_transaction_id = create_detail_transaction_in_db(detail_req_data.model_dump())
            new_detail_transaction = DetailTransaction(id=detail_transaction_id, **detail_req_data.model_dump())
            created_detail_transactions.append(new_detail_transaction)

            # Update product stock
            try:
                produk = ProdukService.get_produk(new_detail_transaction.produk_id)
                if produk:
                    if produk.stok < new_detail_transaction.qty:
                        print(f"Warning: Product {produk.id} stock ({produk.stok}) is less than requested quantity ({new_detail_transaction.qty}). Stock will go negative.")

                    new_stock = produk.stok - new_detail_transaction.qty
                    
                    update_data = ProdukCreationRequest(
                        nama_barang=produk.nama_barang,
                        harga=produk.harga,
                        lokasi=produk.lokasi,
                        deskripsi_suara_lokasi=produk.deskripsi_suara_lokasi,
                        path_qris=produk.path_qris,
                        stok=new_stock
                    )
                    ProdukService.update_produk(new_detail_transaction.produk_id, update_data)
                else:
                    print(f"Error: Product with ID {new_detail_transaction.produk_id} not found. Stock not updated for detail transaction {new_detail_transaction.id}.")
            except Exception as e:
                print(f"Error updating product stock for product ID {new_detail_transaction.produk_id}: {e}")

        result = TransactionWithDetails(transaction=new_transaction, detail_transactions=created_detail_transactions)
        logger.info(f"create_transaction_with_details returning {result}")
        return result
    
    @staticmethod
    def get_transaction_with_details(transaction_id: int) -> TransactionWithDetails:
        """Get a transaction and its detail transactions by transaction ID."""
        logger.info(f"get_transaction_with_details called with transaction_id={transaction_id}")
        
        transaction = TransactionService.get_transaction(transaction_id)
        detail_transactions = DetailTransactionService.get_detail_transactions_by_transaction_id(transaction_id)
        
        if transaction is None:
            logger.info(f"get_transaction_with_details: Transaction with id {transaction_id} not found, raising ValueError")
            raise ValueError(f"Transaction with id {transaction_id} not found")

        result = TransactionWithDetails(transaction=transaction, detail_transactions=detail_transactions)
        logger.info(f"get_transaction_with_details returning {result}")
        return result

    @staticmethod
    def get_all_transactions_with_details() -> List[TransactionWithDetails]:
        """Get all transactions along with their detail transactions."""
        logger.info("get_all_transactions_with_details called")
        all_transactions = TransactionService.get_all_transactions()
        
        transactions_with_details: List[TransactionWithDetails] = []
        for transaction in all_transactions:
            detail_transactions = DetailTransactionService.get_detail_transactions_by_transaction_id(transaction.id)
            transactions_with_details.append(TransactionWithDetails(transaction=transaction, detail_transactions=detail_transactions))
        
        logger.info(f"get_all_transactions_with_details returning {len(transactions_with_details)} transactions with details")
        return transactions_with_details

    @staticmethod
    def update_transaction_with_details(
        transaction_id: int, 
        transaction_data: TransactionCreationRequest, 
        detail_transactions_data: List[DetailTransactionCreationRequest]
    ) -> TransactionWithDetails:
        """Update a transaction and its detail transactions, adjusting product stock."""
        logger.info(f"update_transaction_with_details called with transaction_id={transaction_id}, transaction_data={transaction_data}, detail_transactions_data={detail_transactions_data}")

        # Calculate total_harga_transaksi from detail_transactions_data
        calculated_total_harga_transaksi = sum(detail.total_harga_produk for detail in detail_transactions_data)
        transaction_data.total_harga_transaksi = calculated_total_harga_transaksi

        # Update the main transaction
        updated_transaction = TransactionService.update_transaction(transaction_id, transaction_data)
        
        # Get existing detail transactions for comparison
        existing_detail_transactions = DetailTransactionService.get_detail_transactions_by_transaction_id(transaction_id)
        existing_detail_map = {dt.produk_id: dt for dt in existing_detail_transactions}
        
        updated_detail_transactions: List[DetailTransaction] = []
        
        # Process incoming detail transactions (create new or update existing)
        for incoming_detail_req in detail_transactions_data:
            incoming_detail_req.transaction_id = transaction_id # Ensure correct transaction_id
            incoming_detail_req.produk_id = ProdukService.get_produk_by_name(incoming_detail_req.product_name).id
            # Check if this detail transaction already exists (by produk_id for simplicity, adjust if different logic needed)
            # A more robust check might involve a unique identifier for detail transactions themselves or a more complex matching
            # For now, if a product exists in the old list, we assume it's an update, otherwise it's new.
            if incoming_detail_req.produk_id in existing_detail_map:
                old_detail = existing_detail_map[incoming_detail_req.produk_id]
                # Directly update in DB and then fetch, or pass original ID to a helper
                updated_data_from_db = update_detail_transaction_in_db(old_detail.id, incoming_detail_req.model_dump())
                if updated_data_from_db:
                    updated_dt = DetailTransaction(**updated_data_from_db)
                    updated_detail_transactions.append(updated_dt)
                    del existing_detail_map[incoming_detail_req.produk_id] # Mark as processed

                    # Adjust stock for updated item
                    qty_difference = incoming_detail_req.qty - old_detail.qty
                    try:
                        produk = ProdukService.get_produk(updated_dt.produk_id)
                        if produk:
                            new_stock = produk.stok - qty_difference
                            if new_stock < 0:
                                print(f"Warning: Product {produk.id} stock will go negative after update ({new_stock}).")
                            update_payload = ProdukCreationRequest(
                                nama_barang=produk.nama_barang,
                                harga=produk.harga,
                                lokasi=produk.lokasi,
                                deskripsi_suara_lokasi=produk.deskripsi_suara_lokasi,
                                path_qris=produk.path_qris,
                                stok=new_stock
                            )
                            ProdukService.update_produk(updated_dt.produk_id, update_payload)
                        else:
                            print(f"Error: Product with ID {updated_dt.produk_id} not found. Stock not adjusted for updated detail transaction {updated_dt.id}.")
                    except Exception as e:
                        print(f"Error adjusting product stock for product ID {updated_dt.produk_id} during update: {e}")

            else:
                # This is a new detail transaction for this transaction
                new_dt_id = create_detail_transaction_in_db(incoming_detail_req.model_dump())
                new_dt = DetailTransaction(id=new_dt_id, **incoming_detail_req.model_dump())
                updated_detail_transactions.append(new_dt)

                # Adjust stock for new item
                try:
                    produk = ProdukService.get_produk(new_dt.produk_id)
                    if produk:
                        if produk.stok < new_dt.qty:
                            print(f"Warning: Product {produk.id} stock ({produk.stok}) is less than requested quantity ({new_dt.qty}). Stock will go negative.")
                        new_stock = produk.stok - new_dt.qty
                        update_data = ProdukCreationRequest(
                            nama_barang=produk.nama_barang,
                            harga=produk.harga,
                            lokasi=produk.lokasi,
                            deskripsi_suara_lokasi=produk.deskripsi_suara_lokasi,
                            path_qris=produk.path_qris,
                            stok=new_stock
                        )
                        ProdukService.update_produk(new_dt.produk_id, update_data)
                    else:
                        print(f"Error: Product with ID {new_dt.produk_id} not found. Stock not updated for new detail transaction {new_dt.id}.")
                except Exception as e:
                    print(f"Error updating product stock for product ID {new_dt.produk_id}: {e}")
        
        # Delete any remaining existing detail transactions (those not in the incoming data)
        for remaining_dt in existing_detail_map.values():
            # Replenish stock before deletion
            try:
                produk = ProdukService.get_produk(remaining_dt.produk_id)
                if produk:
                    new_stock = produk.stok + remaining_dt.qty
                    update_payload = ProdukCreationRequest(
                        nama_barang=produk.nama_barang,
                        harga=produk.harga,
                        lokasi=produk.lokasi,
                        deskripsi_suara_lokasi=produk.deskripsi_suara_lokasi,
                        path_qris=produk.path_qris,
                        stok=new_stock
                    )
                    ProdukService.update_produk(produk.id, update_payload)
                else:
                    print(f"Warning: Product with ID {remaining_dt.produk_id} not found during detail transaction deletion. Stock not replenished.")
            except Exception as e:
                print(f"Error replenishing product stock for product ID {remaining_dt.produk_id} during deletion: {e}")
            delete_detail_transaction_from_db(remaining_dt.id)


        result = TransactionWithDetails(transaction=updated_transaction, detail_transactions=updated_detail_transactions)
        logger.info(f"update_transaction_with_details returning {result}")
        return result

    @staticmethod
    def delete_transaction_with_details(transaction_id: int) -> bool:
        """Delete a transaction and all its associated detail transactions, replenishing product stock."""
        logger.info(f"delete_transaction_with_details called with transaction_id={transaction_id}")

        # Get all detail transactions associated with this transaction
        detail_transactions_to_delete = DetailTransactionService.get_detail_transactions_by_transaction_id(transaction_id)
        
        # Delete each detail transaction (which also replenishes stock)
        for detail_transaction in detail_transactions_to_delete:
            try:
                produk = ProdukService.get_produk(detail_transaction.produk_id)
                if produk:
                    new_stock = produk.stok + detail_transaction.qty
                    update_payload = ProdukCreationRequest(
                        nama_barang=produk.nama_barang,
                        harga=produk.harga,
                        lokasi=produk.lokasi,
                        deskripsi_suara_lokasi=produk.deskripsi_suara_lokasi,
                        path_qris=produk.path_qris,
                        stok=new_stock
                    )
                    ProdukService.update_produk(produk.id, update_payload)
                else:
                    print(f"Warning: Product with ID {detail_transaction.produk_id} not found during detail transaction deletion. Stock not replenished.")
            except Exception as e:
                print(f"Error replenishing product stock for product ID {detail_transaction.produk_id} during deletion: {e}")
            delete_detail_transaction_from_db(detail_transaction.id)
        
        # Finally, delete the main transaction
        result = delete_transaction_from_db(transaction_id)
        
        logger.info(f"delete_transaction_with_details returning {result}")
        return result

    @staticmethod
    def to_json_report_with_details(transaction_with_details: TransactionWithDetails) -> str:
        """Convert a transaction with details to a JSON string."""
        logger.info(f"to_json_report_with_details called with transaction_with_details={transaction_with_details}")
        response_data = {
            "transaction": transaction_with_details.transaction.model_dump(),
            "detail_transactions": [detail.model_dump() for detail in transaction_with_details.detail_transactions]
        }
        result = json.dumps(response_data)
        logger.info(f"to_json_report_with_details returning {result}")
        return result

class DetailTransactionService:
    @staticmethod
    def get_detail_transaction(detail_transaction_id: int) -> DetailTransaction:
        """Get a detail transaction by its ID."""
        logger.info(f"get_detail_transaction called with detail_transaction_id={detail_transaction_id}")
        detail_transaction_data = get_detail_transaction_from_db(detail_transaction_id)
        if detail_transaction_data is None:
            logger.info(f"get_detail_transaction: DetailTransaction with id {detail_transaction_id} not found, raising ValueError")
            raise ValueError(f"DetailTransaction with id {detail_transaction_id} not found")
        detail_transaction = DetailTransaction(**detail_transaction_data)
        produk = ProdukService.get_produk(detail_transaction.produk_id)
        if produk:
            detail_transaction.produk = produk
        result = detail_transaction
        logger.info(f"get_detail_transaction returning {result}")
        return result
    
    @staticmethod
    def get_all_detail_transactions() -> List[DetailTransaction]:
        """Get all detail transactions."""
        logger.info("get_all_detail_transactions called")
        detail_transaction_data = get_all_detail_transactions_from_db()
        result = []
        for data in detail_transaction_data:
            detail_transaction = DetailTransaction(**data)
            produk = ProdukService.get_produk(detail_transaction.produk_id)
            if produk:
                detail_transaction.produk = produk
            result.append(detail_transaction)
        logger.info(f"get_all_detail_transactions returning {len(result)} detail transactions")
        return result
    
    @staticmethod
    def get_detail_transactions_by_transaction_id(transaction_id: int) -> List[DetailTransaction]:
        """Get all detail transactions by transaction_id."""
        logger.info(f"get_detail_transactions_by_transaction_id called with transaction_id={transaction_id}")
        detail_transaction_data = get_detail_transactions_by_transaction_id(transaction_id)
        result = []
        for data in detail_transaction_data:
            detail_transaction = DetailTransaction(**data)
            produk = ProdukService.get_produk(detail_transaction.produk_id)
            if produk:
                detail_transaction.produk = produk
            result.append(detail_transaction)
        logger.info(f"get_detail_transactions_by_transaction_id returning {len(result)} detail transactions")
        return result
    
    @staticmethod
    def to_json_report(detail_transaction: DetailTransaction) -> str:
        """Convert a detail transaction to a JSON string."""
        # logger.info(f"to_json_report called with detail_transaction={detail_transaction}")
        result = json.dumps(detail_transaction.model_dump())
        # logger.info(f"to_json_report returning {result}")
        return result