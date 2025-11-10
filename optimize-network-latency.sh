#!/bin/bash
#
# Low-Latency Network Optimization Script for Ubuntu/Hetzner VPS
# Optimizes system for real-time audio streaming (OpenAI S2S)
#
# Usage: sudo bash optimize-network-latency.sh [--aggressive|--moderate|--conservative]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROFILE="moderate"  # Default profile
INTERFACE=""        # Auto-detect
BACKUP_DIR="/root/network-optimization-backup-$(date +%Y%m%d-%H%M%S)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --aggressive)
            PROFILE="aggressive"
            shift
            ;;
        --moderate)
            PROFILE="moderate"
            shift
            ;;
        --conservative)
            PROFILE="conservative"
            shift
            ;;
        --interface)
            INTERFACE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: sudo bash $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --aggressive      Maximum performance, minimal buffering (LAN/fast networks)"
            echo "  --moderate        Balanced optimization (default, recommended)"
            echo "  --conservative    Safe optimizations for slower networks"
            echo "  --interface NAME  Specify network interface (auto-detected if omitted)"
            echo "  --help           Show this help message"
            echo ""
            echo "Profiles:"
            echo "  aggressive:    4KB buffers, all offloads disabled"
            echo "  moderate:      16KB buffers, selective offloads (recommended)"
            echo "  conservative:  64KB buffers, minimal changes"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Low-Latency Network Optimization${NC}"
echo -e "${BLUE}Profile: ${YELLOW}${PROFILE}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Backup directory: $BACKUP_DIR"

# Detect network interface if not specified
if [[ -z "$INTERFACE" ]]; then
    INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
    if [[ -z "$INTERFACE" ]]; then
        echo -e "${RED}✗ Could not detect network interface${NC}"
        echo "Please specify with --interface option"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Network interface: $INTERFACE"
echo ""

# Backup existing configurations
echo -e "${YELLOW}Backing up existing configurations...${NC}"
cp /etc/sysctl.conf "$BACKUP_DIR/sysctl.conf.bak" 2>/dev/null || true
cp /etc/security/limits.conf "$BACKUP_DIR/limits.conf.bak" 2>/dev/null || true
cp /etc/systemd/system.conf "$BACKUP_DIR/system.conf.bak" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Configurations backed up"
echo ""

# Set buffer sizes based on profile
case $PROFILE in
    aggressive)
        RMEM_DEFAULT=65536
        WMEM_DEFAULT=65536
        RMEM_MAX=4194304
        WMEM_MAX=4194304
        TCP_RMEM="4096 87380 4194304"
        TCP_WMEM="4096 65536 4194304"
        DISABLE_OFFLOADS=true
        ;;
    moderate)
        RMEM_DEFAULT=262144
        WMEM_DEFAULT=262144
        RMEM_MAX=16777216
        WMEM_MAX=16777216
        TCP_RMEM="4096 87380 16777216"
        TCP_WMEM="4096 65536 16777216"
        DISABLE_OFFLOADS=partial
        ;;
    conservative)
        RMEM_DEFAULT=524288
        WMEM_DEFAULT=524288
        RMEM_MAX=33554432
        WMEM_MAX=33554432
        TCP_RMEM="4096 131072 33554432"
        TCP_WMEM="4096 131072 33554432"
        DISABLE_OFFLOADS=false
        ;;
esac

# Create sysctl configuration
echo -e "${YELLOW}Configuring kernel parameters...${NC}"

cat > /etc/sysctl.d/99-low-latency-s2s.conf << EOF
# Low-Latency Network Optimization for OpenAI S2S
# Profile: ${PROFILE}
# Generated: $(date)
# Backup: ${BACKUP_DIR}

# TCP Low Latency
net.ipv4.tcp_low_latency = 1

# TCP Features
net.ipv4.tcp_sack = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_fastopen = 3

# Reduce TCP delayed ACK for faster acknowledgments
net.ipv4.tcp_delack_min = 1

