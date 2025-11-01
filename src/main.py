#%%
# Setup paths and environment
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import and run the process
from processes import CheckMarketsHourly

if __name__ == "__main__":
    market_checker = CheckMarketsHourly()
    market_checker.start()