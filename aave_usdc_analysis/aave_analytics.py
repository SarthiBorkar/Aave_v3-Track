import sys
from web3 import Web3

# Polygon RPC URL (use the Alchemy endpoint)
RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/wDSruny3chAxEsPUN60ss"

# Aave V3 Pool address (as specified by user)
POOL_ADDRESS = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"

# Contract address (as specified by user)
CONTRACT_ADDRESS = "0x625E7708f30cA75bfd92586e17077590C6004d88"


# USDC token address on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Comprehensive ABI for Pool contract interactions
POOL_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "configuration", "type": "uint256"},
                    {"internalType": "uint128", "name": "liquidityIndex", "type": "uint128"},
                    {"internalType": "uint128", "name": "currentLiquidityRate", "type": "uint128"},
                    {"internalType": "uint128", "name": "variableBorrowIndex", "type": "uint128"},
                    {"internalType": "uint128", "name": "currentVariableBorrowRate", "type": "uint128"},
                    {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"},
                    {"internalType": "address", "name": "aTokenAddress", "type": "address"},
                    {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
                    {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"}
                ],
                "internalType": "struct DataTypes.ReserveData",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "implementation",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_aave_usdc_analytics():
    """
    Fetch USDC pool analytics from Aave V3 Pool
    """
    # List of RPC endpoints to try
    RPC_ENDPOINTS = [
        "https://polygon-mainnet.g.alchemy.com/v2/wDSruny3chAxEsPUN60ss",
        "https://polygon-rpc.com",
        "https://rpc-mainnet.maticvigil.com"
    ]

    for rpc_url in RPC_ENDPOINTS:
        try:
            # Connect to Polygon network
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 20}))
            
            # Verify connection
            if not w3.is_connected():
                print(f"❌ Failed to connect to {rpc_url}")
                continue

            # Create contract instance
            pool_contract = w3.eth.contract(
                address=w3.to_checksum_address(POOL_ADDRESS), 
                abi=POOL_ABI
            )

            # Try to get implementation address
            try:
                impl_address = pool_contract.functions.implementation().call()
                print(f"🔗 Implementation Address: {impl_address}")
            except Exception as impl_error:
                print(f"⚠️ Could not fetch implementation address: {impl_error}")
                impl_address = None

            # Get USDC reserve data
            usdc_reserve_data = pool_contract.functions.getReserveData(
                w3.to_checksum_address(USDC_ADDRESS)
            ).call()

            # Unpack reserve data
            (
                configuration,
                liquidity_index,
                current_liquidity_rate,
                variable_borrow_index,
                current_variable_borrow_rate,
                last_update_timestamp,
                atoken_address,
                stable_debt_token_address,
                variable_debt_token_address
            ) = usdc_reserve_data

            # Convert rates from ray to percentage
            def ray_to_percentage(ray_value):
                return (ray_value / 10**27) * 100

            # Print analytics
            print("\n🏦 AAVE V3 USDC POOL ANALYTICS")
            print("=" * 50)
            print(f"📍 Pool Address: {POOL_ADDRESS}")
            print(f"📍 Contract Address: {CONTRACT_ADDRESS}")
            if impl_address:
                print(f"📍 Implementation Address: {impl_address}")
            
            print("\n📊 Pool Metrics:")
            print(f"   Liquidity Index: {liquidity_index}")
            print(f"   Current Liquidity Rate: {ray_to_percentage(current_liquidity_rate):.2f}%")
            print(f"   Current Variable Borrow Rate: {ray_to_percentage(current_variable_borrow_rate):.2f}%")
            print(f"   Last Update Timestamp: {last_update_timestamp}")
            
            print("\n🔗 Contract Addresses:")
            print(f"   aToken: {atoken_address}")
            print(f"   Stable Debt Token: {stable_debt_token_address}")
            print(f"   Variable Debt Token: {variable_debt_token_address}")
            print("=" * 50)

            return {
                'pool_address': POOL_ADDRESS,
                'contract_address': CONTRACT_ADDRESS,
                'implementation_address': impl_address,
                'liquidity_index': liquidity_index,
                'liquidity_rate': ray_to_percentage(current_liquidity_rate),
                'borrow_rate': ray_to_percentage(current_variable_borrow_rate),
                'last_update': last_update_timestamp,
                'atoken_address': atoken_address,
                'stable_debt_token': stable_debt_token_address,
                'variable_debt_token': variable_debt_token_address
            }

        except Exception as e:
            print(f"⚠️ Error with RPC {rpc_url}: {e}")

    print("❌ Failed to fetch USDC pool analytics from all endpoints")
    return None

def main():
    try:
        get_aave_usdc_analytics()
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
