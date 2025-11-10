#!/bin/bash
#
# Quick status checker for network optimizations
# Shows current configuration and identifies issues
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Network Optimization Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check status
check_status() {
    local name=$1
    local command=$2
    local expected=$3
    
    result=$(eval "$command" 2>/dev/null)
    
    if [[ "$result" == "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $name: ${GREEN}$result${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $name: ${RED}$result${NC} (expected: $expected)"
        return 1
    fi
}

# Check BBR
echo -e "${YELLOW}Congestion Control:${NC}"
check_status "BBR" "sysctl -n net.ipv4.tcp_congestion_control" "bbr"
echo ""

# Check TCP settings
echo -e "${YELLOW}TCP Settings:${NC}"
check_status "TCP Low Latency" "sysctl -n net.ipv4.tcp_low_latency" "1"
check_status "TCP Fast Open" "sysctl -n net.ipv4.tcp_fastopen" "3"
check_status "TCP SACK" "sysctl -n net.ipv4.tcp_sack" "1"
echo ""

# Check CPU governor
echo -e "${YELLOW}CPU Configuration:${NC}"
if [[ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    check_status "CPU Governor" "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" "performance"
else
    echo -e "${YELLOW}⚠${NC} CPU frequency scaling not available"
fi
echo ""

# Check THP
echo -e "${YELLOW}Memory Configuration:${NC}"
if [[ -f /sys/kernel/mm/transparent_hugepage/enabled ]]; then
    thp_status=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    if [[ "$thp_status" == "never" ]]; then
        echo -e "${GREEN}✓${NC} Transparent Huge Pages: ${GREEN}disabled${NC}"
    else
        echo -e "${RED}✗${NC} Transparent Huge Pages: ${RED}$thp_status${NC} (should be: never)"
    fi
else
    echo -e "${YELLOW}⚠${NC} THP not available"
fi
echo ""

# Check file descriptors
echo -e "${YELLOW}File Descriptors:${NC}"
fd_limit=$(ulimit -n)
if [[ $fd_limit -ge 65536 ]]; then
    echo -e "${GREEN}✓${NC} Limit: ${GREEN}$fd_limit${NC}"
else
    echo -e "${RED}✗${NC} Limit: ${RED}$fd_limit${NC} (should be >= 65536)"
fi
echo ""

# Check network interface
echo -e "${YELLOW}Network Interface:${NC}"
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
if [[ -n "$INTERFACE" ]]; then
    echo -e "  Interface: ${BLUE}$INTERFACE${NC}"
    
    if command -v ethtool &> /dev/null; then
        gro_status=$(ethtool -k "$INTERFACE" 2>/dev/null | grep "generic-receive-offload:" | awk '{print $2}')
        if [[ "$gro_status" == "off" ]]; then
            echo -e "  ${GREEN}✓${NC} GRO: ${GREEN}disabled${NC}"
        else
            echo -e "  ${RED}✗${NC} GRO: ${RED}$gro_status${NC} (should be: off)"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} ethtool not available"
    fi
else
    echo -e "  ${RED}✗${NC} Could not detect network interface"
fi
echo ""

# Check DNS
echo -e "${YELLOW}DNS Configuration:${NC}"
if systemctl is-active --quiet systemd-resolved; then
    dns_servers=$(resolvectl status 2>/dev/null | grep "DNS Servers" | head -1 | awk '{print $3}')
    if [[ -n "$dns_servers" ]]; then
        echo -e "  ${GREEN}✓${NC} systemd-resolved active"
        echo -e "  DNS: $dns_servers"
    else
        echo -e "  ${YELLOW}⚠${NC} systemd-resolved active but no DNS configured"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} systemd-resolved not active"
fi
echo ""

# Buffer sizes
echo -e "${YELLOW}Buffer Sizes:${NC}"
rmem_default=$(sysctl -n net.core.rmem_default)
wmem_default=$(sysctl -n net.core.wmem_default)
echo -e "  RX Default: $(numfmt --to=iec $rmem_default 2>/dev/null || echo $rmem_default)"
echo -e "  TX Default: $(numfmt --to=iec $wmem_default 2>/dev/null || echo $wmem_default)"

if [[ $rmem_default -le 65536 ]]; then
    echo -e "  ${BLUE}Profile: Aggressive (low latency)${NC}"
elif [[ $rmem_default -le 262144 ]]; then
    echo -e "  ${BLUE}Profile: Moderate (balanced)${NC}"
else
    echo -e "  ${BLUE}Profile: Conservative (high throughput)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Quick Actions:${NC}"
echo ""
echo -e "  View detailed config: ${BLUE}cat /etc/sysctl.d/99-low-latency-s2s.conf${NC}"
echo -e "  Test latency: ${BLUE}sudo bash /files/mindroot/test-network-latency.sh${NC}"
echo -e "  Re-optimize: ${BLUE}sudo bash /files/mindroot/optimize-network-latency.sh${NC}"
echo ""
