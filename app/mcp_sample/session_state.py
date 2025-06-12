from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from enum import Enum
from setup_logs import setup_logger

logger = setup_logger("session_state", log_filename="warung.log")

class SessionStatus(str, Enum):
    """Status sesi transaksi"""
    IDLE = "idle"  # Tidak ada transaksi aktif
    COLLECTING_ITEMS = "collecting_items"  # Sedang mengumpulkan item
    WAITING_QUANTITY = "waiting_quantity"  # Menunggu input kuantitas
    WAITING_PAYMENT = "waiting_payment"  # Menunggu pilihan pembayaran
    PROCESSING_PAYMENT = "processing_payment"  # Memproses pembayaran
    COMPLETED = "completed"  # Transaksi selesai

class ItemPesanan(BaseModel):
    """Model untuk item dalam pesanan sementara"""
    produk_id: int
    nama_barang: str
    kuantitas: int
    harga_satuan: int
    subtotal: int
    lokasi: Optional[str] = None

class ProdukKonteks(BaseModel):
    """Model untuk produk yang sedang dalam konteks"""
    produk_id_db: int
    nama_barang_db: str
    harga_db: int
    stok_db: int
    lokasi: Optional[str] = None

class SessionState(BaseModel):
    """Model untuk state management sesi chatbot"""
    session_id: str = Field(..., description="Unique identifier untuk sesi")
    status: SessionStatus = Field(default=SessionStatus.IDLE)
    
    # Variabel transaksi
    metode_bayar: Optional[str] = None
    current_transaction_id: Optional[int] = None
    tanggal_transaksi_saat_ini: Optional[str] = None
    
    # Item pesanan sementara
    daftar_item_pesanan_sementara: List[ItemPesanan] = Field(default_factory=list)
    
    # Produk konteks saat ini
    produk_konteks_saat_ini: Optional[ProdukKonteks] = None
    
    # Metadata tambahan
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_user_message: Optional[str] = None
    conversation_step: Optional[str] = None  # Untuk tracking langkah dalam alur
    
    class Config:
        use_enum_values = True
    
    def update_timestamp(self):
        """Update timestamp saat state berubah"""
        self.updated_at = datetime.now()
    
    def add_item_to_order(self, item: ItemPesanan):
        """Tambah item ke daftar pesanan sementara"""
        self.daftar_item_pesanan_sementara.append(item)
        self.update_timestamp()
        logger.info(f"Added item to order: {item.nama_barang} x{item.kuantitas}")
    
    def clear_product_context(self):
        """Kosongkan konteks produk saat ini"""
        self.produk_konteks_saat_ini = None
        self.update_timestamp()
    
    def set_product_context(self, produk_konteks: ProdukKonteks):
        """Set konteks produk saat ini"""
        self.produk_konteks_saat_ini = produk_konteks
        self.update_timestamp()
    
    def clear_order_items(self):
        """Kosongkan daftar item pesanan sementara"""
        self.daftar_item_pesanan_sementara = []
        self.update_timestamp()
    
    def reset_session(self):
        """Reset sesi ke kondisi awal"""
        self.status = SessionStatus.IDLE
        self.metode_bayar = None
        self.current_transaction_id = None
        self.tanggal_transaksi_saat_ini = None
        self.daftar_item_pesanan_sementara = []
        self.produk_konteks_saat_ini = None
        self.conversation_step = None
        self.update_timestamp()
        logger.info(f"Session {self.session_id} reset to initial state")
    
    def get_total_items(self) -> int:
        """Hitung total item dalam pesanan"""
        return len(self.daftar_item_pesanan_sementara)
    
    def get_total_amount(self) -> int:
        """Hitung total harga pesanan sementara"""
        return sum(item.subtotal for item in self.daftar_item_pesanan_sementara)
    
    def to_dict(self) -> dict:
        """Convert ke dictionary untuk penyimpanan"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create instance dari dictionary"""
        return cls(**data)

# Storage untuk session states (in-memory untuk demo, bisa diganti dengan Redis/DB)
class SessionStateManager:
    """Manager untuk mengelola session states"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        logger.info("SessionStateManager initialized")
    
    def create_session(self, session_id: str) -> SessionState:
        """Buat sesi baru"""
        if session_id in self._sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self._sessions[session_id]
        
        session = SessionState(session_id=session_id)
        self._sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Ambil sesi berdasarkan ID"""
        session = self._sessions.get(session_id)
        if session:
            logger.info(f"Retrieved session: {session_id}")
        else:
            logger.warning(f"Session not found: {session_id}")
        return session
    
    def update_session(self, session_id: str, session_state: SessionState) -> bool:
        """Update sesi"""
        if session_id not in self._sessions:
            logger.error(f"Cannot update non-existent session: {session_id}")
            return False
        
        session_state.update_timestamp()
        self._sessions[session_id] = session_state
        logger.info(f"Updated session: {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Hapus sesi"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        logger.warning(f"Cannot delete non-existent session: {session_id}")
        return False
    
    def list_sessions(self) -> List[str]:
        """List semua session IDs"""
        return list(self._sessions.keys())
    
    def get_session_count(self) -> int:
        """Hitung jumlah sesi aktif"""
        return len(self._sessions)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Bersihkan sesi lama"""
        current_time = datetime.now()
        sessions_to_delete = []
        
        for session_id, session in self._sessions.items():
            age = current_time - session.updated_at
            if age.total_seconds() > (max_age_hours * 3600):
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_delete)} old sessions")
        return len(sessions_to_delete)

# Global instance (singleton pattern)
session_manager = SessionStateManager()