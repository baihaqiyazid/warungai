import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool # Assuming agents.py and FunctionTool are in the accessible path
import json
from typing import List, Dict, Any, Optional
import os
import asyncio
print(os.getcwd())
# Parameters to run the transaction_server.py
transaction_params = StdioServerParameters(command="uv", args=["run", "app/mcp/transaction_server.py"], env=None)

async def list_transaction_tools() -> List[Any]:
    """Lists all available tools from the transaction_server."""
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools

async def call_transaction_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Calls a specific tool on the transaction_server with given arguments.
       Returns the text content from the tool call result as a string.
       Raises Exception if the tool call fails or content is not as expected.
    """
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tool_result = await session.call_tool(tool_name, tool_args)
            
            if tool_result.isError:
                error_message = f"Tool call '{tool_name}' failed."
                if tool_result.content and len(tool_result.content) > 0 and hasattr(tool_result.content[0], 'text') and tool_result.content[0].text:
                    error_message += f" Details: {tool_result.content[0].text}"
                raise Exception(error_message)

            if tool_result.content and len(tool_result.content) > 0 and hasattr(tool_result.content[0], 'text') and tool_result.content[0].text is not None:
                return tool_result.content[0].text
            else:
                raise Exception(f"Tool call '{tool_name}' returned no valid text content. Result: {tool_result}")

# --- Resource Reading Functions ---
async def read_transaction_resource(transaction_id: int) -> Optional[str]:
    """Reads a specific transaction resource by its ID."""
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = f"transaction://transaction_server/transaction/{transaction_id}"
            result = await session.read_resource(resource_uri)
            if result.contents and result.contents[0].text:
                return result.contents[0].text
            return None

async def read_all_transactions_resource() -> List[str]:
    """Reads the resource listing all transactions."""
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = "transaction://transaction_server/all_transactions"
            result = await session.read_resource(resource_uri)
            return [content.text for content in result.contents if content.text]

async def read_detail_transaction_resource(detail_transaction_id: int) -> Optional[str]:
    """Reads a specific detail_transaction resource by its ID."""
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = f"transaction://transaction_server/detail_transaction/{detail_transaction_id}"
            result = await session.read_resource(resource_uri)
            if result.contents and result.contents[0].text:
                return result.contents[0].text
            return None

async def read_all_detail_transactions_resource() -> List[str]:
    """Reads the resource listing all detail_transactions."""
    async with stdio_client(transaction_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = "transaction://transaction_server/all_detail_transactions"
            result = await session.read_resource(resource_uri)
            return [content.text for content in result.contents if content.text]

async def get_transaction_tools_openai() -> List[FunctionTool]:
    """Gets all transaction tools formatted for OpenAI function calling."""
    openai_tools = []
    tools = await list_transaction_tools()
    for tool in tools:
        schema = {**tool.inputSchema, "additionalProperties": False} if tool.inputSchema else {"type": "object", "properties": {}, "additionalProperties": False}
        
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_transaction_tool(toolname, json.loads(args) if isinstance(args, str) else args)
        )
        openai_tools.append(openai_tool)
    return openai_tools

# Example Usage (requires an async runtime)
async def main():
    print("Listing Transaction Tools...")
    tools = await list_transaction_tools()
    for idx, tool in enumerate(tools):
        print(f"Tool {idx+1}: {tool.name} - {tool.description}")
        # print(f"Input Schema: {tool.inputSchema}")

    transaction_id = None
    detail_transaction_id = None

    try:
        # --- Transaction Operations ---
        print("\nCreating a new transaction...")
        created_transaction_str = await call_transaction_tool(
            "create_transaction",
            {
                "tanggal_transaksi": "2024-07-28",
                "total_harga_transaksi": 15000,
                "status": "pending",
                "metode_pembayaran": "cash",
                "catatan": "Test transaction from client"
            }
        )
        print(f"Created Transaction (Raw String): {created_transaction_str}")
        created_transaction = json.loads(created_transaction_str)
        print(f"Created Transaction (Parsed): {created_transaction}")
        transaction_id = created_transaction.get('id')

        if transaction_id:
            print(f"\nGetting transaction with ID: {transaction_id}...")
            retrieved_transaction_str = await call_transaction_tool("get_transaction", {"transaction_id": transaction_id})
            retrieved_transaction = json.loads(retrieved_transaction_str)
            print(f"Retrieved Transaction: {retrieved_transaction}")

            print(f"\nUpdating transaction with ID: {transaction_id}...")
            updated_transaction_str = await call_transaction_tool(
                "update_transaction",
                {
                    "transaction_id": transaction_id,
                    "tanggal_transaksi": "2024-07-28",
                    "total_harga_transaksi": 16000,
                    "status": "success",
                    "metode_pembayaran": "qris",
                    "catatan": "Updated test transaction"
                }
            )
            updated_transaction = json.loads(updated_transaction_str)
            print(f"Updated Transaction: {updated_transaction}")

        # --- Detail Transaction Operations ---
        if transaction_id:
            print("\nCreating a new detail transaction...")
            created_detail_str = await call_transaction_tool(
                "create_detail_transaction",
                {
                    "transaction_id": transaction_id,
                    "produk_id": 1, # Ensure product with ID 1 exists in your 'produk' table
                    "qty": 2,
                    "harga_per_produk": 7500,
                    "total_harga_produk": 15000
                }
            )
            print(f"Created Detail Transaction (Raw String): {created_detail_str}")
            created_detail = json.loads(created_detail_str)
            print(f"Created Detail Transaction (Parsed): {created_detail}")
            detail_transaction_id = created_detail.get('id')

            if detail_transaction_id:
                print(f"\nGetting detail transaction with ID: {detail_transaction_id}...")
                retrieved_detail_str = await call_transaction_tool("get_detail_transaction", {"detail_transaction_id": detail_transaction_id})
                retrieved_detail = json.loads(retrieved_detail_str)
                print(f"Retrieved Detail Transaction: {retrieved_detail}")

                print(f"\nUpdating detail transaction with ID: {detail_transaction_id}...")
                updated_detail_str = await call_transaction_tool(
                    "update_detail_transaction",
                    {
                        "detail_transaction_id": detail_transaction_id,
                        "transaction_id": transaction_id,
                        "produk_id": 1,
                        "qty": 3,
                        "harga_per_produk": 8000,
                        "total_harga_produk": 24000
                    }
                )
                updated_detail = json.loads(updated_detail_str)
                print(f"Updated Detail Transaction: {updated_detail}")
        
        # --- Listing All ---
        print("\nListing all transactions...")
        all_transactions_response_str = await call_transaction_tool("get_all_transactions", {})
        all_transactions_json_strings = json.loads(all_transactions_response_str)
        all_transactions_parsed = [json.loads(tx_str) for tx_str in all_transactions_json_strings]
        print(f"All Transactions: {all_transactions_parsed}")

        print("\nListing all detail transactions...")
        all_detail_transactions_response_str = await call_transaction_tool("get_all_detail_transactions", {})
        all_detail_transactions_json_strings = json.loads(all_detail_transactions_response_str)
        all_detail_transactions_parsed = [json.loads(dt_str) for dt_str in all_detail_transactions_json_strings]
        print(f"All Detail Transactions: {all_detail_transactions_parsed}")

        # --- Reading Resources ---
        if transaction_id:
            print(f"\nReading transaction resource for ID: {transaction_id}...")
            transaction_resource_json = await read_transaction_resource(transaction_id)
            print(f"Transaction Resource (JSON): {transaction_resource_json}")
        
        print("\nReading all transactions resource...")
        all_transactions_res_json_list = await read_all_transactions_resource()
        print(f"All Transactions Resource (JSON List): {all_transactions_res_json_list}")
        # Similar to get_all_transactions tool, the read_all_transactions_resource in server needs a return.


        if detail_transaction_id:
            print(f"\nReading detail transaction resource for ID: {detail_transaction_id}...")
            detail_res_json = await read_detail_transaction_resource(detail_transaction_id)
            print(f"Detail Transaction Resource (JSON): {detail_res_json}")

        print("\nReading all detail transactions resource...")
        all_detail_res_json_list = await read_all_detail_transactions_resource()
        print(f"All Detail Transactions Resource (JSON List): {all_detail_res_json_list}")
        # Similar to get_all_detail_transactions tool, the read_all_detail_transactions_resource in server needs a return.


        # --- OpenAI Tools ---
        print("\nGetting OpenAI tools for Transaction Server...")
        openai_transaction_tools = await get_transaction_tools_openai()
        for tool_def in openai_transaction_tools:
            print(f"OpenAI Tool: {tool_def.name}, Description: {tool_def.description}, Schema: {tool_def.params_json_schema}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # --- Deletion (Cleanup) ---
        if detail_transaction_id:
            print(f"\nDeleting detail transaction with ID: {detail_transaction_id}...")
            delete_status_detail_str = await call_transaction_tool("delete_detail_transaction", {"detail_transaction_id": detail_transaction_id})
            delete_status_detail = json.loads(delete_status_detail_str) # Parses "true" or "false"
            print(f"Deletion status for detail transaction ID {detail_transaction_id}: {delete_status_detail}")

        if transaction_id:
            print(f"\nDeleting transaction with ID: {transaction_id}...")
            delete_status_transaction_str = await call_transaction_tool("delete_transaction", {"transaction_id": transaction_id})
            delete_status_transaction = json.loads(delete_status_transaction_str) # Parses "true" or "false"
            print(f"Deletion status for transaction ID {transaction_id}: {delete_status_transaction}")


if __name__ == "__main__":
    # Ensure `transaction_server.py` can be run by the command.
    # `uv run app/mcp/transaction_server.py`
    # Also, ensure `src/data/warung.db` and its tables (produk, transactions, detail_transactions) are initialized.
    # You might need to run `produk_database.py` and `transaction_database.py` main blocks once.
    # And ensure a product with ID 1 exists if not creating one before running detail transaction examples.
    
    # For testing, it's good to initialize the DB separately first.
    # from app.mcp.produk_database import init_db as init_produk_db
    # from app.mcp.transaction_database import init_db as init_transaction_db
    # print("Initializing databases...")
    # init_produk_db()
    # init_transaction_db()
    # print("Databases initialized.")
    
    asyncio.run(main()) 