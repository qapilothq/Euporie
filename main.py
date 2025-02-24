from utils import encode_image, process_xml, validate_base64
from llm import initialize_llm
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from prompts import system_prompt
import os
import json
from faker import Faker
import base64
from logger_config import setup_logger
import time

logger = setup_logger()

load_dotenv()
app = FastAPI()

class APIRequest(BaseModel):
    image: Optional[str] = None        # Base64 encoded image string
    xml: Optional[str] = None          # XML as string
    xml_url: Optional[str] = None      # XML URL option
    image_url: Optional[str] = None    # Image URL option
    config_data: Optional[Dict[str, Any]] = None

faker = Faker()

# Get all attributes and methods of the Faker instance
all_methods = dir(faker)

# Filter out private methods and attributes (those starting with '_')
faker_fields = [method for method in all_methods if not method.startswith('_')]

def validate_base64(base64_string: str) -> bool:
    try:
        base64.b64decode(base64_string)
        return True
    except Exception:
        return False

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Completed request: {request.method} {request.url} in {process_time:.4f} seconds")
    logger.info(f"Response status: {response.status_code}")
    return response

def clean_markdown_json(content):
    if content.startswith("```json\n"):
        content = content[8:]
    elif content.startswith("```json"):
        content = content[7:]
    
    # Remove the closing fence
    if content.endswith("\n```"):
        content = content[:-4]
    elif content.endswith("```"):
        content = content[:-3]
    
    # Fix Python booleans to be JSON compatible
    content = content.replace("True", "true").replace("False", "false")
    
    return content


def get_field_value(field: Dict[str, Any], config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get field value based on priority:
    1. Use value from parsed output if source is 'config' or 'llm'
    2. Faker function if available
    3. Default placeholder if no value is generated
    """
    field_name = field.get("field_name", "").lower()
    
    # Directly use the value from parsed output if source is 'config' or 'llm'
    if field.get("source") in ["config", "llm"]:
        logger.info(f"Using value from parsed output for field: {field_name} with source: {field['source']}")
        return field

    # Priority 2: Check Faker function
    faker_func = field.get("faker_function")
    if faker_func and faker_func in faker_fields:
        try:
            logger.info(f"Using Faker function '{faker_func}' for field: {field_name}")
            field["value"] = getattr(faker, faker_func)()
            field["source"] = "faker"
            return field
        except Exception as e:
            logger.warning(f"Faker generation failed for {faker_func}: {str(e)}")
            # Continue to default placeholder if Faker fails

    # Default placeholder if no value is generated
    logger.warning(f"No value generated for field: {field_name}, using default placeholder.")
    field["value"] = "Value not generated"
    field["source"] = "llm"
    
    return field

@app.post("/invoke")
async def run_service(request: APIRequest):
    try:
        logger.info("Invoke endpoint called.")

        llm_key = os.getenv("OPENAI_API_KEY")
        if not llm_key:
            logger.error("API key not found.")
            return {"status": "error", "message": "API key not found"}

        logger.info("Initializing LLM.")
        llm = initialize_llm(llm_key)
        messages = [("system", system_prompt)]

        xml_metadata = None

        # Handle config data
        if request.config_data:
            logger.debug(f"Config data provided: {request.config_data}")
            messages.append(
                ("human", f"Configuration data for field generation: {json.dumps(request.config_data, indent=2)}")
            )

        # Process XML or image input
        if request.xml or request.xml_url:
            if request.xml_url:
                logger.debug("XML URL provided.",request.xml_url)
            xml_data = request.xml if request.xml else request.xml_url
            xml_metadata = process_xml(xml_data)
            messages.append(
                ("human", f'This is the xml source of that screen: {xml_metadata}')
            )
        elif request.image or request.image_url:
            if request.image:
                if validate_base64(request.image):
                    encoded_image = request.image
                else:
                    logger.error("Base64 string not provided in image field.")
                    return {
                        "status": "error",
                        "message": "Base64 string not provided in image field."
                    }
            elif request.image_url:
                encoded_image = encode_image(request.image_url)
            else:
                logger.error("Invalid image data provided.")
                return {
                    "status": "error",
                    "message": "Invalid image data provided."
                }
            messages.extend([
                ("human", [
                    {"type": "text", "text": "This is the screenshot of the current screen"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                ])])
        else:
            logger.error("Either image or xml must be provided.")
            return {
                "status": "error",
                "message": "Either image or xml must be provided."
            }

        ai_msg = llm.invoke(messages)
        logger.debug(f"AI message content: {ai_msg.content}")
        cleaned_content = clean_markdown_json(ai_msg.content)
        
        try:
            parsed_output = json.loads(cleaned_content)
            
            # Validate response format
            if "data_generation_required" not in parsed_output:
                return {"status": "error", "message": "Invalid response format"}
            
            # Process fields if data generation is required
            if parsed_output["data_generation_required"] == True:
                if "fields" not in parsed_output:
                    return {"status": "error", "message": "Missing fields array"}
                
                # Process each field with priority logic
                for field in parsed_output["fields"]:
                    field = get_field_value(field, request.config_data)
                    
                    # Add XML metadata if available
                    if xml_metadata and "id" in field:
                        field_id = field["id"]
                        if field_id in xml_metadata:
                            field["metadata"] = xml_metadata[field_id]
            
            return {"status": "success", "agent_response": parsed_output}
            
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse AI response"}

    except Exception as e:
        logger.exception("An error occurred during the invoke process.")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)