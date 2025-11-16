#!/bin/bash
# Job Search Examples
# API Key: 64f7ee93-752d-489f-a2f2-c2221e534af6

API_KEY="64f7ee93-752d-489f-a2f2-c2221e534af6"
BASE="http://localhost:8000"

echo "1. Search by metadata"
curl "$BASE/api/jobs/search?api_key=$API_KEY&claim_id=bft434"

echo -e "\n2. Search with date range"
curl "$BASE/api/jobs/search?api_key=$API_KEY&after_date=2024-01-01&status=completed"

echo -e "\n3. Search by job type"
curl "$BASE/api/jobs/search?api_key=$API_KEY&job_type=text_analysis&limit=10"