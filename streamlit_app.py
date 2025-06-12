import streamlit as st
import pandas as pd
import json
import datetime
import os
from typing import Any, List

st.set_page_config(layout="wide")

from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, ModelSettings, FunctionToolResult, ToolsToFinalOutputResult, RunContextWrapper, RunHooks
from agents.mcp import MCPServerStdio

# Set the current working directory to the project root
# This is important for relative paths in the application
os.chdir('/home/lenov/Documents/warung')

# --- Database and Product Initialization ---
from app.mcp_sample.produk_database import init_db as init_db_produk, create_product_in_db
from app.mcp_sample.transaction_database import init_db as init_db_transaction

sample_product_data_list = [
    {
        "nama_barang": "Indomie Goreng",
        "harga": 3000,
        "lokasi": "Rak Mie Instan",
        "deskripsi_suara_lokasi": "Ada di rak tengah, bagian mie instan.",
        "path_qris": "/qris/indomie_goreng.png",
        "stok": 50
    },
    {
        "nama_barang": "Aqua Botol 600ml",
        "harga": 3500,
        "lokasi": "Kulkas Minuman",
        "deskripsi_suara_lokasi": "Di dalam kulkas minuman, sebelah kanan.",
        "path_qris": "/qris/aqua_600ml.png",
        "stok": 100
    },
    {
        "nama_barang": "Chitato Sapi Panggang",
        "harga": 10000,
        "lokasi": "Rak Snack",
        "deskripsi_suara_lokasi": "Rak snack, di bagian atas.",
        "path_qris": "/qris/chitato_sapi_panggang.png",
        "stok": 30
    },
    {
        "nama_barang": "Susu Ultra Coklat 250ml",
        "harga": 6000,
        "lokasi": "Kulkas Susu",
        "deskripsi_suara_lokasi": "Kulkas khusus produk susu, di baris kedua dari atas.",
        "path_qris": "/qris/susu_ultra_coklat.png",
        "stok": 45
    },
    {
        "nama_barang": "Roti Tawar Sari Roti",
        "harga": 15000,
        "lokasi": "Rak Roti",
        "deskripsi_suara_lokasi": "Area roti, dekat kasir.",
        "path_qris": "/qris/sari_roti_tawar.png",
        "stok": 20
    },
    {
        "nama_barang": "Teh Botol Sosro Kotak",
        "harga": 4000,
        "lokasi": "Kulkas Minuman",
        "deskripsi_suara_lokasi": "Kulkas minuman, di sebelah kiri bawah.",
        "path_qris": "/qris/teh_botol_kotak.png",
        "stok": 70
    },
    {
        "nama_barang": "Sabun Mandi Lifebuoy",
        "harga": 5000,
        "lokasi": "Rak Perlengkapan Mandi",
        "deskripsi_suara_lokasi": "Bagian sabun dan sampo, rak nomor tiga.",
        "path_qris": "/qris/lifebuoy_sabun.png",
        "stok": 60
    },
    {
        "nama_barang": "Pasta Gigi Pepsodent",
        "harga": 8500,
        "lokasi": "Rak Perlengkapan Mandi",
        "deskripsi_suara_lokasi": "Di rak perlengkapan mandi, dekat dengan sikat gigi.",
        "path_qris": "/qris/pepsodent.png",
        "stok": 35
    },
    {
        "nama_barang": "Minyak Goreng Bimoli 1L",
        "harga": 25000,
        "lokasi": "Rak Minyak & Sembako",
        "deskripsi_suara_lokasi": "Rak sembako, di bagian minyak goreng.",
        "path_qris": "/qris/bimoli_1l.png",
        "stok": 25
    },
    {
        "nama_barang": "Kopi Kapal Api Special Mix",
        "harga": 12000, # Harga per renceng atau box kecil
        "lokasi": "Rak Kopi & Teh",
        "deskripsi_suara_lokasi": "Area kopi, di rak paling atas.",
        "path_qris": "/qris/kapal_api_special_mix.png",
        "stok": 40
    }
]

def reset_db():
    init_db_produk()
    init_db_transaction()

    for product_data in sample_product_data_list:
        create_product_in_db(product_data)

def reset_log():
    file_path = "/home/lenov/Documents/warung/logs/warung.log"
    if os.path.exists(file_path):
        os.remove(file_path)

# Ensure database and logs are reset when the app starts
reset_db()
reset_log()

# --- Load Instructions and Products ---
with open(f"{os.getcwd()}/app/instruction.md", 'r', encoding='utf-8') as file:
    base_instructions = file.read()

products_raw = []

@st.cache_resource
async def get_products_data():
    """Loads product data and caches it."""
    params_produk_load = {"command": "uv", "args": ["run", "app/mcp_sample/produk_server.py"]}
    async with MCPServerStdio(params=params_produk_load) as mcp_produk_loader:
        response = await mcp_produk_loader.call_tool("list_all_produk", {})
        for i in response.content:
            produk_dict = json.loads(i.text)
            products_raw.append(produk_dict)
    return products_raw

# Load products at the start of the app
products_raw = [] # Initialize empty list
import asyncio
products_raw = asyncio.run(get_products_data())

