import logging
from typing import Dict, Any, Literal, List, Set, Tuple
import re
from langgraph.graph import StateGraph, START
from langgraph.types import Command
import json

from claude_api import call_claude
from state import GodotState
from config import PROMPTS, BASIC_GODOT_TYPES

logger = logging.getLogger(__name__)

class FileProcessorNode:
    """
    Processes files and manages the file generation queue.
    Detects dependencies and adds new files to the queue when needed.
    """
    def __init__(self, name: str):
        self.name = name
        logger.info(f"FileProcessorNode initialized: {name}")
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["code_writer", "scene_setup"]]:
        pending_files = state.get("pending_files", [])
        generated_code = state.get("generated_code", {})
        processed_files = set(generated_code.keys())
        
        # Check for completed files to detect dependencies
        newest_file = None
        newest_code = None
        
        # Find the most recently completed file
        for filename, code in generated_code.items():
            if filename not in processed_files:
                newest_file = filename
                newest_code = code
                break
        
        # If we have a new file, detect dependencies
        new_dependencies = []
        if newest_file and newest_code:
            logger.info(f"Detecting dependencies in completed file: {newest_file}")
            new_dependencies = self._detect_dependencies(
                newest_file, 
                newest_code, 
                list(generated_code.keys()),
                processed_files
            )
            if new_dependencies:
                logger.info(f"Found {len(new_dependencies)} new dependencies in {newest_file}")
                pending_files.extend(new_dependencies)
        
        # Check if we have more files to process
        if pending_files:
            # Get next file to process
            next_file = pending_files[0]
            remaining_files = pending_files[1:]
            
            logger.info(f"Processing next file: {next_file['filename']}")
            
            # Update state
            return Command(
                goto="code_writer",
                update={
                    "current_file": next_file,
                    "pending_files": remaining_files
                }
            )
        else:
            # All files processed, move to scene setup
            logger.info("All files processed, moving to scene setup")
            return Command(
                goto="scene_setup"
            )

    def _detect_dependencies(self, source_file: str, code: str, existing_files: List[str], processed_files: set) -> List[Dict[str, Any]]:
        """
        Analyze generated code to detect potential dependencies on files that don't exist yet.
        
        Args:
            source_file: The file being analyzed
            code: The source code to analyze
            existing_files: List of files that are already planned or created
            processed_files: Set of filenames that have been processed already

        Returns:
            List of new file definitions that should be created
        """
        logger.info(f"Detecting dependencies in {source_file}")
        new_dependencies = []
        
        # Look for patterns that suggest dependencies on other files
        # 1. Check for class references
        class_references = re.findall(r'(?:var|const)\s+\w+\s*:\s*(\w+)', code)
        # 2. Look for extends statements
        extends_matches = re.findall(r'extends\s+(\w+)', code)
        # 3. Look for preloads and loads
        preload_matches = re.findall(r'preload\s*\(\s*["\']res://(?:scripts/)?(\w+\.gd)["\']', code)
        load_matches = re.findall(r'load\s*\(\s*["\']res://(?:scripts/)?(\w+\.gd)["\']', code)
        
        # 4. Check for instantiate calls - new pattern to look for
        instance_matches = re.findall(r'(\w+)\.new\(\)', code)
        
        # 5. Look for explicit requires comments
        requires_matches = re.findall(r'#\s*requires\s*:\s*(\w+\.gd)', code)
        
        # Create a set of potential dependencies
        potential_deps = set()
        potential_deps.update(class_references)
        potential_deps.update(extends_matches)
        potential_deps.update([m.replace('.gd', '') for m in preload_matches])
        potential_deps.update([m.replace('.gd', '') for m in load_matches])
        potential_deps.update(instance_matches)
        potential_deps.update(requires_matches)
        
        # Filter out basic Godot types and already processed files
        filtered_deps = [dep for dep in potential_deps 
                        if dep not in BASIC_GODOT_TYPES 
                        and f"{dep}.gd" not in existing_files
                        and f"{dep}.gd" not in processed_files
                        and not dep.startswith("_")]
        
        if filtered_deps:
            # For each missing dependency, create a file definition
            prompt = PROMPTS["dependency_analysis"].format(
                dependencies=', '.join(filtered_deps),
                source_file=source_file,
                code=code[:500]  # Truncate code to first 500 chars
            )
            
            # Get descriptions of the missing dependencies
            response = call_claude(prompt)
            json_match = re.search(r'\[[\s\S]*\]', response)
            
            if not json_match:
                msg = f"Failed to generate valid dependency definitions for {source_file}"
                logger.error(msg)
                raise ValueError(msg)
                
            dep_definitions = json.loads(json_match.group(0))
            logger.info(f"Created definitions for {len(dep_definitions)} new dependency files")
            
            # Filter to make sure we're only adding new files
            for def_item in dep_definitions:
                if def_item["filename"] not in existing_files and def_item["filename"] not in processed_files:
                    new_dependencies.append(def_item)
                
        return new_dependencies
