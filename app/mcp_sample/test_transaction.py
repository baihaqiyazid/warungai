import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

from transaction import (
    Transaction,
    TransactionCreationRequest,
    DetailTransaction,
    DetailTransactionCreationRequest,
    TransactionWithDetails,
    TransactionWithDetailsCreationRequest,
    TransactionService,
    DetailTransactionService,
    ProdukService,
    ProdukCreationRequest
)

# Mock database functions
mock_db_module = "app.mcp_sample.transaction"
mock_produk_module = "app.mcp_sample.produk"

class TestTransactionService:
    @patch(f"{mock_db_module}.create_transaction_in_db")
    def test_create_transaction(self, mock_create_transaction_in_db):
        mock_create_transaction_in_db.return_value = 1  # Simulate a new ID for the transaction
        transaction_data = TransactionCreationRequest(
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=10000,
            status="pending",
            metode_pembayaran="cash",
            catatan="Test transaction"
        )
        
        result = TransactionService.create_transaction(transaction_data)
        
        mock_create_transaction_in_db.assert_called_once_with(transaction_data.model_dump())
        assert result.tanggal_transaksi == transaction_data.tanggal_transaksi
        assert result.total_harga_transaksi == transaction_data.total_harga_transaksi
        assert result.status == transaction_data.status
        assert result.metode_pembayaran == transaction_data.metode_pembayaran
        assert result.catatan == transaction_data.catatan 

    @patch(f"{mock_db_module}.get_transaction_from_db")
    def test_get_transaction(self, mock_get_transaction_from_db):
        mock_get_transaction_from_db.return_value = {
            "id": 1,
            "tanggal_transaksi": "2023-01-01",
            "total_harga_transaksi": 10000,
            "status": "pending",
            "metode_pembayaran": "cash",
            "catatan": "Test transaction"
        }
        
        result = TransactionService.get_transaction(1)
        
        mock_get_transaction_from_db.assert_called_once_with(1)
        assert result.id == 1
        assert result.tanggal_transaksi == "2023-01-01"

    @patch(f"{mock_db_module}.get_transaction_from_db")
    def test_get_transaction_not_found(self, mock_get_transaction_from_db):
        mock_get_transaction_from_db.return_value = None
        
        with pytest.raises(ValueError, match="Transaction with id 999 not found"):
            TransactionService.get_transaction(999)
        
        mock_get_transaction_from_db.assert_called_once_with(999)

    @patch(f"{mock_db_module}.get_all_transactions_from_db")
    def test_get_all_transactions(self, mock_get_all_transactions_from_db):
        mock_get_all_transactions_from_db.return_value = [
            {
                "id": 1,
                "tanggal_transaksi": "2023-01-01",
                "total_harga_transaksi": 10000,
                "status": "pending",
                "metode_pembayaran": "cash",
                "catatan": "Test transaction 1"
            },
            {
                "id": 2,
                "tanggal_transaksi": "2023-01-02",
                "total_harga_transaksi": 20000,
                "status": "success",
                "metode_pembayaran": "credit",
                "catatan": "Test transaction 2"
            }
        ]
        
        result = TransactionService.get_all_transactions()
        
        mock_get_all_transactions_from_db.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2 

    @patch(f"{mock_db_module}.update_transaction_in_db")
    def test_update_transaction(self, mock_update_transaction_in_db):
        updated_data = {
            "id": 1,
            "tanggal_transaksi": "2023-01-01",
            "total_harga_transaksi": 12000,
            "status": "success",
            "metode_pembayaran": "credit",
            "catatan": "Updated transaction"
        }
        mock_update_transaction_in_db.return_value = updated_data
        
        transaction_data = TransactionCreationRequest(
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=12000,
            status="success",
            metode_pembayaran="credit",
            catatan="Updated transaction"
        )
        
        result = TransactionService.update_transaction(1, transaction_data)
        
        mock_update_transaction_in_db.assert_called_once_with(1, transaction_data.model_dump())
        assert result.id == 1
        assert result.total_harga_transaksi == 12000
        assert result.status == "success"

    @patch(f"{mock_db_module}.update_transaction_in_db")
    def test_update_transaction_not_found(self, mock_update_transaction_in_db):
        mock_update_transaction_in_db.return_value = None
        
        transaction_data = TransactionCreationRequest(
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=12000,
            status="success",
            metode_pembayaran="credit",
            catatan="Updated transaction"
        )
        
        with pytest.raises(ValueError, match="Transaction with id 999 not found for update"):
            TransactionService.update_transaction(999, transaction_data)
        
        mock_update_transaction_in_db.assert_called_once_with(999, transaction_data.model_dump())

    @patch(f"{mock_db_module}.delete_transaction_from_db")
    def test_delete_transaction(self, mock_delete_transaction_from_db):
        mock_delete_transaction_from_db.return_value = True
        
        result = TransactionService.delete_transaction(1)
        
        mock_delete_transaction_from_db.assert_called_once_with(1)
        assert result is True

    @patch(f"{mock_db_module}.delete_transaction_from_db")
    def test_delete_transaction_not_found(self, mock_delete_transaction_from_db):
        mock_delete_transaction_from_db.return_value = False
        
        result = TransactionService.delete_transaction(999)
        
        mock_delete_transaction_from_db.assert_called_once_with(999)
        assert result is False

    def test_to_json_report(self):
        transaction = Transaction(
            id=1,
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=10000,
            status="pending",
            metode_pembayaran="cash",
            catatan="Test transaction"
        )
        
        result = TransactionService.to_json_report(transaction)
        
        expected_json = json.dumps({
            "id": 1,
            "tanggal_transaksi": "2023-01-01",
            "total_harga_transaksi": 10000,
            "status": "pending",
            "metode_pembayaran": "cash",
            "catatan": "Test transaction"
        })
        assert result == expected_json 

    @patch(f"{mock_db_module}.create_transaction_in_db")
    @patch(f"{mock_db_module}.create_detail_transaction_in_db")
    @patch(f"{mock_produk_module}.ProdukService.get_produk")
    @patch(f"{mock_produk_module}.ProdukService.update_produk")
    def test_create_transaction_with_details(self,
                                              mock_update_produk,
                                              mock_get_produk,
                                              mock_create_detail_transaction_in_db,
                                              mock_create_transaction_in_db):
        # Mock main transaction creation
        mock_create_transaction_in_db.return_value = 1

        # Mock detail transaction creation
        mock_create_detail_transaction_in_db.side_effect = [101, 102]

        # Mock ProdukService.get_produk
        mock_produk1 = MagicMock(
            id=1,
            nama_barang="Produk A",
            harga=5000,
            lokasi="Rak 1",
            deskripsi_suara_lokasi="Deskripsi A",
            path_qris="path/qris_a.png",
            stok=10
        )
        mock_produk2 = MagicMock(
            id=2,
            nama_barang="Produk B",
            harga=7500,
            lokasi="Rak 2",
            deskripsi_suara_lokasi="Deskripsi B",
            path_qris="path/qris_b.png",
            stok=5
        )
        mock_get_produk.side_effect = [mock_produk1, mock_produk2]

        transaction_with_details_data = TransactionWithDetailsCreationRequest(
            tanggal_transaksi="2023-01-03",
            total_harga_transaksi=20000,
            status="pending",
            metode_pembayaran="transfer",
            catatan="Order with details",
            detail_transactions=[
                DetailTransactionCreationRequest(
                    transaction_id=0,  # Will be overridden by the service
                    produk_id=1,
                    qty=2,
                    harga_per_produk=5000,
                    total_harga_produk=10000
                ),
                DetailTransactionCreationRequest(
                    transaction_id=0,  # Will be overridden by the service
                    produk_id=2,
                    qty=1,
                    harga_per_produk=7500,
                    total_harga_produk=7500
                )
            ]
        )

        result = TransactionService.create_transaction_with_details(transaction_with_details_data)

        # Assert main transaction creation
        mock_create_transaction_in_db.assert_called_once_with(transaction_with_details_data.model_dump(exclude={'detail_transactions'}))
        assert result.transaction.id == 1
        assert result.transaction.tanggal_transaksi == "2023-01-03"

        # Assert detail transaction creation
        assert len(result.detail_transactions) == 2
        assert result.detail_transactions[0].id == 101
        assert result.detail_transactions[0].transaction_id == 1
        assert result.detail_transactions[0].produk_id == 1
        assert result.detail_transactions[1].id == 102
        assert result.detail_transactions[1].transaction_id == 1
        assert result.detail_transactions[1].produk_id == 2

        # Assert product stock updates
        assert mock_get_produk.call_count == 2
        mock_update_produk.assert_any_call(
            1,
            ProdukCreationRequest(
                nama_barang="Produk A",
                harga=5000,
                lokasi="Rak 1",
                deskripsi_suara_lokasi="Deskripsi A",
                path_qris="path/qris_a.png",
                stok=8 # 10 - 2
            )
        )
        mock_update_produk.assert_any_call(
            2,
            ProdukCreationRequest(
                nama_barang="Produk B",
                harga=7500,
                lokasi="Rak 2",
                deskripsi_suara_lokasi="Deskripsi B",
                path_qris="path/qris_b.png",
                stok=4 # 5 - 1
            )
        ) 

    @patch("app.mcp_sample.transaction.DetailTransactionService.get_detail_transactions_by_transaction_id")
    @patch(f"{mock_db_module}.get_transaction_from_db")
    def test_get_transaction_with_details(self,
                                          mock_get_transaction_from_db,
                                          mock_get_detail_transactions_by_transaction_id):
        # Mock main transaction data
        mock_get_transaction_from_db.return_value = {
            "id": 1,
            "tanggal_transaksi": "2023-01-01",
            "total_harga_transaksi": 10000,
            "status": "pending",
            "metode_pembayaran": "cash",
            "catatan": "Test transaction"
        }

        # Mock detail transactions data
        mock_get_detail_transactions_by_transaction_id.return_value = [
            {
                "id": 101,
                "transaction_id": 1,
                "produk_id": 1,
                "qty": 2,
                "harga_per_produk": 5000,
                "total_harga_produk": 10000
            },
            {
                "id": 102,
                "transaction_id": 1,
                "produk_id": 2,
                "qty": 1,
                "harga_per_produk": 7500,
                "total_harga_produk": 7500
            }
        ]

        result = TransactionService.get_transaction_with_details(1)

        mock_get_transaction_from_db.assert_called_once_with(1)
        mock_get_detail_transactions_by_transaction_id.assert_called_once_with(1)

        assert result.transaction.id == 1
        assert len(result.detail_transactions) == 2
        assert result.detail_transactions[0].id == 101
        assert result.detail_transactions[1].produk_id == 2

    @patch("app.mcp_sample.transaction.DetailTransactionService.get_detail_transactions_by_transaction_id")
    @patch(f"{mock_db_module}.get_transaction_from_db")
    def test_get_transaction_with_details_transaction_not_found(self,
                                                                mock_get_transaction_from_db,
                                                                mock_get_detail_transactions_by_transaction_id):
        mock_get_transaction_from_db.return_value = None

        with pytest.raises(ValueError, match="Transaction with id 999 not found"):
            TransactionService.get_transaction_with_details(999)

        mock_get_transaction_from_db.assert_called_once_with(999)
        mock_get_detail_transactions_by_transaction_id.assert_not_called() 

    @patch("app.mcp_sample.transaction.DetailTransactionService.get_detail_transactions_by_transaction_id")
    @patch("app.mcp_sample.transaction.TransactionService.get_all_transactions")
    def test_get_all_transactions_with_details(self,
                                                 mock_get_all_transactions,
                                                 mock_get_detail_transactions_by_transaction_id):
        # Mock all transactions
        mock_get_all_transactions.return_value = [
            Transaction(
                id=1,
                tanggal_transaksi="2023-01-01",
                total_harga_transaksi=10000,
                status="pending",
                metode_pembayaran="cash",
                catatan="Test transaction 1"
            ),
            Transaction(
                id=2,
                tanggal_transaksi="2023-01-02",
                total_harga_transaksi=20000,
                status="success",
                metode_pembayaran="credit",
                catatan="Test transaction 2"
            )
        ]

        # Mock detail transactions for each transaction ID
        mock_get_detail_transactions_by_transaction_id.side_effect = [
            [
                DetailTransaction(
                    id=101,
                    transaction_id=1,
                    produk_id=1,
                    qty=2,
                    harga_per_produk=5000,
                    total_harga_produk=10000
                )
            ],
            [
                DetailTransaction(
                    id=102,
                    transaction_id=2,
                    produk_id=2,
                    qty=1,
                    harga_per_produk=7500,
                    total_harga_produk=7500
                )
            ]
        ]

        result = TransactionService.get_all_transactions_with_details()

        mock_get_all_transactions.assert_called_once()
        assert mock_get_detail_transactions_by_transaction_id.call_count == 2

        assert len(result) == 2
        assert result[0].transaction.id == 1
        assert len(result[0].detail_transactions) == 1
        assert result[0].detail_transactions[0].produk_id == 1

        assert result[1].transaction.id == 2
        assert len(result[1].detail_transactions) == 1
        assert result[1].detail_transactions[0].produk_id == 2 

    @patch("app.mcp_sample.transaction.TransactionService.update_transaction")
    @patch("app.mcp_sample.transaction.DetailTransactionService.get_detail_transactions_by_transaction_id")
    @patch(f"{mock_db_module}.update_detail_transaction_in_db")
    @patch(f"{mock_db_module}.create_detail_transaction_in_db")
    @patch(f"{mock_db_module}.delete_detail_transaction_from_db")
    @patch(f"{mock_produk_module}.ProdukService.get_produk")
    @patch(f"{mock_produk_module}.ProdukService.update_produk")
    def test_update_transaction_with_details(self,
                                              mock_produk_update_produk,
                                              mock_produk_get_produk,
                                              mock_delete_detail_transaction_from_db,
                                              mock_create_detail_transaction_in_db,
                                              mock_update_detail_transaction_in_db,
                                              mock_get_detail_transactions_by_transaction_id,
                                              mock_update_transaction):
        # Mock initial transaction and details
        initial_transaction = Transaction(
            id=1,
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=10000,
            status="pending",
            metode_pembayaran="cash",
            catatan="Initial"
        )
        initial_detail_transactions = [
            DetailTransaction(
                id=101,
                transaction_id=1,
                produk_id=1,
                qty=2,
                harga_per_produk=5000,
                total_harga_produk=10000
            ),
            DetailTransaction(
                id=102,
                transaction_id=1,
                produk_id=2,
                qty=1,
                harga_per_produk=7500,
                total_harga_produk=7500
            )
        ]
        mock_update_transaction.return_value = initial_transaction # Return the transaction as if it's updated
        mock_get_detail_transactions_by_transaction_id.return_value = initial_detail_transactions

        # Mock product data
        produk1_initial = MagicMock(id=1, nama_barang="Produk A", harga=5000, lokasi="Rak 1", deskripsi_suara_lokasi="Desc A", path_qris="qrisA.png", stok=10)
        produk2_initial = MagicMock(id=2, nama_barang="Produk B", harga=7500, lokasi="Rak 2", deskripsi_suara_lokasi="Desc B", path_qris="qrisB.png", stok=5)
        produk3_initial = MagicMock(id=3, nama_barang="Produk C", harga=1000, lokasi="Rak 3", deskripsi_suara_lokasi="Desc C", path_qris="qrisC.png", stok=20)
        
        # Scenario: Update produk 1 (change qty), Add produk 3, Delete produk 2
        mock_produk_get_produk.side_effect = [
            produk1_initial, # For qty_difference (produk 1)
            produk3_initial, # For new_dt (produk 3)
            produk2_initial # For remaining_dt (produk 2)
        ]

        # Mock update detail transaction (for existing item update)
        updated_detail_produk1 = DetailTransaction(
            id=101,
            transaction_id=1,
            produk_id=1,
            qty=3, # Changed qty
            harga_per_produk=5000,
            total_harga_produk=15000
        )
        mock_update_detail_transaction_in_db.return_value = updated_detail_produk1.model_dump()

        # Mock create detail transaction (for new item)
        new_detail_produk3 = DetailTransaction(
            id=103,
            transaction_id=1,
            produk_id=3,
            qty=5,
            harga_per_produk=1000,
            total_harga_produk=5000
        )
        mock_create_detail_transaction_in_db.return_value = 103

        transaction_data_update = TransactionCreationRequest(
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=20000, # Updated total
            status="completed",
            metode_pembayaran="transfer",
            catatan="Updated test transaction"
        )
        detail_transactions_data_update = [
            DetailTransactionCreationRequest(
                transaction_id=1,
                produk_id=1,
                qty=3, # Updated qty
                harga_per_produk=5000,
                total_harga_produk=15000
            ),
            DetailTransactionCreationRequest(
                transaction_id=1,
                produk_id=3,
                qty=5,
                harga_per_produk=1000,
                total_harga_produk=5000
            ) # New detail transaction
        ]

        result = TransactionService.update_transaction_with_details(
            1,
            transaction_data_update,
            detail_transactions_data_update
        )

        mock_update_transaction.assert_called_once_with(1, transaction_data_update)
        mock_get_detail_transactions_by_transaction_id.assert_called_once_with(1)

        # Assertions for updates
        mock_update_detail_transaction_in_db.assert_called_once_with(101, detail_transactions_data_update[0].model_dump())
        mock_create_detail_transaction_in_db.assert_called_once_with(detail_transactions_data_update[1].model_dump())
        mock_delete_detail_transaction_from_db.assert_called_once_with(102) # produk 2 should be deleted

        # Assert product stock adjustments
        # For produk 1: old qty 2, new qty 3 => stock -1 (10-1 = 9)
        mock_produk_update_produk.assert_any_call(
            1,
            ProdukCreationRequest(
                nama_barang="Produk A",
                harga=5000,
                lokasi="Rak 1",
                deskripsi_suara_lokasi="Desc A",
                path_qris="qrisA.png",
                stok=9
            )
        )
        # For produk 3: new qty 5 => stock -5 (20-5 = 15)
        mock_produk_update_produk.assert_any_call(
            3,
            ProdukCreationRequest(
                nama_barang="Produk C",
                harga=1000,
                lokasi="Rak 3",
                deskripsi_suara_lokasi="Desc C",
                path_qris="qrisC.png",
                stok=15
            )
        )
        # For produk 2 (deleted): old qty 1 => stock +1 (5+1 = 6)
        mock_produk_update_produk.assert_any_call(
            2,
            ProdukCreationRequest(
                nama_barang="Produk B",
                harga=7500,
                lokasi="Rak 2",
                deskripsi_suara_lokasi="Desc B",
                path_qris="qrisB.png",
                stok=6
            )
        )
        assert mock_produk_update_produk.call_count == 3

        assert result.transaction.id == 1
        assert len(result.detail_transactions) == 2
        assert result.detail_transactions[0].produk_id == 1
        assert result.detail_transactions[0].qty == 3
        assert result.detail_transactions[1].produk_id == 3
        assert result.detail_transactions[1].qty == 5 

    @patch("app.mcp_sample.transaction.DetailTransactionService.get_detail_transactions_by_transaction_id")
    @patch(f"{mock_db_module}.delete_detail_transaction_from_db")
    @patch(f"{mock_db_module}.delete_transaction_from_db")
    @patch(f"{mock_produk_module}.ProdukService.get_produk")
    @patch(f"{mock_produk_module}.ProdukService.update_produk")
    def test_delete_transaction_with_details(self,
                                              mock_produk_update_produk,
                                              mock_produk_get_produk,
                                              mock_delete_transaction_from_db,
                                              mock_delete_detail_transaction_from_db,
                                              mock_get_detail_transactions_by_transaction_id):
        # Mock detail transactions associated with the transaction
        mock_detail_transaction1 = DetailTransaction(
            id=101,
            transaction_id=1,
            produk_id=1,
            qty=2,
            harga_per_produk=5000,
            total_harga_produk=10000
        )
        mock_detail_transaction2 = DetailTransaction(
            id=102,
            transaction_id=1,
            produk_id=2,
            qty=1,
            harga_per_produk=7500,
            total_harga_produk=7500
        )
        mock_get_detail_transactions_by_transaction_id.return_value = [
            mock_detail_transaction1, mock_detail_transaction2
        ]

        # Mock product data for replenishment
        mock_produk1 = MagicMock(id=1, nama_barang="Produk A", harga=5000, lokasi="Rak 1", deskripsi_suara_lokasi="Desc A", path_qris="qrisA.png", stok=10)
        mock_produk2 = MagicMock(id=2, nama_barang="Produk B", harga=7500, lokasi="Rak 2", deskripsi_suara_lokasi="Desc B", path_qris="qrisB.png", stok=5)
        mock_produk_get_produk.side_effect = [mock_produk1, mock_produk2]

        # Mock successful deletion of main transaction
        mock_delete_transaction_from_db.return_value = True
        mock_delete_detail_transaction_from_db.return_value = True

        result = TransactionService.delete_transaction_with_details(1)

        mock_get_detail_transactions_by_transaction_id.assert_called_once_with(1)

        # Assert detail transactions are deleted
        assert mock_delete_detail_transaction_from_db.call_count == 2
        mock_delete_detail_transaction_from_db.assert_any_call(101)
        mock_delete_detail_transaction_from_db.assert_any_call(102)

        # Assert product stock replenishment
        assert mock_produk_get_produk.call_count == 2
        mock_produk_update_produk.assert_any_call(
            1,
            ProdukCreationRequest(
                nama_barang="Produk A",
                harga=5000,
                lokasi="Rak 1",
                deskripsi_suara_lokasi="Desc A",
                path_qris="qrisA.png",
                stok=12 # 10 + 2
            )
        )
        mock_produk_update_produk.assert_any_call(
            2,
            ProdukCreationRequest(
                nama_barang="Produk B",
                harga=7500,
                lokasi="Rak 2",
                deskripsi_suara_lokasi="Desc B",
                path_qris="qrisB.png",
                stok=6 # 5 + 1
            )
        )

        # Assert main transaction is deleted
        mock_delete_transaction_from_db.assert_called_once_with(1)
        assert result is True 

    def test_to_json_report_with_details(self):
        transaction = Transaction(
            id=1,
            tanggal_transaksi="2023-01-01",
            total_harga_transaksi=10000,
            status="pending",
            metode_pembayaran="cash",
            catatan="Test transaction"
        )
        detail_transactions = [
            DetailTransaction(
                id=101,
                transaction_id=1,
                produk_id=1,
                qty=2,
                harga_per_produk=5000,
                total_harga_produk=10000
            ),
            DetailTransaction(
                id=102,
                transaction_id=1,
                produk_id=2,
                qty=1,
                harga_per_produk=7500,
                total_harga_produk=7500
            )
        ]
        transaction_with_details = TransactionWithDetails(
            transaction=transaction,
            detail_transactions=detail_transactions
        )
        
        result = TransactionService.to_json_report_with_details(transaction_with_details)
        
        expected_json = json.dumps({
            "transaction": {
                "id": 1,
                "tanggal_transaksi": "2023-01-01",
                "total_harga_transaksi": 10000,
                "status": "pending",
                "metode_pembayaran": "cash",
                "catatan": "Test transaction"
            },
            "detail_transactions": [
                {
                    "id": 101,
                    "transaction_id": 1,
                    "produk_id": 1,
                    "qty": 2,
                    "harga_per_produk": 5000,
                    "total_harga_produk": 10000
                },
                {
                    "id": 102,
                    "transaction_id": 1,
                    "produk_id": 2,
                    "qty": 1,
                    "harga_per_produk": 7500,
                    "total_harga_produk": 7500
                }
            ]
        })
        assert result == expected_json 

