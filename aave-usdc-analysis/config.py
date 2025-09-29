"""
Configuration file for Aave V3 USDC Supply Analysis
"""

# Aave V3 Pool Contract on Polygon
AAVE_V3_POOL_ADDRESS = "0x625E7708f30cA75bfd92586e17077590C6004d88"

# USDC Token Address on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# USDC has 6 decimals
USDC_DECIMALS = 6

# Polygon RPC Endpoints (add your own endpoints here)
POLYGON_RPC_ENDPOINTS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.matic.network",
    "https://rpc-mainnet.maticvigil.com",
    "https://polygon-mainnet.public.blastapi.io",
    "https://rpc.ankr.com/polygon",
]

# Polygonscan API configuration
POLYGONSCAN_API_URL = "https://polygon-mainnet.g.alchemy.com/v2/HujE-yHioVLapLcDnb2qrWTm77xR4qHJ"
POLYGONSCAN_API_KEY = ""  # Optional: Add your API key for higher rate limits

# Event fetching configuration
TARGET_EVENTS = 1000  # Number of Supply events to fetch
BLOCKS_PER_BATCH = 2000  # Block range per query
MAX_RETRIES = 3  # Max retries per RPC call
RETRY_DELAY = 2  # Seconds to wait between retries

# Output configuration
OUTPUT_CSV = "aave_v3_usdc_supply_analysis.csv"
SUMMARY_CSV = "aave_v3_usdc_supply_summary.csv"