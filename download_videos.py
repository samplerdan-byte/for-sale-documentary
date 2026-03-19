"""
Download free stock videos from Pexels for the documentary.
You need a free Pexels API key from: https://www.pexels.com/api/

Usage: python3 download_videos.py YOUR_PEXELS_API_KEY
"""
import sys
import os
import json
import urllib.request

if len(sys.argv) < 2:
    print("Usage: python3 download_videos.py YOUR_PEXELS_API_KEY")
    print("Get a free key at: https://www.pexels.com/api/")
    sys.exit(1)

API_KEY = sys.argv[1]
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Pexels video IDs matched to documentary segments
VIDEOS = {
    "bg_space":     3194277,   # Outer space nebula
    "bg_explosion": 6151238,   # Cosmic explosion
    "bg_volcano":   9882072,   # Volcano erupting
    "bg_pyramids":  10717893,  # Aerial pyramids Cairo
    "bg_wallst":    7579561,   # Stock market tickers
    "bg_code":      852292,    # Matrix code scrolling
    "bg_capitol":   6133588,   # Capitol building sunrise
    "bg_servers":   5028622,   # Server room
    "bg_digital":   3129977,   # Digital data streams
}


def fetch_video_url(video_id):
    """Get the best HD MP4 URL from Pexels API."""
    url = f"https://api.pexels.com/videos/videos/{video_id}"
    req = urllib.request.Request(url, headers={"Authorization": API_KEY})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    # Find HD quality (or best available)
    files = data.get("video_files", [])
    best = None
    for f in files:
        if f.get("quality") == "hd" and f.get("width", 0) >= 1280:
            if best is None or f.get("width", 0) > best.get("width", 0):
                best = f
    if not best and files:
        best = max(files, key=lambda x: x.get("width", 0))
    return best.get("link") if best else None


def download_file(url, filename):
    """Download a file with progress."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        print(f"  Already exists: {filename}")
        return filepath
    print(f"  Downloading {filename}...")
    urllib.request.urlretrieve(url, filepath)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  Done: {size_mb:.1f} MB")
    return filepath


def main():
    print(f"Downloading {len(VIDEOS)} videos from Pexels...\n")
    for name, vid_id in VIDEOS.items():
        print(f"[{name}] (Pexels ID: {vid_id})")
        try:
            mp4_url = fetch_video_url(vid_id)
            if mp4_url:
                download_file(mp4_url, f"{name}.mp4")
            else:
                print(f"  ERROR: No video file found")
        except Exception as e:
            print(f"  ERROR: {e}")
        print()

    print("All downloads complete!")
    print(f"Videos saved to: {OUTPUT_DIR}")
    print("\nTo use with the documentary, just open the HTML file.")
    print("It will automatically detect and use local video files.")


if __name__ == "__main__":
    main()
