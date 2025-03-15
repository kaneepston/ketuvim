import subprocess
import sys
import os
import json
import cv2

def run_command(command):
    print("Running command:", " ".join(command))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Command failed with error:")
        print(result.stderr)
        sys.exit(result.returncode)
    return result.stdout

def main(input_image_path):
    # Ensure the input image exists
    if not os.path.exists(input_image_path):
        print("Input image does not exist:", input_image_path)
        sys.exit(1)

    # Prepare output filenames based on the input image's basename
    base_name = os.path.splitext(os.path.basename(input_image_path))[0]
    # You can adjust the output directory as needed
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    binarized_image = os.path.join(output_dir, f"{base_name}_binarized.png")
    segmentation_json = os.path.join(output_dir, f"{base_name}_segmentation.json")
    overlay_image = os.path.join(output_dir, f"{base_name}_overlay.png")

    # Binarize the image using Kraken
    binarize_cmd = ["kraken", "-i", input_image_path, binarized_image, "binarize"]
    run_command(binarize_cmd)
    print("Binarized image saved to", binarized_image)

    # Segment the binarized image using Kraken
    segment_cmd = ["kraken", "-i", binarized_image, segmentation_json, "segment"]
    run_command(segment_cmd)
    print("Segmentation JSON saved to", segmentation_json)

    # Load the segmentation JSON file and draw an overlay
    try:
        with open(segmentation_json, 'r') as f:
            seg_data = json.load(f)
    except Exception as e:
        print("Failed to load segmentation JSON:", e)
        sys.exit(1)

    # The JSON output (as seen in your example) is a dictionary with a "lines" key.
    lines = seg_data.get("lines", [])
    print(f"Found {len(lines)} segmented lines.")

    # Load the binarized image (for overlay)
    img = cv2.imread(binarized_image)
    if img is None:
        print("Could not read the binarized image from", binarized_image)
        sys.exit(1)

    # Draw bounding boxes over the image for each segmented line
    for line in lines:
        bbox = line.get("bbox")
        if bbox and len(bbox) == 4:
            x, y, w, h = map(int, bbox)
            # Draw a green rectangle (BGR: (0, 255, 0)) with a thickness of 2 pixels
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        else:
            print("Skipping a line segment with invalid bbox:", line)

    # Save the overlay image
    cv2.imwrite(overlay_image, img)
    print("Overlay image saved as", overlay_image)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python unified_segmentation.py <input_image>")
        sys.exit(1)
    main(sys.argv[1])
