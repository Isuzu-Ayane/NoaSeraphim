import os
import re

html_path = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\index.html'
new_img_dir = r'K:\GoogleAI\tool\image\image_master_1'

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Extract all image filenames currently in the HTML
existing_imgs = re.findall(r'<img src="\./image_master/([^"]+)"', html_content)
existing_imgs_set = set(existing_imgs)

print(f"Number of existing images in HTML: {len(existing_imgs_set)}")

new_imgs = os.listdir(new_img_dir)
new_imgs_to_add = []

for img in new_imgs:
    if img.endswith('.jpg') or img.endswith('.png'):
        if img not in existing_imgs_set:
            new_imgs_to_add.append(img)

print(f"Number of new images to add: {len(new_imgs_to_add)}")
for img in new_imgs_to_add[:10]:
    print(" -", img)