# --- Custom Hooks for Logging ---
class CustomHooks(RunHooks):
    def __init__(self):
        self.event_counter = 0
    
    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        print(f"AGENT {agent.name} START") 

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        print(f"AGENT {agent.name} END")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Any) -> None: # Changed Tool to Any
        print(f"Tool {tool.name} START")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Any, config: Any) -> None: # Changed Tool to Any
        print(f"Tool {tool.name} END")
       
custom_hook = CustomHooks()

# --- Model Initialization ---
url_openrouter = "https://openrouter.ai/api/v1"
model = OpenAIChatCompletionsModel(
    model="openai/gpt-4o-mini",
    openai_client=AsyncOpenAI(
        base_url=url_openrouter,
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
)

# --- Tool to Final Output Function ---
def my_tools_to_final_output_function(
    run_context: RunContextWrapper[Any],
    tool_results: List[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    
    for i in tool_results:
        if i.tool.name == 'create_transaction' or i.tool.name == 'update_transaction':
            try:
                json_obj = json.loads(i.output)
                v = json.loads(json_obj['text'])

                details = []
                for detail in v['detail_transactions']:
                    produk_name = "Unknown Product"
                    for p in products_raw: # Use products_raw here to get stock
                        if p.get('id') == detail.get('produk_id'):
                            produk_name = p.get('nama_barang', "Unknown Product")
                            break
                    details.append({
                        "Produk": produk_name,
                        "Jumlah": detail["qty"],
                        "Harga per Produk": detail["harga_per_produk"],
                        "Total Harga Produk": detail["total_harga_produk"]
                    })
                st.session_state.current_transaction_details_df = pd.DataFrame(details)
            except json.JSONDecodeError as e:
                st.error(f"Error decoding JSON from tool output: {e}")
            except KeyError as e:
                st.error(f"Missing key in tool output: {e}")

    combined_output = "\n".join([result.output for result in tool_results])

    return ToolsToFinalOutputResult(
        final_output=combined_output,
        is_final_output=False  
    )

# --- Conversational History Function ---
def conversational_history(history: list, current_message: str) -> str:
    conversation_history_for_agent = []

    for entry in history:
        user_msg, assistant_msg = entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        conversation_history_for_agent.append(f"{timestamp} | buyer: {user_msg}")
        conversation_history_for_agent.append(f"{timestamp} | assistant: {assistant_msg}")

    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation_history_for_agent.append(f"{current_timestamp} | buyer: {current_message}")
    
    formatted_history_string = "\n".join(conversation_history_for_agent)

    full_request = f"""
Konteks Percakapan Sebelumnya::
---
{formatted_history_string}
---

--- Percakapan Berlanjut ---
Pesan terbaru dari pembeli: {current_message}

"""
    return full_request


# --- Streamlit App --- 
async def main():
    st.title("Warung AI Chatbot")
    st.markdown("Selamat datang di Warung AI! Ketik pesan Anda untuk berinteraksi. AI akan mengingat konteks percakapan sebelumnya.")

    # Initialize chat history and transaction details in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_transaction_details_df" not in st.session_state:
        st.session_state.current_transaction_details_df = pd.DataFrame(columns=["Produk", "Jumlah", "Harga per Produk", "Total Harga Produk"])

    # Layout for chat and transaction details
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input for user message
        if prompt := st.chat_input("Ketik pesan ke Warung AI..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Prepare history for the agent
            # Extract only user and assistant messages for conversational_history
            agent_history = []
            for i in range(0, len(st.session_state.messages) - 1, 2):
                if st.session_state.messages[i]['role'] == 'user' and \
                   st.session_state.messages[i+1]['role'] == 'assistant':
                    agent_history.append((st.session_state.messages[i]['content'], st.session_state.messages[i+1]['content']))

            full_request = conversational_history(agent_history, prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Warung AI sedang memproses..."):
                    params_produk_agent = {"command": "uv", "args": ["run", "app/mcp_sample/produk_server.py"]}
                    params_transaction_agent = {"command": "uv", "args": ["run", "app/mcp_sample/transaction_server.py"]}
                    
                    async with MCPServerStdio(params=params_produk_agent) as mcp_produk:
                        async with MCPServerStdio(params=params_transaction_agent) as mcp_transaction:
                            agent = Agent(
                                name="agent", 
                                instructions=base_instructions, 
                                model=model, 
                                model_settings=ModelSettings(
                                    top_p=0.6,
                                    temperature=0.6,
                                ),
                                hooks=custom_hook,
                                mcp_servers=[mcp_produk, mcp_transaction],
                                tool_use_behavior=my_tools_to_final_output_function,
                            )
                            result = await Runner.run(agent, full_request, max_turns=50)
                            st.markdown(result.final_output)
                            st.session_state.messages.append({"role": "assistant", "content": result.final_output})
            
            # Rerun the app to update the chat and transaction table
            st.experimental_rerun()

    with col2:
        st.header("Ringkasan Transaksi")
        st.dataframe(st.session_state.current_transaction_details_df,
                     hide_index=True,
                     use_container_width=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 