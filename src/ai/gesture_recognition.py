"""
OpenAI-based gesture recognition
"""
import cv2
import base64
from openai import AsyncOpenAI 
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
            self.client = AsyncOpenAI(api_key=self.api_key)
        
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
    
    async def analyze_gesture(self):
        """Send the captured frame to GPT-4o Vision and get facial expressions and gestures"""
        if self.last_frame is None or self.last_frame.size == 0:
            print("Warning: analyze_gesture called with no valid frame.")
            self.last_gesture = "Error: No valid frame"
            return {"facial_expressions": "Error: No valid frame", "gestures": "Error: No valid frame"}
        
        GESTURE_PROMPT = (
            "You are an expert visual analyst. Given an image, analyze the subject(s) and return a description."
            "of any facial expressions and physical gestures visible.\n\n"
            "Note that in the image has left and right flipped, so you need to account for that when describing the gestures.\n\n"
            "Focus only on expressions (e.g. smiling, frowning, eyes widened, brows furrowed) and gestures "
            "(e.g. crossed arms, hands raised, leaning forward). Do not make assumptions about the person's "
            "identity or context beyond what is directly observable. When there is a finger pointing, make sure "
            "to include the direction too (up, down, left, right), and when there are complex hand gestures "
            "(peace, rocker, thumbs up, down, triangle, circle etc.), describe them to the best extent you can.\n\n"
            "If you are unsure or the person is just in a neutral position, then just enter unknown in the output fields.\n\n"
            "Return the output in this JSON format:\n"
            "{\n"
            "  \"facial_expressions\": \"string\",\n"
            "  \"gestures\": \"string\"\n"
            "}"
        )
        
        try:
            # Convert the RGB frame to BGR for OpenCV
            frame_bgr = cv2.cvtColor(self.last_frame, cv2.COLOR_RGB2BGR)
            
            # Encode the image as PNG
            _, png = cv2.imencode(".png", frame_bgr)
            b64_data = base64.b64encode(png.tobytes()).decode()
            
            # Call the OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=200,  # Increased to accommodate JSON response
                response_format={"type": "json_object"},  # Request JSON response
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
            
            # Extract the JSON response
            response_content = response.choices[0].message.content.strip()
            import json
            try:
                result = json.loads(response_content)
                self.last_gesture = result  # Store the full result
                return result
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print(f"Raw response: {response_content}")
                default_result = {"facial_expressions": "Error: Invalid JSON", "gestures": "Error: Invalid JSON"}
                self.last_gesture = default_result
                return default_result
            
        except Exception as e:
            error_message = f"API error: {e}"
            print(error_message)
            error_result = {"facial_expressions": error_message, "gestures": error_message}
            self.last_gesture = error_result
            return error_result 