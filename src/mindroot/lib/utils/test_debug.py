from debug import debug_box, animated_debug_box

print('\n1. Basic debug box with timestamp:')
debug_box("Simple test message")

print('\n2. Debug box with multiple lines and single-line style:')
debug_box("""
System Status Report:
-------------------
CPU Usage: 45%
Memory: 2.1GB
Disk Space: 80% full
Network: Connected
""", style='single')

print('\n3. Animated debug box (watch the colors change):')
animated_debug_box("⚠️ Critical Alert!\nImmediate attention required", width=40, animation_cycles=2)

print('\n4. Wide debug box with detailed information:')
debug_box("""
Detailed Debug Information
=========================
This is a comprehensive debug message that demonstrates
how the box handles longer lines of text and automatically
wraps them to maintain the specified width while keeping
the rainbow-colored borders intact.
""", width=70)
