"""
Smart Contract Deployment Script for FaceVerificationRegistry.sol.
Deploys contract to EVM Testnets (Sepolia / Polygon Amoy / Local Hardhat / Anvil).
Updates .env with deployed CONTRACT_ADDRESS.
"""

import sys
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

import config

load_dotenv()

# Precompiled ABI & Bytecode fallback artifact
COMPILED_ARTIFACT_FILE = config.CONTRACTS_DIR / "FaceVerificationRegistry.json"

def get_or_compile_contract():
    """Returns ABI and Bytecode for FaceVerificationRegistry."""
    sol_file = config.CONTRACTS_DIR / "FaceVerificationRegistry.sol"
    
    # Check if py-solc-x can compile directly
    try:
        from solcx import compile_standard, install_solc
        try:
            install_solc("0.8.20")
        except Exception:
            pass

        with open(sol_file, "r") as f:
            sol_source = f.read()

        compiled_sol = compile_standard(
            {
                "language": "Solidity",
                "sources": {"FaceVerificationRegistry.sol": {"content": sol_source}},
                "settings": {
                    "outputSelection": {
                        "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                    }
                },
            },
            solc_version="0.8.20"
        )
        
        contract_data = compiled_sol["contracts"]["FaceVerificationRegistry.sol"]["FaceVerificationRegistry"]
        abi = contract_data["abi"]
        bytecode = contract_data["evm"]["bytecode"]["object"]

        # Save compiled artifact
        artifact = {"abi": abi, "bytecode": bytecode}
        with open(COMPILED_ARTIFACT_FILE, "w") as f:
            json.dump(artifact, f, indent=2)

        return abi, bytecode
    except Exception as e:
        print(f"[Deployer] Standard solc compile skipped ({e}), checking precompiled artifact...")

    if COMPILED_ARTIFACT_FILE.exists():
        with open(COMPILED_ARTIFACT_FILE, "r") as f:
            art = json.load(f)
            return art["abi"], art["bytecode"]

    raise RuntimeError("Could not compile Solidity contract and no precompiled artifact found.")

def deploy_to_network(rpc_url: str = config.EVM_RPC_URL, private_key: str = config.PRIVATE_KEY):
    """Deploys FaceVerificationRegistry to EVM RPC network."""
    print(f"Connecting to RPC: {rpc_url}...")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"Error: Unable to connect to EVM RPC at '{rpc_url}'. Ensure local EVM node or Sepolia RPC is active.")
        return None

    account = Account.from_key(private_key)
    print(f"Deployer Wallet Address: {account.address}")
    
    balance_wei = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Wallet Balance: {balance_eth:.4f} ETH")

    abi, bytecode = get_or_compile_contract()
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price

    print("Building deployment transaction...")
    construct_tx = contract_factory.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 1500000,
        'gasPrice': gas_price
    })

    print("Signing and sending deployment transaction...")
    signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Tx Hash: {tx_hash.hex()}. Waiting for transaction receipt...")

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    
    print(f"\nSUCCESS! Contract Deployed to Testnet/Local Node!")
    print(f"Contract Address: {contract_address}")
    print(f"Block Height: {tx_receipt.blockNumber}")
    print(f"Gas Used: {tx_receipt.gasUsed}")

    # Update .env file with contract address
    env_file = config.BASE_DIR / ".env"
    env_lines = []
    if env_file.exists():
        with open(env_file, "r") as f:
            env_lines = f.readlines()
    
    updated = False
    new_lines = []
    for line in env_lines:
        if line.startswith("CONTRACT_ADDRESS="):
            new_lines.append(f"CONTRACT_ADDRESS={contract_address}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"CONTRACT_ADDRESS={contract_address}\n")

    with open(env_file, "w") as f:
        f.writelines(new_lines)

    print(f"Updated .env with CONTRACT_ADDRESS={contract_address}")
    return contract_address

if __name__ == "__main__":
    deploy_to_network()
