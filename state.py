from typing import Dict, Any, List, Optional, Union, Set
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
import operator
from functools import reduce

# Define reducer functions
def last_value_reducer(current_val, new_val):
    """Reducer that keeps the last value."""
    return new_val

def dict_merge_reducer(current_dict, new_dict):
    """Reducer that merges dictionary values."""
    if current_dict is None:
        return new_dict
    if new_dict is None:
        return current_dict
    result = current_dict.copy()
    result.update(new_dict)
    return result

def list_extend_reducer(current_list, new_list):
    """Reducer that extends lists."""
    if current_list is None:
        return new_list
    if new_list is None:
        return current_list
    return current_list + new_list

class GodotState(TypedDict, total=False):
    """TypedDict defining the state for the Godot code generation graph."""
    # Input instructions
    instructions: Dict[str, Any]
    
    # Current file being processed - using last_value_reducer for handling concurrent updates
    current_file: Annotated[Optional[Dict[str, Any]], last_value_reducer]
    
    # Files waiting to be processed - use list extension for concurrent additions
    pending_files: Annotated[List[Dict[str, Any]], list_extend_reducer]
    
    # Collection of generated code - merge dictionaries for concurrent updates
    generated_code: Annotated[Dict[str, str], dict_merge_reducer]
    
    # Status of file reviews - merge dictionaries for concurrent reviews
    review_status: Annotated[Dict[str, str], dict_merge_reducer]
    
    # Detailed review feedback - merge dictionaries for concurrent reviews
    detailed_reviews: Annotated[Dict[str, Dict[str, Any]], dict_merge_reducer]
    
    # Scene setup guides
    scene_guide: Annotated[str, last_value_reducer]
    
    # Report
    final_report: Annotated[str, last_value_reducer]
    
    # Log messages - extend list for multiple log entries
    messages: Annotated[List[str], list_extend_reducer]
    
    # Track processed files
    processed_files: Union[List[str], Set[str]]
