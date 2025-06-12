# LLMChatbotWarung.ipynb

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, TypedDict
from uuid import uuid4

import gradio as gr
from dotenv import load_dotenv

# Langchain & LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver # Untuk menyimpan state percakapan
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool, Tool
from langchain_openai import ChatOpenAI

# Untuk menjalankan asyncio di Jupyter
import nest_asyncio
nest_asyncio.apply()

# Muat environment variables (untuk OPENAI_API_KEY)
load_dotenv()

# Pastikan OPENAI_API_KEY tersedia
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY tidak ditemukan. Silakan atur di file .env atau sebagai environment variable.")

print("Pustaka dan setup awal selesai.")

# Sel 3: Inisialisasi Database dan Klien MCP
# (Menggunakan fungsi dari file .py yang sudah ada)
print(os.getcwd())
# Fungsi Inisialisasi Database (langsung dari file database)
from app.mcp_sample.produk_database import init_db as init_produk_db, DATABASE_NAME as PRODUK_DB_PATH
from app.mcp_sample.transaction_database import init_db as init_transaction_db, DATABASE_NAME as TRANSACTION_DB_PATH

# Pastikan direktori database ada
os.makedirs(os.path.join("src", "data"), exist_ok=True)

print(f"Path DB Produk: {os.path.abspath(PRODUK_DB_PATH)}")
print(f"Path DB Transaksi: {os.path.abspath(TRANSACTION_DB_PATH)}")

try:
    init_produk_db()
    init_transaction_db()
    print("Database produk dan transaksi berhasil diinisialisasi.")
except Exception as e:
    print(f"Error saat inisialisasi database: {e}")
    print("Pastikan server MCP tidak berjalan jika error terkait 'database is locked'.")
    print("Atau jalankan notebook ini tanpa sel yang menjalankan server MCP secara otomatis jika perlu.")

# Klien MCP (impor fungsi yang sudah ada dan buat wrapper jika perlu)
# Diasumsikan produk_client.py dan transaction_client.py ada di PWD
from app.mcp_sample import produk_client, transaction_client

# Wrapper untuk konsistensi return value dari call_produk_tool
async def call_produk_tool_wrapper(tool_name: str, tool_args: Dict[str, Any]) -> Optional[str]:
    print(f"Memanggil produk_tool: {tool_name} dengan args: {tool_args}")
    tool_result = await produk_client.call_produk_tool(tool_name, tool_args) # Assumes this is imported

    if tool_result.isError:
        error_message = f"Tool call '{tool_name}' failed."
        if tool_result.content and len(tool_result.content) > 0 and hasattr(tool_result.content[0], 'text') and tool_result.content[0].text:
            error_message += f" Details: {tool_result.content[0].text}"
        print(error_message)
        return json.dumps({"error": error_message})

    if tool_result.content:
        if tool_name == "list_all_produk":
            # Assuming tool_result.content is a list of ContentPart objects,
            # and each part.text is a JSON string of a product.
            # We want to return a JSON string that is an array of these product JSON strings.
            product_json_strings = [
                part.text for part in tool_result.content if hasattr(part, 'text') and part.text
            ]
            return json.dumps(product_json_strings) # e.g., "[ \"{\\\"id\\\":1,...}\", \"{\\\"id\\\":2,...}\" ]"
        elif len(tool_result.content) > 0 and hasattr(tool_result.content[0], 'text') and tool_result.content[0].text is not None:
            # For other tools expected to return a single string
            return tool_result.content[0].text
        else:
            msg = f"Tool call '{tool_name}' returned content but not in expected format. Result: {tool_result}"
            print(msg)
            return json.dumps({"error": msg, "details": str(tool_result)})
    else:
        msg = f"Tool call '{tool_name}' tidak mengembalikan konten teks yang valid. Result: {tool_result}"
        print(msg)
        return json.dumps({"error": msg, "details": str(tool_result)})


async def call_transaction_tool_wrapper(tool_name: str, tool_args: Dict[str, Any]) -> Optional[str]:
    print(f"Memanggil transaction_tool: {tool_name} dengan args: {tool_args}")
    # transaction_client.call_transaction_tool sudah mengembalikan string atau memunculkan Exception
    try:
        result_str = await transaction_client.call_transaction_tool(tool_name, tool_args)
        return result_str
    except Exception as e:
        error_message = f"Tool call '{tool_name}' gagal dengan exception: {str(e)}"
        print(error_message)
        return json.dumps({"error": error_message})