# Buffer sizes (${PROFILE} profile)
net.core.rmem_default = ${RMEM_DEFAULT}
net.core.wmem_default = ${WMEM_DEFAULT}
net.core.rmem_max = ${RMEM_MAX}
net.core.wmem_max = ${WMEM_MAX}

# TCP buffer auto-tuning
net.ipv4.tcp_rmem = ${TCP_RMEM}
net.ipv4.tcp_wmem = ${TCP_WMEM}

# Connection handling
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 5000

# BBR Congestion Control (if available)
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Additional optimizations
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1
EOF

echo -e "${GREEN}✓${NC} Sysctl configuration created"

# Apply sysctl settings
echo -e "${YELLOW}Applying kernel parameters...${NC}"
sysctl -p /etc/sysctl.d/99-low-latency-s2s.conf
echo -e "${GREEN}✓${NC} Kernel parameters applied"
echo ""

# Enable BBR if available
echo -e "${YELLOW}Configuring BBR congestion control...${NC}"
if modprobe tcp_bbr 2>/dev/null; then
    echo "tcp_bbr" > /etc/modules-load.d/tcp_bbr.conf
    echo -e "${GREEN}✓${NC} BBR enabled"
else
    echo -e "${YELLOW}⚠${NC} BBR not available (kernel too old)"
fi
echo ""

# Network interface optimizations
if [[ "$DISABLE_OFFLOADS" != "false" ]]; then
    echo -e "${YELLOW}Optimizing network interface ${INTERFACE}...${NC}"
    
    # Check if ethtool is installed
    if ! command -v ethtool &> /dev/null; then
        echo -e "${YELLOW}Installing ethtool...${NC}"
        apt-get update -qq
        apt-get install -y ethtool
    fi
    
    # Create interface optimization script
    cat > /etc/network/if-up.d/optimize-latency << 'EOFSCRIPT'
#!/bin/bash
INTERFACE="$IFACE"

if [[ "$INTERFACE" == "INTERFACE_PLACEHOLDER" ]]; then
    # Disable offloads based on profile
    PROFILE_PLACEHOLDER
fi
EOFSCRIPT
    
    # Replace placeholders
    sed -i "s/INTERFACE_PLACEHOLDER/${INTERFACE}/g" /etc/network/if-up.d/optimize-latency
    
    if [[ "$DISABLE_OFFLOADS" == "true" ]]; then
        sed -i 's/PROFILE_PLACEHOLDER/ethtool -K $INTERFACE gro off 2>\/dev\/null || true\n    ethtool -K $INTERFACE tso off 2>\/dev\/null || true\n    ethtool -K $INTERFACE gso off 2>\/dev\/null || true/' /etc/network/if-up.d/optimize-latency
    else
        sed -i 's/PROFILE_PLACEHOLDER/ethtool -K $INTERFACE gro off 2>\/dev\/null || true/' /etc/network/if-up.d/optimize-latency
    fi
    
    chmod +x /etc/network/if-up.d/optimize-latency
    
    # Apply now
    if [[ "$DISABLE_OFFLOADS" == "true" ]]; then
        ethtool -K "$INTERFACE" gro off 2>/dev/null || true
        ethtool -K "$INTERFACE" tso off 2>/dev/null || true
        ethtool -K "$INTERFACE" gso off 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Disabled GRO, TSO, GSO"
    else
        ethtool -K "$INTERFACE" gro off 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Disabled GRO"
    fi
fi
echo ""

# CPU Governor
echo -e "${YELLOW}Configuring CPU governor...${NC}"
if ! command -v cpufreq-set &> /dev/null; then
    apt-get update -qq
    apt-get install -y cpufrequtils
fi

echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils

# Apply to all CPUs
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [[ -f "$cpu" ]]; then
        echo performance > "$cpu" 2>/dev/null || true
    fi
done

if systemctl is-active --quiet cpufrequtils; then
    systemctl restart cpufrequtils
fi

echo -e "${GREEN}✓${NC} CPU governor set to performance"
echo ""

