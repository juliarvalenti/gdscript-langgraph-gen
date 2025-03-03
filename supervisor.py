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
        
        # First file to process
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
                    "detailed_reviews": {}
                },
                goto="code_writer"
            )
        else:
            # No files to generate
            logger.warning("No files to generate!")
            return Command(
                update={
                    "generated_code": {},
                    "review_status": {},
                    "detailed_reviews": {}
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
      except json.JSONDecodeError as e:
          logger.error(f"JSON decoding error: {e}")
          raise

      logger.info(f"Successfully planned {len(planned_files)} files with Claude")
      return planned_files