print("Klien MCP siap.")

# Sel 4: Definisi Tools untuk LangGraph Agent (Tools yang Lebih Cerdas)

# --- Product Tools ---
@tool
async def get_product_details(product_id: Optional[int] = None, product_name: Optional[str] = None) -> str:
    """
    Mencari detail produk berdasarkan ID atau nama produk.
    Jika menggunakan nama, akan mengembalikan produk pertama yang cocok (case-insensitive).
    """
    if product_id:
        # This part seems to work fine, assuming get_produk returns a single JSON string
        result_str = await call_produk_tool_wrapper("get_produk", {"produk_id": product_id})
        return result_str
    elif product_name:
        # This is the part that needs adjustment based on the corrected wrapper
        all_products_wrapper_output_str = await call_produk_tool_wrapper("list_all_produk", {})
        try:
            # all_products_wrapper_output_str should now be a JSON string like:
            # "[ \"{\\\"id\\\":1,...}\", \"{\\\"id\\\":2,...}\" ]"
            list_of_product_json_strings = json.loads(all_products_wrapper_output_str)
            
            if isinstance(list_of_product_json_strings, dict) and "error" in list_of_product_json_strings:
                 return all_products_wrapper_output_str # Propagate error

            all_products = []
            for p_str in list_of_product_json_strings:
                try:
                    all_products.append(json.loads(p_str))
                except json.JSONDecodeError:
                    print(f"Peringatan: String produk tidak valid JSON diabaikan: {p_str}")
                    continue # Abaikan string yang tidak bisa di-parse

            for p in all_products:
                if isinstance(p, dict) and product_name.lower() in p.get('nama_barang', '').lower():
                    return json.dumps(p) # Kembalikan produk pertama yang cocok (sebagai JSON string)
            return json.dumps({"error": f"Produk dengan nama '{product_name}' tidak ditemukan."})
        except Exception as e:
            return json.dumps({"error": f"Gagal memproses daftar produk: {str(e)}", "raw_response": all_products_wrapper_output_str})
    return json.dumps({"error": "Harus menyediakan product_id atau product_name."})

@tool
async def list_available_products() -> str:
    """Mendaftar semua produk yang tersedia."""
    return await call_produk_tool_wrapper("list_all_produk", {})

