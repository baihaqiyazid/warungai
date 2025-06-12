import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import FunctionTool # Assuming agents.py and FunctionTool are in the accessible path
import json
from typing import List, Dict, Any, Optional
import os


produk_params = StdioServerParameters(command="uv", args=["run", "app/mcp/produk_server.py"], env=None)

async def list_produk_tools() -> List[Any]: # Return type might be mcp.ToolDefinition
    """Lists all available tools from the produk_server."""
    async with stdio_client(produk_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools

async def call_produk_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """Calls a specific tool on the produk_server with given arguments."""
    async with stdio_client(produk_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result

async def read_produk_resource(produk_id: int) -> Optional[str]:
    """Reads a specific product resource by its ID."""
    async with stdio_client(produk_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = f"produk://produk_server/item/{produk_id}"
            result = await session.read_resource(resource_uri)
            if result.contents and result.contents[0].text:
                return result.contents[0].text
            return None

async def read_all_produk_resource() -> List[str]:
    """Reads the resource listing all products."""
    async with stdio_client(produk_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            resource_uri = "produk://produk_server/all_items"
            result = await session.read_resource(resource_uri)
            # Assuming the resource returns a list of JSON strings directly in contents
            return [content.text for content in result.contents if content.text]

async def get_produk_tools_openai() -> List[FunctionTool]:
    """Gets all produk tools formatted for OpenAI function calling."""
    openai_tools = []
    tools = await list_produk_tools()
    for tool in tools:
        # Ensure inputSchema is correctly transformed if it's not directly a JSON schema dict
        # Pydantic models in FastMCP usually generate compatible schemas.
        schema = {**tool.inputSchema, "additionalProperties": False} if tool.inputSchema else {"type": "object", "properties": {}, "additionalProperties": False}
        
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            # Adjust lambda to correctly parse args if they are not already a JSON string
            # And to handle the return from call_produk_tool (it might be parsed JSON or a string)
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_produk_tool(toolname, json.loads(args) if isinstance(args, str) else args)
        )
        openai_tools.append(openai_tool)
    return openai_tools

# Example Usage (requires an async runtime)
async def main():
    print("Listing Produk Tools...")
    tools = await list_produk_tools()
    for idx, tool in enumerate(tools):
        print(f"Tool {idx+1}: {tool.name} - {tool.description}")
        # print(f"Input Schema: {tool.inputSchema}") # For detailed schema inspection

    # Example: Create a new product
    print("\nCreating a new product...")
    try:
        created_product_json = await call_produk_tool(
            "create_produk", 
            {
                "nama_barang": "Teh Botol", 
                "harga": 3500, 
                "stok": 50,
                "lokasi": "Kulkas Minuman"
            }
        )
        print(f"Created Product (JSON): {created_product_json}")
        created_product = json.loads(created_product_json) # Parse JSON string to dict
        product_id = created_product.get('id')
    except Exception as e:
        print(f"Error creating product: {e}")
        product_id = None

    if product_id:
        # Example: Get the created product
        print(f"\nGetting product with ID: {product_id}...")
        retrieved_product_json = await call_produk_tool("get_produk", {"produk_id": product_id})
        print(f"Retrieved Product (JSON): {retrieved_product_json}")

        # Example: Update the product
        print(f"\nUpdating product with ID: {product_id}...")
        updated_product_json = await call_produk_tool(
            "update_produk",
            {
                "produk_id": product_id,
                "nama_barang": "Teh Botol Sosro",
                "harga": 4000,
                "stok": 45,
                "lokasi": "Kulkas Minuman Dingin"
            }
        )
        print(f"Updated Product (JSON): {updated_product_json}")

    # Example: List all products
    print("\nListing all products...")
    all_products_json_list = await call_produk_tool("list_all_produk", {})
    print(f"All Products (JSON List): {all_products_json_list}")
    # for p_json in all_products_json_list:
    #     print(json.loads(p_json))

    # Example: Read product resource
    if product_id:
        print(f"\nReading product resource for ID: {product_id}...")
        product_resource_json = await read_produk_resource(product_id)
        print(f"Product Resource (JSON): {product_resource_json}")

    # Example: Read all products resource
    print("\nReading all products resource...")
    all_products_resource_json_list = await read_all_produk_resource()
    print(f"All Products Resource (JSON List): {all_products_resource_json_list}")

    # Example: Get OpenAI tools
    print("\nGetting OpenAI tools for Produk...")
    openai_produk_tools = await get_produk_tools_openai()
    for tool in openai_produk_tools:
        print(f"OpenAI Tool: {tool.name}, Description: {tool.description}, Schema: {tool.params_json_schema}")
        
    # Delete if created
    # if product_id:
    #     print(f"\nDeleting product with ID: {product_id}...")
    #     delete_status = await call_produk_tool("delete_produk", {"produk_id": product_id})
    #     print(f"Deletion status for product ID {product_id}: {delete_status}")

if __name__ == "__main__":
    import asyncio
    # Ensure `produk_server.py` is running in a separate process before executing this client.
    # E.g., run `python -m uvicorn produk_server:mcp --port <your_port>` or `uv run produk_server.py`
    # The StdioServerParameters implies it will be started by the client, so ensure the command is correct.
    asyncio.run(main())