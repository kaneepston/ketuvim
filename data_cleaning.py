import cv2
import os
import numpy as np
import hashlib

def compute_hash(image):
    success, encoded_image = cv2.imencode('.png', image)
    if not success:
        return None
    return hashlib.md5(encoded_image.tobytes()).hexdigest()

def is_low_quality(image, threshold=10):
    return np.var(image) < threshold

raw_folder = 'data/raw'
cleaned_folder = 'data/cleaned'
os.makedirs(cleaned_folder, exist_ok=True)

image_hashes = set()

# Traverse raw_folder recursively
for root, dirs, files in os.walk(raw_folder):
    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
            file_path = os.path.join(root, filename)
            img = cv2.imread(file_path)
            if img is None:
                print(f"Skipping unreadable image: {filename}")
                continue

            img_hash = compute_hash(img)
            if img_hash is None:
                print(f"Error computing hash for {filename}, skipping.")
                continue
            if img_hash in image_hashes:
                print(f"Duplicate found, skipping {filename}")
                continue
            image_hashes.add(img_hash)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if is_low_quality(gray):
                print(f"Low quality image detected, skipping: {filename}")
                continue

            # Save the cleaned image with the same relative path structure
            relative_path = os.path.relpath(root, raw_folder)
            save_dir = os.path.join(cleaned_folder, relative_path)
            os.makedirs(save_dir, exist_ok=True)
            cleaned_path = os.path.join(save_dir, filename)
            cv2.imwrite(cleaned_path, gray)
            print(f"Saved cleaned image: {cleaned_path}")
