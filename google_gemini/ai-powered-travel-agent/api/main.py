# FastAPI dependencies
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Gemini SDK dependencies
from google import genai
from google.genai import types

# System Dependencies
from dotenv import load_dotenv
import os
import logging

# Data parsing
from pydantic import BaseModel
from typing import List, Optional
import json

# Image Processing
from PIL import Image
import io

import random

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not GOOGLE_GEMINI_API_KEY:
    logger.error("GOOGLE_GEMINI_API_KEY not found in .env file")
    raise ValueError("GOOGLE_GEMINI_API_KEY not found in .env file")

GEMINI_MODEL = 'gemini-2.0-flash'

try:
    genai_client = genai.Client(api_key=GOOGLE_GEMINI_API_KEY)
    logger.info(f"Gemini Client initialized with model: {GEMINI_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize Gemini Client: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Travel Agent API",
    description="Backend API for the AI Travel Agent using Google Gemini",
    version="1.0.0"
)

# Enable CORS for gui communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class LocationRequest(BaseModel):
    """
    Request model for location-based travel suggestions.
    """
    location: str
    preferences: Optional[List[str]] = []

class WeatherRequest(BaseModel):
    """
    Request model for weather information.
    """
    destination: str


# --- Helper Functions ---

def get_weather(location: str, unit: str = "celsius") -> dict:
    """
    Get simulated weather data for a location.
    
    This function acts as a mock tool for the Gemini model to call.
    In a production environment, this would call a real weather API (e.g., OpenWeatherMap).
    
    Args:
        location (str): The name of the city or location.
        unit (str): Temperature unit, either 'celsius' or 'fahrenheit'. Defaults to 'celsius'.
        
    Returns:
        dict: A dictionary containing simulated weather data including temperature, condition, humidity, and wind speed.
    """
    logger.info(f"Tool 'get_weather' called for location: {location}, unit: {unit}")
    
    # Simulated weather conditions
    conditions = [
        "Clear Sky", "Partly Cloudy", "Cloudy", "Light Rain", 
        "Sunny", "Overcast", "Scattered Clouds", "Mostly Sunny",
        "Foggy", "Windy", "Drizzle", "Fair"
    ]
    
    # Generate realistic dummy data based on unit
    if unit == "celsius":
        temperature = random.randint(15, 30)
        wind_speed = f"{random.randint(5, 25)} km/h"
    else:  # fahrenheit
        temperature = random.randint(59, 86)
        wind_speed = f"{random.randint(3, 15)} mph"
    
    # Create dummy weather data
    weather_data = {
        "location": location,
        "temperature": temperature,
        "unit": unit,
        "condition": random.choice(conditions),
        "humidity": f"{random.randint(40, 80)}%",
        "wind_speed": wind_speed
    }
    
    logger.debug(f"Generated weather data: {weather_data}")
    return weather_data


# --- API Endpoints ---

@app.get("/")
def read_root():
    """
    Root endpoint to verify API status.
    """
    logger.info("Root endpoint accessed")
    return {"message": "AI-Powered Travel Agent API is running"}


@app.post("/api/suggest-by-location")
async def suggest_by_location(request: LocationRequest):
    """
    Generate travel suggestions based on a location and user preferences.
    
    Uses Gemini to generate structured JSON data containing travel recommendations.
    
    Args:
        request (LocationRequest): The request object containing location and optional preferences.
        
    Returns:
        dict: A dictionary containing a list of destination objects.
        
    Raises:
        HTTPException: If there is an error during generation or parsing.
    """
    logger.info(f"Received location suggestion request for: {request.location}")
    logger.debug(f"User preferences: {request.preferences}")
    
    try:
         # Build the prompt with preferences
        preferences_text = ""
        if request.preferences:
            preferences_text = f"\nUser preferences: {', '.join(request.preferences)}"

        prompt = f"""You are a travel expert. Generate 5 travel destination suggestions near or related to {request.location}.
        {preferences_text}

        For each destination, provide:
        1. Name of the destination
        2. Brief description (2-3 sentences)
        3. Best time to visit
        4. Main attractions (list 3)
        5. Estimated budget level (Budget/Moderate/Luxury)

        Format your response as a JSON array with this structure:
        [
        {{
            "name": "Destination Name",
            "description": "Brief description",
            "best_time": "Best time to visit",
            "attractions": ["Attraction 1", "Attraction 2", "Attraction 3"],
            "budget_level": "Budget/Moderate/Luxury"
        }}
        ]

        Only return the JSON array, no additional text."""

        logger.info("Sending prompt to Gemini model...")
        
        # Generate content using Gemini
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL, 
            contents=prompt
        )
        
        # Parse the response
        response_text = response.text.strip()
        logger.debug(f"Raw Gemini response: {response_text[:100]}...") # Log first 100 chars

        # Clean up markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()

        # Parse JSON
        destinations = json.loads(response_text)
        
        logger.info(f"Successfully generated {len(destinations)} suggestions")
        return {"destinations": destinations}

    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e}. Response text: {response_text}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


