"""
OpenAI-based gesture recognition
"""
import cv2
import base64
import openai
import numpy as np
import pygame
import os

class GestureRecognizer:
    def __init__(self, api_key=None):
        self.last_frame = None
        self.last_gesture = ""
        self.captured_preview_surface = None
        # Use API key from parameter, environment variable, or .env file
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: No OpenAI API key found. Please set OPENAI_API_KEY.")
        
        # Initialize OpenAI client if we have an API key
        if self.api_key:
            # api_type_to_use = os.getenv("OPENAI_API_TYPE", "openai")
            self.client = openai.OpenAI(api_key=self.api_key)
        
    def capture_frame(self, frame_rgb):
        """Save the captured frame for analysis"""
        if frame_rgb is None or frame_rgb.size == 0:
            print("Warning: GestureRecognizer.capture_frame received an empty or None frame.")
            self.last_frame = None
            self.captured_preview_surface = None
            return None

        self.last_frame = frame_rgb
        
        try:
            # Build the pygame surface for the thumbnail
            flipped_frame = np.flipud(frame_rgb)  # flip Y so it isn't upside-down
            self.captured_preview_surface = pygame.surfarray.make_surface(flipped_frame)
        except ValueError as e:
            print(f"Error processing frame in GestureRecognizer.capture_frame: {e}")
            print(f"Offending frame_rgb shape: {getattr(frame_rgb, 'shape', 'N/A')}, dtype: {getattr(frame_rgb, 'dtype', 'N/A')}, size: {getattr(frame_rgb, 'size', 'N/A')}")
            self.last_frame = None # Ensure consistency
            self.captured_preview_surface = None
            return None
        
        return self.captured_preview_surface
    
    def analyze_gesture(self):
        """Send the captured frame to GPT-4o Vision and get the gesture"""
        if self.last_frame is None or self.last_frame.size == 0:
            print("Warning: analyze_gesture called with no valid frame.")
            self.last_gesture = "Error: No valid frame"
            return "Error: No valid frame"
        
        GESTURE_PROMPT = (
            "You are a hand-gesture classifier.\n"
            "Look at the image and answer ONLY with one "
            "of these labels (case sensitive):\n"
            "  • ThumbsUp\n  • ThumbsDown\n  • Victory\n  • Stop\n"
            "  • PointLeft\n  • PointRight\n  • Fist\n  • OpenPalm\n"
            "  • Unknown\n"
            "If you are not sure, output Unknown."
        )
        
        try:
            # Convert the RGB frame to BGR for OpenCV
            frame_bgr = cv2.cvtColor(self.last_frame, cv2.COLOR_RGB2BGR)
            
            # Encode the image as PNG
            _, png = cv2.imencode(".png", frame_bgr)
            b64_data = base64.b64encode(png.tobytes()).decode()
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=4,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": GESTURE_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_data}",
                                    "detail": "auto"
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract the gesture from the response
            self.last_gesture = response.choices[0].message.content.strip()
            return self.last_gesture
            
        except Exception as e:
            error_message = f"API error: {e}"
            self.last_gesture = error_message
            return error_message
    
    def map_gesture_to_direction(self, gesture):
        """Map the recognized gesture to a game direction"""
        if gesture == "PointUp":
            return "up"
        elif gesture == "PointDown":
            return "down"
        elif gesture == "PointLeft":
            return "left"
        elif gesture == "PointRight":
            return "right"
        elif gesture == "Stop":
            return "stay"
        elif gesture == "ThumbsUp":
            return "collect"
        else:
            return None  # No matching direction 