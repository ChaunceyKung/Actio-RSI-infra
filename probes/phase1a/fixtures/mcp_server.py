"""Experimental official MCP Python SDK stdio server; synthetic read-only tool."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

root = Path(sys.argv[1]).resolve()
server = Server('phase1a-fixture', version='1')

def record(row):
    with (root / 'mcp.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(row) + '\n')
        f.flush()
        os.fsync(f.fileno())

@server.list_tools()
async def tools():
    params=server.request_context.session.client_params
    record({'kind':'discovery','client_protocol':params.protocolVersion if params else None,
            'client_info':params.clientInfo.model_dump() if params else None})
    return [types.Tool(name='read_fixture', description='Read one synthetic fixture key.',
        inputSchema={'type':'object','properties':{'key':{'type':'string'},'op':{'type':'string'}},'required':['key','op'],'additionalProperties':False},
        annotations=types.ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))]

@server.call_tool()
async def call(name, arguments):
    record({'kind':'received','name':name,'arguments':arguments,'pid':os.getpid()})
    key = arguments['key']
    if key == 'transport': os._exit(73)
    if key in ('timeout', 'hold'):
        try: await asyncio.sleep(120)
        except BaseException as e:
            record({'kind':'cancelled','op':arguments['op'],'error':type(e).__name__})
            raise
    if key == 'error':
        return types.CallToolResult(content=[types.TextContent(type='text', text='synthetic isError')], isError=True)
    # No user-supplied path is opened. Exact data file created by the probe.
    data = json.loads((root / 'data.json').read_text(encoding='utf-8'))
    return [types.TextContent(type='text', text=data.get(key, 'unknown synthetic key'))]

async def main():
    record({'kind':'startup','pid':os.getpid()})
    async with stdio_server() as (rx, tx):
        await server.run(rx, tx, server.create_initialization_options())

asyncio.run(main())
