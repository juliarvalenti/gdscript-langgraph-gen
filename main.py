import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.channels.last_value import LastValue  # Fixed import path

# Import our nodes
from instruction import InstructionNode
from supervisor import SupervisorNode
from scene_setup import SceneSetupNode
from final_report import FinalReportNode
from code_writer import CodeWriterNode
from code_review import CodeReviewNode
from file_processor import FileProcessorNode
from state import GodotState
from config import CORE_GAME_DESCRIPTION
from run_utils import (
    generate_run_id, 
    create_run_folder, 
    save_state_snapshot, 
    save_node_io,
    save_final_state
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gdscript_generator.log")
    ]
)
logger = logging.getLogger(__name__)

def build_graph():
    logger.info("Building LangGraph for Godot prototype generation")
    
    # Initialize the StateGraph with our state definition
    graph = StateGraph(GodotState)
    
    # Create our nodes
    instruction_node = InstructionNode("instruction")
    supervisor_node = SupervisorNode("supervisor", max_iterations=3)
    code_writer_node = CodeWriterNode("code_writer")
    code_review_node = CodeReviewNode("code_review", max_iterations=1)  # Explicitly set to 1 revision
    file_processor_node = FileProcessorNode("file_processor")
    scene_setup_node = SceneSetupNode("scene_setup")
    final_report_node = FinalReportNode("final_report_node")
    
    # Add the nodes to the graph
    graph.add_node("instruction", instruction_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("code_writer", code_writer_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("file_processor", file_processor_node)
    graph.add_node("scene_setup", scene_setup_node)
    graph.add_node("final_report_node", final_report_node)
    
    # Define all edges in the graph to make the flow explicit and debuggable
    # Main Pipeline Flow
    graph.add_edge(START, "instruction")
    graph.add_edge("instruction", "supervisor")
    
    # Code generation flow
    graph.add_edge("supervisor", "code_writer")
    graph.add_edge("code_writer", "code_review")
    
    # Conditional flows from code review
    graph.add_conditional_edges(
        "code_review",
        # Function to route based on code review result
        # Fixed to handle None values properly
        lambda state: "code_writer" if state.get("review_status", {}).get(
            state.get("current_file", {}).get("filename", "") if state.get("current_file") else ""
        ) == "needs_revision" else "file_processor"
    )
    
    # File processor conditional edges
    graph.add_conditional_edges(
        "file_processor",
        # Function to route based on whether there are pending files
        lambda state: "code_writer" if state.get("pending_files") 
            else "scene_setup"
    )
    
    # Supervisor can also go directly to scene setup if no files to generate
    graph.add_conditional_edges(
        "supervisor",
        # Function to determine if we should skip code generation
        lambda state: "scene_setup" if not state.get("pending_files", []) 
            and not state.get("current_file") 
            else "code_writer"
    )
    
    # Final stages
    graph.add_edge("scene_setup", "final_report_node")
    graph.add_edge("final_report_node", END)
    
    logger.info("Graph built successfully with all nodes and connections")
    return graph.compile()


def save_generated_code(code_dict, run_folder, output_subdir="generated_code"):
    """Save generated code files to disk."""
    output_dir = os.path.join(run_folder, output_subdir)
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, code in code_dict.items():
        file_path = os.path.join(output_dir, filename)
        logger.info(f"Saving file: {file_path}")
        # Ensure the directory exists for the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
    
    logger.info(f"Saved {len(code_dict)} files to {output_dir}/")
    return output_dir


if __name__ == "__main__":
    # Generate a unique run ID and create a folder for this run
    run_id = generate_run_id()
    run_folder = create_run_folder(run_id)
    logger.info(f"Starting Godot prototype generation process with run ID: {run_id}")
    
    try:
        graph = build_graph()
        
        # Get user input for game concepts
        game_description = CORE_GAME_DESCRIPTION
        logger.info(f"Received game description: {game_description[:50]}...")
        
        # Initialize state with user input and empty messages list
        initial_state = {
            "instructions": {"game_premise": game_description},
            "messages": [],  # Required for add_messages
            "run_id": run_id,
            "run_folder": run_folder
        }
        
        # Save the initial state
        save_state_snapshot(initial_state, run_folder, "initial")
        
        # Stream the graph execution to see progress
        logger.info("Running generation graph...")
        result = None
        last_state = initial_state
        for step in graph.stream(initial_state, debug=True):
            # Get current node name
            current_node = list(step.keys())[0] if step and END not in step else "END"
            logger.info(f"Executing node: {current_node}")
            
            if current_node != "END":
                # Save the state after each step
                save_state_snapshot(step[current_node], run_folder, current_node)
                
                # Store I/O information for each node
                if last_state != initial_state:
                    save_node_io(run_folder, current_node, last_state, step[current_node])
                
                last_state = step[current_node]
            
            result = step
        
        if result:
            # Get the final report from the result
            final_output = result.get("final_report", {}).get("final_report", "No report found.")
            logger.info("Generation complete!")
            print("\nGeneration complete! Summary of results:")
            print("----------------------------------------")
            
            generated_code = {}
            for key, value in result.items():
                if isinstance(value, dict) and "generated_code" in value:
                    generated_code = value["generated_code"]
                    break
                    
            print(f"Generated {len(generated_code)} GDScript files")
            
            # Save the final state
            save_final_state(last_state, run_folder, "complete")
            
            # Save results to files
            report_path = os.path.join(run_folder, "godot_prototype_report.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(final_output)
            
            # Save the actual code files to the run folder
            output_dir = save_generated_code(generated_code, run_folder)
            
            print(f"\nRun ID: {run_id}")
            print(f"Run data saved to: {run_folder}")
            print(f"Report saved to: {report_path}")
            print(f"Generated code files saved to: {output_dir}")
            logger.info("Process completed successfully")
        else:
            logger.error("Generation failed - no result returned")
            save_final_state(last_state, run_folder, "failed")
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        print(f"\nError occurred: {str(e)}")
        print(f"Run data up to failure saved in: {run_folder}")
        traceback.print_exc()
        
        # Save the state at the time of failure
        if 'last_state' in locals():
            save_final_state(last_state, run_folder, "error")
