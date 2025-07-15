"""
Comprehensive Memory System Test Suite
Tests vector search, ranking, edge cases, and all tag types
Not sure if its the right way to test anymore
"""
import requests
import json
import time

BASE_URL = "http://localhost:8003"

def clear_all_memories():
    """Clear existing memories for clean testing"""
    print("🧹 Clearing existing memories...")
    # Note: We'd need a DELETE endpoint for this. For now, we'll work with existing data.
    pass

def setup_diverse_memories():
    """Setup memories across all tag types with varied content"""
    
    memories = [
        # Preferences
        {"text": "Prefers blunt, direct communication", "tag": "preference"},
        {"text": "Hates small talk and pleasantries", "tag": "preference"},
        {"text": "Likes minimal, clean code without fluff", "tag": "preference"},
        
        # Identity
        {"text": "Software engineer and founder", "tag": "identity"},
        {"text": "Lives in Silicon Valley", "tag": "identity"},
        {"text": "Speaks English and Russian", "tag": "identity"},
        
        # Goals
        {"text": "Build efficient AI memory systems", "tag": "goal"},
        {"text": "Ship MVP before adding complexity", "tag": "goal"},
        {"text": "Reduce 90% of system before optimizing", "tag": "goal"},
        
        # Routines
        {"text": "Always explains logic before giving code", "tag": "routine"},
        {"text": "Reviews code like a senior developer", "tag": "routine"},
        {"text": "Asks blunt questions without softening", "tag": "routine"},
        
        # Tools
        {"text": "Uses FastAPI for web APIs", "tag": "tool"},
        {"text": "Prefers Python for backend development", "tag": "tool"},
        {"text": "Uses Chroma for vector storage", "tag": "tool"},
        
        # Projects
        {"text": "Working on MCP Memory system v0", "tag": "project"},
        {"text": "Building cloud-based vector memory", "tag": "project"},
        
        # Values
        {"text": "Prioritizes speed and clarity over polish", "tag": "value"},
        {"text": "Values first-principles thinking", "tag": "value"},
        {"text": "Believes in eliminating before optimizing", "tag": "value"},
        
        # Constraints
        {"text": "Limited context window for conversations", "tag": "constraint"},
        {"text": "Must use Python 3.13 compatibility", "tag": "constraint"},
        
        # Habits
        {"text": "Says 'Look...' when driving a point", "tag": "habit"},
        {"text": "Admits uncertainty with 'I don't know'", "tag": "habit"},
    ]
    
    print(f"📝 Setting up {len(memories)} diverse memories...")
    stored_ids = []
    
    for memory in memories:
        response = requests.post(f"{BASE_URL}/memories", json=memory)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'skipped':
                print(f"  ⏭️ [{memory['tag']}] {memory['text'][:50]}... (duplicate)")
            else:
                stored_ids.append(result['id'])
                print(f"  ✅ [{memory['tag']}] {memory['text'][:50]}...")
        else:
            print(f"  ❌ Failed to store: {memory['text'][:50]}...")
    
    print(f"✅ Stored {len(stored_ids)} memories")
    return stored_ids

def test_search_scenarios():
    """Test various search scenarios"""
    
    test_cases = [
        # Direct matches
        {
            "query": "How does he communicate?",
            "expected_tags": ["preference"],
            "expected_keywords": ["blunt", "direct"],
            "description": "Communication style query"
        },
        
        # Identity questions
        {
            "query": "What's his background?",
            "expected_tags": ["identity"],
            "expected_keywords": ["engineer", "founder", "Silicon Valley"],
            "description": "Background/identity query"
        },
        
        # Goals and objectives
        {
            "query": "What is he trying to build?",
            "expected_tags": ["goal", "project"],
            "expected_keywords": ["memory", "system", "MVP"],
            "description": "Project goals query"
        },
        
        # Technical preferences
        {
            "query": "What programming languages and tools does he use?",
            "expected_tags": ["tool"],
            "expected_keywords": ["Python", "FastAPI", "Chroma"],
            "description": "Technical stack query"
        },
        
        # Behavioral patterns
        {
            "query": "How does he approach problem solving?",
            "expected_tags": ["routine", "value"],
            "expected_keywords": ["logic", "first-principles", "eliminating"],
            "description": "Problem-solving approach"
        },
        
        # Edge case: very specific
        {
            "query": "Tell me about his speech patterns",
            "expected_tags": ["habit"],
            "expected_keywords": ["Look", "don't know"],
            "description": "Specific speech habits"
        },
        
        # Edge case: broad query
        {
            "query": "What do you know about this person?",
            "expected_tags": ["preference", "identity", "goal", "value"],
            "expected_keywords": ["engineer", "blunt", "memory", "speed"],
            "description": "Broad personality query"
        },
        
        # Edge case: should find nothing
        {
            "query": "What's his favorite ice cream flavor?",
            "expected_tags": [],
            "expected_keywords": [],
            "description": "Query with no relevant memories"
        }
    ]
    
    print("\n🔍 Testing search scenarios...")
    results = []
    
    for i, test in enumerate(test_cases):
        print(f"\n--- Test {i+1}: {test['description']} ---")
        print(f"Query: '{test['query']}'")
        
        search_data = {"query": test['query'], "limit": 5}
        response = requests.post(f"{BASE_URL}/memories/search", json=search_data)
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.text}")
            results.append(False)
            continue
        
        search_result = response.json()
        memories = search_result['results']
        
        print(f"Found {len(memories)} memories:")
        
        # Check if we found relevant memories
        if not test['expected_tags'] and len(memories) == 0:
            print("✅ Correctly found no relevant memories")
            results.append(True)
            continue
        
        if test['expected_tags'] and len(memories) == 0:
            print("❌ Expected to find memories but found none")
            results.append(False)
            continue
        
        # Analyze results
        found_tags = set()
        found_keywords = set()
        
        for memory in memories:
            found_tags.add(memory['tag'])
            text_lower = memory['text'].lower()
            for keyword in test['expected_keywords']:
                if keyword.lower() in text_lower:
                    found_keywords.add(keyword)
            
            print(f"  • [{memory['tag']}] {memory['text']} (sim: {memory['similarity']:.3f})")
        
        # Evaluate results
        tag_match = bool(found_tags.intersection(test['expected_tags'])) if test['expected_tags'] else True
        keyword_match = bool(found_keywords.intersection(test['expected_keywords'])) if test['expected_keywords'] else True
        
        if tag_match and keyword_match:
            print("✅ Search results match expectations")
            results.append(True)
        else:
            print(f"❌ Search results don't match. Found tags: {found_tags}, keywords: {found_keywords}")
            results.append(False)
    
    return results

