# Setup paths and environment
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import and run the unified market data process
from market_data_hourly_load import MarketDataHourlyLoad

if __name__ == "__main__":
    # Initialize and start the single, unified market data loader.
    # This process now handles both historical data refreshes and hourly RSI checks.
    market_loader = MarketDataHourlyLoad()
    market_loader.start()