# --- Transaction Tools (dengan logika kelengkapan) ---
@tool
async def create_new_order(items: List[Dict[str, Any]], tanggal_transaksi: str, metode_pembayaran: str, catatan: Optional[str] = None) -> str:
    """
    Membuat pesanan baru. 'items' adalah list dari dictionary, masing-masing berisi 'product_id' dan 'quantity'.
    Contoh items: [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]
    Fungsi ini akan membuat header transaksi, detail transaksi untuk setiap item,
    dan mengurangi stok produk yang sesuai. Total harga akan dihitung otomatis.
    """
    print(f"Membuat pesanan baru dengan items: {items}")
    # 1. Buat Transaction Header awal
    header_data = {
        "tanggal_transaksi": tanggal_transaksi,
        "total_harga_transaksi": 0, # Akan diupdate nanti
        "status": "pending",
        "metode_pembayaran": metode_pembayaran,
        "catatan": catatan or "Pesanan baru dari chatbot"
    }
    header_str = await call_transaction_tool_wrapper("create_transaction", header_data)
    try:
        header = json.loads(header_str)
        if "error" in header: return header_str
    except Exception as e:
        return json.dumps({"error": f"Gagal membuat header transaksi: {str(e)}", "raw_response": header_str})

    transaction_id = header['id']
    grand_total = 0
    created_details = []
    stock_update_errors = []

    # 2. Proses setiap item: buat detail transaksi & update stok
    for item in items:
        product_id = item['product_id']
        quantity_to_buy = item['quantity']

        # Ambil info produk (harga, stok saat ini)
        product_info_str = await get_product_details.ainvoke({"product_id": product_id})
        try:
            product_info = json.loads(product_info_str)
            if "error" in product_info:
                stock_update_errors.append(f"Produk ID {product_id}: {product_info['error']}")
                continue # Lanjut ke item berikutnya jika produk tidak ditemukan
        except Exception as e:
            stock_update_errors.append(f"Produk ID {product_id}: Gagal parse info produk - {str(e)}")
            continue
        
        current_stock = product_info.get('stok', 0)
        price_per_unit = product_info.get('harga', 0)

        if quantity_to_buy <= 0:
            stock_update_errors.append(f"Produk ID {product_id}: Kuantitas harus lebih dari 0.")
            continue

        if current_stock < quantity_to_buy:
            stock_update_errors.append(f"Produk ID {product_id} ({product_info.get('nama_barang','N/A')}): Stok tidak cukup ({current_stock} tersedia, {quantity_to_buy} diminta).")
            continue # Stok tidak cukup

        # Buat detail transaksi
        total_harga_produk_item = price_per_unit * quantity_to_buy
        detail_data = {
            "transaction_id": transaction_id,
            "produk_id": product_id,
            "qty": quantity_to_buy,
            "harga_per_produk": price_per_unit,
            "total_harga_produk": total_harga_produk_item
        }
        detail_str = await call_transaction_tool_wrapper("create_detail_transaction", detail_data)
        try:
            detail = json.loads(detail_str)
            if "error" in detail:
                stock_update_errors.append(f"Produk ID {product_id}: Gagal buat detail - {detail['error']}")
                continue
            created_details.append(detail)
            grand_total += total_harga_produk_item
        except Exception as e:
            stock_update_errors.append(f"Produk ID {product_id}: Gagal parse detail - {str(e)}")
            continue

        # Update stok produk
        new_stock = current_stock - quantity_to_buy
        update_stock_data = {
            "produk_id": product_id,
            "nama_barang": product_info['nama_barang'], # Perlu field ini dari get_produk
            "harga": product_info['harga'],
            "stok": new_stock,
            "lokasi": product_info.get('lokasi'),
            "deskripsi_suara_lokasi": product_info.get('deskripsi_suara_lokasi'),
            "path_qris": product_info.get('path_qris')
        }
        update_stock_str = await call_produk_tool_wrapper("update_produk", update_stock_data)
        try:
            update_stock_res = json.loads(update_stock_str)
            if "error" in update_stock_res:
                stock_update_errors.append(f"Produk ID {product_id}: Gagal update stok - {update_stock_res['error']}")
                # Pertimbangkan rollback detail yang sudah dibuat jika update stok gagal? Untuk sekarang, kita catat errornya.
        except Exception as e:
             stock_update_errors.append(f"Produk ID {product_id}: Gagal parse update stok - {str(e)}")


    # 3. Update Transaction Header dengan total harga final dan status
    if not created_details and stock_update_errors: # Tidak ada item yang berhasil diproses
        # Hapus header transaksi yang kosong
        await call_transaction_tool_wrapper("delete_transaction", {"transaction_id": transaction_id})
        return json.dumps({
            "error": "Gagal memproses semua item dalam pesanan.",
            "item_errors": stock_update_errors
        })

    final_header_data = {
        "transaction_id": transaction_id,
        "tanggal_transaksi": header_data["tanggal_transaksi"],
        "total_harga_transaksi": grand_total,
        "status": "success" if not stock_update_errors else "partial_success",
        "metode_pembayaran": header_data["metode_pembayaran"],
        "catatan": (header_data["catatan"] or "") + (f" | Item errors: {len(stock_update_errors)}" if stock_update_errors else "")
    }
    updated_header_str = await call_transaction_tool_wrapper("update_transaction", final_header_data)
    
    return json.dumps({
        "message": "Pesanan berhasil dibuat." if not stock_update_errors else "Pesanan dibuat dengan beberapa masalah pada item.",
        "transaction_header": json.loads(updated_header_str),
        "created_details_count": len(created_details),
        "item_processing_errors": stock_update_errors if stock_update_errors else None
    })


