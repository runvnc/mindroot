#!/bin/bash
#
# VPS Environment Diagnostic Script
# Investigates system capabilities and limitations before optimization
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OUTPUT_FILE="/root/vps-diagnostic-$(date +%Y%m%d-%H%M%S).txt"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VPS Environment Diagnostic${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Saving detailed report to: $OUTPUT_FILE"
echo ""

# Start output file
{
    echo "VPS Environment Diagnostic Report"
    echo "Generated: $(date)"
    echo "========================================"
    echo ""
} > "$OUTPUT_FILE"

# Function to test and report
test_feature() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -e "${YELLOW}Testing: $name${NC}"
    result=$(eval "$command" 2>&1 || echo "ERROR")
    
    {
        echo "## $name"
        echo "Command: $command"
        echo "Result: $result"
        echo ""
    } >> "$OUTPUT_FILE"
    
    if [[ "$result" == "ERROR" ]] || [[ "$result" == *"No such file"* ]]; then
        echo -e "  ${RED}✗ Not available${NC}"
        echo "  Result: $result"
    elif [[ -n "$expected" ]] && [[ "$result" == "$expected" ]]; then
        echo -e "  ${GREEN}✓ $result${NC}"
    else
        echo -e "  ${BLUE}→ $result${NC}"
    fi
    echo ""
}

# 1. System Information
echo -e "${BLUE}=== System Information ===${NC}"
echo ""

test_feature "Hostname" "hostname"
test_feature "Kernel Version" "uname -r"
test_feature "OS Release" "cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'"
test_feature "Architecture" "uname -m"
test_feature "Uptime" "uptime -p"

# 2. Virtualization Detection
echo -e "${BLUE}=== Virtualization ===${NC}"
echo ""

test_feature "Virtualization Type" "systemd-detect-virt"
test_feature "Hypervisor" "cat /sys/hypervisor/type 2>/dev/null || lscpu | grep 'Hypervisor vendor' | awk '{print \$3}' || echo 'None detected'"
test_feature "Container" "cat /proc/1/cgroup | head -1"

# Check for common VPS indicators
if [[ -f /proc/user_beancounters ]]; then
    echo -e "  ${YELLOW}⚠ OpenVZ/Virtuozzo detected${NC}"
    echo "OpenVZ/Virtuozzo: YES" >> "$OUTPUT_FILE"
else
    echo "OpenVZ/Virtuozzo: NO" >> "$OUTPUT_FILE"
fi

# 3. CPU Information
echo -e "${BLUE}=== CPU Information ===${NC}"
echo ""

test_feature "CPU Model" "lscpu | grep 'Model name' | cut -d':' -f2 | xargs"
test_feature "CPU Cores" "nproc"
test_feature "CPU Frequency Scaling" "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo 'Not available'"
test_feature "Available Governors" "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors 2>/dev/null || echo 'Not available'"

# 4. Memory Information
echo -e "${BLUE}=== Memory Information ===${NC}"
echo ""

test_feature "Total Memory" "free -h | grep Mem | awk '{print \$2}'"
test_feature "Available Memory" "free -h | grep Mem | awk '{print \$7}'"
test_feature "Swap" "free -h | grep Swap | awk '{print \$2}'"
test_feature "Transparent Huge Pages" "cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo 'Not available'"
test_feature "THP Defrag" "cat /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || echo 'Not available'"

# 5. Network Information
echo -e "${BLUE}=== Network Information ===${NC}"
echo ""

INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
test_feature "Primary Interface" "echo $INTERFACE"
test_feature "IP Address" "ip addr show $INTERFACE | grep 'inet ' | awk '{print \$2}' | cut -d'/' -f1"
test_feature "Network Driver" "ethtool -i $INTERFACE 2>/dev/null | grep driver | awk '{print \$2}' || echo 'Unknown'"
test_feature "Driver Version" "ethtool -i $INTERFACE 2>/dev/null | grep version | awk '{print \$2}' || echo 'Unknown'"

