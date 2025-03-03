import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command
from claude_api import call_claude
import re

from state import GodotState
from config import PROMPTS, GODOT_VERSION

logger = logging.getLogger(__name__)

class CodeWriterNode:
    """
    Interacts with Claude 3.7 to produce GDScript files.
    """
    def __init__(self, name: str):
        self.name = name
        logger.info(f"CodeWriterNode initialized: {name}")
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["code_review"]]:
        instructions = state.get("instructions", {})
        current_file = state.get("current_file", {})
        
        if not current_file:
            logger.error("No current file to process in CodeWriterNode")
            return Command(goto="code_review", update={})
        
        filename = current_file.get("filename", "Unnamed.gd")
        purpose = current_file.get("purpose", "")
        iteration = current_file.get("iteration", 1)
        previous_code = current_file.get("previous_code", "")
        feedback = current_file.get("feedback", "")
        
        logger.info(f"Generating code for {filename}, iteration {iteration}")
        
        # Build a prompt based on whether this is the first iteration or a revision
        if iteration == 1:
            prompt = self._build_initial_prompt(instructions, filename, purpose, current_file.get("details", {}))
            logger.info(f"Created initial prompt for {filename}")
        else:
            prompt = self._build_revision_prompt(instructions, filename, purpose, previous_code, feedback)
            logger.info(f"Created revision prompt for {filename} (iteration {iteration})")
            
        # Call Claude API through our helper
        logger.info(f"Calling Claude API for {filename}")
        response = call_claude(prompt)
        logger.info(f"Received response from Claude for {filename} ({len(response)} chars)")
        
        # Extract code from Claude's response
        code = self._extract_code_from_response(response)
        logger.info(f"Extracted {len(code)} chars of GDScript code for {filename}")
        
        # Update state with generated code
        return Command(
            goto="code_review",
            update={
                "current_file": {
                    "filename": filename,
                    "code": code,
                    "iteration": iteration,
                    **{k: v for k, v in current_file.items() if k not in ["filename", "code", "iteration"]}
                }
            }
        )
    
    def _build_initial_prompt(self, instructions, filename, purpose, details):
        game_premise = instructions.get("game_premise", "")
        
        # Include details if available
        details_section = ""
        if details:
            details_section = "Additional details:\n"
            for key, value in details.items():
                details_section += f"- {key}: {value}\n"
        
        return PROMPTS["code_writer_initial"].format(
            game_premise=game_premise,
            filename=filename,
            purpose=purpose,
            details_section=details_section,
            godot_version=GODOT_VERSION
        )
    
    def _build_revision_prompt(self, instructions, filename, purpose, previous_code, feedback):
        return PROMPTS["code_writer_revision"].format(
            filename=filename,
            purpose=purpose,
            previous_code=previous_code,
            feedback=feedback
        )
        
    def _extract_code_from_response(self, response):
        """Extract code from Claude's response, handling potential formatting variations."""
        # First, try to find code between gdscript code blocks
        code_pattern = r"```(?:gdscript)?\s*([\s\S]*?)```"
        match = re.search(code_pattern, response)
        
        if (match):
            # Return the code found within code blocks
            return match.group(1).strip()
        else:
            # If no code blocks found, assume the entire response is code (with potential cleanup)
            cleaned_response = response.replace("```", "").strip()
            return cleaned_response
