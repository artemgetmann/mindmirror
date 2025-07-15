"""
Conflict Detection for Memory System
Detects potentially conflicting memories and provides resolution options
"""
import requests
import time
import json
from typing import Dict, List, Optional, Tuple, Union

BASE_URL = "http://localhost:8000"
SIMILARITY_THRESHOLD = 0.9  # High similarity threshold for potential conflicts

class ConflictDetector:
    """
    Detects potential conflicts between memories and provides resolution options
    """
    
    def __init__(self, base_url: str = BASE_URL):
        """Initialize the conflict detector"""
        self.base_url = base_url
        
    def check_for_conflicts(self, text: str, tag: str) -> Dict:
        """
        Check if a new memory would conflict with existing memories
        Returns: Dict with conflict info if found, empty dict otherwise
        """
        # Search for highly similar memories with the same tag
        response = requests.post(
            f"{self.base_url}/memories/search",
            json={
                "query": text,
                "tag_filter": tag,
                "limit": 5
            }
        )
        
        if response.status_code != 200:
            print(f"Error searching for conflicts: {response.text}")
            return {}
            
        results = response.json()["results"]
        
        # Filter for high similarity matches
        potential_conflicts = [
            r for r in results 
            if r["similarity"] >= SIMILARITY_THRESHOLD and r["text"] != text
        ]
        
        if not potential_conflicts:
            return {}
            
        # For now, we'll use simple heuristics to detect contradiction
        # Later, we could use sentiment analysis or an LLM to analyze contradiction
        conflicts = []
        
        for conflict in potential_conflicts:
            # Simple contradiction detection heuristics
            # Check for opposite sentiment indicators in the text
            indicators = self._check_basic_contradiction(text, conflict["text"])
            
            if indicators:
                conflicts.append({
                    "memory": conflict,
                    "contradiction_type": indicators,
                    "resolution_options": ["keep_both", "keep_new", "keep_existing"]
                })
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts
        }
    
    def _check_basic_contradiction(self, text1: str, text2: str) -> List[str]:
        """
        Basic contradiction detection using keyword analysis
        Returns a list of contradiction indicators found
        """
        contradictions = []
        
        # Simple opposite pairs that might indicate contradiction
        opposite_pairs = [
            ("love", "hate"), 
            ("always", "never"),
            ("like", "dislike"),
            ("enjoy", "dislike"),
            ("prefer", "avoid"),
            ("yes", "no"),
            ("good", "bad"),
            ("positive", "negative")
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Check for opposite word pairs across texts
        for word1, word2 in opposite_pairs:
            if word1 in text1_lower and word2 in text2_lower:
                contradictions.append(f"opposite_words:{word1}_{word2}")
            elif word2 in text1_lower and word1 in text2_lower:
                contradictions.append(f"opposite_words:{word2}_{word1}")
        
        # Check for negation patterns
        negation_words = ["not", "don't", "doesn't", "isn't", "aren't", "never"]
        
        # Simplistic negation detection - could be improved
        for negation in negation_words:
            # Check if one has negation and other doesn't for same key phrase
            for word in text1_lower.split():
                if word not in negation_words and len(word) > 3:
                    if (negation in text1_lower and word in text1_lower and
                        negation not in text2_lower and word in text2_lower):
                        contradictions.append(f"negation:{negation}_{word}")
                    elif (negation in text2_lower and word in text2_lower and
                          negation not in text1_lower and word in text1_lower):
                        contradictions.append(f"negation:{negation}_{word}")
                        
        return contradictions

    def resolve_conflict(self, conflict_info: Dict, resolution: str = "keep_both") -> Dict:
        """
        Resolve a conflict based on the chosen resolution strategy
        resolution: One of "keep_both", "keep_new", "keep_existing"
        """
        if not conflict_info or "conflicts" not in conflict_info:
            return {"status": "no_conflict_to_resolve"}
            
        if resolution == "keep_both":
            return {"status": "keep_both", "message": "Both memories preserved"}
            
        elif resolution == "keep_new":
            # We would delete the existing memory
            # (Deletion endpoint not implemented yet)
            return {
                "status": "keep_new",
                "message": "Existing memory would be replaced", 
                "action_needed": "API needs DELETE endpoint"
            }
            
        elif resolution == "keep_existing":
            # Don't store the new memory
            return {
                "status": "keep_existing",
                "message": "New memory discarded"
            }
            
        else:
            return {"status": "invalid_resolution"}

# Demo functions to show the conflict detection in action

def demo_conflict_detection():
    """Run a demo of the conflict detection logic"""
    print("\n🔍 CONFLICT DETECTION DEMO")
    print("=" * 50)
    
    detector = ConflictDetector()
    
    # Add a memory
    print("Step 1: Adding a preference memory")
    memory1 = {
        "text": "I prefer working at night",
        "tag": "preference"
    }
    response = requests.post(f"{BASE_URL}/memories", json=memory1)
    print_response(response)
    
    # Add a contradictory memory
    print("\nStep 2: Adding a contradictory preference")
    memory2 = {
        "text": "I enjoy working in the morning, not at night",
        "tag": "preference"
    }
    
    # First, check for conflicts
    print("\nChecking for conflicts before adding...")
    conflicts = detector.check_for_conflicts(memory2["text"], memory2["tag"])
    print(json.dumps(conflicts, indent=2))
    
    if conflicts and conflicts.get("has_conflicts"):
        print("\nConflict detected! In a real system, we would:")
        print("1. Alert the user about the conflict")
        print("2. Show both conflicting memories")
        print("3. Ask how to resolve (keep both, keep new, keep old)")
        
        print("\nFor this demo, we'll keep both...")
        resolution = detector.resolve_conflict(conflicts, "keep_both")
        print(json.dumps(resolution, indent=2))
    
    # Store it anyway for demo purposes
    print("\nStoring the conflicting memory anyway...")
    response = requests.post(f"{BASE_URL}/memories", json=memory2)
    print_response(response)
    
    # Now try searching with a query that would match both
    print("\nSearching for 'When does the user prefer to work?'")
    response = requests.post(
        f"{BASE_URL}/memories/search",
        json={"query": "When does the user prefer to work?", "limit": 3}
    )
    print_response(response)
    
    print("\n➡️ In a conflict situation, both memories are returned.")
    print("   The calling application would need to handle this by:")
    print("   1. Identifying the conflict when both appear")
    print("   2. Presenting the contradiction to the user")
    print("   3. Potentially asking for clarification")

def print_response(response):
    """Pretty print API response"""
    try:
        print(f"Response (Status: {response.status_code}):")
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Memory server not running. Start server first.")
            exit(1)
    except:
        print("❌ Cannot connect to server. Start memory server first.")
        exit(1)
        
    demo_conflict_detection()
