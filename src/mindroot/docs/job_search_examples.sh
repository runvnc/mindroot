#!/bin/bash
# Examples: Job Search
# Replace YOUR_API_KEY with your actual API key

# Search by metadata fields
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&metadata_query={\"project_id\":\"customer_research\",\"priority\":\"high\"}&limit=20"

# Search with date range (jobs completed in 2024)
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&after_date=2024-01-01T00:00:00&before_date=2024-12-31T23:59:59&status=completed&limit=100"

# Search by job type with pagination
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&job_type=text_analysis&offset=0&limit=50"

# Search by status
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&status=failed&limit=25"

# Combined search: metadata + date range + status + job type
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&metadata_query={\"source\":\"quarterly_report\"}&after_date=2024-11-01T00:00:00&status=completed&job_type=document_processing&limit=25&offset=0"

# Search for jobs from the last 7 days
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&after_date=$(date -d '7 days ago' --iso-8601=seconds)&limit=50"

# Get second page of results
curl "http://localhost:8000/api/jobs/search?api_key=YOUR_API_KEY&job_type=text_analysis&offset=50&limit=50"