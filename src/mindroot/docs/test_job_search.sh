#!/bin/bash
# Test script for job search functionality
# Replace YOUR_API_KEY with your actual API key

API_KEY="YOUR_API_KEY"
BASE_URL="http://localhost:8000"

echo "Testing job search with metadata..."
echo "===================================="

# Test 1: Search for claim_id bft434
echo -e "\n1. Searching for claim_id='bft434':"
curl -s "${BASE_URL}/api/jobs/search?api_key=${API_KEY}&metadata_query=%7B%22claim_id%22%3A%22bft434%22%7D" | jq .

# Test 2: Search for all mr_claims jobs
echo -e "\n2. Searching for job_type='mr_claims.process_claim':"
curl -s "${BASE_URL}/api/jobs/search?api_key=${API_KEY}&job_type=mr_claims.process_claim&limit=5" | jq .

# Test 3: Search for jobs by username
echo -e "\n3. Searching for username='system':"
curl -s "${BASE_URL}/api/jobs/search?api_key=${API_KEY}&limit=3" | jq '.jobs[] | {id: .id, username: .username, metadata: .metadata}'

# Test 4: Check what metadata fields are available
echo -e "\n4. Sample job metadata from recent jobs:"
curl -s "${BASE_URL}/api/jobs/search?api_key=${API_KEY}&limit=5" | jq '.jobs[] | {id: .id, metadata: .metadata}'

echo -e "\n===================================="
echo "Test complete!"