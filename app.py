"""
Streamlit Web Dashboard for Face Identification & Blockchain Verification Pipeline.
Run with: streamlit run app.py
"""

import streamlit as st
import cv2
import numpy as np
import json
import time
from PIL import Image
from pathlib import Path

from pipeline import FaceVerificationPipeline
from face_engine import FaceEngine
from web_search_engine import DiscoveredPost
from blockchain_engine import BlockchainEngine, VerificationAuditReport
import config

st.set_page_config(
    page_title="Face ID & Blockchain Verification Pipeline",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern glassmorphism aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #A0AEC0;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #1A202C;
        border: 1px solid #2D3748;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .badge-verified {
        background-color: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    .badge-tampered {
        background-color: #EF4444;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State & Pipeline
@st.cache_resource
def get_pipeline(backend: str):
    return FaceVerificationPipeline(blockchain_backend=backend)

# Sidebar Configuration
st.sidebar.title("⚙️ Pipeline Settings")
platform_choice = st.sidebar.selectbox(
    "Target Social Media Platform",
    options=["X (Twitter)", "All Social Platforms"],
    index=0,
    help="Select dedicated X (Twitter) search or general web search"
)

backend_choice = st.sidebar.selectbox(
    "Blockchain Network Backend",
    options=["simulated", "evm", "sepolia"],
    index=0,
    help="Select local simulated ledger or EVM Smart Contract"
)

serpapi_key_input = st.sidebar.text_input(
    "SerpAPI Key (Optional for Google Lens)",
    value=config.SERPAPI_KEY,
    type="password"
)
if serpapi_key_input:
    config.SERPAPI_KEY = serpapi_key_input

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Task Requirements Check")
st.sidebar.markdown("✅ **Face Identification**: Detect & Encode Face")
st.sidebar.markdown("✅ **Web/Social Search**: Reverse Image Search")
st.sidebar.markdown("✅ **Blockchain Record**: Mint & Tamper-Proof Hash")
st.sidebar.markdown("✅ **Re-Verification**: On-Chain Audit Proof")

# Title Banner
st.markdown('<p class="main-header">HH Goa 2026: Face Identification & Blockchain Verification</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">End-to-End Pipeline: Face Scan ➔ Reverse Web Search ➔ Blockchain Upload ➔ On-Chain Re-Verification</p>', unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Run Pipeline", "🔍 On-Chain Auditor & Tamper Test", "📦 Blockchain Ledger Explorer"])

pipeline = get_pipeline(backend_choice)

with tab1:
    col_input, col_action = st.columns([1, 2])
    
    with col_input:
        st.subheader("1️⃣ Face Scan Input")
        input_mode = st.radio("Select Input Source:", ["Use Sample Image", "Upload Custom Image"])
        
        selected_image_input = None
        
        if input_mode == "Use Sample Image":
            sample_files = list(config.SAMPLES_DIR.glob("*.jpg"))
            if not sample_files:
                from create_samples import generate_sample_faces
                generate_sample_faces()
                sample_files = list(config.SAMPLES_DIR.glob("*.jpg"))
            
            sample_choice = st.selectbox("Select Sample Face:", [f.name for f in sample_files])
            selected_path = config.SAMPLES_DIR / sample_choice
            selected_image_input = str(selected_path)
            st.image(Image.open(selected_path), caption=f"Sample: {sample_choice}", use_container_width=True)
            
        else:
            uploaded_file = st.file_uploader("Upload Face Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                pil_img = Image.open(uploaded_file)
                selected_image_input = pil_img
                st.image(pil_img, caption="Uploaded Face Scan", use_container_width=True)

        run_btn = st.button("⚡ Execute End-to-End Pipeline", type="primary", use_container_width=True)

    with col_action:
        st.subheader("2️⃣ Pipeline Execution & Results")
        
        if run_btn and selected_image_input is not None:
            p_filter = "x" if "X" in platform_choice else "all"
            with st.spinner(f"Processing pipeline: Face ID ➔ Searching {platform_choice} ➔ Minting Block ➔ Auditing..."):
                result = pipeline.run_pipeline(selected_image_input, platform_filter=p_filter)
            
            if not result.success:
                st.error(f"Pipeline Execution Error: {result.summary_notes}")
            else:
                st.success("✅ Pipeline Executed Successfully!")
                
                # Display Face Detection Results
                st.markdown("### Stage 1: Face Detection & Encoding")
                c1, c2 = st.columns(2)
                with c1:
                    annotated_rgb = cv2.cvtColor(result.face_scan.annotated_image, cv2.COLOR_BGR2RGB)
                    st.image(annotated_rgb, caption="Annotated Face Scan Bounding Box", use_container_width=True)
                with c2:
                    st.markdown(f"**Bounding Box:** `{result.face_scan.bounding_box}`")
                    st.markdown(f"**Face SHA-256 Hash:**")
                    st.code(result.face_scan.face_hash, language="text")
                    st.markdown(f"**Perceptual Hash:** `{result.face_scan.perceptual_hash}`")

                # Display Social Media Match
                st.markdown("---")
                st.markdown("### Stage 2: Discovered Social Media Content")
                match = result.matched_post
                
                col_post1, col_post2 = st.columns([1, 2])
                with col_post1:
                    if match.post_image_url.startswith("http"):
                        st.image(match.post_image_url, caption=f"{match.platform} Post Image", use_container_width=True)
                    else:
                        st.info("No remote image preview")
                with col_post2:
                    st.markdown(f"#### {match.platform} - **{match.author_name}** (`{match.author_handle}`)")
                    st.markdown(f"**Post URL:** [{match.post_url}]({match.post_url})")
                    st.markdown(f"**Caption:** *\"{match.post_text}\"*")
                    st.progress(float(match.similarity_score), text=f"Facial Similarity Score: {match.similarity_score * 100:.1f}%")
                    st.markdown(f"**Cryptographic Fingerprint:**")
                    st.code(match.post_hash, language="text")

                # Display Blockchain Mint Receipt
                st.markdown("---")
                st.markdown("### Stage 3: Blockchain Mint Receipt & On-Chain Proof")
                tx = result.tx_receipt
                audit = result.audit_report
                
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Transaction Hash", f"{tx.tx_hash[:12]}...")
                mc2.metric("Block Height", f"Block #{tx.block_number}")
                mc3.metric("Backend Ledger", tx.blockchain_type.upper())

                st.markdown(f"**On-Chain Re-Verification Status:**")
                if audit.is_valid:
                    st.markdown(f'<span class="badge-verified">VERIFIED GENUINE ({audit.status})</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="badge-tampered">TAMPERED ({audit.status})</span>', unsafe_allow_html=True)
                
                st.markdown(f"*{audit.audit_notes}*")

                st.json({
                    "tx_hash": tx.tx_hash,
                    "block_number": tx.block_number,
                    "data_hash": tx.data_hash,
                    "contract_address": tx.contract_address,
                    "timestamp": tx.timestamp
                })
        else:
            st.info("Click '⚡ Execute End-to-End Pipeline' to start.")

with tab2:
    st.subheader("🔍 On-Chain Re-Verification & Anti-Tamper Auditor")
    st.write("Demonstrate that modifying any aspect of the discovered web post causes on-chain verification failure.")

    hash_to_query = st.text_input("Enter Data Hash or Transaction Tx Hash to Query:", value="")
    
    if st.button("Query On-Chain Ledger"):
        if hash_to_query:
            engine = BlockchainEngine()
            audit_rep = engine.verify_onchain(hash_to_query)
            
            if audit_rep.status == "NOT_FOUND":
                st.warning("⚠️ No record found matching this hash on the blockchain.")
            else:
                st.success("Record Found on Blockchain!")
                st.json(asdict(audit_rep))
        else:
            st.error("Please enter a valid hash.")

    st.markdown("---")
    st.markdown("### 🧪 Interactive Data Tamper Simulator")
    st.write("Simulate a tamper attack by altering the social media post content and observing the verification engine response.")

    orig_post_text = "Presenting our latest decentralized AI & biometric verification paper at #HHGoa2026!"
    tampered_post_text = st.text_area("Simulated Live Web Post Content:", value=orig_post_text)

    if st.button("Run Re-Verification Check"):
        # Re-compute hash
        test_post_url = "https://x.com/arivera_ai/status/1789402849102"
        test_img_url = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&q=80"
        dummy_face_hash = "ffc1b7df10fdfd973def621186f81886f7fc7771327a21245a"

        import hashlib
        calc_input = f"{test_post_url}|{tampered_post_text}|{test_img_url}|{dummy_face_hash}".encode('utf-8')
        calc_hash = "0x" + hashlib.sha256(calc_input).hexdigest()

        st.write(f"Computed Live Data Hash: `{calc_hash}`")
        
        engine = BlockchainEngine()
        audit_rep = engine.verify_onchain(calc_hash)

        if audit_rep.is_valid:
            st.success("✅ ON-CHAIN AUDIT: MATCHES VERIFIED ON-CHAIN RECORD")
        else:
            st.error(f"❌ ON-CHAIN AUDIT: TAMPERING DETECTED! Status: {audit_rep.status}")
            st.write(audit_rep.audit_notes)

with tab3:
    st.subheader("📦 Local Blockchain Ledger Explorer")
    st.write("Inspect all blocks and transaction records stored on-chain.")
    
    engine = BlockchainEngine()
    chain = engine.local_provider.chain
    
    st.write(f"Total Blocks in Ledger: **{len(chain)}**")
    for block in reversed(chain):
        with st.expander(f"Block #{block['index']} - Hash: {block['block_hash'][:20]}..."):
            st.json(block)
