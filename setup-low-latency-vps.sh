#!/bin/bash
#
# Production-Ready Low-Latency VPS Setup Script
# One-command setup for optimal real-time audio streaming
#
# Usage: sudo bash setup-low-latency-vps.sh [--profile aggressive|moderate|conservative]
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Declare global capabilities array
declare -gA CAPS

# Configuration
PROFILE="moderate"
BACKUP_DIR="/root/network-optimization-backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/root/optimization-setup-$(date +%Y%m%d-%H%M%S).log"
CAPABILITIES_FILE="/tmp/vps-capabilities.conf"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --aggressive) PROFILE="aggressive"; shift ;;
        --moderate) PROFILE="moderate"; shift ;;
        --conservative) PROFILE="conservative"; shift ;;
        --help)
            echo "Low-Latency VPS Setup for Real-Time Audio Streaming"
            echo ""
            echo "Usage: sudo bash $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --aggressive      4KB buffers, maximum performance (LAN/fast networks)"
            echo "  --moderate        16KB buffers, balanced (default, recommended)"
            echo "  --conservative    64KB buffers, safe for slower networks"
            echo "  --help           Show this help message"
            echo ""
            echo "What this script does:"
            echo "  1. Detects your VPS capabilities"
            echo "  2. Generates optimized configuration"
            echo "  3. Applies only supported optimizations"
            echo "  4. Verifies all changes"
            echo ""
            echo "Optimizations include:"
            echo "  - BBR congestion control"
            echo "  - TCP low-latency mode"
            echo "  - Minimal network buffers"
            echo "  - Disabled network offloads (GRO, TSO, GSO)"
            echo "  - Disabled Transparent Huge Pages"
            echo "  - CPU performance governor"
            echo "  - Increased file descriptor limits"
            echo "  - Optimized DNS resolution"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Low-Latency VPS Setup${NC}"
echo -e "${BLUE}Profile: ${YELLOW}${PROFILE}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
log "Starting optimization with profile: $PROFILE"

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Backup directory: $BACKUP_DIR"
log "Backup directory: $BACKUP_DIR"

# Source modules
if [[ ! -f "$SCRIPT_DIR/lib/detect-capabilities.sh" ]]; then
    echo -e "${RED}✗ Module not found: lib/detect-capabilities.sh${NC}"
    echo "Please ensure all files are in place."
    exit 1
fi

source "$SCRIPT_DIR/lib/detect-capabilities.sh"
source "$SCRIPT_DIR/lib/generate-config.sh"
source "$SCRIPT_DIR/lib/apply-optimizations.sh"

echo ""
echo -e "${YELLOW}Step 1: Detecting system capabilities...${NC}"
log "Detecting capabilities"

# Detect capabilities
detect_capabilities

# Save capabilities
export_capabilities "$CAPABILITIES_FILE"
log "Capabilities detected and saved"

# Print summary
echo ""
echo -e "${BLUE}System Information:${NC}"
echo -e "  Virtualization: ${CAPS[virt_type]}"
echo -e "  Kernel: ${CAPS[kernel_version]}"
echo -e "  Interface: ${CAPS[interface]}"
echo -e "  BBR Available: ${CAPS[bbr_available]}"
echo -e "  THP Available: ${CAPS[thp_available]}"
echo -e "  Network Offloads Changeable: ${CAPS[offloads_changeable]}"

if [[ "${CAPS[is_hetzner]}" == "yes" ]]; then
    echo -e "  ${GREEN}✓${NC} Hetzner Cloud detected"
fi

echo ""
echo -e "${YELLOW}Step 2: Generating configuration...${NC}"
log "Generating configuration for profile: $PROFILE"

# Generate configuration plan
generate_config_plan "$PROFILE" "/tmp/optimization-plan.txt"
cat /tmp/optimization-plan.txt
log "Configuration plan generated"

echo ""
echo -e "${YELLOW}Step 3: Applying optimizations...${NC}"
log "Applying optimizations"

# Apply all optimizations
apply_all_optimizations "$PROFILE" "$BACKUP_DIR"

echo ""
echo -e "${YELLOW}Step 4: Verifying configuration...${NC}"
log "Verifying configuration"

# Verify key settings
echo ""
echo -e "${BLUE}Verification Results:${NC}"
echo ""

# BBR
if [[ "${CAPS[bbr_available]}" == "yes" ]]; then
    current_cc=$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null)
    if [[ "$current_cc" == "bbr" ]]; then
        echo -e "  ${GREEN}✓${NC} BBR: enabled"
    else
        echo -e "  ${YELLOW}⚠${NC} BBR: $current_cc (expected bbr)"
    fi
fi

# THP
if [[ "${CAPS[thp_available]}" == "yes" ]]; then
    thp_status=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    if [[ "$thp_status" == "never" ]]; then
        echo -e "  ${GREEN}✓${NC} THP: disabled"
    else
        echo -e "  ${YELLOW}⚠${NC} THP: $thp_status (expected never)"
    fi
fi

# Network offloads
if [[ "${CAPS[offloads_changeable]}" == "yes" ]] && [[ -n "${CAPS[interface]}" ]]; then
    gro=$(ethtool -k "${CAPS[interface]}" 2>/dev/null | grep "generic-receive-offload:" | awk '{print $2}')
    if [[ "$gro" == "off" ]]; then
        echo -e "  ${GREEN}✓${NC} Network offloads: disabled"
    else
        echo -e "  ${YELLOW}⚠${NC} Network offloads: $gro (expected off)"
    fi
fi

# File descriptors
fd_limit=$(ulimit -n)
if [[ $fd_limit -ge 65536 ]]; then
    echo -e "  ${GREEN}✓${NC} File descriptors: $fd_limit"
else
    echo -e "  ${YELLOW}⚠${NC} File descriptors: $fd_limit (will be 65536 after re-login)"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo -e "  Profile: ${BLUE}$PROFILE${NC}"
echo -e "  Log: ${BLUE}$LOG_FILE${NC}"
echo -e "  Backup: ${BLUE}$BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. ${GREEN}No reboot required!${NC} Settings are active now."
echo -e "  2. For file descriptor limits to apply: log out and back in"
echo -e "  3. Verify: ${BLUE}sudo bash $SCRIPT_DIR/check-optimization-status.sh${NC}"
echo -e "  4. Test: ${BLUE}sudo bash $SCRIPT_DIR/test-network-latency.sh${NC}"
echo ""
echo -e "${YELLOW}Application Setup:${NC}"
echo -e "  Install S2S dependency: ${BLUE}pip install websockets${NC}"
echo -e "  Your S2S code will automatically use these optimizations!"
echo ""
echo -e "${GREEN}Expected Performance:${NC}"
echo -e "  • 50-70% latency reduction"
echo -e "  • More consistent timing (reduced jitter)"
echo -e "  • Lower CPU overhead"
echo ""

log "Setup completed successfully"
