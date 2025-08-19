from mcp_router_example import MCPToolRouter
from mcpnp import UnifiedMCPServer
import os

os.environ['MCP_TRANSPORT'] = 'http'
os.environ['MCP_HOST'] = 'localhost'
os.environ['MCP_PORT'] = '8000'

router = MCPToolRouter()
server = UnifiedMCPServer(tool_router=router)
server.run()
