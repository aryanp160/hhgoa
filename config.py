"""
Global configuration settings for Face Identification & Blockchain Verification Pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Directory Paths
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output"
CONTRACTS_DIR = BASE_DIR / "contracts"

SAMPLES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CONTRACTS_DIR.mkdir(exist_ok=True)

# Face Detection Settings
FACE_SIMILARITY_THRESHOLD = 0.65  # Cosine similarity / distance threshold
FACE_DETECTION_CONFIDENCE = 0.5

# Web Search Settings
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
ENABLE_WEB_SCRAPER = True
MAX_SEARCH_RESULTS = 10

# Blockchain Settings
# Supported backends: 'local_evm', 'sepolia', 'polygon_amoy', 'simulated'
DEFAULT_BLOCKCHAIN_BACKEND = os.getenv("BLOCKCHAIN_BACKEND", "simulated")
EVM_RPC_URL = os.getenv("EVM_RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY", "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

# Local Ledger Storage Path
LOCAL_LEDGER_FILE = OUTPUT_DIR / "blockchain_ledger.json"
