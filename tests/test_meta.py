"""Tests for PLATO Meta-Tile Engine."""

import pytest
import hashlib
from unittest.mock import patch, MagicMock
from plato_meta import MetaTileEngine


@pytest.fixture
def meta_engine():
    """Create a MetaTileEngine instance for testing."""
    return MetaTileEngine(plato_url="http://localhost:8847")


class TestWriteTile:
    """Tests for write_tile method."""

    def test_write_tile_returns_id(self, meta_engine):
        """write_tile should return a string tile ID."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            tile_id = meta_engine.write_tile("Q?", "A!")
            assert isinstance(tile_id, str)
            assert len(tile_id) == 12

    def test_write_tile_generates_deterministic_id(self, meta_engine):
        """Same question+answer should produce same ID."""
        tile_id1 = meta_engine.write_tile("Q1", "A1")
        tile_id2 = meta_engine.write_tile("Q1", "A1")
        assert tile_id1 == tile_id2

    def test_write_tile_different_content_different_id(self, meta_engine):
        """Different question+answer should produce different IDs."""
        tile_id1 = meta_engine.write_tile("Q1", "A1")
        tile_id2 = meta_engine.write_tile("Q2", "A2")
        assert tile_id1 != tile_id2

    def test_write_tile_includes_correct_fields(self, meta_engine):
        """Tile should include all expected fields."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            meta_engine.write_tile(
                question="What is X?",
                answer="X is Y",
                agent="test-agent",
                domain="test-domain",
                confidence=0.95
            )
            call_args = mock_post.call_args
            tile = call_args[1]["json"]
            assert tile["question"] == "What is X?"
            assert tile["answer"] == "X is Y"
            assert tile["agent"] == "test-agent"
            assert tile["domain"] == "test-domain"
            assert tile["confidence"] == 0.95
            assert tile["role"] == "tile_writer"


class TestWriteMetaTile:
    """Tests for write_meta_tile method."""

    def test_write_meta_tile_returns_status(self, meta_engine):
        """write_meta_tile should return a dict with status."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = meta_engine.write_meta_tile(
                about_tile_id="abc123",
                question="Is this accurate?",
                answer="Yes, but missing context."
            )
            assert result["status"] == "written"
            assert result["meta_tile_id"] == "abc123"
            assert result["level"] == 1

    def test_write_meta_tile_includes_meta_fields(self, meta_engine):
        """Meta-tile should include about_tile_id and meta_level."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            meta_engine.write_meta_tile(
                about_tile_id="tile999",
                question="Q?",
                answer="A.",
                meta_level=2,
                agent="agent-x"
            )
            call_args = mock_post.call_args
            tile = call_args[1]["json"]
            assert tile["about_tile_id"] == "tile999"
            assert tile["meta_level"] == 2
            assert tile["tile_type"] == "meta"
            assert "[META-2]" in tile["question"]

    def test_write_meta_tile_uses_meta_room(self, meta_engine):
        """Meta-tiles should be written to plato_meta_tiles room."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            meta_engine.write_meta_tile(
                about_tile_id="abc",
                question="Q?",
                answer="A."
            )
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert "plato_meta_tiles" in url


class TestGetMetaTilesFor:
    """Tests for get_meta_tiles_for method."""

    def test_get_meta_tiles_for_returns_list(self, meta_engine):
        """Should return a list of meta-tiles."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"tiles": []}
            )
            result = meta_engine.get_meta_tiles_for("abc123")
            assert isinstance(result, list)

    def test_get_meta_tiles_for_filters_correctly(self, meta_engine):
        """Should only return tiles about the specified tile_id."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "tiles": [
                        {"about_tile_id": "abc123", "meta_level": 1, "question": "Q1?"},
                        {"about_tile_id": "abc123", "meta_level": 2, "question": "Q2?"},
                        {"about_tile_id": "other", "meta_level": 1, "question": "Q3?"},
                    ]
                }
            )
            result = meta_engine.get_meta_tiles_for("abc123")
            assert len(result) == 2
            assert all(t["about_tile_id"] == "abc123" for t in result)

    def test_get_meta_tiles_for_sorts_by_level(self, meta_engine):
        """Results should be sorted by meta_level ascending."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "tiles": [
                        {"about_tile_id": "abc", "meta_level": 3, "question": "L3"},
                        {"about_tile_id": "abc", "meta_level": 1, "question": "L1"},
                        {"about_tile_id": "abc", "meta_level": 2, "question": "L2"},
                    ]
                }
            )
            result = meta_engine.get_meta_tiles_for("abc")
            assert result[0]["meta_level"] == 1
            assert result[1]["meta_level"] == 2
            assert result[2]["meta_level"] == 3


class TestGetAllMetaTiles:
    """Tests for get_all_meta_tiles method."""

    def test_get_all_meta_tiles_returns_list(self, meta_engine):
        """Should return a list of all meta-tiles."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"tiles": [{"id": 1}, {"id": 2}]}
            )
            result = meta_engine.get_all_meta_tiles()
            assert len(result) == 2


class TestGetMetaLevelSummary:
    """Tests for get_meta_level_summary method."""

    def test_get_meta_level_summary_counts_by_level(self, meta_engine):
        """Should return counts grouped by level."""
        with patch.object(meta_engine, "get_all_meta_tiles") as mock_get:
            mock_get.return_value = [
                {"meta_level": 1},
                {"meta_level": 1},
                {"meta_level": 2},
                {"meta_level": 3},
            ]
            result = meta_engine.get_meta_level_summary()
            assert result["level_1"] == 2
            assert result["level_2"] == 1
            assert result["level_3"] == 1


class TestWriteSelfReflection:
    """Tests for write_self_reflection method."""

    def test_write_self_reflection_returns_status(self, meta_engine):
        """Should return dict with status and agent."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = meta_engine.write_self_reflection(
                agent="test-agent",
                thought="I think X",
                reflection="But actually Y"
            )
            assert result["status"] == "written"
            assert result["agent"] == "test-agent"

    def test_write_self_reflection_includes_thought_and_reflection(self, meta_engine):
        """Tile answer should contain thought and reflection."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            meta_engine.write_self_reflection(
                agent="agent1",
                thought="Original thought",
                reflection="Revised understanding"
            )
            call_args = mock_post.call_args
            tile = call_args[1]["json"]
            assert "Original thought" in tile["answer"]
            assert "Revised understanding" in tile["answer"]
            assert tile["tile_type"] == "reflective"


class TestCreateMetaRoom:
    """Tests for create_meta_room method."""

    def test_create_meta_room_returns_bool(self, meta_engine):
        """Should return True on success, False on failure."""
        with patch("plato_meta.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=201)
            assert meta_engine.create_meta_room() is True

            mock_post.return_value = MagicMock(status_code=500)
            assert meta_engine.create_meta_room() is False


class TestEdgeCases:
    """Edge case tests."""

    def test_plato_url_trailing_slash_stripped(self):
        """URL with trailing slash should be cleaned."""
        engine = MetaTileEngine(plato_url="http://localhost:8847/")
        assert engine.plato_url == "http://localhost:8847"

    def test_empty_tile_id(self, meta_engine):
        """Empty string tile_id should not crash."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"tiles": []}
            )
            result = meta_engine.get_meta_tiles_for("")
            assert result == []

    def test_network_error_returns_empty(self, meta_engine):
        """Network errors should be handled gracefully."""
        with patch("plato_meta.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network failure")
            result = meta_engine.get_meta_tiles_for("abc")
            assert result == []