@tool
async def get_order_details(transaction_id: int) -> str:
    """Mendapatkan detail pesanan/transaksi berdasarkan ID transaksi, termasuk item-itemnya."""
    header_str = await call_transaction_tool_wrapper("get_transaction", {"transaction_id": transaction_id})
    try:
        header = json.loads(header_str)
        if "error" in header: return header_str
    except Exception as e:
        return json.dumps({"error": f"Gagal mendapatkan header transaksi: {str(e)}", "raw_response": header_str})

    # Ambil semua detail, lalu filter. Ini kurang efisien tapi sesuai tool MCP yang ada.
    # Jika ada `get_detail_transaction_by_transaction_id` di MCP akan lebih baik.
    # Untuk sekarang, kita asumsikan `get_all_detail_transactions` mengembalikan semua, dan kita filter.
    # Bug: `get_all_detail_transactions` di server belum tentu ada, atau mungkin `get_all_detail_transactions_from_db`
    # Untuk demo, kita hanya kembalikan header. Idealnya, ambil detail juga.
    # Mari kita coba get_all_detail_transactions, jika gagal, hanya header.
    all_details_str = await call_transaction_tool_wrapper("get_all_detail_transactions", {})
    order_details = []
    try:
        all_details_list_str = json.loads(all_details_str)
        all_details = [json.loads(d_str) for d_str in all_details_list_str]
        for detail in all_details:
            if detail.get("transaction_id") == transaction_id:
                order_details.append(detail)
    except Exception: # Jika gagal mengambil atau memproses detail
        pass # Biarkan order_details kosong, info header tetap ada

    return json.dumps({
        "transaction_header": header,
        "transaction_details": order_details if order_details else "Tidak dapat mengambil detail item atau tidak ada detail."
    })


@tool
async def cancel_order(transaction_id: int) -> str:
    """
    Membatalkan pesanan berdasarkan ID transaksi.
    Ini akan menghapus detail transaksi terkait dan mengembalikan stok produk.
    """
    print(f"Membatalkan pesanan ID: {transaction_id}")
    # 1. Dapatkan header untuk verifikasi (opsional, tapi baik untuk status check)
    header_check_str = await call_transaction_tool_wrapper("get_transaction", {"transaction_id": transaction_id})
    try:
        header_check = json.loads(header_check_str)
        if "error" in header_check:
            return json.dumps({"error": f"Transaksi ID {transaction_id} tidak ditemukan atau gagal diambil: {header_check['error']}"})
        # Anda bisa menambahkan logika di sini, misal hanya boleh cancel jika status 'pending' atau 'success'
    except Exception as e:
         return json.dumps({"error": f"Error saat verifikasi transaksi ID {transaction_id}: {str(e)}"})


    # 2. Dapatkan semua detail transaksi untuk transaction_id ini
    # Perlu cara untuk mendapatkan detail berdasarkan transaction_id.
    # Jika tidak ada tool MCP spesifik, kita harus get_all dan filter.
    all_details_str = await call_transaction_tool_wrapper("get_all_detail_transactions", {})
    details_to_delete = []
    stock_restore_errors = []
    try:
        all_details_list_str = json.loads(all_details_str)
        all_details_obj_list = [json.loads(d_str) for d_str in all_details_list_str]
        for detail_obj in all_details_obj_list:
            if detail_obj.get("transaction_id") == transaction_id:
                details_to_delete.append(detail_obj)
    except Exception as e:
        return json.dumps({"error": f"Gagal mengambil atau memproses detail transaksi untuk pembatalan: {str(e)}", "raw_response": all_details_str})

    if not details_to_delete:
        print(f"Tidak ada detail transaksi ditemukan untuk transaction_id {transaction_id}. Mungkin sudah dihapus atau tidak ada item.")
    
    # 3. Untuk setiap detail: kembalikan stok & hapus detail
    for detail in details_to_delete:
        detail_id = detail['id']
        product_id = detail['produk_id']
        qty_to_restore = detail['qty']

        # Ambil info produk (stok saat ini)
        product_info_str = await get_product_details(product_id=product_id)
        try:
            product_info = json.loads(product_info_str)
            if "error" in product_info:
                stock_restore_errors.append(f"Produk ID {product_id} (Detail ID {detail_id}): Gagal ambil info produk - {product_info['error']}")
                continue
        except Exception as e:
            stock_restore_errors.append(f"Produk ID {product_id} (Detail ID {detail_id}): Gagal parse info produk - {str(e)}")
            continue

        current_stock = product_info.get('stok', 0)
        new_stock = current_stock + qty_to_restore

        update_stock_data = {
            "produk_id": product_id,
            "nama_barang": product_info['nama_barang'],
            "harga": product_info['harga'],
            "stok": new_stock,
            "lokasi": product_info.get('lokasi')
            # field lain jika perlu
        }
        update_stock_str = await call_produk_tool_wrapper("update_produk", update_stock_data)
        try:
            update_stock_res = json.loads(update_stock_str)
            if "error" in update_stock_res :
                 stock_restore_errors.append(f"Produk ID {product_id} (Detail ID {detail_id}): Gagal update stok - {update_stock_res['error']}")
        except Exception as e:
            stock_restore_errors.append(f"Produk ID {product_id} (Detail ID {detail_id}): Gagal parse update stok - {str(e)}")


        # Hapus detail transaksi
        delete_detail_str = await call_transaction_tool_wrapper("delete_detail_transaction", {"detail_transaction_id": detail_id})
        # Periksa apakah delete_detail_str adalah "true"
        if delete_detail_str.lower() != "true": # MCP tool delete mengembalikan "true" atau "false" sebagai string
             stock_restore_errors.append(f"Detail ID {detail_id}: Gagal menghapus detail - {delete_detail_str}")

    # 4. Hapus Transaction Header
    delete_header_str = await call_transaction_tool_wrapper("delete_transaction", {"transaction_id": transaction_id})
    
    if delete_header_str.lower() == "true":
        return json.dumps({
            "message": f"Pesanan ID {transaction_id} berhasil dibatalkan.",
            "stock_restore_errors": stock_restore_errors if stock_restore_errors else None
        })
    else:
        return json.dumps({
            "error": f"Gagal menghapus header pesanan ID {transaction_id}.",
            "details": delete_header_str,
            "stock_restore_errors": stock_restore_errors if stock_restore_errors else None
        })

