# Binance USDⓈ-M Futures aggTrades Stream Parser
## Overview

This script connects to Binance’s USDⓈ-M Futures Aggregate Trades (aggTrades) endpoint, retrieves recent trades via REST, then switches to a WebSocket stream for live updates. It parses each trade into the required format and measures per-trade parse latency.

## Features:
- Initialize aggTrade data via REST: GET /fapi/v1/aggTrades to fetch recent trades.
- Live streaming via WebSocket: <symbol>@aggTrade for real-time updates.
- Deduplication: Drops trades already received from the REST initialization.
- Exact output shape (prints each trade as):
```
[
  {
    "a": 26129,
    "p": "0.01633102",
    "q": "4.70443515",
    "f": 27781,
    "l": 27781,
    "T": 1498793709153,
    "m": true
  }
]
```
- Latency metrics: Reports p50/p95 parse time in microseconds.

## Requirements
- Python 3.9+
- Dependencies:
```
    pip install aiohttp websockets
```

## Usage

Default (hardcoded symbol BTCUSDT):
```
python aggtrade_stream.py
```

Optional (commented out) CLI arguments using `argparse`:
```
python aggtrade_stream.py --symbol ETHUSDT --limit 500 --print-speed
```

## Algorithmic Complexity and Speed

Parsing algorithm:
- Per message:
  - JSON decode: O(m), where m = message size (bounded and small → treated as O(1))
  - Data extraction and dedupe check: O(1)
  - Output formatting: O(1)
- Total over N messages: O(N) time.


Sample latency outputs:
```
parse_us p50=26.4 p95=125.8 n=10000
parse_us p50=26.9 p95=122.2 n=10000
parse_us p50=25.3 p95=124.2 n=10000
parse_us p50=23.9 p95=116.2 n=10000
parse_us p50=21.8 p95=111.5 n=10000
parse_us p50=20.7 p95=105.4 n=10000
```

On my machine, measured per-message processing (excluding network receive) over 10k-message windows shows p50 ≈ 21–27 µs and p95 ≈ 105–126 µs, implying a theoretical capacity on the order of ~37k–48k trades/sec at median and ~8k–9.5k trades/sec at the 95th percentile. End-to-end latency is dominated by network and stdout I/O, not the parsing algorithm itself.

## Notes
- WebSocket connections may be terminated periodically by Binance; the script auto-reconnects.
- Currently, data is only printed to stdout. If storage, return values, or processing are needed, the logic would need to be adapted (e.g., using `dataclasses` or another structured format).
- If the WebSocket connection is delayed or reconnects, trades may be missed. Can use the REST api to fill gaps using `last_seen_a` variable in code and `fromId` api param.
- Binance has REST rate limits that need to be taken into account. WebSocket connection my be affected if limits are exceeded.
- API streams more variables than needed, which is fine. Changes to shema  (e.g., changing fields) would need to be monitored.
- Current implementation is for a single currency pair (hardcoded but can be changed). Multiple currency functionality not implemented.