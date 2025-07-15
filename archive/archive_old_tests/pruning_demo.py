"""
Memory Pruning Demo

This script demonstrates the pruning logic for memory systems.
It identifies memories that should be archived based on age, access time, and importance.
"""
from datetime import datetime, timedelta
import chromadb
import json
import time

# Initialize ChromaDB
print("Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="memories")

# Constants for pruning logic
ARCHIVE_AGE_DAYS = 90  # Archive memories older than 90 days
ACCESS_THRESHOLD_DAYS = 30  # Archive if not accessed in last 30 days
CORE_TAGS = ["identity", "value"]  # Never prune these core memories

def clear_text():
    """Clear console text for better readability"""
    print("\033c", end="")

def print_header(text):
    """Print a formatted header"""
    print(f"\n\033[1;36m{text}\033[0m")
    print("=" * 50)

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def get_all_memories():
    """Get all memories from the database"""
    if collection.count() == 0:
        return []
    
    result = collection.get()
    
    memories = []
    for i, doc in enumerate(result['documents']):
        memory = {
            "id": result['ids'][i],
            "text": doc,
            "metadata": result['metadatas'][i]
        }
        memories.append(memory)
    
    return memories

def add_test_memories():
    """Add test memories with various timestamps for pruning demo"""
    now = datetime.utcnow()
    
    test_memories = [
        # Recent memories (should not be pruned)
        {
            "id": "recent_memory_1",
            "text": "I like to read fiction books",
            "tag": "preference",
            "timestamp": (now - timedelta(days=15)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=5)).isoformat() + "Z"
        },
        {
            "id": "recent_memory_2",
            "text": "I exercise three times a week",
            "tag": "routine",
            "timestamp": (now - timedelta(days=20)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=3)).isoformat() + "Z"
        },
        
        # Old but recently accessed (should not be pruned)
        {
            "id": "old_accessed_memory",
            "text": "I need to drink more water",
            "tag": "goal",
            "timestamp": (now - timedelta(days=120)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=2)).isoformat() + "Z"
        },
        
        # Old and not accessed (should be pruned)
        {
            "id": "old_unused_memory_1",
            "text": "I want to try that new restaurant downtown",
            "tag": "goal",
            "timestamp": (now - timedelta(days=95)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=40)).isoformat() + "Z"
        },
        {
            "id": "old_unused_memory_2",
            "text": "I should call my friend about that project",
            "tag": "project",
            "timestamp": (now - timedelta(days=100)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=45)).isoformat() + "Z"
        },
        
        # Core memories (should never be pruned regardless of age)
        {
            "id": "core_memory_1",
            "text": "I value honesty above all else",
            "tag": "value",
            "timestamp": (now - timedelta(days=150)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=50)).isoformat() + "Z"
        },
        {
            "id": "core_memory_2",
            "text": "I'm a software engineer",
            "tag": "identity",
            "timestamp": (now - timedelta(days=180)).isoformat() + "Z",
            "last_accessed": (now - timedelta(days=60)).isoformat() + "Z"
        }
    ]
    
    for memory in test_memories:
        memory_id = memory.pop("id")
        tag = memory.pop("tag")
        text = memory.pop("text")
        
        # Add dummy embedding (not used for pruning demo)
        empty_embedding = [0.0] * 384
        
        # Store in Chroma
        metadata = memory
        metadata["tag"] = tag
        
        collection.add(
            embeddings=[empty_embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        print(f"Added test memory: {memory_id}")
    
    print(f"Added {len(test_memories)} test memories")

def prune_memories():
    """Identify memories for pruning based on age, access time, and importance"""
    print_header("Finding memories to prune")
    
    now = datetime.utcnow()
    archive_cutoff = now - timedelta(days=ARCHIVE_AGE_DAYS)
    access_cutoff = now - timedelta(days=ACCESS_THRESHOLD_DAYS)
    
    # Format cutoff dates for display
    print(f"Archive cutoff date: {archive_cutoff.isoformat()} (older than {ARCHIVE_AGE_DAYS} days)")
    print(f"Access cutoff date: {access_cutoff.isoformat()} (not accessed in {ACCESS_THRESHOLD_DAYS} days)")
    print(f"Core tags (never pruned): {CORE_TAGS}")
    
    # Get all memories
    memories = get_all_memories()
    
    # Split into categories
    to_prune = []
    keep = []
    
    for memory in memories:
        metadata = memory["metadata"]
        
        # Skip core memories
        if "tag" in metadata and metadata["tag"] in CORE_TAGS:
            keep.append(memory)
            continue
        
        # Check timestamp
        timestamp = datetime.fromisoformat(metadata["timestamp"].rstrip("Z"))
        
        # Check last_accessed (if available)
        last_accessed = None
        if "last_accessed" in metadata:
            last_accessed = datetime.fromisoformat(metadata["last_accessed"].rstrip("Z"))
        else:
            # If no last_accessed, use timestamp
            last_accessed = timestamp
        
        # Apply pruning logic
        if timestamp < archive_cutoff and last_accessed < access_cutoff:
            to_prune.append(memory)
        else:
            keep.append(memory)
    
    # Report results
    print(f"\nFound {len(to_prune)} memories to prune out of {len(memories)} total memories")
    
    # Report details for memories to be pruned
    if to_prune:
        print("\nMemories to prune:")
        for memory in to_prune:
            print(f"- {memory['id']}: '{memory['text'][:50]}...' (Tag: {memory['metadata']['tag']})")
            print(f"  Created: {memory['metadata']['timestamp']}")
            print(f"  Last accessed: {memory['metadata'].get('last_accessed', 'N/A')}")
    
    # Return pruning results
    return {
        "total_memories": len(memories),
        "to_prune": to_prune,
        "to_keep": keep
    }

def archive_memories(memories_to_prune):
    """Demonstrate archiving pruned memories"""
    print_header("Archiving Pruned Memories")
    
    if not memories_to_prune:
        print("No memories to archive")
        return
    
    # In a real implementation, you might:
    # 1. Move memories to an archive collection
    # 2. Generate summaries of related memories before deletion
    # 3. Update references in other memories
    # 4. Log the archive action
    
    # For demo, we'll just simulate archiving
    for memory in memories_to_prune:
        print(f"Archiving memory {memory['id']}: '{memory['text'][:50]}...'")
        
        # In production, would move to archive collection here
        # For demo, just update status in metadata
        metadata = memory["metadata"]
        metadata["archived"] = True
        metadata["archive_date"] = datetime.utcnow().isoformat() + "Z"
        metadata["archive_reason"] = "age_and_access"
        
        # Update metadata in collection
        collection.update(
            ids=[memory["id"]],
            metadatas=[metadata]
        )
    
    print(f"\nArchived {len(memories_to_prune)} memories")

def main():
    """Run the pruning demo"""
    clear_text()
    print_header("🧹 MEMORY PRUNING DEMO")
    
    # Check if we have any memories
    existing_count = collection.count()
    print(f"Found {existing_count} existing memories in database")
    
    # Add test memories if needed
    if existing_count < 7:  # Our demo needs at least 7 test memories
        print_header("Adding test memories for demonstration")
        add_test_memories()
    
    # Run pruning logic
    print_header("Running pruning logic")
    pruning_results = prune_memories()
    
    # Archive pruned memories
    if pruning_results["to_prune"]:
        archive_memories(pruning_results["to_prune"])
    
    # Summary
    print_header("Pruning Summary")
    print(f"Total memories: {pruning_results['total_memories']}")
    print(f"Memories kept: {len(pruning_results['to_keep'])}")
    print(f"Memories pruned: {len(pruning_results['to_prune'])}")
    
    # Pruning strategy explanation
    print_header("Pruning Strategy")
    print("The memory system prunes memories based on three criteria:")
    print(f"1. Age: Memories older than {ARCHIVE_AGE_DAYS} days")
    print(f"2. Access: Memories not accessed in the last {ACCESS_THRESHOLD_DAYS} days")
    print(f"3. Importance: Core memories with tags {CORE_TAGS} are never pruned")
    print("\nA memory is pruned only if it meets BOTH age AND access criteria,")
    print("unless it has a core tag, in which case it is never pruned.")
    
    print("\nIn a production system, pruned memories would be:")
    print("- Moved to an archive collection")
    print("- Potentially summarized or combined if related")
    print("- Accessible via specific archive retrieval endpoints")

if __name__ == "__main__":
    main()
