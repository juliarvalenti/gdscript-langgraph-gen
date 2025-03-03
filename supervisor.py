import logging
from typing import Dict, Any, List, Literal
import re
import json
from langgraph.types import Command

from claude_api import call_claude
from state import GodotState
from config import PROMPTS

logger = logging.getLogger(__name__)

class SupervisorNode:
    """
    Manages the entire code generation workflow with iterative refinement.
    """

    def __init__(self, name: str, max_iterations: int = 3):
        self.name = name  # Just store the name directly, no super() call needed
        self.max_iterations = max_iterations
        logger.info(f"SupervisorNode initialized with max_iterations={max_iterations}")
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["code_writer", "scene_setup"]]:
        instructions = state.get("instructions")
        if not instructions:
            msg = "No instructions found for SupervisorNode."
            logger.error(msg)
            raise ValueError(msg)

        # Dynamically plan files to generate based on game premise
        game_premise = instructions.get("game_premise", "")
        logger.info(f"Planning necessary files based on game premise: {game_premise[:50]}...")
        files_to_generate = self._plan_necessary_files(game_premise, instructions)
        logger.info(f"Initial plan: {len(files_to_generate)} files to generate")
        
        # If we already have generated code, we're in a subsequent iteration
        if state.get("generated_code"):
            # We have some code already, send to scene setup
            logger.info(f"Code generation complete with {len(state['generated_code'])} files")
            return Command(goto="scene_setup")
        
        # First file to process - ensure we have valid files with filenames
        if files_to_generate:
            validated_files = []
            for file_def in files_to_generate:
                if not file_def.get("filename"):
                    logger.error(f"Skipping file with missing filename: {file_def}")
                    continue
                if file_def.get("filename") == "Unnamed.gd":
                    logger.error(f"Skipping unnamed file in initial plan: {file_def}")
                    continue
                validated_files.append(file_def)
                
            if len(validated_files) < len(files_to_generate):
                logger.warning(f"Filtered out {len(files_to_generate) - len(validated_files)} invalid files from initial plan")
                
            files_to_generate = validated_files
            
            if files_to_generate:
                first_file = files_to_generate[0]
                logger.info(f"Starting code generation with file: {first_file['filename']}")
                
                # Set current file and file list for the code writer node
                return Command(
                    update={
                        "current_file": first_file,
                        "pending_files": files_to_generate[1:],
                        "generated_code": {},
                        "review_status": {},
                        "detailed_reviews": {},
                        "processed_files": []
                    },
                    goto="code_writer"
                )
            else:
                logger.warning("No valid files to generate after filtering!")
                # No valid files to generate
                return Command(
                    update={
                        "generated_code": {},
                        "review_status": {},
                        "detailed_reviews": {},
                        "processed_files": []
                    },
                    goto="scene_setup"
                )
        else:
            # No files to generate
            logger.warning("No files to generate!")
            return Command(
                update={
                    "generated_code": {},
                    "review_status": {},
                    "detailed_reviews": {},
                    "processed_files": []
                },
                goto="scene_setup"
            )

    
    def _plan_necessary_files(self, game_premise: str, instructions: Dict[str, Any]) -> List[Dict[str, Any]]:
      """Dynamically determine which files to generate based on game premise."""
      logger.info("Creating dynamic file plan for game")
      
      logger.info(PROMPTS["file_planning"])

      # Build a prompt to ask Claude about necessary files
      prompt = PROMPTS["file_planning"].format(game_premise=game_premise)

      # Call Claude to get file planning
      response = call_claude(prompt)

      # DEBUG: Log full response
      logger.info(f"Raw Claude response:\n{response}")

      # Extract JSON from response
      json_match = re.search(r'\[[\s\S]*\]', response)
      if not json_match:
          msg = "Failed to extract valid JSON from Claude's file planning response"
          logger.error(msg)
          raise ValueError(msg)

      json_text = json_match.group(0)

      # DEBUG: Log extracted JSON
      logger.info(f"Extracted JSON:\n{json_text}")

      try:
          planned_files = json.loads(json_text)
          
          # Validate the planned files to ensure they have filenames
          valid_files = []
          for file in planned_files:
              if not isinstance(file, dict):
                  logger.error(f"Skipping non-dict file entry: {file}")
                  continue
                  
              if not file.get("filename"):
                  logger.error(f"File is missing filename: {file}")
                  continue
                  
              if file.get("filename") == "Unnamed.gd":
                  logger.error(f"Found unnamed file in plan: {file}")
                  continue
                  
              valid_files.append(file)
          
          if len(valid_files) < len(planned_files):
              logger.warning(f"Filtered out {len(planned_files) - len(valid_files)} invalid files from plan")
          
          # Limit the number of initial files to prevent explosion
          MAX_INITIAL_FILES = 25
          if len(valid_files) > MAX_INITIAL_FILES:
              logger.warning(f"Too many initial files ({len(valid_files)}), limiting to {MAX_INITIAL_FILES}")
              valid_files = valid_files[:MAX_INITIAL_FILES]
          
          logger.info(f"Successfully planned {len(valid_files)} files with Claude")
          return valid_files
          
      except json.JSONDecodeError as e:
          logger.error(f"JSON decoding error: {e}")
          raise

