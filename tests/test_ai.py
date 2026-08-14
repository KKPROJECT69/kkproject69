from hacker.analysis.market_analyzer import MarketAnalysis
from hacker.decision.ai import (
    AIApproval,
    GeminiAIService,
    GroqAIService,
    RuleBasedAIService,
    _extract_json,
    _parse_llm_answer,
)
from hacker.decision.engine import SignalDecisionEngine
from hacker.models.enums import Direction
from hacker.models.signal import AggregateEvidence, StrategyResult


def _analysis() -> MarketAnalysis:
    return MarketAnalysis(
        pair="X", trend="UP", structure="BULLISH", momentum=1.0, rsi=55.0,
        volatility=0.1, support_levels=[], resistance_levels=[], fvg=[],
        breakout_level=1.0, breakdown_level=1.0, last_close=100.0,
    )


def _evidence(direction: Direction = Direction.CALL) -> AggregateEvidence:
    return AggregateEvidence(
        direction=direction, confidence=80.0, agreement=1.0, conflicting=False,
        supporting=["a", "b"], opposing=[], risks=["r1"],
        total_directional=2, total_active=3,
    )


def test_rule_based_approves_direction():
    ai = RuleBasedAIService()
    out = ai.approve(Direction.CALL, _evidence(), _analysis())
    assert out.approved is True
    assert "CALL" in out.verdict


def test_extract_json_handles_markdown_fence():
    raw = '```json\n{"approved": true, "verdict": "STRONG CALL", "reasoning": "good"}\n```'
    assert _extract_json(raw)["approved"] is True


def test_parse_llm_answer_falls_back_on_garbage():
    out = _parse_llm_answer("not json at all", Direction.CALL, _evidence(), _analysis())
    assert out.approved is True  # falls back to local (which approves)


def test_parse_llm_answer_respects_verdict():
    raw = '{"approved": false, "verdict": "NO TRADE", "reasoning": "weak"}'
    out = _parse_llm_answer(raw, Direction.CALL, _evidence(), _analysis())
    assert out.approved is False


async def test_gemini_no_key_falls_back_to_local():
    ai = GeminiAIService(api_key="")
    out = await ai.approve_async(Direction.CALL, _evidence(), _analysis())
    assert out.approved is True  # no key -> local fallback, no error


async def test_groq_no_key_falls_back_to_local():
    ai = GroqAIService(api_key="")
    out = await ai.approve_async(Direction.PUT, _evidence(Direction.PUT), _analysis())
    assert out.approved is True


async def test_decision_engine_async_awaits_ai():
    calls = {"n": 0}

    class FakeAI:
        def approve(self, *a, **k):
            calls["n"] += 1
            return AIApproval(True, "STRONG CALL", "ok")

        async def approve_async(self, *a, **k):
            calls["n"] += 1
            return AIApproval(True, "STRONG CALL", "ok")

    eng = SignalDecisionEngine(ai=FakeAI(), min_confidence=70.0)  # type: ignore[arg-type]
    results = [
        StrategyResult("a", "a", Direction.CALL, 80.0),
        StrategyResult("b", "b", Direction.CALL, 76.0),
    ]
    decision = await eng.decide_async(results, _analysis())
    assert decision.approved is True
    assert calls["n"] == 1  # async path used
