#!/bin/bash
#
# Fix specific optimization issues found by diagnostic
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fixing Optimization Issues${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Fix 1: Remove tcp_delack_min from config
echo -e "${YELLOW}Fix 1: Removing unsupported tcp_delack_min parameter...${NC}"
if grep -q "tcp_delack_min" /etc/sysctl.d/99-low-latency-s2s.conf 2>/dev/null; then
    sed -i '/tcp_delack_min/d' /etc/sysctl.d/99-low-latency-s2s.conf
    sysctl -p /etc/sysctl.d/99-low-latency-s2s.conf >/dev/null 2>&1
    echo -e "${GREEN}✓${NC} Removed tcp_delack_min"
else
    echo -e "${GREEN}✓${NC} Already removed"
fi
echo ""

# Fix 2: Force disable THP
echo -e "${YELLOW}Fix 2: Disabling Transparent Huge Pages...${NC}"
if [[ -f /sys/kernel/mm/transparent_hugepage/enabled ]]; then
    echo never > /sys/kernel/mm/transparent_hugepage/enabled
    echo never > /sys/kernel/mm/transparent_hugepage/defrag
    
    # Verify
    current=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    if [[ "$current" == "never" ]]; then
        echo -e "${GREEN}✓${NC} THP disabled (current: $current)"
    else
        echo -e "${RED}✗${NC} THP still enabled: $current"
    fi
    
    # Ensure systemd service exists and is enabled
    if [[ ! -f /etc/systemd/system/disable-thp.service ]]; then
        echo -e "${YELLOW}Creating systemd service for THP...${NC}"
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
        systemctl start disable-thp.service
        echo -e "${GREEN}✓${NC} Systemd service created and enabled"
    else
        systemctl enable disable-thp.service 2>/dev/null || true
        systemctl restart disable-thp.service
        echo -e "${GREEN}✓${NC} Systemd service restarted"
    fi
else
    echo -e "${YELLOW}⚠${NC} THP not available on this system"
fi
echo ""

# Fix 3: Set file descriptor limits for current session
echo -e "${YELLOW}Fix 3: Setting file descriptor limits...${NC}"

# For current session
ulimit -n 65536 2>/dev/null || true
echo -e "${GREEN}✓${NC} Current session limit set to $(ulimit -n)"

# Verify limits.conf
if grep -q "^\* soft nofile 65536" /etc/security/limits.conf && \
   grep -q "^\* hard nofile 65536" /etc/security/limits.conf; then
    echo -e "${GREEN}✓${NC} limits.conf already configured"
else
    echo -e "${YELLOW}Updating limits.conf...${NC}"
    # Remove old entries
    sed -i '/# Low-latency S2S optimization/,+4d' /etc/security/limits.conf
    # Add new entries
    cat >> /etc/security/limits.conf << 'EOF'

# Low-latency S2S optimization
* soft nofile 65536
* hard nofile 65536
root soft nofile 65536
root hard nofile 65536
EOF
    echo -e "${GREEN}✓${NC} limits.conf updated"
fi

# Update systemd limits
if ! grep -q "^DefaultLimitNOFILE=65536" /etc/systemd/system.conf; then
    sed -i 's/^#\?DefaultLimitNOFILE=.*/DefaultLimitNOFILE=65536/' /etc/systemd/system.conf
    systemctl daemon-reexec
    echo -e "${GREEN}✓${NC} Systemd limits updated"
else
    echo -e "${GREEN}✓${NC} Systemd limits already configured"
fi

# Also set in systemd user config
if ! grep -q "^DefaultLimitNOFILE=65536" /etc/systemd/user.conf; then
    sed -i 's/^#\?DefaultLimitNOFILE=.*/DefaultLimitNOFILE=65536/' /etc/systemd/user.conf
    echo -e "${GREEN}✓${NC} Systemd user limits updated"
fi

echo -e "${YELLOW}Note: New login sessions will have 65536 file descriptors${NC}"
echo ""

# Fix 4: Disable network offloads
echo -e "${YELLOW}Fix 4: Disabling network offloads...${NC}"

INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)

if [[ -z "$INTERFACE" ]]; then
    echo -e "${RED}✗${NC} Could not detect network interface"
else
    echo -e "Interface: $INTERFACE"
    
    # Disable offloads
    ethtool -K "$INTERFACE" gro off 2>/dev/null && echo -e "  ${GREEN}✓${NC} GRO disabled" || echo -e "  ${YELLOW}⚠${NC} GRO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'generic-receive-offload:' | awk '{print $2}')"
    ethtool -K "$INTERFACE" tso off 2>/dev/null && echo -e "  ${GREEN}✓${NC} TSO disabled" || echo -e "  ${YELLOW}⚠${NC} TSO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'tcp-segmentation-offload:' | awk '{print $2}')"
    ethtool -K "$INTERFACE" gso off 2>/dev/null && echo -e "  ${GREEN}✓${NC} GSO disabled" || echo -e "  ${YELLOW}⚠${NC} GSO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'generic-segmentation-offload:' | awk '{print $2}')"
    
    # Create if-up.d script
    echo -e "${YELLOW}Creating persistent network optimization script...${NC}"
    cat > /etc/network/if-up.d/optimize-latency << EOFSCRIPT
#!/bin/bash
# Disable network offloads for low latency

if [[ "\$IFACE" == "$INTERFACE" ]]; then
    ethtool -K "$INTERFACE" gro off 2>/dev/null || true
    ethtool -K "$INTERFACE" tso off 2>/dev/null || true
    ethtool -K "$INTERFACE" gso off 2>/dev/null || true
    logger "Low-latency network offloads disabled on $INTERFACE"
fi
EOFSCRIPT
    
    chmod +x /etc/network/if-up.d/optimize-latency
    echo -e "${GREEN}✓${NC} Persistent script created"
    
    # Also create a systemd service as backup
    cat > /etc/systemd/system/disable-network-offloads.service << EOFSERVICE
[Unit]
Description=Disable Network Offloads for Low Latency
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ethtool -K $INTERFACE gro off
ExecStart=/usr/sbin/ethtool -K $INTERFACE tso off
ExecStart=/usr/sbin/ethtool -K $INTERFACE gso off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOFSERVICE
    
    systemctl daemon-reload
    systemctl enable disable-network-offloads.service
    systemctl start disable-network-offloads.service
    echo -e "${GREEN}✓${NC} Systemd service created and enabled"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Fixes Applied!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Verification:${NC}"
echo ""

# Verify each fix
echo -e "1. THP Status: $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null | grep -o '\[.*\]' | tr -d '[]')"
echo -e "2. File Descriptors (current session): $(ulimit -n)"
echo -e "3. Network Offloads:"
echo -e "   GRO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'generic-receive-offload:' | awk '{print $2}')"
echo -e "   TSO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'tcp-segmentation-offload:' | awk '{print $2}')"
echo -e "   GSO: $(ethtool -k $INTERFACE 2>/dev/null | grep 'generic-segmentation-offload:' | awk '{print $2}')"
echo -e "4. BBR: $(sysctl -n net.ipv4.tcp_congestion_control)"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  • File descriptor limits apply to NEW login sessions"
echo -e "  • Current session has been updated to 65536"
echo -e "  • Network offloads will persist across reboots"
echo -e "  • Run check-optimization-status.sh to verify all settings"
echo ""
echo -e "${GREEN}No reboot required!${NC} Settings are active now."
echo ""
