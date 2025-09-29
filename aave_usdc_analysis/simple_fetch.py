import sys
from web3 import Web3

def fetch_aave_v3_usdc_supply():
    """
    Fetch USDC supply information from Aave V3 Pool on Polygon
    """
    # Polygon RPC endpoints (multiple for redundancy)
    RPC_ENDPOINTS = [
        "https://polygon-mainnet.g.alchemy.com/v2/wDSruny3chAxEsPUN60ss",
        "https://capable-attentive-daylight.matic.quiknode.pro/513fb36c6d1d6c5a3a340d703e1aa87c8136314e/",
        "https://polygon-mainnet.infura.io/v3/0d41b31a1502442ebadaa011c2e11311"
    ]

    # Aave V3 Pool contract address
    POOL_ADDRESS = "0x625E7708f30cA75bfd92586e17077590C6004d88"

    # USDC token address on Polygon
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    # Simplified ABI for Supply event
    POOL_ABI = [{
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "reserve", "type": "address"},
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": True, "name": "onBehalfOf", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "referralCode", "type": "uint16"}
        ],
        "name": "Supply",
        "type": "event"
    }]

    # Try multiple RPC endpoints
    for rpc_url in RPC_ENDPOINTS:
        try:
            # Connect to Polygon network with extended timeout
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
            
            # Verify connection
            if not w3.is_connected():
                print(f"❌ Failed to connect to {rpc_url}")
                continue

            # Create contract instance
            pool_contract = w3.eth.contract(
                address=w3.to_checksum_address(POOL_ADDRESS), 
                abi=POOL_ABI
            )

            # Get current block
            current_block = w3.eth.block_number
            
            # Define block range (last 20 blocks)
            from_block = max(0, current_block - 20)
            to_block = current_block

            # Prepare event signature
            event_signature_hash = w3.keccak(
                text="Supply(address,address,address,uint256,uint16)"
            ).hex()

            # Prepare topics with proper hex encoding
            topics = [
                event_signature_hash,
                None,  # user
                None,  # onBehalfOf
                '0x' + w3.to_hex(w3.to_bytes(hexstr=w3.to_checksum_address(USDC_ADDRESS)))[2:].zfill(64)  # reserve
            ]

            # Fetch logs
            logs = w3.eth.get_logs({
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': w3.to_checksum_address(POOL_ADDRESS),
                'topics': topics
            })

            # Analyze events
            print(f"\n📊 Found {len(logs)} USDC Supply events")

            # Aggregate data
            suppliers = {}
            total_supply = 0

            for log in logs:
                try:
                    # Decode log
                    event_data = pool_contract.events.Supply().process_log(log)
                    
                    user = event_data['args']['user']
                    amount = event_data['args']['amount'] / (10 ** 6)  # USDC has 6 decimals
                    
                    if user not in suppliers:
                        suppliers[user] = {
                            'total_supply': 0,
                            'transaction_count': 0
                        }
                    
                    suppliers[user]['total_supply'] += amount
                    suppliers[user]['transaction_count'] += 1
                    total_supply += amount
                
                except Exception as event_error:
                    print(f"⚠️ Error processing event: {event_error}")

            # Sort suppliers by total supply
            sorted_suppliers = sorted(
                suppliers.items(), 
                key=lambda x: x[1]['total_supply'], 
                reverse=True
            )

            # Print results
            print("\n🏆 TOP 10 SUPPLIERS:")
            print("-" * 60)
            print(f"{'Address':<42} {'Total Supply (USDC)':>20} {'Transactions':>15}")
            print("-" * 60)
            
            for address, data in sorted_suppliers[:10]:
                print(f"{address} {data['total_supply']:>20.2f} {data['transaction_count']:>15}")
            
            print("\n-" * 60)
            print(f"💰 Total USDC Supplied: {total_supply:.2f}")
            print(f"👥 Total Unique Suppliers: {len(suppliers)}")

            # Successful execution, exit the function
            return

        except Exception as rpc_error:
            print(f"⚠️ Error with RPC {rpc_url}: {rpc_error}")
    
    # If all RPC endpoints fail
    print("❌ Failed to fetch data from all RPC endpoints")
    sys.exit(1)

def main():
    try:
        fetch_aave_v3_usdc_supply()
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
