import logging
from typing import Dict, Any, Literal, List, Set, Tuple
import re
from langgraph.graph import StateGraph, START
from langgraph.types import Command
import json

from claude_api import call_claude
from state import GodotState
from config import PROMPTS, BASIC_GODOT_TYPES
from file_deduplication import FileDedupTracker

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
        
        # Get processed_files and ensure it's a set for our operations
        processed_files = state.get("processed_files", [])
        if not isinstance(processed_files, set):
            processed_files = set(processed_files)
        
        # Check for completed files to detect dependencies
        newest_file = None
        newest_code = None
        
        # Find the most recently completed file
        current_file = state.get("current_file", {})
        if current_file and current_file.get("status") == "completed":
            newest_file = current_file.get("filename")
            if newest_file and newest_file in generated_code and newest_file not in processed_files:
                newest_code = generated_code[newest_file]
        
        # If we have a new file, detect dependencies
        new_dependencies = []
        if newest_file and newest_code:
            logger.info(f"Detecting dependencies in completed file: {newest_file}")
            # Add the file to processed_files set
            processed_files.add(newest_file)
            
            new_dependencies = self._detect_dependencies(
                newest_file, 
                newest_code, 
                list(generated_code.keys()),
                processed_files,
                pending_files
            )
            if new_dependencies:
                logger.info(f"Found {len(new_dependencies)} new dependencies in {newest_file}")
                
                # Validate dependencies before adding them
                valid_dependencies = []
                for dep in new_dependencies:
                    if not dep.get("filename"):
                        logger.error(f"Skipping dependency with missing filename from {newest_file}")
                        continue
                    if dep.get("filename") == "Unnamed.gd":
                        logger.error(f"Skipping unnamed dependency from {newest_file}")
                        continue
                    valid_dependencies.append(dep)
                
                if len(valid_dependencies) != len(new_dependencies):
                    logger.warning(f"Filtered out {len(new_dependencies) - len(valid_dependencies)} invalid dependencies")
                
                pending_files.extend(valid_dependencies)
        
        # Safety check - break out of infinite loops by detecting if we've been processing for too long
        max_files_threshold = 100
        
        if len(processed_files) > max_files_threshold:
            logger.warning(f"Processed more than {max_files_threshold} files. Terminating to avoid infinite loop.")
            return Command(
                goto="scene_setup",
                update={
                    "processed_files": list(processed_files),
                    "pending_files": []
                }
            )
        
        # Emergency full reset of pending files if they contain invalid entries
        valid_pending_files = []
        for file_info in pending_files:
            if not isinstance(file_info, dict):
                continue
                
            if not file_info.get("filename"):
                continue
                
            if file_info.get("filename") == "Unnamed.gd":
                continue
                
            valid_pending_files.append(file_info)
            
        # If we fixed any files, update the pending files
        if len(valid_pending_files) != len(pending_files):
            logger.warning(f"Emergency filtering of pending files: {len(pending_files)} -> {len(valid_pending_files)}")
            pending_files = valid_pending_files
            
        # Deduplicate pending files to prevent loops
        if pending_files:
            unique_pending_files = []
            seen_filenames = set()
            
            for file_def in pending_files:
                filename = file_def.get("filename", "")
                if not filename:
                    logger.error(f"Found pending file with missing filename: {file_def}")
                    continue
                    
                norm_filename = FileDedupTracker.normalize_filename(filename)
                if norm_filename not in seen_filenames:
                    seen_filenames.add(norm_filename)
                    unique_pending_files.append(file_def)
            
            # Check if this actually deduped anything
            if len(unique_pending_files) < len(pending_files):
                logger.info(f"Deduplicated pending files from {len(pending_files)} to {len(unique_pending_files)}")
            
            pending_files = unique_pending_files
        
        # Safety check: break infinite loops by limiting the number of pending files
        # This is a guard against dependency explosion
        MAX_PENDING_FILES = 30
        if len(pending_files) > MAX_PENDING_FILES:
            logger.warning(f"Too many pending files ({len(pending_files)}), truncating to {MAX_PENDING_FILES}")
            pending_files = pending_files[:MAX_PENDING_FILES]
        
        # Process pending files
        if pending_files:
            # We need to find the next valid file to process
            valid_file = None
            remaining_files = []
            
            # Look for a valid file in the pending list
            for idx, file_info in enumerate(pending_files):
                # Skip invalid entries
                if not isinstance(file_info, dict):
                    logger.error(f"Skipping invalid file entry that is not a dict: {file_info}")
                    continue
                    
                filename = file_info.get("filename", "")
                if not filename:
                    logger.error(f"Skipping file with missing filename: {file_info}")
                    continue
                
                if filename == "Unnamed.gd":
                    logger.error("Skipping unnamed file")
                    continue
                    
                # Check if this file is already processed
                if FileDedupTracker.is_duplicate_file(filename, list(generated_code.keys()), [], processed_files):
                    logger.warning(f"Skipping already processed file: {filename}")
                    continue
                    
                # Found a valid file!
                valid_file = file_info
                remaining_files = pending_files[:idx] + pending_files[idx+1:]
                break
                
            # If we found a valid file, process it
            if valid_file:
                logger.info(f"Processing next file: {valid_file['filename']}")
                
                # Update state and go to code writer
                return Command(
                    goto="code_writer",
                    update={
                        "current_file": valid_file,
                        "pending_files": remaining_files,
                        "processed_files": list(processed_files)
                    }
                )
            else:
                # No valid files found, go to scene setup
                logger.warning("No valid files found in pending files, moving to scene setup")
                return Command(
                    goto="scene_setup",
                    update={
                        "processed_files": list(processed_files),
                        "pending_files": []
                    }
                )
        else:
            # All files processed, move to scene setup
            logger.info("All files processed, moving to scene setup")
            return Command(
                goto="scene_setup",
                update={
                    "processed_files": list(processed_files),
                    "pending_files": []
                }
            )

    def _detect_dependencies(self, source_file: str, code: str, existing_files: List[str], 
                          processed_files: set, pending_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze generated code to detect potential dependencies on files that don't exist yet.
        
        Args:
            source_file: The file being analyzed
            code: The source code to analyze
            existing_files: List of files that are already planned or created
            processed_files: Set of filenames that have been processed already
            pending_files: List of files pending processing

        Returns:
            List of new file definitions that should be created
        """
        # Safety check on inputs
        if not source_file or not code:
            logger.warning("Missing required inputs for dependency detection")
            return []
            
        logger.info(f"Detecting dependencies in {source_file}")
        new_dependencies = []
        
        try:
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
            potential_deps.update([m.replace('.gd', '') for m in requires_matches])
            
            # Filter out basic Godot types and already processed files
            filtered_deps = []
            for dep in potential_deps:
                dep_filename = f"{dep}.gd"
                if not dep.startswith("_") and not dep in BASIC_GODOT_TYPES:
                    # Use the deduplication helper
                    if not FileDedupTracker.is_duplicate_file(dep_filename, existing_files, pending_files, processed_files):
                        filtered_deps.append(dep)
            
            # Limit number of dependencies to prevent explosion
            MAX_DEPENDENCIES = 3
            if len(filtered_deps) > MAX_DEPENDENCIES:
                logger.warning(f"Too many dependencies detected ({len(filtered_deps)}), limiting to {MAX_DEPENDENCIES}")
                filtered_deps = filtered_deps[:MAX_DEPENDENCIES]
            
            if filtered_deps:
                # For each missing dependency, create a file definition
                prompt = PROMPTS["dependency_analysis"].format(
                    dependencies=', '.join(filtered_deps),
                    source_file=source_file,
                    code=code[:500]  # Truncate code to first 500 chars
                )
                
                try:
                    # Get descriptions of the missing dependencies
                    response = call_claude(prompt)
                    json_match = re.search(r'\[[\s\S]*\]', response)
                    
                    if not json_match:
                        logger.error(f"Failed to generate valid dependency definitions for {source_file}")
                        return []
                        
                    dep_definitions = json.loads(json_match.group(0))
                    
                    # Validate dependency definitions before returning
                    validated_deps = []
                    for dep in dep_definitions:
                        if not isinstance(dep, dict):
                            logger.error(f"Skipping non-dict dependency: {dep}")
                            continue
                            
                        if not dep.get("filename"):
                            logger.error(f"Skipping dependency with missing filename from {source_file}")
                            continue
                            
                        if dep.get("filename") == "Unnamed.gd":
                            logger.error(f"Skipping unnamed dependency from {source_file}")
                            continue
                            
                        validated_deps.append(dep)
                        
                    logger.info(f"Created definitions for {len(validated_deps)} new dependency files")
                    
                    # Filter to make sure we're only adding new files using our deduplication helper
                    new_dependencies = FileDedupTracker.deduplicate_dependencies(
                        validated_deps, existing_files, pending_files, processed_files
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse dependency JSON: {e}")
                    return []
        except Exception as e:
            logger.error(f"Error in dependency detection: {str(e)}")
            return []
                
        return new_dependencies