# Kumpulkan semua tools
llm_tools = [
    get_product_details,
    list_available_products,
    create_new_order,
    get_order_details,
    cancel_order
]

print(f"Tools untuk LLM Agent ({len(llm_tools)} tools) berhasil didefinisikan.")


# Sel 5: Definisi LangGraph Agent

# Definisikan State untuk Graph
class AgentState(TypedDict):
    messages: List[AnyMessage]

# Inisialisasi LLM (Model OpenAI)
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0) # Ganti dengan gpt-4 atau model lain jika perlu
llm = ChatOpenAI(model="gpt-4o", temperature=0) 


# Bind tools ke LLM agar ia tahu tools apa saja yang tersedia
llm_with_tools = llm.bind_tools(llm_tools)

# Node: Agent (LLM untuk memutuskan tindakan)
def agent_node(state: AgentState):
    print("---AGENT NODE---")
    print(f"Messages so far: {[m.type + ': ' + str(m.content)[:100] for m in state['messages']]}")
    response = llm_with_tools.invoke(state["messages"])
    print(f"LLM Response: {response.type + ': ' + str(response.content)[:100]}")
    return {"messages": [response]}

# Node: Tool Executor (untuk menjalankan tool yang dipanggil LLM)
async def tool_executor_node(state: AgentState):
    print("---TOOL EXECUTOR NODE---")
    tool_message = state["messages"][-1] # Pesan terakhir harus berupa AIMessage dengan tool_calls
    tool_invocations = []

    if not hasattr(tool_message, 'tool_calls') or not tool_message.tool_calls:
        print("Tidak ada tool calls pada pesan terakhir. Mengembalikan state apa adanya.")
        return {"messages": [AIMessage(content="Tidak ada tool yang dipanggil atau tool call tidak valid.")]}

    for tool_call in tool_message.tool_calls:
        tool_name = tool_call["name"]
        # Cari tool yang sesuai dari list llm_tools
        selected_tool = next((t for t in llm_tools if t.name == tool_name), None)
        if not selected_tool:
            tool_invocations.append(
                ToolMessage(content=f"Error: Tool '{tool_name}' tidak ditemukan.", tool_call_id=tool_call["id"])
            )
            continue
        
        try:
            tool_args = tool_call["args"]
            print(f"Executing tool: {tool_name} with args: {tool_args}")
            # Menjalankan tool (yang merupakan fungsi async)
            # Pastikan selected_tool.func adalah callable async
            if asyncio.iscoroutinefunction(selected_tool.func):
                output = await selected_tool.func(**tool_args)
            else: # Jika tool didefinisikan sebagai sync (seharusnya tidak untuk tool kita)
                output = selected_tool.func(**tool_args)
            
            tool_invocations.append(
                ToolMessage(content=str(output), tool_call_id=tool_call["id"])
            )
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            tool_invocations.append(
                ToolMessage(content=f"Error executing tool {tool_name}: {str(e)}", tool_call_id=tool_call["id"])
            )
    print(f"Tool invocation results: {tool_invocations}")
    return {"messages": tool_invocations}