# Check network offloads
if command -v ethtool &> /dev/null; then
    echo -e "${YELLOW}Network Offloads:${NC}"
    {
        echo "## Network Offloads"
        ethtool -k "$INTERFACE" 2>/dev/null
        echo ""
    } >> "$OUTPUT_FILE"
    
    gro=$(ethtool -k "$INTERFACE" 2>/dev/null | grep "generic-receive-offload:" | awk '{print $2}')
    tso=$(ethtool -k "$INTERFACE" 2>/dev/null | grep "tcp-segmentation-offload:" | awk '{print $2}')
    gso=$(ethtool -k "$INTERFACE" 2>/dev/null | grep "generic-segmentation-offload:" | awk '{print $2}')
    
    echo -e "  GRO: $gro"
    echo -e "  TSO: $tso"
    echo -e "  GSO: $gso"
    echo ""
fi

# 6. Kernel Parameters
echo -e "${BLUE}=== Kernel Parameters (TCP) ===${NC}"
echo ""

test_feature "BBR Available" "modinfo tcp_bbr 2>/dev/null | grep filename || echo 'Not available'"
test_feature "BBR Loaded" "lsmod | grep tcp_bbr || echo 'Not loaded'"
test_feature "Current Congestion Control" "sysctl -n net.ipv4.tcp_congestion_control"
test_feature "Available Congestion Control" "sysctl -n net.ipv4.tcp_available_congestion_control"

# Test specific parameters
echo -e "${YELLOW}Testing TCP Parameters:${NC}"
PARAMS=(
    "net.ipv4.tcp_low_latency"
    "net.ipv4.tcp_delack_min"
    "net.ipv4.tcp_fastopen"
    "net.ipv4.tcp_sack"
    "net.ipv4.tcp_timestamps"
    "net.ipv4.tcp_window_scaling"
    "net.ipv4.tcp_tw_reuse"
    "net.ipv4.tcp_fin_timeout"
    "net.core.somaxconn"
    "net.core.netdev_max_backlog"
)

for param in "${PARAMS[@]}"; do
    value=$(sysctl -n "$param" 2>/dev/null || echo "NOT_AVAILABLE")
    if [[ "$value" == "NOT_AVAILABLE" ]]; then
        echo -e "  ${RED}✗ $param: Not available${NC}"
    else
        echo -e "  ${GREEN}✓ $param: $value${NC}"
    fi
    echo "$param: $value" >> "$OUTPUT_FILE"
done
echo ""

# 7. File System
echo -e "${BLUE}=== File System ===${NC}"
echo ""

test_feature "Root FS Type" "df -T / | tail -1 | awk '{print \$2}'"
test_feature "Root FS Mount Options" "mount | grep 'on / ' | cut -d'(' -f2 | cut -d')' -f1"

# 8. Init System
echo -e "${BLUE}=== Init System ===${NC}"
echo ""

test_feature "Init System" "ps -p 1 -o comm="
test_feature "Systemd Version" "systemctl --version | head -1 || echo 'Not systemd'"

# 9. Security and Limits
echo -e "${BLUE}=== Security and Limits ===${NC}"
echo ""

test_feature "SELinux Status" "getenforce 2>/dev/null || echo 'Not installed'"
test_feature "AppArmor Status" "aa-status 2>/dev/null | grep 'apparmor module is loaded' || echo 'Not loaded'"
test_feature "Current ulimit (nofile)" "ulimit -n"
test_feature "Hard limit (nofile)" "ulimit -Hn"
test_feature "Soft limit (nofile)" "ulimit -Sn"

# Check limits.conf
echo -e "${YELLOW}Checking /etc/security/limits.conf:${NC}"
if grep -q "nofile" /etc/security/limits.conf; then
    echo -e "  ${GREEN}✓ nofile entries found${NC}"
    grep "nofile" /etc/security/limits.conf | grep -v "^#"
else
    echo -e "  ${RED}✗ No nofile entries found${NC}"
fi
echo ""

# 10. Systemd Service Status
echo -e "${BLUE}=== Systemd Services ===${NC}"
echo ""

