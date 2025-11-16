#!/bin/bash
# Bulk Job Submission Examples
# API Key: 64f7ee93-752d-489f-a2f2-c2221e534af6

API_KEY="64f7ee93-752d-489f-a2f2-c2221e534af6"
BASE="http://localhost:8000"

echo "1. Multiple form fields (simplest)"
curl -X POST "$BASE/api/jobs/bulk?api_key=$API_KEY" \
  -F "instructions=Analyze customer feedback" \
  -F "instructions=Extract key topics" \
  -F "instructions=Generate summary" \
  -F "agent=analysis_agent" \
  -F "job_type=text_analysis"

echo -e "\n2. File upload (one per line)"
curl -X POST "$BASE/api/jobs/bulk?api_key=$API_KEY" \
  -F "instructions_file=@tasks.txt" \
  -F "agent=worker"

echo -e "\n3. CSV format"
curl -X POST "$BASE/api/jobs/bulk?api_key=$API_KEY" \
  -F "instructions_csv=Task 1,Task 2,Task 3" \
  -F "agent=worker"