def test_ranking_quality():
    """Test if similar memories are ranked appropriately"""
    
    print("\n🏆 Testing ranking quality...")
    
    # Test queries that should have clear ranking preferences
    ranking_tests = [
        {
            "query": "What kind of communication does he prefer?",
            "expected_top": "blunt",  # Should rank communication preferences high
            "description": "Communication preference ranking"
        },
        {
            "query": "What's his job?",
            "expected_top": "engineer",  # Should rank identity/profession high
            "description": "Professional identity ranking"
        }
    ]
    
    results = []
    
    for test in ranking_tests:
        print(f"\n--- {test['description']} ---")
        print(f"Query: '{test['query']}'")
        
        search_data = {"query": test['query'], "limit": 3}
        response = requests.post(f"{BASE_URL}/memories/search", json=search_data)
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.text}")
            results.append(False)
            continue
        
        memories = response.json()['results']
        
        if not memories:
            print("❌ No memories found")
            results.append(False)
            continue
        
        # Check if expected keyword appears in top result
        top_memory = memories[0]
        if test['expected_top'].lower() in top_memory['text'].lower():
            print(f"✅ Top result contains '{test['expected_top']}': {top_memory['text']}")
            print(f"   Similarity: {top_memory['similarity']:.3f}")
            results.append(True)
        else:
            print(f"❌ Top result doesn't contain '{test['expected_top']}': {top_memory['text']}")
            print(f"   Similarity: {top_memory['similarity']:.3f}")
            results.append(False)
    
    return results

def test_tag_filtering():
    """Test tag-based filtering"""
    
    print("\n🏷️ Testing tag filtering...")
    
    results = []
    
    for tag in ["preference", "identity", "goal", "tool"]:
        print(f"\n--- Testing tag filter: {tag} ---")
        
        search_data = {"query": "anything", "tag_filter": tag, "limit": 10}
        response = requests.post(f"{BASE_URL}/memories/search", json=search_data)
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.text}")
            results.append(False)
            continue
        
        memories = response.json()['results']
        
        # Check all results have correct tag
        all_correct = all(mem['tag'] == tag for mem in memories)
        
        if all_correct and len(memories) > 0:
            print(f"✅ Found {len(memories)} memories with tag '{tag}'")
            results.append(True)
        else:
            print(f"❌ Tag filtering failed. Found {len(memories)} memories, correct tags: {all_correct}")
            results.append(False)
    
    return results

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    
    print("🧠 Comprehensive Memory System Test Suite")
    print("=" * 50)
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False
    
    print("✅ Server is healthy\n")
    
    # Setup test data
    setup_diverse_memories()
    
    # Run test suites
    search_results = test_search_scenarios()
    ranking_results = test_ranking_quality() 
    filtering_results = test_tag_filtering()
    
    # Calculate overall results
    total_tests = len(search_results) + len(ranking_results) + len(filtering_results)
    passed_tests = sum(search_results) + sum(ranking_results) + sum(filtering_results)
    
    print(f"\n📊 COMPREHENSIVE TEST RESULTS")
    print(f"=" * 50)
    print(f"Search scenarios: {sum(search_results)}/{len(search_results)}")
    print(f"Ranking quality: {sum(ranking_results)}/{len(ranking_results)}")
    print(f"Tag filtering: {sum(filtering_results)}/{len(filtering_results)}")
    print(f"Total: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🚀 ALL TESTS PASSED! Memory system is robust.")
        return True
    else:
        print(f"💥 {total_tests - passed_tests} tests failed. System needs work.")
        return False

if __name__ == "__main__":
    run_comprehensive_tests()