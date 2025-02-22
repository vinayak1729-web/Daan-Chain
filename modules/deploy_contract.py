from web3 import Web3
import json

# Connect to local blockchain (Ganache)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# Load contract ABI and bytecode
with open('contracts/EmergencyRelief.json', 'r') as f:
    contract_data = json.load(f)

contract_abi = contract_data['abi']
contract_bytecode = contract_data['bytecode']

# Deploy contract
account = w3.eth.accounts[0]
Contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
tx_hash = Contract.constructor().transact({'from': account})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# Save contract address
contract_address = tx_receipt.contractAddress
with open('contracts/contract_config.json', 'w') as f:
    json.dump({
        'address': contract_address,
        'abi': contract_abi
    }, f)

print(f"Contract deployed at: {contract_address}")
