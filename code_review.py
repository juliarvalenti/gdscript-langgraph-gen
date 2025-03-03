import logging
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command

from state import GodotState
from claude_api import call_claude
from config import PROMPTS

logger = logging.getLogger(__name__)

class CodeReviewNode:
    """
    Uses Claude LLM to review code for issues and provide feedback.
    Acts as a "smart" reviewer rather than using fixed validation rules.
    """
    def __init__(self, name: str, max_iterations: int = 1):
        self.name = name
        self.max_iterations = max_iterations  # Store max iterations as instance variable
        logger.info(f"CodeReviewNode initialized: {name} with max {max_iterations} revision(s)")
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["code_writer", "file_processor"]]:
        current_file = state.get("current_file", {})
        instructions = state.get("instructions", {})
        
        if not current_file:
            logger.error("No current file to review in CodeReviewNode")
            return Command(goto="file_processor", update={})

        code_text = current_file.get("code", "")
        filename = current_file.get("filename", "")
        purpose = current_file.get("purpose", "")
        iteration = current_file.get("iteration", 1)
        
        logger.info(f"Reviewing {filename} (iteration {iteration})")
        
        # Get existing collections or create new ones
        generated_code = state.get("generated_code", {})
        review_status = state.get("review_status", {})
        detailed_reviews = state.get("detailed_reviews", {})
        
        # Get processed_files and ensure it's a set for operations (but store as list)
        processed_files = state.get("processed_files", [])
        if not isinstance(processed_files, set):
            processed_files = set(processed_files)
        
        # Only do a full LLM review if we haven't reached max iterations
        if iteration < self.max_iterations:
            # Have Claude evaluate the code
            review_prompt = self._build_review_prompt(filename, code_text, purpose, instructions.get("game_premise", ""))
            feedback = call_claude(review_prompt)
            
            logger.info(f"Received feedback on {filename} from Claude")
            
            # Simply check if feedback indicates any issues by its length
            if len(feedback.strip()) > 30:  # Assume non-trivial feedback means issues found
                logger.info(f"LLM provided feedback for {filename}, sending for revision")
                
                # Update for another attempt, passing the raw feedback
                return Command(
                    goto="code_writer",
                    update={
                        "current_file": {
                            **current_file,
                            "iteration": iteration + 1,
                            "previous_code": code_text,
                            "feedback": feedback
                        }
                    }
                )
        
        # If no issues found or we've reached max iterations, proceed
        logger.info(f"Code for {filename} approved or max iterations reached")
        review_message = "Code meets requirements." if iteration == 1 else f"Completed after {iteration} iteration(s)."
        review_status[filename] = "Approved"
        
        # Store the code and reviews
        generated_code[filename] = code_text
        detailed_reviews[filename] = {
            "feedback": review_message,
            "issues": []
        }
        
        # Convert processed_files back to a list for state storage
        return Command(
            goto="file_processor",
            update={
                "generated_code": generated_code,
                "review_status": review_status,
                "detailed_reviews": detailed_reviews,
                "current_file": {"status": "completed", "filename": filename},
                "processed_files": list(processed_files)  # Ensure it's stored as a list
            }
        )
    
    def _build_review_prompt(self, filename: str, code: str, purpose: str, game_premise: str) -> str:
        """Build a prompt for the LLM to review the code."""
        return PROMPTS["code_review"].format(
            filename=filename,
            code=code,
            purpose=purpose,
        )
