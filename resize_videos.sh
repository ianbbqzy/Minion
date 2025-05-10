#!/bin/bash

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Installing..."
    brew install ffmpeg
fi

# Create output directory if it doesn't exist
mkdir -p assets/videos/resized

# Process each video
for video in "green.mp4" "pink.mp4" "yellow.mp4"; do
    if [ -f "assets/minions/$video" ]; then
        echo "Processing $video..."
        ffmpeg -i "assets/minions/$video" \
               -vf "scale=100:100:flags=lanczos" \
               -c:v libx264 -crf 18 -preset slow \
               -pix_fmt yuv420p \
               "assets/minions/${video%.*}_resized.mp4"
        echo "Finished processing $video"
    else
        echo "Warning: $video not found in assets/videos/"
    fi
done

echo "All videos processed!" 