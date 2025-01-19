import os
import json

def get_folder_structure(path):
    structure = {}
    
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        
        # Skip .git and node_modules directories
        if item in ['.git', 'node_modules', 'venv']:
            continue
            
        if os.path.isfile(item_path):
            structure[item] = "file"
        elif os.path.isdir(item_path):
            structure[item] = get_folder_structure(item_path)
            
    return structure

def save_structure(workspace_path, output_file="folder_structure.json"):
    structure = get_folder_structure(workspace_path)
    
    with open(output_file, 'w') as f:
        json.dump(structure, f, indent=2)
        
    return structure

# Usage example
if __name__ == "__main__":
    workspace_path = "." # Current directory
    save_structure(workspace_path)