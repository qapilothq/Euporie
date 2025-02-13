from utils import encode_image, process_xml
from llm import initialize_llm
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from prompts import system_prompt
import os
import json

load_dotenv()
app = FastAPI()

class APIRequest(BaseModel):
    image: Optional[str] = None
    xml: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None



@app.post("/invoke")
async def run_service(request: APIRequest):
    try:
        llm_key = os.getenv("OPENAI_API_KEY")
        if not llm_key:
            raise HTTPException(
                status_code=500, 
                detail="API key not found. Please check your environment variables."
            )

        llm = initialize_llm(llm_key)
        messages = [("system", system_prompt)]

        if request.config_data:
            messages.append(
                ("human", f"Configuration data for field generation: {json.dumps(request.config_data, indent=2)}")
            )   

        if request.xml:
            xml = process_xml(request.xml)
            messages.append(
                ("human", f'This is the xml source of that screen: {xml}')
            )
        elif request.image:
            encoded_image = encode_image(request.image)
            messages.append(
                ("human", json.dumps([
                    {"type": "text", "text": "This is the screenshot of the current screen"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                    },
                ]))
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either image or xml must be provided."
            )

        ai_msg = llm.invoke(messages)

        print(ai_msg)
        
        # Clean and parse the AI response
        cleaned_content = str(ai_msg.content).strip("```json\n").strip("\n```")
        try:
            parsed_output = json.loads(cleaned_content)
            
            # Validate response format
            if "data_generation_required" not in parsed_output:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid response format: missing 'data_generation_required' field"
                )
                
            if parsed_output["data_generation_required"] not in ["yes", "no"]:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid value for 'data_generation_required'. Expected 'yes' or 'no'"
                )
                
            if parsed_output["data_generation_required"] == "yes" and "fields" not in parsed_output:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid response format: 'fields' array missing for data generation"
                )
                
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to parse AI message content as JSON. Content: {ai_msg.content}"
            )

        return {
            "status": "success",
            "agent_response": parsed_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)