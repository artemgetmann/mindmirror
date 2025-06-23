"""
Batch Stress Test for Memory System
Tests performance with 500+ entries and varied semantic queries
Measures response times and embedding token usage
"""

import requests
import json
import time
import random
import matplotlib.pyplot as plt
from datetime import datetime
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
NUM_MEMORIES = 550  # Generate 550 test memories
BATCH_SIZES = [10, 50, 100]  # Test different batch sizes
TEST_QUERIES = [
    "What kind of person is this?", 
    "What are their goals?",
    "How do they communicate?",
    "What tools do they use?",
    "What skills do they have?",
    "What are their preferences in code?",
    "How do they approach problem solving?",
    "What projects are they working on?",
    "What habits do they have?",
    "Tell me about their values"
]

# Performance tracking
insertion_times = []
search_times = []
total_token_count = 0  # Rough approximation based on text length

# Log start time
start_time = datetime.now()
print(f"Starting batch stress test at {start_time}")
print(f"Testing with {NUM_MEMORIES} memories and varied batch sizes: {BATCH_SIZES}")

def generate_memories(count):
    """Generate varied test memories across all tags"""
    
    adjectives = ["efficient", "reliable", "scalable", "fast", "robust", "simple", "clean", "minimal", 
                 "elegant", "optimized", "consistent", "maintainable", "readable", "modular", "extensible"]
    
    verbs = ["building", "developing", "creating", "designing", "implementing", "shipping", "testing", 
            "architecting", "engineering", "coding", "debugging", "optimizing", "refactoring"]
    
    tech = ["Python", "FastAPI", "React", "TypeScript", "Docker", "Kubernetes", "AWS", "GCP", 
           "MongoDB", "PostgreSQL", "Redis", "ChakraUI", "TailwindCSS", "Rust", "Go"]
    
    concepts = ["APIs", "microservices", "cloud functions", "databases", "UI components", 
               "authentication", "state management", "real-time updates", "CI/CD pipelines",
               "unit tests", "end-to-end tests", "monitoring", "logging", "alerts"]
    
    goals = [f"Build {adj} {concept}" for adj, concept in zip(random.sample(adjectives, 10), random.sample(concepts, 10))]
    preferences = [f"Prefers {adj} code" for adj in adjectives]
    routines = [f"Always {verb} before deploying" for verb in random.sample(verbs, 10)]
    tools = [f"Uses {t} for {c}" for t, c in zip(random.sample(tech, 10), random.sample(concepts, 10))]
    identities = [
        "Backend developer with focus on API design",
        "Full-stack engineer specializing in React and Node",
        "DevOps engineer with Kubernetes expertise", 
        "ML engineer working on embedding models",
        "Systems architect focused on distributed systems"
    ]
    projects = [f"{verb} a {adj} {concept} using {tech}" for verb, adj, concept, tech in 
               zip(random.sample(verbs, 8), random.sample(adjectives, 8), 
                   random.sample(concepts, 8), random.sample(tech, 8))]
    habits = [
        "Writes tests before implementation",
        "Documents code thoroughly",
        "Refactors regularly",
        "Reviews PRs promptly",
        "Participates actively in design discussions"
    ]
    values = [
        "Values simplicity over complexity",
        "Believes in test-driven development",
        "Prioritizes user experience",
        "Focuses on maintainable solutions",
        "Champions open source contribution"
    ]
    constraints = [
        "Limited by deployment schedule",
        "Must maintain backward compatibility",
        "Needs to support legacy systems",
        "Required to use specific framework versions",
        "Has to meet strict performance SLAs"
    ]
    
    # Map tags to their respective content lists
    tag_content_map = {
        "goal": goals,
        "preference": preferences,
        "routine": routines,
        "tool": tools,
        "identity": identities,
        "project": projects,
        "habit": habits,
        "value": values,
        "constraint": constraints
    }
    
    # Generate memories ensuring distribution across tags
    memories = []
    tags = ["goal", "preference", "routine", "tool", "identity", "project", "habit", "value", "constraint"]
    
    for i in range(count):
        tag = tags[i % len(tags)]  # Rotate through tags
        content_list = tag_content_map[tag]
        content_idx = (i // len(tags)) % len(content_list)
        
        # Add some variation to avoid duplicates
        variation = "" if i < len(tags) * len(content_list) else f" (variant {i})"
        
        memory = {
            "text": content_list[content_idx] + variation,
            "tag": tag,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        memories.append(memory)
    
    return memories

def batch_insert_memories(memories, batch_size):
    """Insert memories in batches and track performance"""
    num_batches = len(memories) // batch_size
    if len(memories) % batch_size > 0:
        num_batches += 1
    
    print(f"\nInserting {len(memories)} memories in {num_batches} batches (size: {batch_size})")
    
    stored_count = 0
    skipped_count = 0
    batch_times = []
    
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, len(memories))
        batch = memories[start_idx:end_idx]
        
        print(f"  Batch {i+1}/{num_batches}: {len(batch)} memories", end="", flush=True)
        
        batch_start = time.time()
        for memory in batch:
            # Track approximate tokens (characters / 4)
            global total_token_count
            total_token_count += len(memory['text']) // 4
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/memories", json=memory)
            end_time = time.time()
            insertion_times.append(end_time - start_time)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'skipped':
                    skipped_count += 1
                else:
                    stored_count += 1
            else:
                print(f"\nError inserting memory: {response.text}")
        
        batch_end = time.time()
        batch_time = batch_end - batch_start
        batch_times.append(batch_time)
        
        print(f" (took {batch_time:.2f}s)")
    
    avg_batch_time = statistics.mean(batch_times)
    print(f"\nComplete: {stored_count} memories stored, {skipped_count} duplicates skipped")
    print(f"Average batch time: {avg_batch_time:.2f}s, Average per memory: {statistics.mean(insertion_times):.4f}s")
    
    return stored_count, skipped_count

def measure_search_performance():
    """Measure search performance with various queries"""
    print("\nTesting search performance...")
    
    results = []
    for i, query in enumerate(TEST_QUERIES):
        print(f"  Query {i+1}/{len(TEST_QUERIES)}: '{query}'", end="", flush=True)
        
        # Track approximate tokens (characters / 4)
        global total_token_count
        total_token_count += len(query) // 4
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/memories/search", 
            json={"query": query, "limit": 10}
        )
        end_time = time.time()
        
        duration = end_time - start_time
        search_times.append(duration)
        
        if response.status_code == 200:
            search_result = response.json()
            num_results = len(search_result['results'])
            avg_similarity = statistics.mean([r['similarity'] for r in search_result['results']]) if search_result['results'] else 0
            results.append({
                "query": query,
                "duration": duration,
                "num_results": num_results,
                "avg_similarity": avg_similarity
            })
            print(f" - {num_results} results in {duration:.3f}s, avg similarity: {avg_similarity:.3f}")
        else:
            print(f"Error: {response.text}")
    
    return results

