# Trading Bot Project Plan

A agent/bot to monitor the crypto market, send alerts when a token is oversold (oportunity) and open/close orders in a perpetuals exchange via commands on telegram bot

## Completed
- [x] Function to call CoinGecko API and fetch market data.
- [x] Implement RSI (Relative Strength Index) calculation.
- [x] Integrate with a Telegram bot for sending alerts.
- [x] Implement a robust API rate limiter to prevent getting blocked.
- [x] Refactor the data loading process into a single, unified, and scheduled job.

## Next Steps
- [ ] Add docker and docker-compose files.
- [ ] Integrate with a cryptocurrency exchange API to place trade orders.
- [ ] Create a log file
- [ ] Send the chart togehter with the alert