if command -v systemctl &> /dev/null; then
    test_feature "systemd-resolved" "systemctl is-active systemd-resolved"
    test_feature "disable-thp service" "systemctl is-enabled disable-thp.service 2>/dev/null || echo 'Not found'"
    test_feature "cpufrequtils" "systemctl is-active cpufrequtils 2>/dev/null || echo 'Not found'"
fi

# 11. Network Scripts
echo -e "${BLUE}=== Network Scripts ===${NC}"
echo ""

test_feature "if-up.d scripts" "ls -la /etc/network/if-up.d/ 2>/dev/null | grep optimize || echo 'Not found'"

if [[ -f /etc/network/if-up.d/optimize-latency ]]; then
    echo -e "${YELLOW}Content of optimize-latency script:${NC}"
    cat /etc/network/if-up.d/optimize-latency
    echo ""
fi

# 12. Hetzner Specific
echo -e "${BLUE}=== Hetzner Detection ===${NC}"
echo ""

test_feature "Hetzner Cloud" "curl -s -m 2 http://169.254.169.254/hetzner/v1/metadata/hostname 2>/dev/null || echo 'Not Hetzner Cloud'"
test_feature "DMI System Manufacturer" "cat /sys/class/dmi/id/sys_vendor 2>/dev/null || echo 'Unknown'"
test_feature "DMI Product Name" "cat /sys/class/dmi/id/product_name 2>/dev/null || echo 'Unknown'"

# 13. Current Optimization Status
echo -e "${BLUE}=== Current Optimization Files ===${NC}"
echo ""

if [[ -f /etc/sysctl.d/99-low-latency-s2s.conf ]]; then
    echo -e "${GREEN}✓ Optimization config exists${NC}"
    echo -e "${YELLOW}Content:${NC}"
    cat /etc/sysctl.d/99-low-latency-s2s.conf
    echo ""
else
    echo -e "${RED}✗ No optimization config found${NC}"
fi

# 14. Kernel Modules
echo -e "${BLUE}=== Loaded Kernel Modules ===${NC}"
echo ""

test_feature "tcp_bbr module" "lsmod | grep tcp_bbr || echo 'Not loaded'"
test_feature "All network modules" "lsmod | grep -E '(tcp|net)' | head -10"

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Diagnostic Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Full report saved to:${NC} $OUTPUT_FILE"
echo ""
echo -e "${YELLOW}Key Findings:${NC}"
echo ""

# Analyze and provide recommendations
VIRT_TYPE=$(systemd-detect-virt 2>/dev/null || echo "unknown")
echo -e "  Virtualization: ${BLUE}$VIRT_TYPE${NC}"

if [[ "$VIRT_TYPE" == "kvm" ]]; then
    echo -e "    ${GREEN}✓ KVM - Full optimization support expected${NC}"
elif [[ "$VIRT_TYPE" == "openvz" ]]; then
    echo -e "    ${YELLOW}⚠ OpenVZ - Limited kernel parameter access${NC}"
else
    echo -e "    ${BLUE}→ $VIRT_TYPE - Check report for capabilities${NC}"
fi

if [[ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    echo -e "  CPU Frequency Scaling: ${GREEN}Available${NC}"
else
    echo -e "  CPU Frequency Scaling: ${YELLOW}Not available (VM limitation)${NC}"
fi

if [[ -f /sys/kernel/mm/transparent_hugepage/enabled ]]; then
    THP_STATUS=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    if [[ "$THP_STATUS" == "never" ]]; then
        echo -e "  Transparent Huge Pages: ${GREEN}Disabled${NC}"
    else
        echo -e "  Transparent Huge Pages: ${RED}Enabled ($THP_STATUS)${NC}"
    fi
fi

FD_LIMIT=$(ulimit -n)
if [[ $FD_LIMIT -ge 65536 ]]; then
    echo -e "  File Descriptors: ${GREEN}$FD_LIMIT${NC}"
else
    echo -e "  File Descriptors: ${RED}$FD_LIMIT (should be 65536)${NC}"
fi

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review the full report: cat $OUTPUT_FILE"
echo "  2. Based on findings, re-run optimization with appropriate profile"
echo "  3. Some settings may require manual intervention (see report)"
echo ""
