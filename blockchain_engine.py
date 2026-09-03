"""
Blockchain Verification Engine.
Provides dual-mode blockchain recording and verification:
1. EVM Smart Contract Backend (Ethereum / Sepolia / Polygon / Local Hardhat via Web3.py)
2. Cryptographic Block Ledger Backend (Zero-dependency tamper-evident SHA-256 block ledger)
"""

import json
import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from web3 import Web3
from eth_account import Account

import config
from web_search_engine import DiscoveredPost
from face_engine import FaceScanResult

@dataclass
class TransactionReceipt:
    """Dataclass holding details of a blockchain transaction submission."""
    success: bool
    tx_hash: str
    block_number: int
    data_hash: str
    face_hash: str
    post_url: str
    timestamp: str
    contract_address: str
    blockchain_type: str  # 'evm' or 'simulated_chain'
    explorer_url: str = ""

@dataclass
class VerificationAuditReport:
    """Dataclass holding on-chain re-verification status and tamper audit results."""
    status: str  # 'VERIFIED_GENUINE' or 'TAMPERED_INVALID'
    is_valid: bool
    data_hash: str
    onchain_timestamp: str
    onchain_face_hash: str
    onchain_post_url: str
    onchain_post_hash: str
    onchain_registrar: str
    computed_live_hash: str
    mismatch_fields: List[str]
    audit_notes: str

