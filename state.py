from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.channels.last_value import LastValue  # Fixed import path

class GodotState(TypedDict, total=False):
    """TypedDict defining the state for the Godot code generation graph."""
    # Input instructions
    instructions: Dict[str, Any]
    
    # Current file being processed - using LastValue reducer to handle concurrent updates
    current_file: Annotated[Optional[Dict[str, Any]], LastValue[Dict[str, Any]]]
    
    # Files waiting to be processed
    pending_files: List[Dict[str, Any]]
    
    # Collection of generated code
    generated_code: Dict[str, str]
    
    # Status of file reviews
    review_status: Dict[str, str]
    
    # Detailed review feedback
    detailed_reviews: Dict[str, Dict[str, Any]]
    
    # Scene setup guides
    scene_guide: str
    
    # Report
    final_report: str
    
    # Log messages
    messages: List[str]
