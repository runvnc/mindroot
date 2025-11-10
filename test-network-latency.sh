#!/bin/bash
#
# Network Latency Testing and Benchmarking Script
# Tests network performance before/after optimization
#
# Usage: sudo bash test-network-latency.sh [--save-baseline|--compare]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASELINE_FILE="/root/network-baseline.txt"
MODE="test"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --save-baseline)
            MODE="baseline"
            shift
            ;;
        --compare)
            MODE="compare"
            shift
            ;;
        --help)
            echo "Usage: sudo bash $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --save-baseline  Run tests and save as baseline (before optimization)"
            echo "  --compare        Run tests and compare with baseline (after optimization)"
            echo "  (no options)     Just run tests and display results"
            echo ""
            echo "Typical workflow:"
            echo "  1. Before optimization: sudo bash $0 --save-baseline"
            echo "  2. Run optimization script"
            echo "  3. After reboot: sudo bash $0 --compare"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Network Latency Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for required tools
echo -e "${YELLOW}Checking required tools...${NC}"

if ! command -v ping &> /dev/null; then
    echo -e "${RED}✗ ping not found${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}Installing curl...${NC}"
    apt-get update -qq
    apt-get install -y curl
fi

if ! command -v bc &> /dev/null; then
    echo -e "${YELLOW}Installing bc...${NC}"
    apt-get update -qq
    apt-get install -y bc
fi

echo -e "${GREEN}✓${NC} All tools available"
echo ""

# Test targets
TARGETS=(
    "1.1.1.1:Cloudflare"
    "8.8.8.8:Google_DNS"
    "api.openai.com:OpenAI"
)

# Function to test latency
test_latency() {
    local target=$1
    local name=$2
    
    echo -e "${YELLOW}Testing $name ($target)...${NC}"
    
    # Ping test
    if ping -c 20 -i 0.2 "$target" &> /tmp/ping_test.txt; then
        local avg_latency=$(grep 'rtt min/avg/max' /tmp/ping_test.txt | awk -F'/' '{print $5}')
        local packet_loss=$(grep 'packet loss' /tmp/ping_test.txt | awk '{print $6}')
        echo -e "  Avg Latency: ${GREEN}${avg_latency}ms${NC}"
        echo -e "  Packet Loss: ${GREEN}${packet_loss}${NC}"
        echo "${name}:${avg_latency}:${packet_loss}"
    else
        echo -e "  ${RED}Failed to reach $target${NC}"
        echo "${name}:N/A:N/A"
    fi
}

# Function to test TCP connection time
test_tcp_connection() {
    local host=$1
    local port=$2
    local name=$3
    
    echo -e "${YELLOW}Testing TCP connection to $name...${NC}"
    
    local total_time=0
    local success_count=0
    
    for i in {1..10}; do
        local start=$(date +%s%N)
        if timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            local end=$(date +%s%N)
            local duration=$(( (end - start) / 1000000 ))
            total_time=$(( total_time + duration ))
            success_count=$(( success_count + 1 ))
        fi
        sleep 0.1
    done
    
    if [[ $success_count -gt 0 ]]; then
        local avg_time=$(( total_time / success_count ))
        echo -e "  Avg Connection Time: ${GREEN}${avg_time}ms${NC}"
        echo -e "  Success Rate: ${GREEN}${success_count}/10${NC}"
        echo "${name}_tcp:${avg_time}:${success_count}"
    else
        echo -e "  ${RED}All connections failed${NC}"
        echo "${name}_tcp:N/A:0"
    fi
}

# Function to test HTTP latency
test_http_latency() {
    local url=$1
    local name=$2
    
    echo -e "${YELLOW}Testing HTTP latency to $name...${NC}"
    
    local total_time=0
    local success_count=0
    
    for i in {1..5}; do
        local time_total=$(curl -o /dev/null -s -w '%{time_total}' "$url" 2>/dev/null || echo "0")
        if [[ "$time_total" != "0" ]]; then
            local time_ms=$(echo "$time_total * 1000" | bc)
            total_time=$(echo "$total_time + $time_ms" | bc)
            success_count=$(( success_count + 1 ))
        fi
        sleep 0.2
    done
    
    if [[ $success_count -gt 0 ]]; then
        local avg_time=$(echo "scale=2; $total_time / $success_count" | bc)
        echo -e "  Avg Response Time: ${GREEN}${avg_time}ms${NC}"
        echo "${name}_http:${avg_time}:${success_count}"
    else
        echo -e "  ${RED}All requests failed${NC}"
        echo "${name}_http:N/A:0"
    fi
}

