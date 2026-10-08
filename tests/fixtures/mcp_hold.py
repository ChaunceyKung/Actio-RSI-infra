"""Test-only MCP hold after durable received marker, before any result."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from actio.mcp_server import SCHEMA,DESCRIPTION

root=Path(sys.argv[1]);server=Server('hold',version='1')
@server.list_tools()
async def tools():
    return [types.Tool(name='read_fixture',description=DESCRIPTION,inputSchema=SCHEMA)]
@server.call_tool()
async def call(name,arguments):
    with (root/'mcp.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps({'kind':'received','arguments':arguments,'pid':os.getpid()})+'\n');f.flush();os.fsync(f.fileno())
    await asyncio.Event().wait()
async def main():
    async with stdio_server() as (rx,tx):
        await server.run(rx,tx,server.create_initialization_options())
asyncio.run(main())
