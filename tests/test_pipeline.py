"""
Pytest Test Suite for Face Identification & Blockchain Verification Pipeline.
Run with: pytest
"""

import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import numpy as np
import hashlib

from face_engine import FaceEngine, FaceScanResult
from web_search_engine import WebSearchEngine, DiscoveredPost
from blockchain_engine import BlockchainEngine, LocalLedgerProvider
from pipeline import FaceVerificationPipeline
import config

@pytest.fixture
def sample_image_path():
    p = config.SAMPLES_DIR / "sample_face_1.jpg"
    if not p.exists():
        from create_samples import generate_sample_faces
        generate_sample_faces()
    return str(p)

def test_face_engine(sample_image_path):
    engine = FaceEngine()
    scan = engine.process_image(sample_image_path)
    
    assert scan is not None
    assert scan.face_hash != ""
    assert scan.perceptual_hash != ""
    assert scan.embedding is not None
    assert len(scan.embedding) > 0
    assert scan.bounding_box is not None

def test_facial_similarity_calculation():
    engine = FaceEngine()
    emb1 = np.ones(128) / np.sqrt(128)
    emb2 = np.ones(128) / np.sqrt(128)
    emb3 = np.zeros(128)
    emb3[0] = 1.0

    score_same = engine.calculate_similarity(emb1, emb2)
    assert pytest.approx(score_same, 0.01) == 1.0

    score_diff = engine.calculate_similarity(emb1, emb3)
    assert score_diff < 0.9

def test_web_search_engine(sample_image_path):
    face_eng = FaceEngine()
    scan = face_eng.process_image(sample_image_path)
    
    search_eng = WebSearchEngine(face_engine=face_eng)
    posts = search_eng.search_web_for_face(scan)

    assert len(posts) > 0
    top_post = posts[0]
    assert isinstance(top_post, DiscoveredPost)
    assert top_post.post_hash.startswith("0x")
    assert top_post.similarity_score >= 0.0

def test_x_search_provider(sample_image_path):
    face_eng = FaceEngine()
    scan = face_eng.process_image(sample_image_path)
    
    search_eng = WebSearchEngine(face_engine=face_eng)
    x_posts = search_eng.search_web_for_face(scan, platform_filter="x")

    assert len(x_posts) > 0
    for p in x_posts:
        assert p.platform in ["X (Twitter)", "X", "Twitter"]
        assert "x.com" in p.post_url or "twitter.com" in p.post_url

def test_blockchain_local_ledger(tmp_path):
    ledger_file = tmp_path / "test_ledger.json"
    provider = LocalLedgerProvider(ledger_path=ledger_file)
    
    data_hash = "0x" + hashlib.sha256(b"test_content").hexdigest()
    receipt = provider.register_record(
        data_hash=data_hash,
        face_hash="0xface123",
        post_url="https://x.com/test",
        post_hash=data_hash,
        metadata_uri="0xmeta123"
    )

    assert receipt.success is True
    assert receipt.block_number == 1
    assert provider.validate_chain() is True

    record = provider.query_record(data_hash)
    assert record is not None
    assert record["face_hash"] == "0xface123"

def test_pipeline_end_to_end(sample_image_path):
    pipeline = FaceVerificationPipeline(blockchain_backend="simulated")
    result = pipeline.run_pipeline(sample_image_path)

    assert result.success is True
    assert result.matched_post is not None
    assert result.tx_receipt is not None
    assert result.audit_report is not None
    assert result.audit_report.is_valid is True
    assert result.audit_report.status == "VERIFIED_GENUINE"

def test_tamper_detection(sample_image_path):
    pipeline = FaceVerificationPipeline(blockchain_backend="simulated")
    result = pipeline.run_pipeline(sample_image_path)

    # Tamper with the post hash
    tampered_hash = "0x" + hashlib.sha256(b"tampered_fake_content").hexdigest()
    audit = pipeline.reverify_record(tampered_hash)

    assert audit.is_valid is False
    assert audit.status == "NOT_FOUND"