def generate_report(stored_count, skipped_count, search_results):
    """Generate performance report"""
    end_time = datetime.now()
    test_duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print(f"MEMORY SYSTEM STRESS TEST REPORT")
    print("="*60)
    print(f"Completed at: {end_time}")
    print(f"Total test duration: {test_duration:.2f}s")
    print("\nMEMORY STATISTICS:")
    print(f"  - Memories stored: {stored_count}")
    print(f"  - Duplicates skipped: {skipped_count}")
    print(f"  - Total memories attempted: {stored_count + skipped_count}")
    
    print("\nPERFORMANCE METRICS:")
    print(f"  - Average insertion time: {statistics.mean(insertion_times):.4f}s")
    print(f"  - Min insertion time: {min(insertion_times):.4f}s")
    print(f"  - Max insertion time: {max(insertion_times):.4f}s")
    print(f"  - Average search time: {statistics.mean(search_times):.4f}s")
    print(f"  - Min search time: {min(search_times):.4f}s")
    print(f"  - Max search time: {max(search_times):.4f}s")
    
    print("\nTOKEN USAGE:")
    print(f"  - Estimated total tokens processed: {total_token_count}")
    print(f"  - Tokens per memory (avg): {total_token_count / (stored_count + skipped_count):.1f}")
    
    print("\nQUERY PERFORMANCE:")
    for result in search_results:
        print(f"  - '{result['query']}': {result['num_results']} results in {result['duration']:.3f}s, avg similarity: {result['avg_similarity']:.3f}")

    # Plot performance graphs
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Insert time histogram
    ax1.hist(insertion_times, bins=20, alpha=0.7)
    ax1.set_title('Memory Insertion Time Distribution')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Count')
    
    # Search time histogram
    ax2.bar([r['query'][:10] + '...' for r in search_results], 
            [r['duration'] for r in search_results], alpha=0.7)
    ax2.set_title('Search Time by Query')
    ax2.set_xlabel('Query')
    ax2.set_ylabel('Time (seconds)')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('stress_test_performance.png')
    print("\nPerformance graphs saved to 'stress_test_performance.png'")

def run_stress_test():
    """Run complete stress test"""
    print("Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"Server health check failed: {response.status_code}")
            return
        print("✅ Server is healthy")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the memory server first.")
        return
    
    # Generate test data
    memories = generate_memories(NUM_MEMORIES)
    print(f"Generated {len(memories)} test memories")
    
    # Test with different batch sizes
    best_batch_size = None
    best_avg_time = float('inf')
    
    for batch_size in BATCH_SIZES:
        print(f"\n--- Testing with batch size: {batch_size} ---")
        batch_memories = memories[:100]  # Use same 100 memories for each batch size test
        
        batch_start = time.time()
        stored, skipped = batch_insert_memories(batch_memories, batch_size)
        batch_end = time.time()
        
        avg_time = (batch_end - batch_start) / len(batch_memories)
        if avg_time < best_avg_time:
            best_avg_time = avg_time
            best_batch_size = batch_size
    
    print(f"\nBest batch size: {best_batch_size} (avg time: {best_avg_time:.4f}s per memory)")
    
    # Insert remaining memories with best batch size
    remaining_memories = memories[100:]
    stored, skipped = batch_insert_memories(remaining_memories, best_batch_size)
    
    # Test search performance
    search_results = measure_search_performance()
    
    # Generate report
    generate_report(stored, skipped, search_results)

if __name__ == "__main__":
    run_stress_test()