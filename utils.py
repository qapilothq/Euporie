import xml.etree.ElementTree as ET
import base64
import os
import requests

def process_xml(xml_input):
    """
    Extracts all interactable elements from the given XML input.

    Args:
    xml_input (str): XML file path, URL, or XML content representing the screen hierarchy

    Returns:
    list: A list of dictionaries, each containing details of an interactable element
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
        

        # Find all clickable elements
        clickable_elements = root.findall('.//*[@clickable="true"]')
        
        interactable_elements = {}

        for idx, action_elem in enumerate(clickable_elements, start=1):
            
            action_details = {
                'text': action_elem.get('text', ''),
                'resource_id': action_elem.get('resource-id', ''),
                'type': action_elem.tag.split('.')[-1],
                'bounds': action_elem.get('bounds', ''),
                'class': action_elem.get('class', ''),
                'content_desc': action_elem.get('content-desc', ''),
                'enabled': action_elem.get('enabled', 'true') == 'true',
                'focused': action_elem.get('focused', 'false') == 'true',
                'scrollable': action_elem.get('scrollable', 'false') == 'true',
                'long_clickable': action_elem.get('long-clickable', 'false') == 'true',
                'password': action_elem.get('password', 'false') == 'true',
                'selected': action_elem.get('selected', 'false') == 'true'
            }
            interactable_elements[str(idx)] = action_details  # Use id as the key
        
        return interactable_elements
    
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


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

def validate_base64(base64_string: str) -> bool:
    try:
        base64.b64decode(base64_string)
        return True
    except Exception:
        return False