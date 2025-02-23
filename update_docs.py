#!/usr/bin/env python3

import json
import os

def read_file(fname):
    with open(fname, 'r') as f:
        return f.read()

def update_index_json(index_path, plugins_content):
    with open(index_path, 'r') as f:
        index = json.load(f)
    
    # Update the MindRoot Expert Agent description
    for item in index.get('items', []):
        if item.get('name') == 'MindRoot Expert':
            item['description'] = plugins_content
            break
    
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

def main():
    # File paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_md = os.path.join(base_dir, 'plugins.md')
    index_path = os.path.join(base_dir, 'src/mindroot/coreplugins/index/indices/default/index.json')
    
    # Read plugins.md content
    plugins_content = read_file(plugins_md)
    
    # Update index.json
    update_index_json(index_path, plugins_content)
    print("Updated index.json with plugins.md documentation")

if __name__ == '__main__':
    main()
