"""
Web3 Connection Manager with RPC rotation and failover
"""

import time
import requests
from typing import Optional, List
from web3 import Web3
from web3.exceptions import Web3Exception
from .config import (
    POLYGON_RPC_ENDPOINTS,
    POLYGONSCAN_API_URL,
    POLYGONSCAN_API_KEY,
    MAX_RETRIES,
    RETRY_DELAY,
)


class Web3ConnectionManager:
    """Manages Web3 connections with automatic RPC rotation"""
    
    def __init__(self, rpc_endpoints: List[str] = None):
        """
        Initialize connection manager
        
        Args:
            rpc_endpoints: List of RPC endpoint URLs
        """
        self.rpc_endpoints = rpc_endpoints or POLYGON_RPC_ENDPOINTS
        self.current_rpc_index = 0
        self.w3: Optional[Web3] = None
        self._connect()
    
    def _connect(self) -> bool:
        """
        Establish connection to current RPC endpoint
        
        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(len(self.rpc_endpoints)):
            try:
                endpoint = self.rpc_endpoints[self.current_rpc_index]
                print(f"Connecting to RPC: {endpoint}")
                
                self.w3 = Web3(Web3.HTTPProvider(endpoint))
                
                if self.w3.is_connected():
                    print(f"✓ Connected to {endpoint}")
                    return True
                else:
                    print(f"✗ Failed to connect to {endpoint}")
                    self._rotate_rpc()
            except Exception as e:
                print(f"✗ Error connecting to {endpoint}: {e}")
                self._rotate_rpc()
        
        raise ConnectionError("Failed to connect to any RPC endpoint")
    
    def _rotate_rpc(self):
        """Switch to next RPC endpoint"""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_endpoints)
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic and RPC rotation
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the function call
        """
        retries = 0
        last_exception = None
        
        while retries < MAX_RETRIES * len(self.rpc_endpoints):
            try:
                return func(*args, **kwargs)
            except (Web3Exception, requests.exceptions.RequestException) as e:
                last_exception = e
                retries += 1
                
                print(f"✗ Error (attempt {retries}): {e}")
                
                if retries % MAX_RETRIES == 0:
                    print("Rotating to next RPC endpoint...")
                    self._rotate_rpc()
                    self._connect()
                else:
                    time.sleep(RETRY_DELAY)
        
        raise last_exception or Exception("Max retries exceeded")
    
    def get_web3(self) -> Web3:
        """Get current Web3 instance"""
        return self.w3


def fetch_contract_abi(contract_address: str) -> dict:
    """
    Fetch contract ABI for Aave V3 Pool proxy contract
    
    Args:
        contract_address: Contract address to fetch ABI for
        
    Returns:
        Contract ABI as dict
    """
    print(f"\nFetching ABI for contract {contract_address}...")
    
    # Proxy contract ABI
    proxy_abi = [
        {"inputs":[{"internalType":"address","name":"admin","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
        {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"implementation","type":"address"}],"name":"Upgraded","type":"event"},
        {"stateMutability":"payable","type":"fallback"},
        {"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[],"name":"implementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[{"internalType":"address","name":"_logic","type":"address"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"initialize","outputs":[],"stateMutability":"payable","type":"function"},
        {"inputs":[{"internalType":"address","name":"newImplementation","type":"address"}],"name":"upgradeTo","outputs":[],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[{"internalType":"address","name":"newImplementation","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"upgradeToAndCall","outputs":[],"stateMutability":"payable","type":"function"}
    ]
    
    print("✓ Using proxy contract ABI")
    return proxy_abi


def load_contract(w3: Web3, address: str, abi: dict):
    """
    Load contract with checksum address
    
    Args:
        w3: Web3 instance
        address: Contract address
        abi: Contract ABI
        
    Returns:
        Web3 contract instance
    """
    checksum_address = Web3.to_checksum_address(address)
    return w3.eth.contract(address=checksum_address, abi=abi)


def get_implementation_address(w3: Web3, proxy_address: str) -> str:
    """
    Get the implementation contract address from a proxy contract
    
    Args:
        w3: Web3 instance
        proxy_address: Address of the proxy contract
        
    Returns:
        Implementation contract address
    """
    print(f"\nFetching implementation address for {proxy_address}...")
    
    # ABI for getting implementation address (multiple possible methods)
    proxy_abis = [
        # Method 1: Standard implementation() function
        {
            "inputs": [],
            "name": "implementation",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        # Method 2: Alternative implementation retrieval
        {
            "inputs": [],
            "name": "getImplementation",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Checksum the address
    checksum_address = w3.to_checksum_address(proxy_address)
    
    # Try different ABI methods
    for abi in proxy_abis:
        try:
            # Create contract instance with current ABI
            proxy_contract = w3.eth.contract(address=checksum_address, abi=[abi])
            
            # Try to call the function
            implementation_address = getattr(proxy_contract.functions, abi['name'])().call()
            
            print(f"✓ Found implementation contract: {implementation_address}")
            return implementation_address
        
        except Exception as e:
            print(f"✗ Method {abi['name']} failed: {e}")
    
    # If all methods fail, raise an informative error
    raise ValueError(f"Could not retrieve implementation address for {proxy_address}. "
                     "Verify the contract is a proxy and the address is correct.")