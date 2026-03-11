import os
from PIL import Image, ImageDraw, ImageFont

# 1. Configuration
BASE_DIR = r"K:\GoogleAI\NoaSeraphim\Seraphim_Growth_Project"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure assets directory exists
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)
    print(f"Created directory: {ASSETS_DIR}")

# 2. Image Lists
ages = [6, 9, 12, 15, 18]
actions = {
    "study": ("勉強", (100, 149, 237)),     # CornflowerBlue
    "exercise": ("運動", (255, 99, 71)),   # Tomato
    "life": ("生活", (60, 179, 113)),      # MediumSeaGreen
    "socialize": ("交流", (255, 105, 180)),# HotPink
    "rest": ("休憩", (147, 112, 219)),     # MediumPurple
}

endings = {
    "ending_archangel": "大天使エンド",
    "ending_scholar": "学者天使エンド",
    "ending_warrior": "戦士天使エンド",
    "ending_partner": "永遠のパートナー",
    "ending_human": "人間界定住エンド",
    "ending_fragile": "儚き天使エンド",
    "ending_fallen": "堕天エンド",
    "ending_leader": "指導者エンド",
    "ending_adventurer": "冒険者エンド",
    "ending_departure": "旅立ちのエンド"
}

# 3. Generation Function
def create_placeholder(filename, text, color):
    # Image size (matches typical mobile/web portrait aspect)
    width, height = 400, 600
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    # Draw Text (Centered logic simplified for standard PIL)
    # We will just place text at specific positions to avoid font path issues
    d.rectangle([10, 10, width-10, height-10], outline=(255, 255, 255), width=5)
    d.text((20, 50), "Seraphim Project", fill=(255, 255, 255))
    d.text((20, 100), text, fill=(255, 255, 255))
    
    # Save
    filepath = os.path.join(ASSETS_DIR, filename)
    img.save(filepath)
    print(f"Generated: {filename}")

# 4. Generate Main Assets
for age in ages:
    for action_key, (action_name, color) in actions.items():
        filename = f"age{age}_{action_key}.jpg"
        text = f"Age: {age}\nAction: {action_name}"
        create_placeholder(filename, text, color)
        
    # Sick image
    create_placeholder(f"age{age}_sick.jpg", f"Age: {age}\nState: Sick", (105, 105, 105))

# 5. Generate Endings
for filename_base, end_name in endings.items():
    filename = f"{filename_base}.jpg"
    create_placeholder(filename, f"ENDING:\n{end_name}", (255, 215, 0)) # Gold

print("\nAll placeholder assets generated successfully!")
