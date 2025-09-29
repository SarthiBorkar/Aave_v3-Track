from web3 import Web3

# Replace with your Alchemy or Infura RPC URL
rpc_url = "https://eth-mainnet.g.alchemy.com/v2/HujE-yHioVLapLcDnb2qrWTm77xR4qHJ"

w3 = Web3(Web3.HTTPProvider(rpc_url))

print("Connected:", w3.is_connected())
print("Latest block:", w3.eth.block_number)
