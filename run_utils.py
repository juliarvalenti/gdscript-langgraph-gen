import os
import uuid
import json
import datetime
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_run_id() -> str:
    """Generate a unique run ID with timestamp prefix"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"

def create_run_folder(run_id: str, base_dir: str = "runs") -> str:
    """Create a folder for the current run"""
    run_folder = os.path.join(base_dir, run_id)
    os.makedirs(run_folder, exist_ok=True)
    logger.info(f"Created run folder: {run_folder}")
    return run_folder

def save_state_snapshot(state: Dict[str, Any], run_folder: str, step_name: str) -> None:
    """Save a snapshot of the current state after a step execution"""
    try:
        # Create a JSON-serializable version of the state
        serializable_state = prepare_state_for_serialization(state)
        
        # Save to a JSON file
        filename = os.path.join(run_folder, f"{step_name}_state.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved state snapshot after step {step_name}")
    except Exception as e:
        logger.error(f"Failed to save state snapshot: {str(e)}")

def prepare_state_for_serialization(state: Dict[str, Any]) -> Dict[str, Any]:
    """Convert state to a JSON-serializable format"""
    serializable = {}
    
    # Process each key in the state dictionary
    for key, value in state.items():
        # Skip special keys that might cause issues
        if key in ["_graph_runner"]:
            continue
            
        try:
            # Test JSON serializability
            json.dumps(value)
            serializable[key] = value
        except (TypeError, OverflowError):
            # If not JSON serializable, convert to string representation
            if isinstance(value, dict):
                # Recursively process dictionaries
                serializable[key] = prepare_state_for_serialization(value)
            else:
                # Convert other non-serializable objects to string
                serializable[key] = str(value)
    
    return serializable

def save_node_io(run_folder: str, node_name: str, inputs: Any, outputs: Any) -> None:
    """Save the inputs and outputs of a node execution"""
    try:
        node_dir = os.path.join(run_folder, "node_io", node_name)
        os.makedirs(node_dir, exist_ok=True)
        
        # Save inputs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(os.path.join(node_dir, f"{timestamp}_input.json"), "w", encoding="utf-8") as f:
            json.dump(prepare_state_for_serialization(inputs), f, indent=2, ensure_ascii=False)
            
        # Save outputs
        with open(os.path.join(node_dir, f"{timestamp}_output.json"), "w", encoding="utf-8") as f:
            json.dump(prepare_state_for_serialization(outputs), f, indent=2, ensure_ascii=False)
            
        logger.debug(f"Saved I/O for node {node_name}")
    except Exception as e:
        logger.error(f"Failed to save node I/O: {str(e)}")

def save_final_state(state: Dict[str, Any], run_folder: str, status: str = "complete") -> None:
    """Save the final state of the run"""
    try:
        # Save the complete final state
        serializable_state = prepare_state_for_serialization(state)
        
        with open(os.path.join(run_folder, f"final_state_{status}.json"), "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, indent=2, ensure_ascii=False)
        
        # Save a run summary with key information
        summary = {
            "status": status,
            "timestamp": datetime.datetime.now().isoformat(),
            "file_count": len(state.get("generated_code", {})),
            "run_id": os.path.basename(run_folder)
        }
        
        with open(os.path.join(run_folder, "run_summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Saved final state with status: {status}")
    except Exception as e:
        logger.error(f"Failed to save final state: {str(e)}")
