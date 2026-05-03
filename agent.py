#!/usr/bin/env python3
"""
plato-meta-tiles — Meta-tile management for the PLATO knowledge system
Meta-tiles are tiles about tiles — tracking quality, connections, and evolution.
"""

import json, time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class MetaTile:
    id: str
    target_tile: str  # The tile this meta-tile describes
    metric: str  # quality, freshness, relevance, connections
    value: float
    reason: str
    timestamp: float
    agent: str

class MetaTileManager:
    def __init__(self, plato_url="http://147.224.38.131:8847"):
        self.plato_url = plato_url
        self.meta_tiles: Dict[str, List[MetaTile]] = {}  # target_tile -> list of meta-tiles
    
    def evaluate(self, tile_id: str, question: str, answer: str, agent: str) -> Dict:
        """Generate meta-tiles evaluating a tile's quality."""
        meta_id = f"meta-{tile_id}-{int(time.time())}"
        
        # Quality heuristics
        quality = min(1.0, len(answer) / 500)  # Longer answers = more detail
        if len(answer) < 50:
            quality = 0.2
        
        freshness = 1.0  # Brand new
        
        # Check for references
        has_refs = "http" in answer or "ref" in answer.lower() or "source" in answer.lower()
        relevance = 0.8 if has_refs else 0.5
        
        metas = [
            MetaTile(meta_id + "-q", tile_id, "quality", quality, f"Answer length: {len(answer)} chars", time.time(), agent),
            MetaTile(meta_id + "-f", tile_id, "freshness", freshness, "New tile", time.time(), agent),
            MetaTile(meta_id + "-r", tile_id, "relevance", relevance, f"Has references: {has_refs}", time.time(), agent)
        ]
        
        if tile_id not in self.meta_tiles:
            self.meta_tiles[tile_id] = []
        self.meta_tiles[tile_id].extend(metas)
        
        self._submit(f"Meta-evaluation of {tile_id}", f"Quality: {quality:.2f}, Freshness: {freshness:.2f}, Relevance: {relevance:.2f}")
        return {"tile_id": tile_id, "quality": quality, "freshness": freshness, "relevance": relevance}
    
    def get_tile_score(self, tile_id: str) -> float:
        """Aggregate score for a tile."""
        if tile_id not in self.meta_tiles:
            return 0.5  # Default
        
        scores = {}
        for mt in self.meta_tiles[tile_id]:
            if mt.metric not in scores:
                scores[mt.metric] = []
            scores[mt.metric].append(mt.value)
        
        # Average per metric, then overall
        metric_avgs = {m: sum(v)/len(v) for m, v in scores.items()}
        return sum(metric_avgs.values()) / len(metric_avgs) if metric_avgs else 0.5
    
    def find_stale_tiles(self, threshold_days: int = 7) -> List[str]:
        """Find tiles that haven't been evaluated recently."""
        stale = []
        cutoff = time.time() - (threshold_days * 86400)
        for tile_id, metas in self.meta_tiles.items():
            latest = max(m.timestamp for m in metas)
            if latest < cutoff:
                stale.append(tile_id)
        return stale
    
    def get_fleet_quality_report(self) -> Dict:
        """Overall quality metrics."""
        if not self.meta_tiles:
            return {"error": "No meta-tiles yet"}
        
        scores = [self.get_tile_score(tid) for tid in self.meta_tiles.keys()]
        return {
            "tiles_evaluated": len(self.meta_tiles),
            "avg_quality": round(sum(scores)/len(scores), 2),
            "high_quality": len([s for s in scores if s > 0.8]),
            "needs_work": len([s for s in scores if s < 0.5]),
            "stale_tiles": len(self.find_stale_tiles())
        }
    
    def _submit(self, q: str, a: str):
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(f"{self.plato_url}/submit", data=json.dumps({"question": q, "answer": a, "agent": "plato-meta-tiles", "room": "meta"}).encode(), headers={"Content-Type": "application/json"}), timeout=5)
        except: pass

def demo():
    manager = MetaTileManager()
    
    print("=== Evaluating tiles ===")
    manager.evaluate("tile-1", "What is Rust?", "Rust is a systems programming language with ownership and borrowing.", "test-agent")
    manager.evaluate("tile-2", "What is PLATO?", "PLATO is the fleet knowledge system.", "test-agent")
    manager.evaluate("tile-3", "What is a crab?", "A crab is a crustacean.", "test-agent")
    
    print(f"\nTile-1 score: {manager.get_tile_score('tile-1'):.2f}")
    print(f"Tile-2 score: {manager.get_tile_score('tile-2'):.2f}")
    print(f"Tile-3 score: {manager.get_tile_score('tile-3'):.2f}")
    
    print("\n=== Fleet Quality Report ===")
    print(json.dumps(manager.get_fleet_quality_report(), indent=2))

if __name__ == "__main__":
    demo()
