"""
Main Pipeline Orchestrator.
Combines:
Stage 1: Face Detection & Embedding (face_engine.py)
Stage 2: Web & Social Media Search (web_search_engine.py)
Stage 3: Blockchain Mint & Register (blockchain_engine.py)
Stage 4: On-Chain Data Re-Verification (blockchain_engine.py)
"""

import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path

from face_engine import FaceEngine, FaceScanResult
from web_search_engine import WebSearchEngine, DiscoveredPost
from blockchain_engine import BlockchainEngine, TransactionReceipt, VerificationAuditReport
import config

@dataclass
class PipelineResult:
    """Dataclass containing complete end-to-end execution results."""
    success: bool
    face_scan: FaceScanResult
    discovered_posts: List[DiscoveredPost]
    matched_post: Optional[DiscoveredPost]
    tx_receipt: Optional[TransactionReceipt]
    audit_report: Optional[VerificationAuditReport]
    execution_time_seconds: float
    summary_notes: str

class FaceVerificationPipeline:
    def __init__(self, blockchain_backend: str = config.DEFAULT_BLOCKCHAIN_BACKEND):
        self.face_engine = FaceEngine()
        self.search_engine = WebSearchEngine(face_engine=self.face_engine)
        self.blockchain_engine = BlockchainEngine(backend_type=blockchain_backend)

    def run_pipeline(self, image_input, sample_db: Optional[List[Dict[str, Any]]] = None) -> PipelineResult:
        """
        Runs full end-to-end pipeline:
        Input Face Scan -> Social Search -> Blockchain Mint -> On-Chain Re-Verification.
        """
        start_time = time.time()

        # Step 1: Face Detection & Encoding
        face_scan = self.face_engine.process_image(image_input)
        if not face_scan.face_detected:
            # Note: face_scan fallback center region handles images without strict haar face cascade hits
            pass

        # Step 2: Reverse Web & Social Media Search
        discovered_posts = self.search_engine.search_web_for_face(face_scan, sample_database=sample_db)
        
        if not discovered_posts:
            exec_time = time.time() - start_time
            return PipelineResult(
                success=False,
                face_scan=face_scan,
                discovered_posts=[],
                matched_post=None,
                tx_receipt=None,
                audit_report=None,
                execution_time_seconds=round(exec_time, 2),
                summary_notes="No matching web/social posts found for face scan."
            )

        top_match = discovered_posts[0]

        # Step 3: Upload post fingerprint & metadata to Blockchain
        tx_receipt = self.blockchain_engine.register_verification(top_match, face_scan)

        # Step 4: Re-verify data against on-chain record to demonstrate tamper-evidence
        audit_report = self.blockchain_engine.verify_onchain(top_match.post_hash, live_post=top_match)

        exec_time = time.time() - start_time

        notes = (
            f"Successfully identified matching social post on {top_match.platform} "
            f"({top_match.author_handle}) with similarity score {top_match.similarity_score * 100:.1f}%. "
            f"On-chain record created at Block #{tx_receipt.block_number} (Tx: {tx_receipt.tx_hash[:16]}...). "
            f"Re-verification status: {audit_report.status}."
        )

        return PipelineResult(
            success=True,
            face_scan=face_scan,
            discovered_posts=discovered_posts,
            matched_post=top_match,
            tx_receipt=tx_receipt,
            audit_report=audit_report,
            execution_time_seconds=round(exec_time, 2),
            summary_notes=notes
        )

    def reverify_record(self, data_hash: str, live_post: Optional[DiscoveredPost] = None) -> VerificationAuditReport:
        """Re-verify any post or hash against on-chain ledger."""
        return self.blockchain_engine.verify_onchain(data_hash, live_post=live_post)
