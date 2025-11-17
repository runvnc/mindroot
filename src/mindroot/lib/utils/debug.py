from colorama import init, Fore, Back, Style
import textwrap
from itertools import cycle
import time
from datetime import datetime
init(autoreset=True)
RAINBOW_COLORS = [(Fore.RED, Back.BLACK), (Fore.YELLOW, Back.BLACK), (Fore.GREEN, Back.BLACK), (Fore.CYAN, Back.BLACK), (Fore.BLUE, Back.BLACK), (Fore.MAGENTA, Back.BLACK)]

def debug_box(text, width=60, add_timestamp=True, style='double'):
    """
    Print debug text in a box with rainbow-colored borders.
    
    Args:
        text (str): The text to display (can be multiline)
        width (int): Maximum width of the box (default: 60)
        add_timestamp (bool): Add timestamp to the box header
        style (str): Box style - 'double' or 'single'
    """
    if style == 'double':
        TOP_LEFT = '╔'
        TOP_RIGHT = '╗'
        BOTTOM_LEFT = '╚'
        BOTTOM_RIGHT = '╝'
        HORIZONTAL = '═'
        VERTICAL = '║'
    else:
        TOP_LEFT = '┌'
        TOP_RIGHT = '┐'
        BOTTOM_LEFT = '└'
        BOTTOM_RIGHT = '┘'
        HORIZONTAL = '─'
        VERTICAL = '│'
    if add_timestamp:
        timestamp = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        text = f'{timestamp}\n{text}'
    lines = []
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=width - 4)
        lines.extend(wrapped if wrapped else [''])
    content_width = max((len(line) for line in lines))
    box_width = content_width + 4
    colors = cycle(RAINBOW_COLORS)
    color, bg = next(colors)
    for line in lines:
        color, bg = next(colors)
        padding = ' ' * (content_width - len(line))
    color, bg = next(colors)

def animated_debug_box(text, width=60, animation_cycles=1):
    """
    Print debug text in a box with animated rainbow borders.
    
    Args:
        text (str): The text to display
        width (int): Maximum width of the box
        animation_cycles (int): Number of color rotation cycles
    """
    for _ in range(animation_cycles):
        for color, bg in RAINBOW_COLORS:
            debug_box(text, width=width, style='single')
            time.sleep(0.1)
    debug_box(text, width=width)
if __name__ == '__main__':
    test_text = "This is a test of the debug box.\nIt can handle multiple lines\nand will wrap them if they are too long for the specified width.\n    \nHere's some more text to demonstrate the rainbow borders!"
    debug_box(test_text, width=50)
    debug_box('Important debug message!', width=40)
    animated_debug_box('Alert: System status critical!', width=40, animation_cycles=2)