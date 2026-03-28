
from pappers_mcp.server import create_mcp

mcp = create_mcp()

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001,
        path="/mcp/",
    )