class TestDetailTransactionService:
    @patch(f"{mock_db_module}.get_detail_transaction_from_db")
    def test_get_detail_transaction(self, mock_get_detail_transaction_from_db):
        mock_get_detail_transaction_from_db.return_value = {
            "id": 101,
            "transaction_id": 1,
            "produk_id": 1,
            "qty": 2,
            "harga_per_produk": 5000,
            "total_harga_produk": 10000
        }
        
        result = DetailTransactionService.get_detail_transaction(101)
        
        mock_get_detail_transaction_from_db.assert_called_once_with(101)
        assert result.id == 101
        assert result.transaction_id == 1

    @patch(f"{mock_db_module}.get_detail_transaction_from_db")
    def test_get_detail_transaction_not_found(self, mock_get_detail_transaction_from_db):
        mock_get_detail_transaction_from_db.return_value = None
        
        with pytest.raises(ValueError, match="DetailTransaction with id 999 not found"):
            DetailTransactionService.get_detail_transaction(999)
        
        mock_get_detail_transaction_from_db.assert_called_once_with(999) 

    @patch(f"{mock_db_module}.get_all_detail_transactions_from_db")
    def test_get_all_detail_transactions(self, mock_get_all_detail_transactions_from_db):
        mock_get_all_detail_transactions_from_db.return_value = [
            {
                "id": 101,
                "transaction_id": 1,
                "produk_id": 1,
                "qty": 2,
                "harga_per_produk": 5000,
                "total_harga_produk": 10000
            },
            {
                "id": 102,
                "transaction_id": 1,
                "produk_id": 2,
                "qty": 1,
                "harga_per_produk": 7500,
                "total_harga_produk": 7500
            }
        ]
        
        result = DetailTransactionService.get_all_detail_transactions()
        
        mock_get_all_detail_transactions_from_db.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 101
        assert result[1].id == 102 

    @patch(f"{mock_db_module}.get_detail_transactions_by_transaction_id")
    def test_get_detail_transactions_by_transaction_id(self, mock_get_detail_transactions_by_transaction_id):
        mock_get_detail_transactions_by_transaction_id.return_value = [
            {
                "id": 101,
                "transaction_id": 1,
                "produk_id": 1,
                "qty": 2,
                "harga_per_produk": 5000,
                "total_harga_produk": 10000
            }
        ]
        
        result = DetailTransactionService.get_detail_transactions_by_transaction_id(1)
        
        mock_get_detail_transactions_by_transaction_id.assert_called_once_with(1)
        assert len(result) == 1
        assert result[0].transaction_id == 1

    def test_to_json_report(self):
        detail_transaction = DetailTransaction(
            id=101,
            transaction_id=1,
            produk_id=1,
            qty=2,
            harga_per_produk=5000,
            total_harga_produk=10000
        )
        
        result = DetailTransactionService.to_json_report(detail_transaction)
        
        expected_json = json.dumps({
            "id": 101,
            "transaction_id": 1,
            "produk_id": 1,
            "qty": 2,
            "harga_per_produk": 5000,
            "total_harga_produk": 10000
        })
        assert result == expected_json 