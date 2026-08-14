"""AI service layer — reasoning / approval for approved signals.

Provider strategy (100% free, zero-error):

- ``local``  → offline rule-based reviewer. No key, no network, deterministic.
               This is the guaranteed-zero-error default.
- ``gemini`` → Google Gemini **free tier** (free API key, no credit card).
- ``groq``   → Groq **free tier** (free API key, no credit card).

Every remote provider internally falls back to the local reviewer on *any*
failure (network error, rate limit, bad JSON, missing key), so the decision
layer can never hard-fail.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from ..analysis.market_analyzer import MarketAnalysis
from ..config.settings import get_settings
from ..models.enums import Direction
from ..models.signal import AggregateEvidence


@dataclass
class AIApproval:
    approved: bool
    verdict: str
    reasoning: str


class AIService(ABC):
    @abstractmethod
    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        """Sync approval (used by the offline/local path)."""

    async def approve_async(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        """Async approval (used by the pipeline). Defaults to sync approval."""
        return self.approve(direction, evidence, analysis)


class RuleBasedAIService(AIService):
    """Offline AI. Approves non-NO_TRADE directional setups that already
    cleared the confidence/conflict gates, with deterministic wording."""

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        if direction == Direction.NO_TRADE:
            return AIApproval(False, "NO TRADE", "No valid directional setup was approved.")
        supporting = ", ".join(evidence.supporting) or "combined evidence"
        risks = "; ".join(evidence.risks) if evidence.risks else "none flagged"
        reasoning = (
            f"Trend {analysis.trend.lower()}, structure {analysis.structure.lower()}, "
            f"RSI {analysis.rsi:.0f}. {len(evidence.supporting)} of "
            f"{evidence.total_directional} directional strategies agree "
            f"({evidence.agreement * 100:.0f}% agreement, {evidence.confidence:.0f}% confidence). "
            f"Supporting: {supporting}. Risks: {risks}."
        )
        verdict = f"STRONG {direction.value}"
        return AIApproval(True, verdict, reasoning)


def _build_prompt(
    direction: Direction, evidence: AggregateEvidence, analysis: MarketAnalysis
) -> str:
    return (
        "You are the AI decision layer of HACKER GenAI+, an AI trading assistant. "
        "Decide whether to APPROVE or REJECT the proposed signal.\n\n"
        f"Proposed direction: {direction.value}\n"
        f"Confidence: {evidence.confidence:.0f}%\n"
        f"Strategy agreement: {evidence.agreement * 100:.0f}% "
        f"({len(evidence.supporting)}/{evidence.total_directional})\n"
        f"Supporting: {', '.join(evidence.supporting) or 'none'}\n"
        f"Opposing: {', '.join(evidence.opposing) or 'none'}\n"
        f"Risks: {'; '.join(evidence.risks) or 'none'}\n"
        f"Market: trend={analysis.trend}, structure={analysis.structure}, "
        f"RSI={analysis.rsi:.0f}, momentum={analysis.momentum}%\n\n"
        'Respond ONLY with valid JSON, no markdown: '
        '{"approved": true|false, "verdict": "short verdict", '
        '"reasoning": "1-3 sentences why"}'
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _local_fallback(direction: Direction, evidence: AggregateEvidence, analysis: MarketAnalysis) -> AIApproval:
    return RuleBasedAIService().approve(direction, evidence, analysis)


def _parse_llm_answer(
    raw: str,
    direction: Direction,
    evidence: AggregateEvidence,
    analysis: MarketAnalysis,
) -> AIApproval:
    try:
        obj = _extract_json(raw)
        approved = bool(obj.get("approved", False))
        verdict = str(obj.get("verdict") or "").strip()
        reasoning = str(obj.get("reasoning") or "").strip()
    except (ValueError, TypeError, AttributeError):
        return _local_fallback(direction, evidence, analysis)
    if not reasoning:
        reasoning = _local_fallback(direction, evidence, analysis).reasoning
    if not verdict:
        verdict = f"STRONG {direction.value}" if approved else "NO TRADE"
    # Safety gate: an approved direction must be CALL/PUT.
    approved = approved and direction in (Direction.CALL, Direction.PUT)
    return AIApproval(approved=approved, verdict=verdict, reasoning=reasoning)


class GeminiAIService(AIService):
    """Google Gemini free-tier reasoning (optional; falls back to local)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        timeout: float = 25.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        return _local_fallback(direction, evidence, analysis)

    async def approve_async(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        if not self.api_key:
            return _local_fallback(direction, evidence, analysis)
        try:
            raw = await self._call(direction, evidence, analysis)
            return _parse_llm_answer(raw, direction, evidence, analysis)
        except Exception:  # noqa: BLE001 - AI failure falls back to local (fail-safe)
            return _local_fallback(direction, evidence, analysis)

    async def _call(
        self, direction: Direction, evidence: AggregateEvidence, analysis: MarketAnalysis
    ) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": _build_prompt(direction, evidence, analysis)}]}]
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class GroqAIService(AIService):
    """Groq free-tier reasoning (optional; falls back to local)."""

    url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        timeout: float = 25.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        return _local_fallback(direction, evidence, analysis)

    async def approve_async(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        if not self.api_key:
            return _local_fallback(direction, evidence, analysis)
        try:
            raw = await self._call(direction, evidence, analysis)
            return _parse_llm_answer(raw, direction, evidence, analysis)
        except Exception:  # noqa: BLE001 - AI failure falls back to local (fail-safe)
            return _local_fallback(direction, evidence, analysis)

    async def _call(
        self, direction: Direction, evidence: AggregateEvidence, analysis: MarketAnalysis
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a disciplined AI trading-assistant decision layer."},
                {"role": "user", "content": _build_prompt(direction, evidence, analysis)},
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]


class AIServiceRouter(AIService):
    """Picks the configured provider, guaranteeing a local fallback."""

    def __init__(self, provider: str = "local") -> None:
        settings = get_settings()
        self.local = RuleBasedAIService()
        self.remote: AIService | None = None
        if provider == "gemini" and settings.gemini_api_key:
            self.remote = GeminiAIService(settings.gemini_api_key, settings.gemini_model)
        elif provider == "groq" and settings.groq_api_key:
            self.remote = GroqAIService(settings.groq_api_key, settings.groq_model)

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        return self.local.approve(direction, evidence, analysis)

    async def approve_async(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        if self.remote is not None:
            return await self.remote.approve_async(direction, evidence, analysis)
        return self.local.approve(direction, evidence, analysis)


def build_ai_service() -> AIService:
    settings = get_settings()
    return AIServiceRouter(provider=settings.ai_provider.lower())
