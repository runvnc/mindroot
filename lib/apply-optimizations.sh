#!/bin/bash
#
# Apply Optimizations Module
# Applies the generated configuration to the system
#
# Usage: source lib/apply-optimizations.sh
#        apply_all_optimizations <profile> <backup_dir>
#

# Apply sysctl configuration
apply_sysctl() {
    local config_file="$1"
    
    echo -e "${YELLOW}Applying sysctl configuration...${NC}"
    
    if [[ -f "$config_file" ]]; then
        cp "$config_file" /etc/sysctl.d/99-low-latency-s2s.conf
        sysctl -p /etc/sysctl.d/99-low-latency-s2s.conf 2>&1 | grep -v "cannot stat" || true
        echo -e "${GREEN}✓${NC} Sysctl configuration applied"
        return 0
    else
        echo -e "${RED}✗${NC} Config file not found: $config_file"
        return 1
    fi
}

# Enable BBR
apply_bbr() {
    if [[ "${CAPS[bbr_available]}" == "yes" ]]; then
        echo -e "${YELLOW}Enabling BBR congestion control...${NC}"
        
        modprobe tcp_bbr 2>/dev/null || true
        
        if ! grep -q "tcp_bbr" /etc/modules-load.d/modules.conf 2>/dev/null; then
            echo "tcp_bbr" >> /etc/modules-load.d/modules.conf
        fi
        
        if lsmod | grep -q tcp_bbr; then
            echo -e "${GREEN}✓${NC} BBR enabled"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} BBR module not loaded (may require reboot)"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} BBR not available on this kernel"
        return 1
    fi
}

# Disable Transparent Huge Pages
apply_thp_disable() {
    if [[ "${CAPS[thp_available]}" != "yes" ]]; then
        echo -e "${YELLOW}⚠${NC} THP not available"
        return 1
    fi
    
    echo -e "${YELLOW}Disabling Transparent Huge Pages...${NC}"
    
    # Disable immediately
    echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
    echo never > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true
    
    # Create systemd service
    local service_file="/tmp/disable-thp.service"
    generate_thp_service "$service_file"
    cp "$service_file" /etc/systemd/system/disable-thp.service
    
    systemctl daemon-reload
    systemctl enable disable-thp.service 2>/dev/null || true
    systemctl start disable-thp.service 2>/dev/null || true
    
    # Verify
    local current=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    if [[ "$current" == "never" ]]; then
        echo -e "${GREEN}✓${NC} THP disabled"
        return 0
    else
        echo -e "${RED}✗${NC} THP still enabled: $current"
        return 1
    fi
}

# Disable network offloads
apply_network_offloads() {
    if [[ "${CAPS[offloads_changeable]}" != "yes" ]]; then
        echo -e "${YELLOW}⚠${NC} Network offloads cannot be changed"
        return 1
    fi
    
    local interface="${CAPS[interface]}"
    echo -e "${YELLOW}Disabling network offloads on $interface...${NC}"
    
    # Disable immediately
    ethtool -K "$interface" gro off 2>/dev/null && echo -e "  ${GREEN}✓${NC} GRO disabled" || echo -e "  ${YELLOW}⚠${NC} GRO: failed"
    ethtool -K "$interface" tso off 2>/dev/null && echo -e "  ${GREEN}✓${NC} TSO disabled" || echo -e "  ${YELLOW}⚠${NC} TSO: failed"
    ethtool -K "$interface" gso off 2>/dev/null && echo -e "  ${GREEN}✓${NC} GSO disabled" || echo -e "  ${YELLOW}⚠${NC} GSO: failed"
    
    # Create systemd service
    local service_file="/tmp/disable-network-offloads.service"
    generate_network_offload_service "$interface" "$service_file"
    cp "$service_file" /etc/systemd/system/disable-network-offloads.service
    
    systemctl daemon-reload
    systemctl enable disable-network-offloads.service 2>/dev/null || true
    systemctl start disable-network-offloads.service 2>/dev/null || true
    
    # Create if-up.d script
    if [[ -d /etc/network/if-up.d ]]; then
        generate_ifup_script "$interface" "/etc/network/if-up.d/optimize-latency"
        echo -e "  ${GREEN}✓${NC} if-up.d script created"
    fi
    
    echo -e "${GREEN}✓${NC} Network offloads configuration complete"
    return 0
}

