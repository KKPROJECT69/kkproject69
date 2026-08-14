from hacker.data_sources.mock import MockMarketSource
from hacker.models.enums import Timeframe


async def test_mock_source_returns_ordered_candles():
    source = MockMarketSource(seed=1)
    candles = await source.get_candles("USDBDT_otc", Timeframe.M1, count=50)
    assert len(candles) == 50
    assert candles[0].timestamp < candles[-1].timestamp
    assert all(c.low <= c.high for c in candles)