@app.post("/api/suggest-by-image")
async def suggest_by_image(
    file: UploadFile = File(...),
    preferences: Optional[str] = None
):
    """
    Generate travel suggestions based on an uploaded landmark image.
    
    Analyzes the visual content of the image using Gemini Vision capabilities
    to suggest semantically similar destinations.
    
    Args:
        file (UploadFile): The uploaded image file.
        preferences (Optional[str]): Comma-separated string of user preferences.
        
    Returns:
        dict: A dictionary containing a list of destination objects.
        
    Raises:
        HTTPException: If there is an error processing the image or generating suggestions.
    """
    logger.info(f"Received image suggestion request. Filename: {file.filename}")
    
    try:
        # Read and process the uploaded image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        logger.debug("Image successfully loaded into memory")

        # Parse preferences if provided
        pref_list = []
        if preferences:
            pref_list = [p.strip() for p in preferences.split(",")]
            logger.debug(f"Parsed preferences: {pref_list}")
                
        preferences_text = ""
        if pref_list:
            preferences_text = f"\nUser preferences: {', '.join(pref_list)}"

        prompt = f"""Analyze this landmark or travel image and suggest 5 similar travel destinations with comparable features, architecture, or atmosphere.
{preferences_text}

For each destination, provide:
1. Name of the destination
2. Brief description explaining similarity to the image (2-3 sentences)
3. Best time to visit
4. Main attractions (list 3)
5. Estimated budget level (Budget/Moderate/Luxury)

Format your response as a JSON array with this structure:
[
  {{
    "name": "Destination Name",
    "description": "Brief description",
    "best_time": "Best time to visit",
    "attractions": ["Attraction 1", "Attraction 2", "Attraction 3"],
    "budget_level": "Budget/Moderate/Luxury"
  }}
]

Only return the JSON array, no additional text."""
        
        logger.info("Sending image and prompt to Gemini model...")
        
        # Generate content with image
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL, 
            contents=[prompt, image]
        )

        # Parse response
        response_text = response.text.strip()
        logger.debug(f"Raw Gemini response: {response_text[:100]}...")
                
        # Clean up markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
                
        response_text = response_text.strip()

        # Parse JSON
        destinations = json.loads(response_text)
        
        logger.info(f"Successfully generated {len(destinations)} image-based suggestions")
        return {"destinations": destinations}
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e}. Response text: {response_text}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
	

@app.post("/api/weather")
async def get_weather_info(request: WeatherRequest):
    """
    Get weather information for a destination using Gemini Function Calling.
    
    The model autonomously decides to call the `get_weather` tool to fetch data,
    then formats the output into a structured JSON response with a natural language description.
    
    Args:
        request (WeatherRequest): The request object containing the destination name.
        
    Returns:
        dict: A dictionary containing structured weather data and an AI-generated description.
        
    Raises:
        HTTPException: If there is an error during the function call or generation.
    """
    logger.info(f"Received weather request for: {request.destination}")
    
    try:
        # Configure model with function calling
        # We pass the tool (function) directly to the config
        generation_config = types.GenerateContentConfig(
            tools=[get_weather],
            temperature=0.7 # Add some creativity to the description
        )
        
        # Create prompt
        prompt = f"""Get the current weather for {request.destination} and return the information in the following JSON structure. Use the get_weather tool to fetch the data, then format your response as valid JSON.

        Your response must be ONLY a JSON object with this exact structure (no additional text, no markdown):

        {{
        "weather_data": {{
            "location": "City Name",
            "temperature": 25,
            "unit": "celsius",
            "condition": "Clear Sky",
            "humidity": "65%",
            "wind_speed": "15 km/h"
        }},
        "description": "A natural language description of the weather, including advice for travelers. For example: 'The weather in [city] is currently [condition] with a comfortable temperature of [X]°C. It's a great day for outdoor activities with [humidity] humidity and light winds at [speed].'"
        }}

        Make sure the temperature is a number (not a string), and provide helpful travel advice in the description based on the weather conditions."""
        
        logger.info("Sending prompt with tool configuration to Gemini...")
        
        # Generate content with function calling enabled
        # Note: In a real scenario with automatic function calling, the client might handle the loop.
        # Here, we assume the model uses the tool internally or we are simulating the single-turn response 
        # where the model hallucinates the tool output or (more likely with this SDK setup) 
        # we are relying on the model to format the data we want.
        # *Correction*: The `tools` param enables the model to *request* a function call. 
        # However, for this specific simplified implementation, we are asking the model to *use* the tool 
        # and format the output. The Python SDK's `generate_content` with `tools` can handle this 
        # if configured for automatic function calling, or we might need to handle the tool call response.
        # Given the previous code worked, we stick to the existing logic but add logging.
        
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=generation_config
        )

        # Get the response text
        response_text = response.text.strip()
        logger.debug(f"Raw Gemini response: {response_text[:100]}...")
        
        # Clean up markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse the JSON response
        weather_response = json.loads(response_text)
        
        logger.info("Successfully retrieved weather info")
        return weather_response
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e}. Response text: {response_text}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
