#!/bin/bash
#
# Configuration Generator Module
# Generates optimization config based on detected capabilities and profile
#
# Usage: source lib/generate-config.sh
#        generate_config <profile>
#

# Generate sysctl configuration
generate_sysctl_config() {
    local profile="$1"
    local output_file="$2"
    
    # Set buffer sizes based on profile
    case $profile in
        aggressive)
            local rmem_default=65536
            local wmem_default=65536
            local rmem_max=4194304
            local wmem_max=4194304
            local tcp_rmem="4096 87380 4194304"
            local tcp_wmem="4096 65536 4194304"
            ;;
        moderate)
            local rmem_default=262144
            local wmem_default=262144
            local rmem_max=16777216
            local wmem_max=16777216
            local tcp_rmem="4096 87380 16777216"
            local tcp_wmem="4096 65536 16777216"
            ;;
        conservative)
            local rmem_default=524288
            local wmem_default=524288
            local rmem_max=33554432
            local wmem_max=33554432
            local tcp_rmem="4096 131072 33554432"
            local tcp_wmem="4096 131072 33554432"
            ;;
    esac
    
    # Start config file
    cat > "$output_file" << EOF
# Low-Latency Network Optimization for OpenAI S2S
# Profile: ${profile}
# Generated: $(date)
# Virtualization: ${CAPS[virt_type]}
# Kernel: ${CAPS[kernel_version]}

EOF
    
    # Add TCP parameters that are available
    if [[ "${CAPS[tcp_params_available]}" == *"net.ipv4.tcp_low_latency"* ]]; then
        echo "net.ipv4.tcp_low_latency = 1" >> "$output_file"
    fi
    
    # Standard TCP features
    cat >> "$output_file" << EOF
net.ipv4.tcp_sack = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_window_scaling = 1
EOF
    
    if [[ "${CAPS[tcp_params_available]}" == *"net.ipv4.tcp_fastopen"* ]]; then
        echo "net.ipv4.tcp_fastopen = 3" >> "$output_file"
    fi
    
    # Buffer sizes
    cat >> "$output_file" << EOF

# Buffer sizes (${profile} profile)
net.core.rmem_default = ${rmem_default}
net.core.wmem_default = ${wmem_default}
net.core.rmem_max = ${rmem_max}
net.core.wmem_max = ${wmem_max}
net.ipv4.tcp_rmem = ${tcp_rmem}
net.ipv4.tcp_wmem = ${tcp_wmem}

# Connection handling
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 5000
EOF
    
    # BBR if available
    if [[ "${CAPS[bbr_available]}" == "yes" ]]; then
        cat >> "$output_file" << EOF

# BBR Congestion Control
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
    fi
    
    # Additional optimizations
    cat >> "$output_file" << EOF

# Additional optimizations
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1
EOF
}

# Generate systemd service for THP
generate_thp_service() {
    local output_file="$1"
    
    cat > "$output_file" << 'EOF'
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
}

# Generate network offload disable service
generate_network_offload_service() {
    local interface="$1"
    local output_file="$2"
    
    cat > "$output_file" << EOF
[Unit]
Description=Disable Network Offloads for Low Latency
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ethtool -K ${interface} gro off
ExecStart=/usr/sbin/ethtool -K ${interface} tso off
ExecStart=/usr/sbin/ethtool -K ${interface} gso off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
}

# Generate if-up.d script for network offloads
generate_ifup_script() {
    local interface="$1"
    local output_file="$2"
    
    cat > "$output_file" << EOF
#!/bin/bash
# Disable network offloads for low latency

if [[ "\$IFACE" == "${interface}" ]]; then
    ethtool -K "${interface}" gro off 2>/dev/null || true
    ethtool -K "${interface}" tso off 2>/dev/null || true
    ethtool -K "${interface}" gso off 2>/dev/null || true
    logger "Low-latency network offloads disabled on ${interface}"
fi
EOF
    chmod +x "$output_file"
}

# Generate limits.conf entries
generate_limits_config() {
    cat << 'EOF'

# Low-latency S2S optimization
* soft nofile 65536
* hard nofile 65536
root soft nofile 65536
root hard nofile 65536
EOF
}

# Generate complete configuration plan
generate_config_plan() {
    local profile="$1"
    local plan_file="$2"
    
    {
        echo "Configuration Plan"
        echo "=================="
        echo "Profile: $profile"
        echo "Generated: $(date)"
        echo ""
        echo "Actions to be performed:"
        echo ""
        
        # Sysctl
        echo "1. Sysctl Configuration:"
        echo "   - File: /etc/sysctl.d/99-low-latency-s2s.conf"
        echo "   - BBR: ${CAPS[bbr_available]}"
        echo "   - TCP low latency: $(echo ${CAPS[tcp_params_available]} | grep -q tcp_low_latency && echo 'yes' || echo 'no')"
        echo ""
        
        # THP
        if [[ "${CAPS[thp_available]}" == "yes" ]]; then
            echo "2. Transparent Huge Pages:"
            echo "   - Current: ${CAPS[thp_current]}"
            echo "   - Target: never"
            echo "   - Method: systemd service"
            echo ""
        fi
        
        # Network offloads
        if [[ "${CAPS[offloads_changeable]}" == "yes" ]]; then
            echo "3. Network Offloads:"
            echo "   - Interface: ${CAPS[interface]}"
            echo "   - GRO: ${CAPS[gro_current]} -> off"
            echo "   - TSO: ${CAPS[tso_current]} -> off"
            echo "   - GSO: ${CAPS[gso_current]} -> off"
            echo "   - Method: systemd service + if-up.d script"
            echo ""
        fi
        
        # CPU governor
        if [[ "${CAPS[cpu_freq_scaling]}" == "yes" ]]; then
            echo "4. CPU Governor:"
            echo "   - Target: performance"
            echo "   - Method: cpufrequtils"
            echo ""
        fi
        
        # File descriptors
        echo "5. File Descriptors:"
        echo "   - Current soft: ${CAPS[fd_soft_limit]}"
        echo "   - Target: 65536"
        echo "   - Method: limits.conf + systemd"
        echo ""
        
        # DNS
        if [[ "${CAPS[systemd_available]}" == "yes" ]]; then
            echo "6. DNS Optimization:"
            echo "   - Method: systemd-resolved"
            echo "   - Servers: Cloudflare + Google"
            echo ""
        fi
        
    } > "$plan_file"
}
