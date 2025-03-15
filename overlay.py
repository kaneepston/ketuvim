import json
import cv2

# Load the segmentation JSON file
with open('data/kraken_segmented.json', 'r') as f:
    seg_data = json.load(f)

# Print out the keys to confirm structure (optional)
print("Top-level keys:", list(seg_data.keys()))

# Extract the list of lines (each line is a dict)
lines = seg_data.get('lines', [])
print("Found", len(lines), "line segments.")

# Load the binarized image (or original image if you prefer)
img = cv2.imread('data/kraken_binarized.png')
if img is None:
    raise Exception("Could not read the image file.")

# Iterate over each line segment and draw the bounding box
for line in lines:
    bbox = line.get('bbox')
    if bbox and len(bbox) == 4:
        x, y, w, h = map(int, bbox)
        # Draw a rectangle on the image (green, thickness 2)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    else:
        print("Skipping a line segment with invalid bbox:", line)

# Save the overlay image
overlay_filename = 'data/segmentation_overlay.png'
cv2.imwrite(overlay_filename, img)
print("Overlay image saved as", overlay_filename)
