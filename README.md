# Ai Gateway

> By [MEOK AI Labs](https://meok.ai) — MEOK AI Labs — AI Gateway. Multi-model routing with intelligent fallback, cost optimization, and compliance-aware model selection.

AI Gateway MCP — MEOK AI Labs. Multi-model routing, load balancing, fallback chains.

## Installation

```bash
pip install ai-gateway-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install ai-gateway-mcp
```

## Tools

### `route_request`
Route an AI request to the optimal model based on task, cost, speed, and compliance requirements.

**Parameters:**
- `task` (str)
- `priority` (str)
- `max_cost` (float)
- `require_compliance` (str)
- `prefer_local` (bool)

### `list_models`
List all available models with capabilities and pricing.

**Parameters:**
- `filter_provider` (str)
- `filter_compliance` (str)

### `cost_estimator`
Estimate cost for a specific request across models.

**Parameters:**
- `prompt_tokens` (int)
- `completion_tokens` (int)
- `model` (str)

### `get_gateway_stats`
Get gateway usage statistics.


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/ai-gateway-mcp](https://github.com/CSOAI-ORG/ai-gateway-mcp)
- **PyPI**: [pypi.org/project/ai-gateway-mcp](https://pypi.org/project/ai-gateway-mcp/)

## License

MIT — MEOK AI Labs
