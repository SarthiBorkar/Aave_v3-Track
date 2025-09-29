"""
Main script for Aave V3 USDC Supply Analysis on Polygon
"""

import sys
from web3 import Web3
from aave_usdc_analysis.connection import (
    Web3ConnectionManager, 
    fetch_contract_abi, 
    load_contract,
    get_implementation_address
)
from rotation.event_fetcher import SupplyEventFetcher
from rotation.analyzer import SupplyEventAnalyzer
from aave_usdc_analysis.config import AAVE_V3_POOL_ADDRESS, TARGET_EVENTS, POLYGON_RPC_ENDPOINTS


def main():
    """Main execution flow"""
    print("="*60)
    print("AAVE V3 USDC SUPPLY ANALYSIS - POLYGON")
    print("="*60)
    
    try:
        # Step 1: Initialize Web3 connection with RPC rotation
        print("\n[1/5] Initializing Web3 connection...")
        conn_mgr = Web3ConnectionManager(POLYGON_RPC_ENDPOINTS)
        w3 = conn_mgr.get_web3()
        
        # Verify connection
        chain_id = conn_mgr.execute_with_retry(lambda: w3.eth.chain_id)
        print(f"✓ Connected to Polygon (Chain ID: {chain_id})")
        
        # Step 2: Determine contract address to use
        print("\n[2/5] Preparing contract interaction...")
        contract_address = AAVE_V3_POOL_ADDRESS
        
        try:
            # Attempt to get implementation address
            impl_address = get_implementation_address(w3, contract_address)
            print(f"✓ Using implementation address: {impl_address}")
            contract_address = impl_address
        except Exception as impl_error:
            print(f"⚠️ Could not retrieve implementation address: {impl_error}")
            print("Falling back to original contract address")
        
        # Fetch contract ABI
        print("\nFetching Aave V3 Pool contract ABI...")
        abi = fetch_contract_abi(contract_address)
        
        # Load contract
        contract = load_contract(w3, contract_address, abi)
        print(f"✓ Contract loaded: {contract_address}")
        
        # Step 3: Fetch Supply events
        print(f"\n[3/5] Fetching Supply events...")
        fetcher = SupplyEventFetcher(conn_mgr, contract)
        events = fetcher.fetch_supply_events(target_count=TARGET_EVENTS)
        
        if not events:
            print("✗ No events found. Exiting.")
            return
        
        # Optional: Add timestamps for time-series analysis
        # Uncomment the line below if you want timestamps (slower)
        # events = fetcher.enrich_events_with_timestamps(events)
        
        # Step 4: Analyze data
        print(f"\n[4/5] Analyzing data...")
        analyzer = SupplyEventAnalyzer(events)
        results = analyzer.analyze()
        
        # Step 5: Save results
        print(f"\n[5/5] Saving results...")
        output_files = analyzer.save_to_csv()
        
        # Print top 10 suppliers
        print("\n🏆 TOP 10 SUPPLIERS BY TOTAL USDC:")
        top_suppliers = analyzer.get_top_suppliers(10)
        for idx, row in top_suppliers.iterrows():
            print(f"   {idx+1}. {row['address']}")
            print(f"       Total: ${row['total_usdc']:,.2f} | Transactions: {int(row['tx_count'])}")
        
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE!")
        print("="*60)
        print(f"📁 Output files:")
        for file in output_files:
            print(f"   - {file}")
        print("\nYou can now use these CSV files for further analysis or dashboarding.")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()