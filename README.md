# Face ID & Blockchain Verification Pipeline 🛡️⛓️

> **HH Goa 2026 Shortlisting Task 3 Submission**  
> An end-to-end Python pipeline that takes a face scan image as input, performs reverse image search to find matching social media posts on the web, uploads cryptographic fingerprints to a blockchain, and demonstrates on-chain tamper-evident data re-verification.

---

## 🌟 Features & Pipeline Overview

```
[ Input Face Image ]
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Face Identification & Encoding                           │
│    - Face detection via OpenCV Haar/DNN Cascade             │
│    - Bounding box & landmark visual overlay extraction      │
│    - 128D facial feature vector embedding & SHA-256 hash   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Web & Social Media Reverse Search                        │
│    - Multi-provider reverse search (SerpAPI Google Lens /   │
│      Web Scraper / Visual Similarity Matcher)               │
│    - Downloads candidate posts from X, LinkedIn, IG, etc.   │
│    - Filters matches using cosine embedding similarity       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Blockchain Fingerprinting & Upload                       │
│    - Constructs payload data_hash SHA-256                   │
│    - Dual Blockchain Backend:                               │
│      • EVM Smart Contract (`FaceVerificationRegistry.sol`)  │
│      • Zero-dependency Local Cryptographic Block Ledger     │
│    - Returns Tx Hash, Block Number & Receipt                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. On-Chain Data Re-Verification                            │
│    - Directly queries blockchain state using Tx/Data Hash   │
│    - Re-computes live post fingerprint                      │
│    - Audits record: `VERIFIED_GENUINE` vs `TAMPERED`        │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Technical Architecture

### 1. Face Identification (`face_engine.py`)
- Detects face regions `(x, y, w, h)` and bounding boxes.
- Extracts a 128-dimensional facial embedding vector combining HSV spatial color histograms, HOG (Histogram of Oriented Gradients), and facial texture metrics.
- Computes SHA-256 image hashes and perceptual difference hashes (`dhash`).

### 2. Reverse Web & Social Search (`web_search_engine.py`)
- Executes reverse image search across social platforms (X/Twitter, LinkedIn, Instagram, Reddit).
- Supports **SerpAPI Google Lens** API integration when an API key is provided, with fallback to an automated visual search crawler.
- Measures cosine similarity between candidate face embeddings and input scan.

### 3. Blockchain Upload & Smart Contract (`blockchain_engine.py` & `contracts/FaceVerificationRegistry.sol`)
- **Blockchains Supported**:
  1. **Local Cryptographic Ledger** (Default): Zero-dependency local block chain with SHA-256 block hashing, Merkle proofs, and timestamping. Ensures reproducible 100% offline runs.
  2. **EVM Testnet / Local Node (Sepolia / Polygon / Hardhat / Anvil)**: Interfacing with `FaceVerificationRegistry.sol` via `web3.py`.
- Smart contract methods:
  - `registerVerification(bytes32 dataHash, string faceHash, string postUrl, string postHash, string metadataUri)`
  - `verifyRecord(bytes32 dataHash)`

### 4. Re-Verification & Tamper Detection
- Compares live post data against the immutable record on-chain.
- Any modification to post text, image, URL, or metadata causes the re-verification check to flag **`TAMPERED_INVALID`**.

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10+
- Git

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/hhgoa-task3-face-chain.git
cd hhgoa-task3-face-chain

pip install -r requirements.txt
```

### 2. Generate Test Sample Images (Optional)
```bash
python create_samples.py
```

---

## 💻 Running the Pipeline

### Option A: Command Line Interface (CLI)

#### 1. Run End-to-End Scan
```bash
python cli.py scan --image samples/sample_face_1.jpg
```

#### 2. Run Automated Multi-Image Demo
```bash
python cli.py demo
```

#### 3. Re-Verify an On-Chain Record
```bash
python cli.py verify --hash TX-4a61c050007a
```

#### 4. View Blockchain Ledger
```bash
python cli.py ledger
```

---

### Option B: Streamlit Web Dashboard

To launch the interactive visual interface:
```bash
streamlit run app.py
```

The web dashboard opens at `http://localhost:8501` featuring:
- **Visual Bounding Boxes**: Real-time display of face detection bounding boxes.
- **Social Media Cards**: Discovered post preview, author handles, and similarity match meter.
- **Blockchain Receipts**: Live transaction receipts, Tx hashes, and block height.
- **Tamper Simulator**: Test modifying post text and observing the instant on-chain audit failure.

---

## 🧪 Running Tests

Run the automated pytest suite:
```bash
pytest
```
Test suite validates face detection, embedding similarity calculations, reverse image search matching, smart contract transactions, and tamper-detection logic.

---

## 🔗 Smart Contract Information

- **Contract Name**: `FaceVerificationRegistry`
- **Solidity Version**: `^0.8.20`
- **Location**: [`contracts/FaceVerificationRegistry.sol`](contracts/FaceVerificationRegistry.sol)
- **Key Functions**:
  - `registerVerification`: Stores face and post hashes on-chain.
  - `verifyRecord`: Retrieves verifiable record given a data hash.

---

## ⚠️ Known Limitations

1. **API Rate Limits**: Reverse image search via SerpAPI requires an active API key (`SERPAPI_KEY`) for full web Lens results. The pipeline falls back to visual similarity indexing if no API key is provided.
2. **Public Social API Restrictions**: Directly fetching posts behind authentication walls (e.g. private Instagram accounts) requires candidate fallback indexers.
3. **EVM Gas Fees**: Deploying to public EVM testnets (Sepolia/Polygon) requires testnet ETH in the deployer wallet.

---

## 📹 Submission Links & Recording

- **Submission Form Link**: [Google Form](https://forms.gle/oZbQGuwiNeHVcHWo8)
- **GitHub Repository**: [Your Repo Link Here]
- **Working Screen Recording**: [Your Screen Recording Video Link Here (Loom/YouTube Unlisted/Google Drive)]
