"""Repo Cost Scanner — Static Codebase AI API Cost & Margin Auditor.

Scans real Python/TypeScript/JavaScript repositories to detect:
  - Paid AI/media SDKs (OpenAI, Anthropic, Google GenAI, Replicate, ElevenLabs)
  - Hardcoded model names & their estimated per-request inference cost
  - Dangerous cost anti-patterns:
      * UNBOUNDED_LOOP_COST (AI API call inside a for/while loop)
      * MISSING_TOKEN_CAP (LLM call without max_tokens / max_output_tokens)
      * HIGH_COST_MODEL_ON_LOW_TIER (frontier reasoning/video model on cheap plan)
  - Computes real monthly COGS per user vs subscription price!
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from ideastress.finance.engine import q2

# Estimated average cost per single API call (assuming ~2500 input / 800 output tokens or 1 media gen)
MODEL_CALL_COST_USD: Dict[str, tuple[Decimal, str]] = {
    "gpt-4o-mini": (Decimal("0.0009"), "openai"),
    "gpt-4o": (Decimal("0.0143"), "openai"),
    "o1": (Decimal("0.0855"), "openai"),
    "o3": (Decimal("0.0500"), "openai"),
    "claude-3-5-sonnet": (Decimal("0.0195"), "anthropic"),
    "claude-sonnet-4": (Decimal("0.0195"), "anthropic"),
    "claude-3-opus": (Decimal("0.0975"), "anthropic"),
    "claude-opus": (Decimal("0.0975"), "anthropic"),
    "claude-3-5-haiku": (Decimal("0.0052"), "anthropic"),
    "gemini-2.5-pro": (Decimal("0.0111"), "google"),
    "gemini-2.5-flash": (Decimal("0.0012"), "google"),
    "eleven_multilingual_v2": (Decimal("0.0300"), "elevenlabs"),
    "flux-pro": (Decimal("0.0550"), "replicate"),
    "runway": (Decimal("0.2500"), "runwayml"),
}

SDK_PATTERNS = {
    "openai": re.compile(r"\b(?:from\s+openai|import\s+openai|new\s+OpenAI|chat\.completions\.create)\b"),
    "anthropic": re.compile(r"\b(?:from\s+anthropic|import\s+anthropic|new\s+Anthropic|messages\.create)\b"),
    "google_genai": re.compile(r"\b(?:google\.genai|google\.generativeai|@google/genai|generate_content)\b"),
    "replicate": re.compile(r"\b(?:import\s+replicate|from\s+replicate|replicate\.run)\b"),
    "elevenlabs": re.compile(r"\b(?:elevenlabs|text_to_speech\.convert)\b"),
}

CALL_LINE_RE = re.compile(
    r"(completions\.create|messages\.create|generate_content|replicate\.run|text_to_speech\.convert)",
    re.IGNORECASE,
)
LOOP_LINE_RE = re.compile(r"^\s*(for\s+|while\s+)")
TOKEN_CAP_RE = re.compile(r"(max_tokens|max_output_tokens|max_completion_tokens)", re.IGNORECASE)

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
ALLOWED_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx"}


class CodeCostFinding(BaseModel):
    file_path: str
    line_number: int
    severity: str  # high | critical | medium
    rule_id: str  # UNBOUNDED_LOOP_COST | MISSING_TOKEN_CAP | HIGH_COST_MODEL
    detail: str


class RepoCostAuditReport(BaseModel):
    repo_path: str
    files_scanned: int
    sdks_detected: List[str]
    models_detected: List[str]
    estimated_cost_per_call_usd: Decimal
    estimated_monthly_cogs_per_user_usd: Decimal
    subscription_price_usd: Decimal
    estimated_gross_margin_pct: Decimal
    findings: List[CodeCostFinding]
    verdict: str  # HEALTHY | MARGIN_AT_RISK | BANKRUPTCY_RISK
    summary: str


def scan_repo_api_costs(
    repo_path: str | Path,
    *,
    subscription_price_usd: Decimal = Decimal("29"),
    assumed_daily_calls_per_user: int = 20,
) -> RepoCostAuditReport:
    """Statically scan a codebase to estimate real AI API COGS and surface margin-killing code patterns."""
    root = Path(repo_path)
    if not root.exists():
        raise FileNotFoundError(f"Repository path not found: {root}")

    files_scanned = 0
    sdks_found = set()
    models_found: Dict[str, Decimal] = {}
    findings: List[CodeCostFinding] = []

    files = [root] if root.is_file() else [
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in ALLOWED_EXTS
        and not any(part in SKIP_DIRS for part in p.parts)
    ]

    for fpath in files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        files_scanned += 1
        rel = str(fpath.relative_to(root)) if root.is_dir() else fpath.name
        lower_content = content.lower()

        for sdk_name, pat in SDK_PATTERNS.items():
            if pat.search(content):
                sdks_found.add(sdk_name)

        for model_key, (est_cost, _vendor) in MODEL_CALL_COST_USD.items():
            if model_key in lower_content:
                models_found[model_key] = est_cost
                if est_cost >= Decimal("0.05"):
                    findings.append(
                        CodeCostFinding(
                            file_path=rel,
                            line_number=1,
                            severity="high",
                            rule_id="HIGH_COST_MODEL",
                            detail=f"Detected expensive model '{model_key}' (~${est_cost}/call); ensure usage caps or higher pricing tier.",
                        )
                    )

        lines = content.splitlines()
        in_loop_indent: Optional[int] = None
        for idx, line in enumerate(lines, 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if LOOP_LINE_RE.match(line):
                in_loop_indent = indent
            elif stripped and in_loop_indent is not None and indent <= in_loop_indent:
                in_loop_indent = None

            if CALL_LINE_RE.search(line):
                # Check loop nesting
                if in_loop_indent is not None and indent > in_loop_indent:
                    findings.append(
                        CodeCostFinding(
                            file_path=rel,
                            line_number=idx,
                            severity="critical",
                            rule_id="UNBOUNDED_LOOP_COST",
                            detail="AI/Media API call detected inside a loop — a single user action can multiply token COGS unpredictably.",
                        )
                    )
                # Check nearby lines for max_tokens cap
                window = "\n".join(lines[max(0, idx - 2) : min(len(lines), idx + 8)])
                if not TOKEN_CAP_RE.search(window):
                    findings.append(
                        CodeCostFinding(
                            file_path=rel,
                            line_number=idx,
                            severity="medium",
                            rule_id="MISSING_TOKEN_CAP",
                            detail="LLM call has no explicit max_tokens / max_output_tokens cap in surrounding call site.",
                        )
                    )

    # Estimate weighted per-call cost
    if models_found:
        avg_call_cost = sum(models_found.values()) / Decimal(len(models_found))
    elif sdks_found:
        avg_call_cost = Decimal("0.0100")  # Conservative mid-tier fallback when SDK present without literal model string
    else:
        avg_call_cost = Decimal("0.0000")

    monthly_cogs = q2(avg_call_cost * Decimal(assumed_daily_calls_per_user * 30))
    stripe_fee = q2(subscription_price_usd * Decimal("0.029") + Decimal("0.30"))
    net_gp = subscription_price_usd - monthly_cogs - stripe_fee
    gm_pct = q2((net_gp / subscription_price_usd) * Decimal("100")) if subscription_price_usd > 0 else Decimal("0.00")

    has_critical = any(f.severity == "critical" for f in findings)
    if net_gp <= Decimal("0") or gm_pct < Decimal("35.00"):
        verdict = "BANKRUPTCY_RISK"
    elif has_critical or gm_pct < Decimal("65.00"):
        verdict = "MARGIN_AT_RISK"
    else:
        verdict = "HEALTHY"

    summary = (
        f"Scanned {files_scanned} file(s): detected SDKs={sorted(sdks_found) or ['none']}, "
        f"models={sorted(models_found.keys()) or ['none']}. Estimated AI COGS ${monthly_cogs}/user/mo "
        f"-> {gm_pct}% gross margin on ${subscription_price_usd}/mo plan ({verdict}; {len(findings)} finding(s))."
    )

    return RepoCostAuditReport(
        repo_path=str(root),
        files_scanned=files_scanned,
        sdks_detected=sorted(sdks_found),
        models_detected=sorted(models_found.keys()),
        estimated_cost_per_call_usd=avg_call_cost.quantize(Decimal("0.0001")),
        estimated_monthly_cogs_per_user_usd=monthly_cogs,
        subscription_price_usd=q2(subscription_price_usd),
        estimated_gross_margin_pct=gm_pct,
        findings=findings,
        verdict=verdict,
        summary=summary,
    )
