import asyncio
import sys
import time
import json

from typing import Dict, Any, List

import aiohttp
import websockets


SYMBOL = "BTCUSDT"  # Default trading pair, implemented optionally via argparse
REST_BASE = "https://fapi.binance.com"
WS_BASE   = "wss://fstream.binance.com/ws"
    

class AggTradeStreamer:
    """
    Binance USD(S)-M Futures aggregate trades:
    - Bootstrap recent aggTrades via REST
    - Stream live aggTrade events via WebSocket
    - Parse and print each trade in the exact requested shape
    """
    def __init__(self, symbol: str = "BTCUSDT", limit: int = 1000, print_speed: bool = True):
        self.symbol = symbol.upper()
        self.limit = limit
        self.print_speed = print_speed
        self.last_seen_a: int = -1
        self._latencies: List[float] = []

    @staticmethod
    def _format_trade(obj: Dict[str, Any]) -> str:
        out = [{
            "a": obj["a"],  # Aggregate tradeId
            "p": obj["p"],  # Price
            "q": obj["q"],  # Quantity
            "f": obj["f"],  # First tradeId
            "l": obj["l"],  # Last tradeId
            "T": obj["T"],  # Timestamp
            "m": obj["m"],  # Buyer is maker
        }]
        return json.dumps(out)

    def _print_trade(self, obj: Dict[str, Any]) -> None:
        trade = self._format_trade(obj)
        sys.stdout.write('.')
        # sys.stdout.write(self._format_trade(obj) + "\n")

    async def initialize_from_rest(self) -> None:
        """Fetch recent aggTrades via REST and print them; track highest aggregate tradeId.
        
        Ex 2 bullet point 1.

        Not necessary to async as this is a one-time operation before the websocket connection 
        but made async so it doesn't block the event loop.
        """
        url = f"{REST_BASE}/fapi/v1/aggTrades"
        params = {"symbol": self.symbol, "limit": self.limit}
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                trades = await resp.json()

        # REST returns a list of aggTrades already with desired keys (possibly with extras)
        for t in trades:
            self._print_trade(t)
            if t["a"] > self.last_seen_a:
                self.last_seen_a = t["a"]

    def _report_latency(self) -> None:
        """Report latency statistics.
        
        Ex 2 bullet point 3.
        """
        if not self.print_speed or not self._latencies:
            return
        xs = sorted(self._latencies)
        n = len(xs)
        p50 = xs[n // 2]
        p95 = xs[int(n * 0.95)]
        sys.stderr.write(f"parse_us p50={p50:.1f} p95={p95:.1f} n={n}\n")
        self._latencies.clear()

    async def stream(self) -> None:
        """Connect to websocket and parse aggTrade stream.
        
        Ex 2 bullet point 2.
        """
        ws_url = f"{WS_BASE}/{self.symbol.lower()}@aggTrade"
        # Server pings ~every few minutes; let client handle pings automatically.
        async with websockets.connect(ws_url, ping_interval=180, ping_timeout=600) as ws:
            async for raw in ws:
                t0 = time.perf_counter()
                evt = json.loads(raw)
                # websocket output includes extra fields.
                obj = {
                    "a": evt["a"],
                    "p": evt["p"],
                    "q": evt["q"],
                    "f": evt["f"],
                    "l": evt["l"],
                    "T": evt["T"],
                    "m": evt["m"]
                }
                # Drop duplicates that overlap with the REST initialization.
                if obj["a"] <= self.last_seen_a:
                    continue
                self._print_trade(obj)
                self.last_seen_a = obj["a"]

                if self.print_speed:
                    dt = (time.perf_counter() - t0) * 1e6
                    self._latencies.append(dt)
                    if len(self._latencies) >= 10_000:
                        self._report_latency()

    async def run(self) -> None:
        await self.initialize_from_rest()
        # Reconnect loop
        while True:
            try:
                await self.stream()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                sys.stderr.write(f"ws error: {e}; reconnecting shortly...\n")
                await asyncio.sleep(2)

## Optional CLI argument parsing
# import argparse
# def parse_args():
#     p = argparse.ArgumentParser(description="Binance Futures aggTrades stream parser")
#     p.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading pair, e.g. BTCUSDT")
#     p.add_argument("--limit", type=int, default=1000, help="Bootstrap aggTrades limit")
#     p.add_argument("--print-speed", action="store_true", help="Print parse latency stats")
#     return p.parse_args()

async def main():
    # args = parse_args()
    # streamer = AggTradeStreamer(symbol=args.symbol, limit=args.limit, print_speed=args.print_speed)
    streamer = AggTradeStreamer(symbol=SYMBOL, limit=1000, print_speed=True)
    await streamer.run()


if __name__ == "__main__":
    asyncio.run(main())