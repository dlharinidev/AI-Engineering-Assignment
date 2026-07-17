import uuid
import pytest
from app import versioning

class DummyNode:
    def __init__(self, level, heading, content_hash, logical_node_id=None):
        self.level = level
        self.heading = heading
        self.content_hash = content_hash
        self.logical_node_id = logical_node_id or str(uuid.uuid4())

def test_match_existing_node_preserves_id_and_staleness():
    v1_node = DummyNode(level=1, heading="1.0 Introduction", content_hash="hash1", logical_node_id="log123")
    v2_nodes = [{
        "level": 1,
        "heading": "1.0 Introduction",
        "content_hash": "hash2"
    }]
    result = versioning.match_nodes_v1_v2([v1_node], v2_nodes)
    assert result[0]["logical_node_id"] == "log123"
    assert result[0]["is_stale"] is True

def test_match_new_node_generates_uuid_and_not_stale():
    v2_nodes = [{
        "level": 2,
        "heading": "2.1 Safety",
        "content_hash": "hash_new"
    }]
    result = versioning.match_nodes_v1_v2([], v2_nodes)
    assert "logical_node_id" in result[0]
    assert isinstance(result[0]["logical_node_id"], str)
    assert result[0]["is_stale"] is False

def test_get_diff_shows_changes():
    text1 = "Line A\nLine B"
    text2 = "Line A\nLine C"
    diff = versioning.get_diff(text1, text2)
    assert "- Line B" in diff
    assert "+ Line C" in diff
