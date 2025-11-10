#!/bin/bash
#
# System Capabilities Detection Module
# Probes the system and outputs a JSON-like config of what's available
#
# Usage: source lib/detect-capabilities.sh
#        detect_capabilities
#

# Detect all system capabilities
detect_capabilities() {
    # Initialize detection results
    declare -gA CAPS
    
    # Basic system info
    CAPS[virt_type]=$(systemd-detect-virt 2>/dev/null || echo "unknown")
    CAPS[kernel_version]=$(uname -r)
    CAPS[os_release]=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"')
    CAPS[interface]=$(ip route | grep default | awk '{print $5}' | head -n1)
    
    # CPU frequency scaling
    if [[ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
        CAPS[cpu_freq_scaling]="yes"
        CAPS[available_governors]=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors 2>/dev/null || echo "")
    else
        CAPS[cpu_freq_scaling]="no"
    fi
    
    # Transparent Huge Pages
    if [[ -f /sys/kernel/mm/transparent_hugepage/enabled ]]; then
        CAPS[thp_available]="yes"
        CAPS[thp_current]=$(cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\[.*\]' | tr -d '[]')
    else
        CAPS[thp_available]="no"
    fi
    
    # BBR support
    if modinfo tcp_bbr &>/dev/null; then
        CAPS[bbr_available]="yes"
        CAPS[bbr_loaded]=$(lsmod | grep -q tcp_bbr && echo "yes" || echo "no")
    else
        CAPS[bbr_available]="no"
    fi
    
    # Current congestion control
    CAPS[current_cc]=$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo "unknown")
    CAPS[available_cc]=$(sysctl -n net.ipv4.tcp_available_congestion_control 2>/dev/null || echo "unknown")
    
    # Network driver
    if [[ -n "${CAPS[interface]}" ]] && command -v ethtool &>/dev/null; then
        CAPS[network_driver]=$(ethtool -i "${CAPS[interface]}" 2>/dev/null | grep driver | awk '{print $2}' || echo "unknown")
        CAPS[ethtool_available]="yes"
    else
        CAPS[ethtool_available]="no"
    fi
    
    # Test TCP parameters availability
    local tcp_params=(
        "net.ipv4.tcp_low_latency"
        "net.ipv4.tcp_delack_min"
        "net.ipv4.tcp_fastopen"
        "net.ipv4.tcp_sack"
        "net.ipv4.tcp_timestamps"
    )
    
    CAPS[tcp_params_available]=""
    for param in "${tcp_params[@]}"; do
        if sysctl -n "$param" &>/dev/null; then
            CAPS[tcp_params_available]+="$param "
        fi
    done
    
    # Init system
    CAPS[init_system]=$(ps -p 1 -o comm= 2>/dev/null || echo "unknown")
    
    # File descriptor limits
    CAPS[fd_soft_limit]=$(ulimit -Sn)
    CAPS[fd_hard_limit]=$(ulimit -Hn)
    
    # Check if limits.conf exists and is writable
    if [[ -w /etc/security/limits.conf ]]; then
        CAPS[limits_conf_writable]="yes"
    else
        CAPS[limits_conf_writable]="no"
    fi
    
    # Systemd availability
    if command -v systemctl &>/dev/null; then
        CAPS[systemd_available]="yes"
    else
        CAPS[systemd_available]="no"
    fi
    
    # Network interface capabilities
    if [[ "${CAPS[ethtool_available]}" == "yes" ]] && [[ -n "${CAPS[interface]}" ]]; then
        local gro=$(ethtool -k "${CAPS[interface]}" 2>/dev/null | grep "generic-receive-offload:" | awk '{print $2}')
        local tso=$(ethtool -k "${CAPS[interface]}" 2>/dev/null | grep "tcp-segmentation-offload:" | awk '{print $2}')
        local gso=$(ethtool -k "${CAPS[interface]}" 2>/dev/null | grep "generic-segmentation-offload:" | awk '{print $2}')
        
        CAPS[gro_current]="$gro"
        CAPS[tso_current]="$tso"
        CAPS[gso_current]="$gso"
        
        # Test if we can change them
        if ethtool -K "${CAPS[interface]}" gro off &>/dev/null; then
            CAPS[offloads_changeable]="yes"
            ethtool -K "${CAPS[interface]}" gro "$gro" &>/dev/null  # Restore
        else
            CAPS[offloads_changeable]="no"
        fi
    fi
    
    # Detect Hetzner
    if curl -s -m 2 http://169.254.169.254/hetzner/v1/metadata/hostname &>/dev/null; then
        CAPS[is_hetzner]="yes"
    else
        CAPS[is_hetzner]="no"
    fi
}

# Print capabilities in human-readable format
print_capabilities() {
    echo "System Capabilities Detection Results:"
    echo "======================================"
    echo ""
    echo "System:"
    echo "  Virtualization: ${CAPS[virt_type]}"
    echo "  Kernel: ${CAPS[kernel_version]}"
    echo "  OS: ${CAPS[os_release]}"
    echo "  Init: ${CAPS[init_system]}"
    echo "  Hetzner: ${CAPS[is_hetzner]}"
    echo ""
    echo "Network:"
    echo "  Interface: ${CAPS[interface]}"
    echo "  Driver: ${CAPS[network_driver]}"
    echo "  Ethtool: ${CAPS[ethtool_available]}"
    echo "  Offloads changeable: ${CAPS[offloads_changeable]}"
    echo ""
    echo "CPU:"
    echo "  Frequency scaling: ${CAPS[cpu_freq_scaling]}"
    [[ "${CAPS[cpu_freq_scaling]}" == "yes" ]] && echo "  Available governors: ${CAPS[available_governors]}"
    echo ""
    echo "Memory:"
    echo "  THP available: ${CAPS[thp_available]}"
    [[ "${CAPS[thp_available]}" == "yes" ]] && echo "  THP current: ${CAPS[thp_current]}"
    echo ""
    echo "TCP:"
    echo "  BBR available: ${CAPS[bbr_available]}"
    echo "  Current CC: ${CAPS[current_cc]}"
    echo "  Available CC: ${CAPS[available_cc]}"
    echo "  Supported params: ${CAPS[tcp_params_available]}"
    echo ""
    echo "Limits:"
    echo "  FD soft: ${CAPS[fd_soft_limit]}"
    echo "  FD hard: ${CAPS[fd_hard_limit]}"
    echo "  limits.conf writable: ${CAPS[limits_conf_writable]}"
    echo ""
}

# Export capabilities to a file
export_capabilities() {
    local output_file="$1"
    {
        for key in "${!CAPS[@]}"; do
            echo "$key=${CAPS[$key]}"
        done
    } > "$output_file"
}

# Load capabilities from a file
load_capabilities() {
    local input_file="$1"
    if [[ -f "$input_file" ]]; then
        while IFS='=' read -r key value; do
            CAPS[$key]="$value"
        done < "$input_file"
        return 0
    else
        return 1
    fi
}
