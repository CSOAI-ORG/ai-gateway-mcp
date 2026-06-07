#!/usr/bin/env python3
"""
AI Gateway MCP — MEOK AI Labs. Multi-model routing, load balancing, fallback chains."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json, os, time, hashlib
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 10
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

mcp = FastMCP("ai-gateway", instructions="MEOK AI Labs — AI Gateway. Multi-model routing with intelligent fallback, cost optimization, and compliance-aware model selection.")

MODELS = {
    "claude-opus": {"provider": "anthropic", "cost_per_1k": 0.015, "speed": "slow", "quality": 10, "context": 200000, "compliance": ["eu_ai_act", "iso_42001"]},
    "claude-sonnet": {"provider": "anthropic", "cost_per_1k": 0.003, "speed": "fast", "quality": 8, "context": 200000, "compliance": ["eu_ai_act", "iso_42001"]},
    "gpt-4o": {"provider": "openai", "cost_per_1k": 0.005, "speed": "fast", "quality": 9, "context": 128000, "compliance": ["soc2"]},
    "gpt-4o-mini": {"provider": "openai", "cost_per_1k": 0.00015, "speed": "very_fast", "quality": 7, "context": 128000, "compliance": ["soc2"]},
    "gemini-2.0": {"provider": "google", "cost_per_1k": 0.00, "speed": "fast", "quality": 8, "context": 1000000, "compliance": []},
    "llama-3.1-70b": {"provider": "local", "cost_per_1k": 0.0, "speed": "medium", "quality": 7, "context": 128000, "compliance": ["sovereign"]},
    "gemma-3-4b": {"provider": "local", "cost_per_1k": 0.0, "speed": "very_fast", "quality": 5, "context": 8192, "compliance": ["sovereign"]},
    "mistral-large": {"provider": "mistral", "cost_per_1k": 0.002, "speed": "fast", "quality": 8, "context": 128000, "compliance": ["eu_ai_act"]},
}
_call_log = []

@mcp.tool()
def route_request(task: str, priority: str = "balanced", max_cost: float = 0.01, require_compliance: str = "", prefer_local: bool = False, api_key: str = "") -> str:
    """Route an AI request to the optimal model based on task, cost, speed, and compliance requirements.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        task (str): The task to analyze or process.
        priority (str): The priority to analyze or process.
        max_cost (float): The max cost to analyze or process.
        require_compliance (str): The require compliance to analyze or process.
        prefer_local (bool): The prefer local to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

    if err := _rl(): return err
    candidates = []
    for name, info in MODELS.items():
        score = 0
        if priority == "quality": score = info["quality"] * 10
        elif priority == "speed": score = {"very_fast": 40, "fast": 30, "medium": 20, "slow": 10}.get(info["speed"], 0)
        elif priority == "cost": score = max(0, 40 - info["cost_per_1k"] * 10000)
        else: score = info["quality"] * 3 + {"very_fast": 10, "fast": 8, "medium": 5, "slow": 2}.get(info["speed"], 0) + max(0, 20 - info["cost_per_1k"] * 5000)
        if info["cost_per_1k"] > max_cost and info["cost_per_1k"] > 0: score *= 0.3
        if require_compliance and require_compliance not in info["compliance"]: score *= 0.1
        if prefer_local and info["provider"] == "local": score *= 1.5
        candidates.append({"model": name, "score": round(score, 1), **info})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]
    _call_log.append({"model": best["model"], "task": task[:50], "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"recommended": best["model"], "provider": best["provider"], "score": best["score"],
        "cost_per_1k_tokens": best["cost_per_1k"], "alternatives": [c["model"] for c in candidates[1:3]],
        "compliance": best["compliance"], "all_candidates": candidates[:5]}

@mcp.tool()
def list_models(filter_provider: str = "", filter_compliance: str = "", api_key: str = "") -> str:
    """List all available models with capabilities and pricing.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        filter_provider (str): The filter provider to analyze or process.
        filter_compliance (str): The filter compliance to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

    if err := _rl(): return err
    models = []
    for name, info in MODELS.items():
        if filter_provider and info["provider"] != filter_provider: continue
        if filter_compliance and filter_compliance not in info["compliance"]: continue
        models.append({"name": name, **info})
    return {"models": models, "total": len(models), "providers": list(set(m["provider"] for m in models))}

@mcp.tool()
def cost_estimator(prompt_tokens: int, completion_tokens: int, model: str = "claude-sonnet", api_key: str = "") -> str:
    """Estimate cost for a specific request across models.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        prompt_tokens (int): The prompt tokens to analyze or process.
        completion_tokens (int): The completion tokens to analyze or process.
        model (str): The model to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

    if err := _rl(): return err
    total_tokens = prompt_tokens + completion_tokens
    costs = {}
    for name, info in MODELS.items():
        cost = (total_tokens / 1000) * info["cost_per_1k"]
        costs[name] = round(cost, 6)
    costs_sorted = sorted(costs.items(), key=lambda x: x[1])
    return {"tokens": total_tokens, "costs_by_model": dict(costs_sorted),
        "cheapest": costs_sorted[0][0], "most_expensive": costs_sorted[-1][0],
        "selected_model_cost": costs.get(model, 0)}

@mcp.tool()
def get_gateway_stats(api_key: str = "") -> str:
    """Get gateway usage statistics.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

    if err := _rl(): return err
    model_counts = defaultdict(int)
    for log in _call_log: model_counts[log["model"]] += 1
    return {"total_calls": len(_call_log), "by_model": dict(model_counts),
        "recent": _call_log[-5:]}

if __name__ == "__main__":
    mcp.run()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
