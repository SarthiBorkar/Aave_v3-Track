"""Configuration for Aave V3 USDC Supply Analysis"""

# Polygon RPC Endpoints (replace with actual endpoints)
POLYGON_RPC_ENDPOINTS = [
    "https://polygon-mainnet.g.alchemy.com/v2/wDSruny3chAxEsPUN60ss",
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://matic-mainnet.chainstacklabs.com"
]

# Polygonscan API Configuration
POLYGONSCAN_API_URL = "https://polygon-mainnet.g.alchemy.com/v2/wDSruny3chAxEsPUN60ss"
POLYGONSCAN_API_KEY = "YourApiKeyToken"  # Replace with your actual Polygonscan API key

# Aave V3 Pool Contract Address on Polygon
AAVE_V3_POOL_ADDRESS = "0x625E7708f30cA75bfd92586e17077590C6004d88"

# Analysis Configuration
TARGET_EVENTS = 1000  # Number of events to fetch
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Output CSV file paths
OUTPUT_CSV = "usdc_supply_events.csv"
SUMMARY_CSV = "top_suppliers_summary.csv"