# Configure CPU governor
apply_cpu_governor() {
    if [[ "${CAPS[cpu_freq_scaling]}" != "yes" ]]; then
        echo -e "${YELLOW}⚠${NC} CPU frequency scaling not available"
        return 1
    fi
    
    echo -e "${YELLOW}Setting CPU governor to performance...${NC}"
    
    # Install cpufrequtils if needed
    if ! command -v cpufreq-set &>/dev/null; then
        apt-get update -qq
        apt-get install -y cpufrequtils >/dev/null 2>&1
    fi
    
    # Set governor
    echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils
    
    # Apply to all CPUs
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        if [[ -f "$cpu" ]]; then
            echo performance > "$cpu" 2>/dev/null || true
        fi
    done
    
    if systemctl is-active --quiet cpufrequtils 2>/dev/null; then
        systemctl restart cpufrequtils
    fi
    
    echo -e "${GREEN}✓${NC} CPU governor set to performance"
    return 0
}

# Configure file descriptor limits
apply_fd_limits() {
    echo -e "${YELLOW}Configuring file descriptor limits...${NC}"
    
    # Update limits.conf
    if ! grep -q "# Low-latency S2S optimization" /etc/security/limits.conf; then
        generate_limits_config >> /etc/security/limits.conf
        echo -e "  ${GREEN}✓${NC} limits.conf updated"
    else
        echo -e "  ${GREEN}✓${NC} limits.conf already configured"
    fi
    
    # Update systemd system.conf
    if ! grep -q "^DefaultLimitNOFILE=65536" /etc/systemd/system.conf; then
        sed -i 's/^#\?DefaultLimitNOFILE=.*/DefaultLimitNOFILE=65536/' /etc/systemd/system.conf
        echo -e "  ${GREEN}✓${NC} systemd system.conf updated"
    fi
    
    # Update systemd user.conf
    if ! grep -q "^DefaultLimitNOFILE=65536" /etc/systemd/user.conf; then
        sed -i 's/^#\?DefaultLimitNOFILE=.*/DefaultLimitNOFILE=65536/' /etc/systemd/user.conf
        echo -e "  ${GREEN}✓${NC} systemd user.conf updated"
    fi
    
    systemctl daemon-reexec 2>/dev/null || true
    
    # Set for current session
    ulimit -n 65536 2>/dev/null || true
    
    echo -e "${GREEN}✓${NC} File descriptor limits configured"
    echo -e "  ${YELLOW}Note: New login sessions will have 65536 FD limit${NC}"
    return 0
}

# Configure DNS
apply_dns_optimization() {
    if [[ "${CAPS[systemd_available]}" != "yes" ]]; then
        echo -e "${YELLOW}⚠${NC} systemd not available"
        return 1
    fi
    
    if ! systemctl is-active --quiet systemd-resolved 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC} systemd-resolved not active"
        return 1
    fi
    
    echo -e "${YELLOW}Optimizing DNS resolution...${NC}"
    
    mkdir -p /etc/systemd/resolved.conf.d
    cat > /etc/systemd/resolved.conf.d/low-latency.conf << 'EOF'
[Resolve]
DNS=1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4
FallbackDNS=9.9.9.9
DNSOverTLS=opportunistic
Cache=yes
DNSStubListener=yes
EOF
    
    systemctl restart systemd-resolved 2>/dev/null || true
    
    echo -e "${GREEN}✓${NC} DNS optimized (Cloudflare + Google)"
    return 0
}

# Apply all optimizations
apply_all_optimizations() {
    local profile="$1"
    local backup_dir="$2"
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Applying Optimizations${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Backup existing configs
    echo -e "${YELLOW}Backing up existing configurations...${NC}"
    cp /etc/sysctl.conf "$backup_dir/sysctl.conf.bak" 2>/dev/null || true
    cp /etc/security/limits.conf "$backup_dir/limits.conf.bak" 2>/dev/null || true
    cp /etc/systemd/system.conf "$backup_dir/system.conf.bak" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Backups created in $backup_dir"
    echo ""
    
    # Generate configurations
    local sysctl_config="/tmp/99-low-latency-s2s.conf"
    generate_sysctl_config "$profile" "$sysctl_config"
    
    # Apply each optimization
    local success_count=0
    local total_count=0
    
    ((total_count++)); apply_sysctl "$sysctl_config" && ((success_count++))
    ((total_count++)); apply_bbr && ((success_count++))
    ((total_count++)); apply_thp_disable && ((success_count++))
    ((total_count++)); apply_network_offloads && ((success_count++))
    ((total_count++)); apply_cpu_governor && ((success_count++))
    ((total_count++)); apply_fd_limits && ((success_count++))
    ((total_count++)); apply_dns_optimization && ((success_count++))
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Optimization Complete!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Applied: ${GREEN}$success_count${NC}/$total_count optimizations"
    echo ""
    
    return 0
}