# Disable Transparent Huge Pages
echo -e "${YELLOW}Disabling Transparent Huge Pages...${NC}"
if [[ -f /sys/kernel/mm/transparent_hugepage/enabled ]]; then
    echo never > /sys/kernel/mm/transparent_hugepage/enabled
    echo never > /sys/kernel/mm/transparent_hugepage/defrag
    
    # Make permanent
    cat > /etc/systemd/system/disable-thp.service << 'EOF'
[Unit]
Description=Disable Transparent Huge Pages (THP)
DefaultDependencies=no
After=sysinit.target local-fs.target
Before=basic.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled'
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=basic.target
EOF
    
    systemctl daemon-reload
    systemctl enable disable-thp.service
    echo -e "${GREEN}✓${NC} Transparent Huge Pages disabled"
else
    echo -e "${YELLOW}⚠${NC} THP not available on this system"
fi
echo ""

# File descriptor limits
echo -e "${YELLOW}Increasing file descriptor limits...${NC}"

if ! grep -q "# Low-latency S2S optimization" /etc/security/limits.conf; then
    cat >> /etc/security/limits.conf << 'EOF'

# Low-latency S2S optimization
* soft nofile 65536
* hard nofile 65536
root soft nofile 65536
root hard nofile 65536
EOF
    echo -e "${GREEN}✓${NC} File descriptor limits increased"
else
    echo -e "${YELLOW}⚠${NC} Limits already configured"
fi

# Systemd limits
if ! grep -q "^DefaultLimitNOFILE=" /etc/systemd/system.conf; then
    sed -i 's/^#DefaultLimitNOFILE=.*/DefaultLimitNOFILE=65536/' /etc/systemd/system.conf
    systemctl daemon-reexec
    echo -e "${GREEN}✓${NC} Systemd limits configured"
fi
echo ""

# DNS optimization
echo -e "${YELLOW}Optimizing DNS resolution...${NC}"
if systemctl is-active --quiet systemd-resolved; then
    mkdir -p /etc/systemd/resolved.conf.d
    cat > /etc/systemd/resolved.conf.d/low-latency.conf << 'EOF'
[Resolve]
DNS=1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4
FallbackDNS=9.9.9.9
DNSOverTLS=opportunistic
Cache=yes
DNSStubListener=yes
EOF
    systemctl restart systemd-resolved
    echo -e "${GREEN}✓${NC} DNS optimized (Cloudflare + Google)"
else
    echo -e "${YELLOW}⚠${NC} systemd-resolved not active"
fi
echo ""

# Create verification script
cat > /root/verify-network-optimization.sh << 'EOF'
#!/bin/bash
echo "=== Network Optimization Status ==="
echo ""
echo "BBR Congestion Control:"
sysctl net.ipv4.tcp_congestion_control
echo ""
echo "TCP Low Latency:"
sysctl net.ipv4.tcp_low_latency
echo ""
echo "CPU Governor:"
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "N/A"
echo ""
echo "Transparent Huge Pages:"
cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo "N/A"
echo ""
echo "File Descriptor Limit:"
ulimit -n
echo ""
echo "Network Interface Offloads:"
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
ethtool -k "$INTERFACE" 2>/dev/null | grep -E "(generic-receive-offload|tcp-segmentation-offload|generic-segmentation-offload)" || echo "ethtool not available"
EOF

chmod +x /root/verify-network-optimization.sh

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Optimization Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Profile:${NC} $PROFILE"
echo -e "${YELLOW}Backup:${NC} $BACKUP_DIR"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Reboot for all changes to take effect: ${BLUE}sudo reboot${NC}"
echo "  2. Verify optimizations: ${BLUE}sudo bash /root/verify-network-optimization.sh${NC}"
echo "  3. Test your S2S application"
echo ""
echo -e "${YELLOW}To rollback:${NC}"
echo "  sudo rm /etc/sysctl.d/99-low-latency-s2s.conf"
echo "  sudo cp $BACKUP_DIR/*.bak /etc/"
echo "  sudo sysctl -p"
echo ""
