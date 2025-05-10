import cv2
import openai
import tkinter as tk
from PIL import Image, ImageTk
import base64

# Initialize OpenAI API
openai.api_key = 'YOUR_OPENAI_API_KEY'

def capture_frame(cap):
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Could not read frame.")
        return None
    
    return frame

def update_frame():
    frame = capture_frame(cap)
    if frame is not None:
        # Convert the frame to an image
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
    lmain.after(10, update_frame)

def capture_and_send():
    frame = capture_frame(cap)
    if frame is not None:
        response = send_frame_to_openai(frame)
        print(response)

def send_frame_to_openai(frame):
    # Convert the frame to a base64 string
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Call OpenAI API
    response = openai.Completion.create(
        model="gpt-4",
        prompt=f"Analyze this image: {frame_base64}",
        max_tokens=100
    )
    
    return response

# Initialize the main window
root = tk.Tk()
root.title("Camera Feed")

# Open the default camera
cap = cv2.VideoCapture(0)

# Create a label to display the camera feed
lmain = tk.Label(root)
lmain.pack()

# Create a button to capture and send the frame
capture_button = tk.Button(root, text="Capture and Send", command=capture_and_send)
capture_button.pack()

# Start the video loop
update_frame()

# Run the application
root.mainloop()

# Release the camera when the window is closed
cap.release()
