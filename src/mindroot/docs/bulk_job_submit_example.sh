#!/bin/bash
# Example: Bulk Job Submission
# Replace YOUR_API_KEY with your actual API key

# Basic bulk submission with multiple instructions
curl -X POST "http://localhost:8000/api/jobs/bulk?api_key=YOUR_API_KEY" \
  -F "instructions_list=[\"Analyze customer feedback for sentiment\", \"Extract key topics from reviews\", \"Generate summary report\"]" \
  -F "agent_name=analysis_agent" \
  -F "job_type=text_analysis" \
  -F 'metadata={"project_id": "customer_research", "priority": "high"}'

# Bulk submission with file upload (shared across all jobs)
curl -X POST "http://localhost:8000/api/jobs/bulk?api_key=YOUR_API_KEY" \
  -F "instructions_list=[\"Process file section 1\", \"Process file section 2\", \"Process file section 3\"]" \
  -F "agent_name=document_processor" \
  -F "job_type=document_processing" \
  -F 'metadata={"source": "quarterly_report"}' \
  -F "files=@/path/to/document.pdf"

# Bulk submission with minimal parameters (job_type is optional)
curl -X POST "http://localhost:8000/api/jobs/bulk?api_key=YOUR_API_KEY" \
  -F "instructions_list=[\"Task one\", \"Task two\", \"Task three\"]" \
  -F "agent_name=general_worker"