# Run tests
echo -e "${BLUE}Running network tests...${NC}"
echo ""

RESULTS_FILE="/tmp/network_test_results_$(date +%s).txt"

# ICMP tests
for target_info in "${TARGETS[@]}"; do
    IFS=':' read -r target name <<< "$target_info"
    test_latency "$target" "$name" >> "$RESULTS_FILE"
    echo ""
done

# TCP connection tests
test_tcp_connection "1.1.1.1" "443" "Cloudflare_HTTPS" >> "$RESULTS_FILE"
echo ""
test_tcp_connection "api.openai.com" "443" "OpenAI_HTTPS" >> "$RESULTS_FILE"
echo ""

# HTTP latency tests
test_http_latency "https://1.1.1.1" "Cloudflare" >> "$RESULTS_FILE"
echo ""
test_http_latency "https://www.google.com" "Google" >> "$RESULTS_FILE"
echo ""

# System information
echo -e "${YELLOW}Collecting system information...${NC}"
echo "" >> "$RESULTS_FILE"
echo "=== System Info ===" >> "$RESULTS_FILE"
echo "Date: $(date)" >> "$RESULTS_FILE"
echo "Kernel: $(uname -r)" >> "$RESULTS_FILE"
echo "BBR: $(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo 'N/A')" >> "$RESULTS_FILE"
echo "TCP Low Latency: $(sysctl -n net.ipv4.tcp_low_latency 2>/dev/null || echo 'N/A')" >> "$RESULTS_FILE"
echo "CPU Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo 'N/A')" >> "$RESULTS_FILE"
echo ""

# Handle different modes
if [[ "$MODE" == "baseline" ]]; then
    cp "$RESULTS_FILE" "$BASELINE_FILE"
    echo -e "${GREEN}✓${NC} Baseline saved to $BASELINE_FILE"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run optimization: sudo bash optimize-network-latency.sh"
    echo "  2. Reboot: sudo reboot"
    echo "  3. Compare results: sudo bash $0 --compare"
    
elif [[ "$MODE" == "compare" ]]; then
    if [[ ! -f "$BASELINE_FILE" ]]; then
        echo -e "${RED}✗ No baseline found${NC}"
        echo "Run with --save-baseline first"
        exit 1
    fi
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Comparison with Baseline${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Compare key metrics
    echo -e "${YELLOW}Latency Improvements:${NC}"
    echo ""
    
    for target_info in "${TARGETS[@]}"; do
        IFS=':' read -r target name <<< "$target_info"
        
        baseline_latency=$(grep "^${name}:" "$BASELINE_FILE" | cut -d':' -f2)
        current_latency=$(grep "^${name}:" "$RESULTS_FILE" | cut -d':' -f2)
        
        if [[ "$baseline_latency" != "N/A" && "$current_latency" != "N/A" ]]; then
            improvement=$(echo "scale=2; (($baseline_latency - $current_latency) / $baseline_latency) * 100" | bc)
            
            echo -e "  ${name}:"
            echo -e "    Before: ${baseline_latency}ms"
            echo -e "    After:  ${current_latency}ms"
            
            if (( $(echo "$improvement > 0" | bc -l) )); then
                echo -e "    ${GREEN}Improvement: ${improvement}%${NC}"
            elif (( $(echo "$improvement < 0" | bc -l) )); then
                echo -e "    ${RED}Regression: ${improvement}%${NC}"
            else
                echo -e "    No change"
            fi
            echo ""
        fi
    done
    
    echo -e "${YELLOW}Full results saved to:${NC} $RESULTS_FILE"
    echo -e "${YELLOW}Baseline:${NC} $BASELINE_FILE"
    
else
    echo -e "${GREEN}✓${NC} Tests complete"
    echo -e "${YELLOW}Results saved to:${NC} $RESULTS_FILE"
    echo ""
    echo -e "${YELLOW}To save as baseline:${NC} sudo bash $0 --save-baseline"
fi

echo ""
