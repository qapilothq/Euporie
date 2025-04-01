import xml.etree.ElementTree as ET
import base64
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import uuid
import matplotlib.pyplot as plt


def process_xml(xml_input):
    """
    Extracts all input field elements from the given XML input.

    Args:
        xml_input (str): XML file path, URL, or XML content representing the screen hierarchy

    Returns:
        dict: A dictionary of dictionaries, each containing details of an input field element
    """
    try:
        # Parse XML input
        if isinstance(xml_input, str):
            if xml_input.startswith('http://') or xml_input.startswith('https://'):
                response = requests.get(xml_input)
                response.raise_for_status()
                xml_content = response.text
                root = ET.fromstring(xml_content)
            elif os.path.isfile(xml_input):
                tree = ET.parse(xml_input)
                root = tree.getroot()
            else:
                root = ET.fromstring(xml_input)
        else:
            raise ValueError("Invalid XML input type.")

        # Define types that are typically input fields
        input_field_types = {  'EditText', 'TextInputEditText', 'TextInputLayout', 
            'AutoCompleteTextView', 'MultiAutoCompleteTextView'}  # Add other types if needed, e.g., 'TextView' for specific cases
        
        # Find all clickable elements and filter for input fields
        clickable_elements = root.findall('.//*[@clickable="true"]')
        interactable_elements = {}

        for idx, action_elem in enumerate(clickable_elements, start=1):
            element_type = action_elem.tag.split('.')[-1]
            # Check if the element is an input field type and enabled
            if (element_type in input_field_types and 
                action_elem.get('enabled', 'true') == 'true'):
                action_details = {
                    'text': action_elem.get('text', ''),
                    'resource_id': action_elem.get('resource-id', ''),
                    'type': element_type,
                    'bounds': action_elem.get('bounds', ''),
                    'class': action_elem.get('class', ''),
                    'content_desc': action_elem.get('content-desc', ''),
                    'enabled': action_elem.get('enabled', 'true') == 'true',
                    'password': action_elem.get('password', 'false') == 'true'
                }
                interactable_elements[str(idx)] = action_details  # Use id as the key

        return interactable_elements

    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

def encode_image(input_source):
    """
    Encodes an image from a file path, file object, or URL into a base64 string.

    Args:
    input_source (str or file-like object): The image file path, file object, or URL.

    Returns:
    str: Base64 encoded string of the image.
    """
    try:
        if isinstance(input_source, str):
            # Check if it's a URL
            if input_source.startswith('http://') or input_source.startswith('https://'):
                response = requests.get(input_source)
                response.raise_for_status()
                image_data = response.content
            # Check if it's a file path
            elif os.path.isfile(input_source):
                with open(input_source, 'rb') as image_file:
                    image_data = image_file.read()
            else:
                raise ValueError("Invalid file path or URL.")
        else:
            # Assume it's a file-like object
            image_data = input_source.read()

        # Encode the image data
        encoded_image = base64.b64encode(image_data).decode()
        return encoded_image

    except Exception as e:
        print(f"Error encoding image: {e}")
        return None


def annotate_image(base64_image, xml_data):
    """
    Annotate the image with bounding boxes and element IDs for all interactable elements.
    
    Args:
        base64_image (str): Base64 encoded image string
        xml_data (dict): Processed XML data containing interactable elements
        
    Returns:
        str: Base64 encoded annotated image
    """

    # Decode base64 image
    print(xml_data)
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data))

    if image.mode == 'RGBA':
        image = image.convert('RGB')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, use default if not available
    try:
        font = ImageFont.truetype("Arial.ttf", 50)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw bounding boxes and element IDs for all interactable elements
    for element_id, element_data in xml_data.items():
        if "bounds" in element_data:
            bounds = element_data["bounds"]
            if isinstance(bounds, str):
                # Parse bounds string like "[0,0][100,100]"
                coords = bounds.replace("][", ",").strip("[]").split(",")
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    # Draw rectangle
                    draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)  # Increased outline width
                    # Draw element ID
                    draw.text((x1-30, y1-30), element_id, fill="red", font=font)  # Position text at top-left corner

    # plt.figure(figsize=(8, 8))
    # plt.imshow(image)
    # plt.axis('off')  # Hide the axis
    # plt.show()
    # Convert back to base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    annotated_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Ensure the directory exists
    os.makedirs("screenshot_combined_debug", exist_ok=True)

    # Generate a unique filename using a timestamp and UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex
    filename = f"screenshot_combined_debug/annotated_image_{timestamp}_{unique_id}.jpg"

    # Save the annotated image
    try:
        image.save(filename)
        print(f"Annotated image saved as {filename}")
    except Exception as e:
        print(f"Error saving annotated image: {e}")

    return annotated_base64

def validate_base64(base64_string: str) -> bool:
    try:
        base64.b64decode(base64_string)
        return True
    except Exception:
        return False