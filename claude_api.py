import os
import requests
import json
import logging
from typing import Dict, Any, Optional
from time import sleep
import re

from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS

logger = logging.getLogger(__name__)

# Load from .env
from dotenv import load_dotenv
load_dotenv()

# Try to import Anthropic's library if available
try:
    import anthropic
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except ImportError:
    logger.warning("Anthropic library not found. Using mock responses.")
    client = None

def call_claude(prompt: str, model: str = CLAUDE_MODEL, max_tokens: int = CLAUDE_MAX_TOKENS) -> str:
    """
    Calls the Claude API with the given prompt.
    
    Args:
        prompt: The prompt to send to Claude
        model: The model name to use
        max_tokens: Maximum tokens to generate
        
    Returns:
        Claude's response as a string
    """
    logger.info(f"Calling Claude API with prompt of length {len(prompt)}")
    
    if not client:
        logger.warning("No Anthropic client available. Using mock response.")
        return _generate_mock_response(prompt)
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response = message.content[0].text
        logger.info(f"Received response from Claude ({len(response)} chars)")
        return response
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        return f"Error: {str(e)}"

def _generate_mock_response(prompt: str) -> str:
    """
    Generate a mock response when Claude API is not available.
    This is a simple implementation that just returns placeholder GDScript.
    
    Args:
        prompt: The original prompt that would have been sent to Claude
        
    Returns:
        A mock response with basic GDScript code
    """
    logger.warning("Using mock response - NO REAL CLAUDE API IS BEING CALLED")
    
    # Extract filename from the prompt if possible
    filename_match = re.search(r'GDScript file named [\'"]([^\'"]+)[\'"]', prompt)
    filename = filename_match.group(1) if filename_match else "Unknown.gd"
    
    # Create a very basic GDScript file based on the filename
    class_name = filename.replace(".gd", "").capitalize()
    
    mock_script = f"""
extends Node

class_name {class_name}

# This is a mock script created when Claude API was unavailable
# You should replace this with actual implementation

var name: String = "{class_name}"
var active: bool = true

func _ready() -> void:
    print("{class_name} initialized")
    
func get_name() -> String:
    return name
    
func is_active() -> bool:
    return active
    
func set_active(value: bool) -> void:
    active = value
    
# NOTE: This is a mock implementation - please implement real functionality
"""
    return mock_script