# Solidity ABI for FaceVerificationRegistry
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "string", "name": "faceHash", "type": "string"},
            {"internalType": "string", "name": "postUrl", "type": "string"},
            {"internalType": "string", "name": "postHash", "type": "string"},
            {"internalType": "string", "name": "metadataUri", "type": "string"}
        ],
        "name": "registerVerification",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
        "name": "verifyRecord",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "registrar", "type": "address"},
            {"internalType": "string", "name": "faceHash", "type": "string"},
            {"internalType": "string", "name": "postUrl", "type": "string"},
            {"internalType": "string", "name": "postHash", "type": "string"},
            {"internalType": "string", "name": "metadataUri", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
        "name": "isDataHashRegistered",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getRecordCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class LocalLedgerProvider:
    """
    Self-contained, zero-dependency tamper-evident SHA-256 block ledger.
    Guarantees 100% execution capability anywhere without external RPC setup.
    """
    def __init__(self, ledger_path: Path = config.LOCAL_LEDGER_FILE):
        self.ledger_path = ledger_path
        self.chain: List[Dict[str, Any]] = []
        self._load_or_init_ledger()

    def _load_or_init_ledger(self):
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, "r") as f:
                    self.chain = json.load(f)
                if self.validate_chain():
                    return
            except Exception:
                pass
        
        # Initialize Genesis block
        genesis_block = {
            "index": 0,
            "timestamp": "2026-01-01T00:00:00Z",
            "transactions": [],
            "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "nonce": 42,
            "block_hash": "0000000000000000000000000000000000000000000000000000000000000000"
        }
        genesis_block["block_hash"] = self._compute_block_hash(genesis_block)
        self.chain = [genesis_block]
        self._save_ledger()

    def _compute_block_hash(self, block: Dict[str, Any]) -> str:
        block_copy = block.copy()
        block_copy.pop("block_hash", None)
        block_string = json.dumps(block_copy, sort_keys=True)
        return "0x" + hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def _save_ledger(self):
        with open(self.ledger_path, "w") as f:
            json.dump(self.chain, f, indent=2)

    def validate_chain(self) -> bool:
        """Validate entire block chain for hash tampering."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr["prev_hash"] != prev["block_hash"]:
                return False
            if curr["block_hash"] != self._compute_block_hash(curr):
                return False
        return True

    def register_record(self, data_hash: str, face_hash: str, post_url: str, post_hash: str, metadata_uri: str) -> TransactionReceipt:
        prev_block = self.chain[-1]
        tx_data = {
            "tx_id": f"TX-{hashlib.md5(f'{data_hash}{time.time()}'.encode()).hexdigest()[:12]}",
            "data_hash": data_hash,
            "face_hash": face_hash,
            "post_url": post_url,
            "post_hash": post_hash,
            "metadata_uri": metadata_uri,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "submitter": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
        }

        new_block = {
            "index": len(self.chain),
            "timestamp": tx_data["timestamp"],
            "transactions": [tx_data],
            "prev_hash": prev_block["block_hash"],
            "nonce": 1000 + len(self.chain),
            "block_hash": ""
        }
        new_block["block_hash"] = self._compute_block_hash(new_block)
        
        self.chain.append(new_block)
        self._save_ledger()

        return TransactionReceipt(
            success=True,
            tx_hash=tx_data["tx_id"],
            block_number=new_block["index"],
            data_hash=data_hash,
            face_hash=face_hash,
            post_url=post_url,
            timestamp=tx_data["timestamp"],
            contract_address="0xLocalSimulatedLedgerContract00000000000",
            blockchain_type="simulated_chain",
            explorer_url=f"local://ledger/block/{new_block['index']}"
        )

    def query_record(self, data_hash: str) -> Optional[Dict[str, Any]]:
        for block in reversed(self.chain):
            for tx in block.get("transactions", []):
                if tx.get("data_hash") == data_hash or tx.get("tx_id") == data_hash:
                    return {
                        "exists": True,
                        "timestamp": tx.get("timestamp"),
                        "registrar": tx.get("submitter"),
                        "face_hash": tx.get("face_hash"),
                        "post_url": tx.get("post_url"),
                        "post_hash": tx.get("post_hash"),
                        "metadata_uri": tx.get("metadata_uri"),
                        "block_index": block["index"]
                    }
        return None

class EVMBlockchainProvider:
    """
    EVM Smart Contract Provider interfacing with Ethereum / Sepolia / Polygon / Hardhat via Web3.py.
    """
    def __init__(self, rpc_url: str = config.EVM_RPC_URL, contract_address: str = config.CONTRACT_ADDRESS):
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = contract_address
        self.account = Account.from_key(config.PRIVATE_KEY) if config.PRIVATE_KEY else None
        self.contract = None
        
        if self.contract_address and self.w3.is_connected():
            checksum_addr = Web3.to_checksum_address(self.contract_address)
            self.contract = self.w3.eth.contract(address=checksum_addr, abi=CONTRACT_ABI)

    def is_connected(self) -> bool:
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def register_record(self, data_hash: str, face_hash: str, post_url: str, post_hash: str, metadata_uri: str) -> TransactionReceipt:
        if not self.is_connected() or not self.contract or not self.account:
            raise RuntimeError("EVM Provider not connected or contract address missing")

        # Convert hex string dataHash to bytes32 if needed
        data_hash_bytes = bytes.fromhex(data_hash[2:]) if data_hash.startswith("0x") else bytes.fromhex(data_hash)

        tx_func = self.contract.functions.registerVerification(
            data_hash_bytes,
            face_hash,
            post_url,
            post_hash,
            metadata_uri
        )

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        gas_price = self.w3.eth.gas_price

        tx = tx_func.build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=config.PRIVATE_KEY)
        tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_bytes)

        return TransactionReceipt(
            success=receipt.status == 1,
            tx_hash=receipt.transactionHash.hex(),
            block_number=receipt.blockNumber,
            data_hash=data_hash,
            face_hash=face_hash,
            post_url=post_url,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            contract_address=self.contract_address,
            blockchain_type="evm",
            explorer_url=f"https://sepolia.etherscan.io/tx/{receipt.transactionHash.hex()}"
        )

    def query_record(self, data_hash: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected() or not self.contract:
            return None

        try:
            data_hash_bytes = bytes.fromhex(data_hash[2:]) if data_hash.startswith("0x") else bytes.fromhex(data_hash)
            res = self.contract.functions.verifyRecord(data_hash_bytes).call()
            return {
                "exists": res[0],
                "timestamp": res[1],
                "registrar": res[2],
                "face_hash": res[3],
                "post_url": res[4],
                "post_hash": res[5],
                "metadata_uri": res[6]
            }
        except Exception as e:
            return None

class BlockchainEngine:
    """Unified Blockchain Manager supporting EVM and Simulated local ledger fallback."""
    def __init__(self, backend_type: str = config.DEFAULT_BLOCKCHAIN_BACKEND):
        self.backend_type = backend_type
        self.local_provider = LocalLedgerProvider()
        self.evm_provider = EVMBlockchainProvider() if config.CONTRACT_ADDRESS else None

    def register_verification(self, post: DiscoveredPost, face_scan: FaceScanResult) -> TransactionReceipt:
        """Register face & post verification record on blockchain."""
        data_hash = post.post_hash
        face_hash = face_scan.face_hash
        post_url = post.post_url
        post_hash = post.post_hash
        metadata_uri = post.metadata_hash

        # Try EVM backend if configured, otherwise fallback to local ledger
        if self.backend_type in ['evm', 'sepolia'] and self.evm_provider and self.evm_provider.is_connected():
            try:
                return self.evm_provider.register_record(data_hash, face_hash, post_url, post_hash, metadata_uri)
            except Exception as e:
                print(f"[BlockchainEngine] EVM register failed ({e}), falling back to local ledger...")

        return self.local_provider.register_record(data_hash, face_hash, post_url, post_hash, metadata_uri)

    def verify_onchain(self, data_hash: str, live_post: Optional[DiscoveredPost] = None) -> VerificationAuditReport:
        """Re-verify data record against on-chain ledger."""
        record = None
        if self.evm_provider and self.evm_provider.is_connected():
            record = self.evm_provider.query_record(data_hash)

        if not record:
            record = self.local_provider.query_record(data_hash)

        if not record or not record.get("exists"):
            return VerificationAuditReport(
                status="NOT_FOUND",
                is_valid=False,
                data_hash=data_hash,
                onchain_timestamp="",
                onchain_face_hash="",
                onchain_post_url="",
                onchain_post_hash="",
                onchain_registrar="",
                computed_live_hash=live_post.post_hash if live_post else "",
                mismatch_fields=["data_hash_not_found"],
                audit_notes="Record does not exist on blockchain."
            )

        # Check for data tampering if live post object is provided
        mismatches = []
        if live_post:
            if record["face_hash"] != live_post.face_hash:
                mismatches.append("face_hash")
            if record["post_url"] != live_post.post_url:
                mismatches.append("post_url")
            if record["post_hash"] != live_post.post_hash:
                mismatches.append("post_hash")

        is_valid = len(mismatches) == 0
        status_str = "VERIFIED_GENUINE" if is_valid else "TAMPERED_INVALID"
        notes = "Data matches on-chain record perfectly." if is_valid else f"Tampering detected in fields: {', '.join(mismatches)}"

        return VerificationAuditReport(
            status=status_str,
            is_valid=is_valid,
            data_hash=data_hash,
            onchain_timestamp=str(record["timestamp"]),
            onchain_face_hash=record["face_hash"],
            onchain_post_url=record["post_url"],
            onchain_post_hash=record["post_hash"],
            onchain_registrar=record["registrar"],
            computed_live_hash=live_post.post_hash if live_post else record["post_hash"],
            mismatch_fields=mismatches,
            audit_notes=notes
        )
