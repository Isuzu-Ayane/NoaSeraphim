import os
import re

# New Mapping
SILO_MAP = {
    'sd-install': 'ai-guide/sd-install',
    'comfyui-install': 'ai-guide/comfyui-install',
    'local-llm-install': 'ai-guide/local-llm-install',
    'ai-specs': 'ai-guide/ai-specs',
    'ai-checkpoints': 'models/ai-checkpoints',
    'ai-lora': 'models/ai-lora',
    'ai-vae': 'models/ai-vae',
    'ai-embeddings': 'models/ai-embeddings',
    'ai-ComfyUI': 'Tools/ai-ComfyUI',
    'ai-tools': 'Tools/ai-tools',
    'Noaplugin': 'Tools/Noaplugin',
    'Tools': 'Tools',
    'ai-character': 'creative/ai-character',
    'ai-personality': 'creative/ai-personality',
    'ai-dialogue': 'creative/ai-dialogue',
    'ai-image': 'creative/ai-image',
    'ai-girlfriend': 'creative/ai-girlfriend',
    'ai-waifu': 'creative/ai-waifu',
    'Failure_Yet_Alive': 'creative/Failure_Yet_Alive',
    'Nora_Tweets': 'creative/Nora_Tweets',
    'NoaSeraphim_AI': 'creative/NoaSeraphim_AI',
    'image-song': 'creative/image-song'
}

ROOT_ASSETS = ['styles.css', 'script.js', 'assets/', 'index.html', 'index_en.html']

MOVED_SILOS = ['ai-guide', 'models', 'Tools', 'creative']

def fix_content(content):
    # 1. Update root assets: ../asset -> ../../asset
    for asset in ROOT_ASSETS:
        pattern = re.compile(re.escape('../' + asset))
        content = pattern.sub('../../' + asset, content)
    
    # 2. Update cross-links: ../old-dir -> ../../new-silo/old-dir
    # Note: We must be careful not to double-replace.
    for old_dir, new_path in SILO_MAP.items():
        # Only replace if it starts with ../ and is NOT followed by another / (already replaced)
        pattern = re.compile(r'\.\./' + re.escape(old_dir) + r'(?=[/\'"])')
        content = pattern.sub('../../' + new_path, content)
        
    return content

def process_dir(root_path):
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith(('.html', '.py', '.css', '.js')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = fix_content(content)
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed links in: {filepath}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == '__main__':
    base_dir = r'K:\GoogleAI\NoaSeraphim'
    for silo in MOVED_SILOS:
        silo_path = os.path.join(base_dir, silo)
        if os.path.exists(silo_path):
            print(f"Processing silo: {silo}")
            process_dir(silo_path)
