#!/bin/bash
API_URL="http://localhost:8000"

echo "--- 1. Ingesting v1 Manual ---"
curl -X POST "$API_URL/ingest?version=1" -F "file=@data/ct200_v1.pdf"

echo -e "\n\n--- 2. Fetching nodes to create selection ---"
# Assuming node 1 and 2 exist
curl -X POST "$API_URL/selections" \
     -H "Content-Type: application/json" \
     -d '{"name": "Safety Checks", "node_ids": [1, 2], "version": 1}'

echo -e "\n\n--- 3. Generating LLM Test Cases for Selection 1 ---"
curl -X POST "$API_URL/generate/1"

echo -e "\n\n--- 4. Ingesting v2 (The Change) ---"
curl -X POST "$API_URL/ingest?version=2" -F "file=@data/ct200_v2.pdf"

echo -e "\n\n--- 5. Checking Staleness of v1 Selection against v2 ---"
curl -X GET "$API_URL/staleness/1"