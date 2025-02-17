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


@app.post("/invoke")
async def run_service(request: APIRequest):
    try:
        logger.info("Invoke endpoint called.")
        # logger.debug(f"Request data: {request.json()}")

        llm_key = os.getenv("OPENAI_API_KEY")
        if not llm_key:
            logger.error("API key not found.")
            return {
                "status": "error",
                "message": "API key not found. Please check your environment variables."
            }

        logger.info("Initializing LLM.")
        llm = initialize_llm(llm_key)
        messages = [("system", system_prompt)]

        if request.config_data:
            messages.append(
                ("human", f"Configuration data for field generation: {json.dumps(request.config_data, indent=2)}")
            )   
        if request.xml or request.xml_url:
            if request.xml_url:
                logger.debug("XML URL provided.",request.xml_url)
            xml_data = request.xml if request.xml else request.xml_url
            xml = process_xml(xml_data)
            messages.append(
                ("human", f'This is the xml source of that screen: {xml}')
            )
        elif request.image or request.image_url:
            if request.image and validate_base64(request.image):
                encoded_image = request.image
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

        # Clean and parse the AI response
     

        cleaned_content = clean_markdown_json(ai_msg.content)
        try:
            parsed_output = json.loads(cleaned_content)
            
            # Validate response format
            if "data_generation_required" not in parsed_output:
                return {
                    "status": "error",
                    "message": "Invalid response format: missing 'data_generation_required' field"
                }
                
            if parsed_output["data_generation_required"] not in [True, False]:
                return {
                    "status": "error",
                    "message": "Invalid value for 'data_generation_required'. Expected 'True' or 'False'"
                }
                
            if parsed_output["data_generation_required"] == True and "fields" not in parsed_output:
                return {
                    "status": "error",
                    "message": "Invalid response format: 'fields' array missing for data generation"
                }
                
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": f"Failed to parse AI message content as JSON. Content: {ai_msg.content}"
            }
        
        logger.debug(f"Parsed output: {parsed_output}")

        # If data generation is required, process each field:
        if parsed_output["data_generation_required"] == True:
            for field in parsed_output["fields"]:
                # Check if the field specifies a faker function
                if "faker_function" in field and field["faker_function"]:
                    faker_func = field["faker_function"]
                    if faker_func in faker_fields:
                        try:
                            # Generate the fake value using the corresponding faker method
                            field["value"] = getattr(faker, faker_func)()
                            field["source"] = "faker"
                        except Exception as e:
                            # In case of an error, fallback to the provided value
                            field["value"] = field.get("value", f"Error generating with {faker_func}: {str(e)}")
                    else:
                        # If the faker function is not available, use the LLM provided value
                        field["value"] = field.get("value", "Value not generated")
        
        return {
            "status": "success",
            "agent_response": parsed_output
        }

    except Exception as e:
        logger.exception("An error occurred during the invoke process.")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)