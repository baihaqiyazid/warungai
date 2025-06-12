from mcp.server.fastmcp import FastMCP
from session_state import (
    SessionState, SessionStateManager, SessionStatus, 
    ItemPesanan, ProdukKonteks, session_manager
)
from typing import List, Optional, Dict, Any
import json
from setup_logs import setup_logger

logger = setup_logger("session_server", log_filename="warung.log")
logger.info("========================== session_server Starting ==============================")

mcp = FastMCP("session_server")

@mcp.tool()
async def create_session(session_id: str) -> str:
    """Buat sesi baru untuk chatbot
    
    Args:
        session_id: Unique identifier untuk sesi (misal: user_id atau conversation_id)
    """
    logger.info(f"create_session called with session_id={session_id}")
    session = session_manager.create_session(session_id)
    result = session.model_dump_json()
    logger.info(f"create_session success: {result}")
    return result

@mcp.tool()
async def get_session(session_id: str) -> Optional[str]:
    """Ambil state sesi saat ini
    
    Args:
        session_id: ID sesi yang ingin diambil
    """
    logger.info(f"get_session called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if session:
        result = session.model_dump_json()
        logger.info(f"get_session success: {result}")
        return result
    logger.info("get_session success: None")
    return None

@mcp.tool()
async def update_session_status(session_id: str, status: str) -> bool:
    """Update status sesi
    
    Args:
        session_id: ID sesi
        status: Status baru (idle, collecting_items, waiting_quantity, waiting_payment, processing_payment, completed)
    """
    logger.info(f"update_session_status called with session_id={session_id}, status={status}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    try:
        session.status = SessionStatus(status)
        session.conversation_step = f"Status changed to {status}"
        result = session_manager.update_session(session_id, session)
        logger.info(f"update_session_status success: {result}")
        return result
    except ValueError as e:
        logger.error(f"Invalid status value: {status}, error: {e}")
        return False

@mcp.tool()
async def set_payment_method(session_id: str, method: str) -> bool:
    """Set metode pembayaran
    
    Args:
        session_id: ID sesi
        method: Metode pembayaran (Cash, QRIS, atau None untuk reset)
    """
    logger.info(f"set_payment_method called with session_id={session_id}, method={method}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    session.metode_bayar = method if method.lower() != "none" else None
    result = session_manager.update_session(session_id, session)
    logger.info(f"set_payment_method success: {result}")
    return result

@mcp.tool()
async def set_transaction_id(session_id: str, transaction_id: int, tanggal_transaksi: str) -> bool:
    """Set ID transaksi dan tanggal
    
    Args:
        session_id: ID sesi
        transaction_id: ID transaksi dari database
        tanggal_transaksi: Tanggal transaksi dalam format string
    """
    logger.info(f"set_transaction_id called with session_id={session_id}, transaction_id={transaction_id}, tanggal_transaksi={tanggal_transaksi}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    session.current_transaction_id = transaction_id
    session.tanggal_transaksi_saat_ini = tanggal_transaksi
    result = session_manager.update_session(session_id, session)
    logger.info(f"set_transaction_id success: {result}")
    return result

@mcp.tool()
async def add_item_to_order(
    session_id: str,
    produk_id: int,
    nama_barang: str,
    kuantitas: int,
    harga_satuan: int,
    lokasi: Optional[str] = None
) -> bool:
    """Tambah item ke pesanan sementara
    
    Args:
        session_id: ID sesi
        produk_id: ID produk
        nama_barang: Nama barang
        kuantitas: Jumlah barang
        harga_satuan: Harga per unit
        lokasi: Lokasi barang (opsional)
    """
    logger.info(f"add_item_to_order called with session_id={session_id}, produk_id={produk_id}, nama_barang={nama_barang}, kuantitas={kuantitas}, harga_satuan={harga_satuan}, lokasi={lokasi}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    subtotal = kuantitas * harga_satuan
    item = ItemPesanan(
        produk_id=produk_id,
        nama_barang=nama_barang,
        kuantitas=kuantitas,
        harga_satuan=harga_satuan,
        subtotal=subtotal,
        lokasi=lokasi
    )
    
    session.add_item_to_order(item)
    result = session_manager.update_session(session_id, session)
    logger.info(f"add_item_to_order success: {result}")
    return result

@mcp.tool()
async def get_order_items(session_id: str) -> Optional[str]:
    """Ambil daftar item dalam pesanan sementara
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"get_order_items called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return None
    
    items_data = [item.model_dump() for item in session.daftar_item_pesanan_sementara]
    result = json.dumps(items_data)
    logger.info(f"get_order_items success: {result}")
    return result

@mcp.tool()
async def clear_order_items(session_id: str) -> bool:
    """Kosongkan daftar item pesanan sementara
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"clear_order_items called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    session.clear_order_items()
    result = session_manager.update_session(session_id, session)
    logger.info(f"clear_order_items success: {result}")
    return result

@mcp.tool()
async def set_product_context(
    session_id: str,
    produk_id_db: int,
    nama_barang_db: str,
    harga_db: int,
    stok_db: int,
    lokasi: Optional[str] = None
) -> bool:
    """Set konteks produk yang sedang diproses
    
    Args:
        session_id: ID sesi
        produk_id_db: ID produk di database
        nama_barang_db: Nama barang dari database
        harga_db: Harga dari database
        stok_db: Stok dari database
        lokasi: Lokasi barang (opsional)
    """
    logger.info(f"set_product_context called with session_id={session_id}, produk_id_db={produk_id_db}, nama_barang_db={nama_barang_db}, harga_db={harga_db}, stok_db={stok_db}, lokasi={lokasi}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    konteks = ProdukKonteks(
        produk_id_db=produk_id_db,
        nama_barang_db=nama_barang_db,
        harga_db=harga_db,
        stok_db=stok_db,
        lokasi=lokasi
    )
    
    session.set_product_context(konteks)
    result = session_manager.update_session(session_id, session)
    logger.info(f"set_product_context success: {result}")
    return result

@mcp.tool()
async def get_product_context(session_id: str) -> Optional[str]:
    """Ambil konteks produk yang sedang diproses
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"get_product_context called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return None
    
    if session.produk_konteks_saat_ini:
        result = session.produk_konteks_saat_ini.model_dump_json()
        logger.info(f"get_product_context success: {result}")
        return result
    
    logger.info("get_product_context success: None")
    return None

@mcp.tool()
async def clear_product_context(session_id: str) -> bool:
    """Kosongkan konteks produk
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"clear_product_context called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    session.clear_product_context()
    result = session_manager.update_session(session_id, session)
    logger.info(f"clear_product_context success: {result}")
    return result

@mcp.tool()
async def reset_session(session_id: str) -> bool:
    """Reset sesi ke kondisi awal
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"reset_session called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return False
    
    session.reset_session()
    result = session_manager.update_session(session_id, session)
    logger.info(f"reset_session success: {result}")
    return result

@mcp.tool()
async def get_session_summary(session_id: str) -> Optional[str]:
    """Ambil ringkasan sesi untuk debugging
    
    Args:
        session_id: ID sesi
    """
    logger.info(f"get_session_summary called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return None
    
    summary = {
        "session_id": session.session_id,
        "status": session.status,
        "total_items": session.get_total_items(),
        "total_amount": session.get_total_amount(),
        "has_product_context": session.produk_konteks_saat_ini is not None,
        "current_transaction_id": session.current_transaction_id,
        "payment_method": session.metode_bayar,
        "conversation_step": session.conversation_step,
        "updated_at": session.updated_at.isoformat()
    }
    
    result = json.dumps(summary)
    logger.info(f"get_session_summary success: {result}")
    return result

@mcp.tool()
async def list_all_sessions() -> str:
    """List semua sesi aktif (untuk debugging)"""
    logger.info("list_all_sessions called")
    sessions = session_manager.list_sessions()
    count = session_manager.get_session_count()
    
    result = json.dumps({
        "active_sessions": sessions,
        "total_count": count
    })
    logger.info(f"list_all_sessions success: {result}")
    return result

@mcp.tool()
async def cleanup_old_sessions(max_age_hours: int = 24) -> int:
    """Cleanup sesi lama
    
    Args:
        max_age_hours: Maksimal umur sesi dalam jam (default: 24)
    """
    logger.info(f"cleanup_old_sessions called with max_age_hours={max_age_hours}")
    cleaned_count = session_manager.cleanup_old_sessions(max_age_hours)
    logger.info(f"cleanup_old_sessions success: {cleaned_count}")
    return cleaned_count

@mcp.resource("session://session_server/state/{session_id}")
async def read_session_resource(session_id: str) -> Optional[str]:
    """Resource untuk mengakses session state"""
    logger.info(f"read_session_resource called with session_id={session_id}")
    session = session_manager.get_session(session_id)
    if session:
        result = session.model_dump_json()
        logger.info(f"read_session_resource success: {result}")
        return result
    logger.info("read_session_resource success: None")
    return None

@mcp.resource("session://session_server/all_sessions")
async def read_all_sessions_resource() -> str:
    """Resource untuk mengakses semua session"""
    logger.info("read_all_sessions_resource called")
    sessions = session_manager.list_sessions()
    count = session_manager.get_session_count()
    
    result = json.dumps({
        "active_sessions": sessions,
        "total_count": count
    })
    logger.info(f"read_all_sessions_resource success: {result}")
    return result

if __name__ == "__main__":
    mcp.run(transport='stdio')