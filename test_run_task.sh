#!/bin/bash

# Check if API key is provided
if [ -z "$MINDROOT_API_KEY" ]; then
    echo "Error: MINDROOT_API_KEY environment variable not set"
    exit 1
fi

# Default values
AGENT_NAME="default"
SERVER_URL="http://localhost:8000"
TIMEOUT=300

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --agent)
        AGENT_NAME="$2"
        shift
        shift
        ;;
        --url)
        SERVER_URL="$2"
        shift
        shift
        ;;
        --timeout)
        TIMEOUT="$2"
        shift
        shift
        ;;
        *)
        # Unknown option
        shift
        ;;
    esac
done

# Instructions for the agent (can be customized)
INSTRUCTIONS="Please analyze the following data and provide insights: This is a test of the long-running task endpoint."

echo "Testing run_task endpoint with agent: $AGENT_NAME"
echo "Server URL: $SERVER_URL"
echo "Timeout: $TIMEOUT seconds"
echo "Instructions: $INSTRUCTIONS"
echo ""

# Make the request with curl
echo "Sending request..."
curl -s -X POST \
    "$SERVER_URL/task/$AGENT_NAME?api_key=$MINDROOT_API_KEY" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "{\"instructions\": \"$INSTRUCTIONS\"}" \
    --max-time $TIMEOUT \
    | jq .

echo ""
echo "Request completed."
