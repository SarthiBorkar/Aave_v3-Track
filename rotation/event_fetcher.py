"""
Event Fetcher for Aave V3 Pool Supply Events
"""

from typing import List, Dict
from web3 import Web3
from aave_usdc_analysis.connection import Web3ConnectionManager
from aave_usdc_analysis.config import TARGET_EVENTS
import time

# Add missing configuration constants
BLOCKS_PER_BATCH = 10000  # Number of blocks to fetch in each batch
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC token address on Polygon
USDC_DECIMALS = 6  # USDC has 6 decimal places


class SupplyEventFetcher:
    """Fetches and parses Supply events from Aave V3 Pool"""
    
    def __init__(self, connection_manager: Web3ConnectionManager, contract):
        """
        Initialize event fetcher
        
        Args:
            connection_manager: Web3 connection manager instance
            contract: Web3 contract instance for Aave V3 Pool
        """
        self.conn_mgr = connection_manager
        self.w3 = connection_manager.get_web3()
        self.contract = contract
        self.usdc_checksum = Web3.to_checksum_address(USDC_ADDRESS)
    
    def fetch_supply_events(self, target_count: int = TARGET_EVENTS) -> List[Dict]:
        """
        Fetch the last N Supply events for USDC
        
        Args:
            target_count: Number of events to fetch
            
        Returns:
            List of parsed event dictionaries
        """
        print(f"\nFetching last {target_count} USDC Supply events...")
        
        # Get current block
        current_block = self.conn_mgr.execute_with_retry(
            lambda: self.w3.eth.block_number
        )
        print(f"Current block: {current_block}")
        
        all_events = []
        from_block = current_block
        
        # Fetch events in batches going backwards
        max_attempts = 5
        attempt = 0
        
        while len(all_events) < target_count and from_block > 0 and attempt < max_attempts:
            to_block = from_block
            from_block = max(0, to_block - BLOCKS_PER_BATCH)
            
            print(f"Fetching blocks {from_block} to {to_block}...", end=" ")
            
            try:
                # Create event filter for Supply events with USDC reserve
                event_filter = self.contract.events.Supply.create_filter(
                    fromBlock=from_block,
                    toBlock=to_block,
                    argument_filters={'reserve': self.usdc_checksum} if hasattr(self, 'usdc_checksum') else {}
                )
                
                # Get all entries
                events = event_filter.get_all_entries()
                
                if events:
                    # Parse events
                    parsed_events = []
                    for event in events:
                        parsed_event = self._parse_supply_event(event)
                        if parsed_event:
                            parsed_events.append(parsed_event)
                    
                    all_events.extend(parsed_events)
                    print(f"✓ Found {len(parsed_events)} events (total: {len(all_events)})")
                else:
                    print("✓ No events in this range")
                
                # Stop if we have enough events
                if len(all_events) >= target_count:
                    break
                    
            except Exception as e:
                print(f"✗ Error in event fetching: {e}")
                attempt += 1
                
                # Exponential backoff
                import time
                time.sleep(2 ** attempt)
        
        # Return only the requested number of events (most recent)
        result = all_events[:target_count]
        print(f"\n✓ Successfully fetched {len(result)} Supply events")
        
        if len(result) == 0:
            print("⚠️ WARNING: No events were found. Check contract address and RPC endpoint.")
        
        return result
    
    def _fetch_events_batch(self, from_block: int, to_block: int) -> List[Dict]:
        """
        Fetch events for a specific block range
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            
        Returns:
            List of parsed events
        """
        # Get Supply event logs
        event_filter = self.contract.events.Supply.create_filter(
            fromBlock=from_block,
            toBlock=to_block,
            argument_filters={'reserve': self.usdc_checksum}
        )
        
        events = event_filter.get_all_entries()
        
        # Parse events
        parsed_events = []
        for event in events:
            parsed_event = self._parse_supply_event(event)
            if parsed_event:
                parsed_events.append(parsed_event)
        
        return parsed_events
    
    def _parse_supply_event(self, event) -> Dict:
        """
        Parse a Supply event into a structured dictionary
        
        Args:
            event: Raw event from Web3
            
        Returns:
            Parsed event dictionary
        """
        try:
            args = event['args']
            
            # Convert amount from raw units to USDC (6 decimals)
            amount_raw = args['amount']
            amount_usdc = amount_raw / (10 ** USDC_DECIMALS)
            
            return {
                'block_number': event['blockNumber'],
                'transaction_hash': event['transactionHash'].hex(),
                'reserve': args['reserve'],
                'user': args['user'],
                'on_behalf_of': args['onBehalfOf'],
                'amount_raw': amount_raw,
                'amount_usdc': amount_usdc,
                'referral_code': args.get('referralCode', 0),
            }
        except Exception as e:
            print(f"Warning: Failed to parse event: {e}")
            return None
    
    def get_block_timestamp(self, block_number: int) -> int:
        """
        Get timestamp for a block number
        
        Args:
            block_number: Block number
            
        Returns:
            Unix timestamp
        """
        try:
            block = self.conn_mgr.execute_with_retry(
                lambda: self.w3.eth.get_block(block_number)
            )
            return block['timestamp']
        except Exception as e:
            print(f"Warning: Could not fetch timestamp for block {block_number}: {e}")
            return 0
    
    def enrich_events_with_timestamps(self, events: List[Dict]) -> List[Dict]:
        """
        Add timestamps to events (optional, for time-series analysis)
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Events with timestamps added
        """
        print("\nEnriching events with timestamps...")
        
        # Get unique block numbers
        unique_blocks = list(set(event['block_number'] for event in events))
        
        # Fetch timestamps for unique blocks
        block_timestamps = {}
        for i, block in enumerate(unique_blocks, 1):
            if i % 10 == 0:
                print(f"Fetching timestamps: {i}/{len(unique_blocks)}")
            
            timestamp = self.get_block_timestamp(block)
            block_timestamps[block] = timestamp
        
        # Add timestamps to events
        for event in events:
            event['timestamp'] = block_timestamps.get(event['block_number'], 0)
        
        print("✓ Timestamps added")
        return events