# Conditional Edges: Menentukan alur berikutnya
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"  # Panggil tools jika ada tool_calls
    return END  # Selesai jika tidak ada tool_calls (LLM memberi respons final)

# Membuat Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_executor_node) # tool_executor_node dibuat async

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent") # Setelah tools dijalankan, kembali ke agent untuk memproses hasilnya

# Konfigurasi Checkpoint (untuk menyimpan histori percakapan)
# SqliteSaver memerlukan path ke file database sqlite.
# Jika file tidak ada, akan dibuat.
memory = SqliteSaver.from_conn_string(":memory:") # Simpan di memori untuk demo, atau ganti dengan path file
# memory = SqliteSaver.from_conn_string("langgraph_chatbot_memory.sqlite")


# Kompilasi Graph dengan checkpoint
# app = workflow.compile() # Tanpa memory
app = workflow.compile(checkpointer=memory) # Dengan memory
print("LangGraph App berhasil dikompilasi.")


# Sel 6: Fungsi untuk interaksi dengan Chatbot dan Gradio UI

# System Prompt untuk Chatbot
SYSTEM_PROMPT = """Anda adalah asisten AI untuk Warung Cerdas.
Tugas Anda adalah membantu pelanggan dengan pertanyaan tentang produk, membuat pesanan, memeriksa status pesanan, dan membatalkan pesanan.
Selalu konfirmasi ID produk sebelum membuat atau memodifikasi pesanan jika pengguna menyebutkan nama produk.
Jika Anda perlu mencari produk berdasarkan nama, gunakan tool `get_product_details` dengan argumen `product_name`.
Jika pengguna ingin memesan, pastikan Anda mendapatkan daftar item yang jelas (product_id dan quantity).
Gunakan tool `create_new_order` untuk membuat pesanan.
Format tanggal transaksi adalah YYYY-MM-DD.
Saat membuat pesanan, jika pengguna tidak menyebutkan tanggal atau metode pembayaran, Anda boleh mengasumsikan tanggal hari ini (misal "2025-06-04") dan metode pembayaran "cash".
Berikan respons yang ramah dan informatif.
Jika terjadi error dari tool, sampaikan kepada pengguna dengan cara yang mudah dimengerti dan tawarkan bantuan lebih lanjut.
Jangan membuat informasi jika tidak ada di hasil tool.
"""

