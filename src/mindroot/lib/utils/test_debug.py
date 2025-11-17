from debug import debug_box, animated_debug_box
debug_box('Simple test message')
debug_box('\nSystem Status Report:\n-------------------\nCPU Usage: 45%\nMemory: 2.1GB\nDisk Space: 80% full\nNetwork: Connected\n', style='single')
animated_debug_box('⚠️ Critical Alert!\nImmediate attention required', width=40, animation_cycles=2)
debug_box('\nDetailed Debug Information\n=========================\nThis is a comprehensive debug message that demonstrates\nhow the box handles longer lines of text and automatically\nwraps them to maintain the specified width while keeping\nthe rainbow-colored borders intact.\n', width=70)