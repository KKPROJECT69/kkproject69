from hacker.data_sources.mock import MockMarketSource
from hacker.data_sources.novex import _to_novex_pair
from hacker.data_sources.oanda import OandaMarketSource, normalize_oanda_instrument
from hacker.data_sources.quotex import QuotexProxySource, to_quotex_symbol
from hacker.data_sources.router import MarketSourceRouter, is_otc
from hacker.models.enums import Timeframe

# --- captured real payloads -------------------------------------------------

QUOTEX_PAYLOAD = {
    "symbol": "USDBDT-OTC",
    "interval": "1m",
    "updated_at": "2026-08-14T07:08:07.632Z",
    "candles": {
        "symbol": "USDBDT-OTCQ",
        "interval": "1m",
        "candles": [
            {"time": 1786691160, "open": 127.986, "high": 127.994, "low": 127.957, "close": 127.994, "volume": 1},
            {"time": 1786691220, "open": 127.989, "high": 127.999, "low": 127.921, "close": 127.927, "volume": 1},
            {"time": 1786691280, "open": 127.929, "high": 127.93, "low": 127.92, "close": 127.92, "volume": 1},
        ],
    },
}

OANDA_PAYLOAD = {
    "instrument": "EUR_USD",
    "granularity": "M1",
    "candles": [
        {
            "complete": True,
            "volume": 123,
            "time": "2026-08-14T07:00:00.000000000Z",
            "mid": {"o": "1.08000", "h": "1.09000", "l": "1.07000", "c": "1.08500"},
        }
    ],
}


async def test_mock_source_returns_ordered_candles():
    source = MockMarketSource(seed=1)
    candles = await source.get_candles("USDBDT_otc", Timeframe.M1, count=50)
    assert len(candles) == 50
    assert candles[0].timestamp < candles[-1].timestamp
    assert all(c.low <= c.high for c in candles)


def test_quotex_symbol_normalization():
    assert to_quotex_symbol("USDBDT_otc") == "USDBDT-OTC"
    assert to_quotex_symbol("USDBDT-OTC") == "USDBDT-OTC"
    assert to_quotex_symbol("usdbdt_otc") == "USDBDT-OTC"


def test_novex_pair_normalization():
    assert _to_novex_pair("USDBDT-OTC") == "USDBDT_otc"
    assert _to_novex_pair("USDBDT_otc") == "USDBDT_otc"


def test_oanda_instrument_normalization():
    assert normalize_oanda_instrument("EURUSD") == "EUR_USD"
    assert normalize_oanda_instrument("EUR_USD") == "EUR_USD"
    assert normalize_oanda_instrument("eur/usd") == "EUR_USD"


def test_quotex_parse_candles():
    candles = QuotexProxySource._parse_candles(QUOTEX_PAYLOAD)
    assert len(candles) == 3
    assert candles[0].close == 127.994
    assert candles[0].timestamp.tzinfo is not None  # aware UTC


def test_oanda_parse_candles():
    candles = OandaMarketSource._parse_candles(OANDA_PAYLOAD)
    assert len(candles) == 1
    assert candles[0].close == 1.085
    assert candles[0].open == 1.08


def test_is_otc():
    assert is_otc("USDBDT_otc") is True
    assert is_otc("USDBDT-OTC") is True
    assert is_otc("EUR_USD") is False


def test_router_routes_otc_to_quotex():
    router = MarketSourceRouter()
    assert router._source_for("USDBDT_otc").name == "quotex"
    assert router._source_for("EUR_USD").name == "oanda"