# Fungsi untuk menjalankan graph (interaksi dengan chatbot)
async def predict_fn(message: str, history: List[List[str]], thread_id: str):
    print(f"\n--- New Invocation (Thread ID: {thread_id}) ---")
    print(f"User message: {message}")
    print(f"History: {history}")

    # Buat config unik untuk setiap thread_id (sesi percakapan)
    config = {"configurable": {"thread_id": thread_id}}
    
    # Siapkan input messages untuk LangGraph
    current_messages = [HumanMessage(content=message)]
    if not history: # Jika ini pesan pertama, tambahkan system prompt
        current_messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    # Jalankan graph secara streaming untuk mendapatkan respons
    response_content = ""
    async for event in app.astream_events(
        {"messages": current_messages}, config=config, version="v2"
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # print(content, end="") # Cetak token streaming ke konsol
                response_content += content
        elif kind == "on_tool_start":
            print(f"\nTool Start: {event['name']} with input {event['data'].get('input')}")
        elif kind == "on_tool_end":
            print(f"\nTool End: {event['name']} with output {event['data'].get('output')}")
            # Anda bisa menambahkan logika di sini jika ingin menampilkan status tool ke UI
            # response_content += f"\n*Menjalankan tool: {event['name']}... Hasil: {str(event['data'].get('output'))[:100]}...*\n"

    # Jika setelah semua proses, respons_content masih kosong (misal hanya ada tool call)
    # Ambil pesan AI terakhir dari state
    if not response_content:
        final_state = await app.aget_state(config)
        if final_state and final_state.values['messages']:
            last_ai_message = next((m for m in reversed(final_state.values['messages']) if isinstance(m, AIMessage) and not m.tool_calls), None)
            if last_ai_message:
                response_content = last_ai_message.content

    print(f"\nFinal AI response for UI: {response_content}")
    return response_content


# Fungsi wrapper untuk Gradio (menangani state thread_id)
# Gradio tidak secara native menangani state thread_id antar panggilan dalam satu sesi UI.
# Kita akan generate thread_id baru untuk setiap "sesi" Gradio, tapi Gradio ChatInterface
# akan mengelola histori dalam list of lists untuk UI.
# `predict_fn` akan menggunakan thread_id untuk mengambil state yang benar dari SqliteSaver.
# Kita buat thread_id unik untuk setiap kali chatbot di-load/refresh di Gradio.
# Untuk percakapan berkelanjutan dalam satu sesi Gradio, kita butuh cara
# mengelola thread_id yang konsisten atau meneruskannya.
# Cara sederhana: buat thread_id saat UI pertama kali dimuat.
# Gradio's ChatInterface akan mengirimkan seluruh histori chat.

# Kita akan buat satu thread_id per sesi Gradio (saat UI pertama kali dimuat)
# atau per "submit" jika ingin setiap interaksi diisolasi (kurang ideal untuk percakapan).
# Untuk demo ini, satu thread_id saat UI start.
global_thread_id = str(uuid4()) # Thread ID unik untuk sesi Gradio ini

async def gradio_predict_wrapper(message: str, history: List[List[str]]):
    # Gunakan global_thread_id yang dibuat saat notebook/UI dimulai
    # `history` dari Gradio adalah [[user_msg1, ai_msg1], [user_msg2, ai_msg2], ...]
    # `predict_fn` kita sudah menangani pembuatan `HumanMessage` dari `message`
    # dan penambahan `SystemMessage` jika histori kosong.
    # Kita tidak perlu mengubah `current_messages` di sini secara signifikan.
    # predict_fn sudah mengambil `message` dan `history`
    
    # Kita harus memastikan bahwa `predict_fn` menggunakan `history` untuk membangun
    # state pesan yang benar jika LangGraph tidak mengambilnya dari checkpoint untuk UI.
    # Namun, dengan `SqliteSaver` dan `thread_id`, LangGraph *seharusnya* mengelola state.
    # Mari kita coba jalankan `predict_fn` secara langsung.

    # Perlu menjalankan event loop asyncio secara manual jika dipanggil dari konteks sync Gradio
    # (tergantung bagaimana Gradio menjalankan fungsi async)
    # Gradio > 4.0 mendukung fungsi async secara langsung.

    response = await predict_fn(message, history, global_thread_id)
    return response


# Membuat Gradio Chat Interface
# (Pastikan Anda menjalankan ini di sel terakhir atau notebook akan berhenti di sini)
if __name__ == '__main__': # Agar tidak auto-run saat import jika file ini jadi modul
    # Hanya untuk pengujian langsung di notebook.
    # Anda mungkin perlu membungkusnya dengan if __name__ == "__main__": di skrip .py
    # atau menjalankan server Gradio secara manual.

    # Contoh menjalankan fungsi tool secara manual untuk testing
    async def test_tools():
        print("--- Testing Tools ---")
        
        # Test list_available_products
        print("\n[Test] list_available_products:")
        products_str = await list_available_products.ainvoke({})
        print(products_str)
        try:
            products_list = json.loads(products_str) # Ini adalah list of JSON strings
            if products_list and isinstance(products_list, list) and products_list[0]:
                 first_prod = json.loads(products_list[0])
                 print(f"Produk pertama: {first_prod.get('nama_barang')}")
                 global test_product_id
                 test_product_id = first_prod.get('id') # Simpan untuk tes berikutnya
            else:
                print("Tidak ada produk atau format tidak sesuai.")
                # Buat produk jika tidak ada
                created_prod_str = await call_produk_tool_wrapper("create_produk", {"nama_barang": "Produk Tes Otomatis", "harga": 1000, "stok": 10})
                print(f"Membuat produk tes: {created_prod_str}")
                created_prod = json.loads(created_prod_str)
                test_product_id = created_prod.get('id')


        except Exception as e:
            print(f"Error parsing produk: {e}")

        # Test get_product_details by ID (gunakan ID dari tes sebelumnya jika ada)
        if 'test_product_id' in globals() and test_product_id:
            print(f"\n[Test] get_product_details by ID ({test_product_id}):")
            print(await get_product_details.ainvoke({"product_id": test_product_id}))
        
        # Test get_product_details by Name
        print("\n[Test] get_product_details by Name (Produk Tes Otomatis):")
        print(await get_product_details.ainvoke({"product_name": "Produk Tes Otomatis"}))
        
        # Test create_new_order (gunakan ID dari tes sebelumnya jika ada)
        if 'test_product_id' in globals() and test_product_id:
            print("\n[Test] create_new_order:")
            order_items = [{"product_id": test_product_id, "quantity": 1}]
            order_result_str = await create_new_order.ainvoke({
                "items": order_items,
                "tanggal_transaksi": "2025-06-04",
                "metode_pembayaran": "cash"
                # 'catatan' is optional, so it's fine not to include it if you want the default
            })
            print(order_result_str)
            try:
                order_result = json.loads(order_result_str)
                if "transaction_header" in order_result and "id" in order_result["transaction_header"]:
                    global test_transaction_id
                    test_transaction_id = order_result["transaction_header"]["id"]
                    print(f"Order dibuat dengan ID: {test_transaction_id}")
            except Exception as e:
                print(f"Error parsing hasil order: {e}")

        # Test get_order_details (gunakan ID dari tes order sebelumnya jika ada)
        if 'test_transaction_id' in globals() and test_transaction_id:
            print(f"\n[Test] get_order_details ({test_transaction_id}):")
            print(await get_order_details.ainvoke({"transaction_id": test_transaction_id}))

        # Test cancel_order (gunakan ID dari tes order sebelumnya jika ada)
        # if 'test_transaction_id' in globals() and test_transaction_id:
        #     print(f"\n[Test] cancel_order ({test_transaction_id}):")
        #     print(await cancel_order(transaction_id=test_transaction_id))
        #     # Hapus test_transaction_id agar tidak dicoba cancel lagi jika notebook dijalankan ulang
        #     del globals()['test_transaction_id']


    # Jalankan tes tools (opsional, bagus untuk debugging)
    # Loop event asyncio harus sudah berjalan (nest_asyncio)
    # Jika Anda menjalankan ini di skrip Python, gunakan asyncio.run(test_tools())
    # Di notebook dengan nest_asyncio, bisa langsung await.
    # Matikan jika tidak ingin auto-testing saat sel dijalankan
    # print("Menjalankan tes tools... Mohon tunggu.")
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(test_tools())
    # print("Tes tools selesai.")


    # Gradio UI (jalankan di sel terpisah jika test_tools() lama)
    print("\nUntuk menjalankan UI Gradio, jalankan sel berikutnya.")


# Sel 7: Jalankan Gradio UI
# Pastikan semua sel di atas sudah dijalankan.
# UI akan muncul di output sel ini.

# Matikan server MCP lama jika ada sebelum memulai yang baru oleh klien.
# Atau pastikan port tidak konflik.

# Jalankan tes tools sebelum UI untuk memastikan tools berfungsi
async def run_tests_then_ui():
    print("Menjalankan tes tools sebelum UI... Mohon tunggu.")
    await test_tools() # Pastikan test_tools didefinisikan sebagai async
    print("Tes tools selesai.")
    
    print("Memulai Gradio UI...")
    # Gradio ChatInterface
    # Fungsi `gradio_predict_wrapper` harus async
    chat_interface = gr.ChatInterface(
        fn=gradio_predict_wrapper, # Fungsi async
        title="Warung Cerdas Chatbot",
        description="Chat dengan AI untuk memesan produk dari Warung Cerdas.",
        examples=[
            ["Halo, produk apa saja yang ada?"],
            ["Saya mau lihat detail produk Kopi Instan A"],
            ["Saya mau pesan Kopi Instan A sebanyak 2 dan Mie Instan B sebanyak 1, tanggal hari ini, bayar cash"],
            ["Cek pesanan saya dengan ID 1"], # Ganti dengan ID yang valid
            ["Batalkan pesanan dengan ID 1"]  # Ganti dengan ID yang valid
        ],
        chatbot=gr.Chatbot(height=600),
    )
    chat_interface.launch() # share=True jika ingin diakses dari luar

# Jalankan
asyncio.run(run_tests_then_ui())