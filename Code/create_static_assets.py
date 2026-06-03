import os
import base64
from PIL import Image
import io
import shutil

def create_static_directory():
    """Create static directory if it doesn't exist"""
    if not os.path.exists("static"):
        os.makedirs("static")
        print("Created static directory")
    else:
        print("Static directory already exists")

def save_system_diagram():
    """Save the system diagram image to static/bias_design_flow.png"""
    # Create an empty image as placeholder (in a real scenario, you would use the actual diagram)
    # In a real implementation, you would save the provided system diagram here
    # For now, we'll create a placeholder image
    placeholder_image = Image.new('RGB', (800, 400), color='white')
    
    # Save the image
    placeholder_image.save('static/bias_design_flow.png')
    
    print("Created system diagram placeholder at static/bias_design_flow.png")
    print("Note: In a real implementation, you should replace this with the actual system diagram.")

if __name__ == "__main__":
    create_static_directory()
    save_system_diagram()
    print("Static assets created successfully!") 