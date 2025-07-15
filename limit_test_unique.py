#!/usr/bin/env python3
"""
Test memory limit with unique content
"""
import requests
import time

API_BASE = "http://localhost:8001"

# Generate token
print("1. Generating token...")
token_resp = requests.post(f"{API_BASE}/api/generate-token", json={"user_name": "Limit Test"})
token = token_resp.json()["token"]
print(f"   Token: {token[:20]}...")

# Add first memory
print("2. Adding first memory...")
resp1 = requests.post(f"{API_BASE}/memories?token={token}", json={"text": "I like Python programming", "tag": "preference"})
print(f"   Result: {resp1.json()}")

# Add second memory
print("3. Adding second memory...")
resp2 = requests.post(f"{API_BASE}/memories?token={token}", json={"text": "I prefer drinking coffee in the morning", "tag": "preference"})
print(f"   Result: {resp2.json()}")

# Add third memory (should fail with limit)
print("4. Adding third memory (should hit limit)...")
resp3 = requests.post(f"{API_BASE}/memories?token={token}", json={"text": "I work remotely from home", "tag": "preference"})
result3 = resp3.json()
print(f"   Result: {result3}")

if "error" in result3:
    print("✅ MEMORY LIMIT WORKING!")
else:
    print("❌ MEMORY LIMIT NOT WORKING!")