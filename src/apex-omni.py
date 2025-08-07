from apexomni.constants import APEX_OMNI_HTTP_TEST
from apexomni.http_public import HttpPublic

client = HttpPublic(APEX_OMNI_HTTP_TEST)
print(client.configs_v3())
print(client.klines_v3(symbol="ETHUSDT",interval=5,start=1718358480, end=1718950620, limit=5))
print(client.depth_v3(symbol="BTCUSDT"))
print(client.trades_v3(symbol="BTCUSDT"))
print(client.klines_v3(symbol="BTCUSDT",interval="15"))
print(client.ticker_v3(symbol="BTCUSDT"))
print(client.history_funding_v3(symbol="BTC-USDT"))