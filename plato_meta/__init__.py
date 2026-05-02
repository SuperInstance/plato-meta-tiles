"""
PLATO Meta-Tile Engine — tiles about tiles

Higher-order thoughts: tiles that reference and reason about other tiles.
This enables the fleet to think about what it's thinking about.

Based on Higher-Order Theories of Mind:
- First-order: "The fleet is attending to X"
- Second-order: "The fleet knows it is attending to X"
- Third-order: "The fleet reasons about its reasoning about attending to X"

Usage:
    from plato_meta import MetaTileEngine
    meta = MetaTileEngine(plato_url="http://localhost:8847")
    
    # Write a first-order tile
    tile_id = meta.write_tile("What is the fleet doing?", "The fleet is coordinating agents.")
    
    # Write a meta-tile about that tile
    meta.write_meta_tile(
        about_tile_id=tile_id,
        question="Is this tile accurate?",
        answer="Yes, the fleet is coordinating. But it's missing the CCC heartbeat aspect."
    )
    
    # Query the meta-level
    meta_tiles = meta.get_meta_tiles_for(tile_id)
"""

import time
import hashlib
import requests
from typing import List, Dict, Any, Optional

class MetaTileEngine:
    def __init__(self, plato_url: str = "http://localhost:8847"):
        self.plato_url = plato_url.rstrip("/")
        self.meta_room = "plato_meta_tiles"
    
    def write_tile(
        self,
        question: str,
        answer: str,
        agent: str = "oracle1",
        domain: str = "fleet_orchestration",
        confidence: float = 0.8
    ) -> str:
        """Write a first-order tile and return its ID (hash of content)."""
        tile = {
            "question": question,
            "answer": answer,
            "agent": agent,
            "domain": domain,
            "confidence": confidence,
            "model": agent,
            "role": "tile_writer"
        }
        
        try:
            resp = requests.post(f"{self.plato_url}/room/{domain}", json=tile, timeout=5)
            if resp.status_code == 200:
                tile_id = hashlib.md5(f"{question}{answer}".encode()).hexdigest()[:12]
                return tile_id
        except:
            pass
        
        # Fallback: generate deterministic ID
        return hashlib.md5(f"{question}{answer}".encode()).hexdigest()[:12]
    
    def write_meta_tile(
        self,
        about_tile_id: str,
        question: str,
        answer: str,
        meta_level: int = 1,
        agent: str = "oracle1",
        confidence: float = 0.75
    ) -> Dict[str, Any]:
        """
        Write a meta-tile — a tile that reasons about another tile.
        
        about_tile_id: the tile being reasoned about
        meta_level: 1 = first-order meta, 2 = second-order meta, etc.
        """
        tile = {
            "question": f"[META-{meta_level}] {question}",
            "answer": f"About tile {about_tile_id}: {answer}",
            "agent": agent,
            "domain": self.meta_room,
            "confidence": confidence,
            "model": agent,
            "role": f"meta_tile_level_{meta_level}",
            "about_tile_id": about_tile_id,
            "meta_level": meta_level,
            "tile_type": "meta"
        }
        
        try:
            resp = requests.post(f"{self.plato_url}/room/{self.meta_room}", json=tile, timeout=5)
            return {"status": "written", "meta_tile_id": about_tile_id, "level": meta_level}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_meta_tiles_for(self, tile_id: str) -> List[Dict[str, Any]]:
        """Get all meta-tiles that reason about a specific tile."""
        try:
            resp = requests.get(f"{self.plato_url}/room/{self.meta_room}?limit=100", timeout=5)
            if resp.status_code == 200:
                tiles = resp.json().get("tiles", [])
                meta_tiles = [
                    t for t in tiles
                    if t.get("about_tile_id") == tile_id
                ]
                return sorted(meta_tiles, key=lambda x: x.get("meta_level", 0))
        except:
            pass
        return []
    
    def get_all_meta_tiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all meta-tiles across the fleet."""
        try:
            resp = requests.get(f"{self.plato_url}/room/{self.meta_room}?limit={limit}", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("tiles", [])
        except:
            pass
        return []
    
    def get_meta_level_summary(self) -> Dict[str, int]:
        """Count meta-tiles by level across the fleet."""
        meta_tiles = self.get_all_meta_tiles(limit=200)
        
        by_level: Dict[str, int] = {}
        for t in meta_tiles:
            level = t.get("meta_level", 0)
            key = f"level_{level}"
            by_level[key] = by_level.get(key, 0) + 1
        
        return by_level
    
    def write_self_reflection(
        self,
        agent: str,
        thought: str,
        reflection: str
    ) -> Dict[str, Any]:
        """
        Agent writes a self-reflective tile: "I was thinking X, now I think Y."
        This is attention schema in action.
        """
        tile = {
            "question": f"What is {agent} thinking about their own thinking?",
            "answer": f"Thought: {thought}\nReflection: {reflection}\nAgent: {agent}",
            "agent": agent,
            "domain": self.meta_room,
            "confidence": 0.85,
            "model": agent,
            "role": "self_reflection",
            "tile_type": "reflective"
        }
        
        try:
            requests.post(f"{self.plato_url}/room/{self.meta_room}", json=tile, timeout=5)
            return {"status": "written", "agent": agent}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def create_meta_room(self) -> bool:
        """Ensure the meta-tiles room exists."""
        try:
            resp = requests.post(
                f"{self.plato_url}/room/{self.meta_room}",
                json={"action": "create", "room": self.meta_room},
                timeout=5
            )
            return resp.status_code in (200, 201)
        except:
            return False
