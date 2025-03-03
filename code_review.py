import logging
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command
import re

from state import GodotState
from config import CODE_VALIDATION_RULES, MAX_ITERATIONS_PER_FILE

logger = logging.getLogger(__name__)

class CodeReviewNode:
    """
    Reviews the code output for errors, style issues, or alignment with instructions.
    """
    def __init__(self, name: str):
        self.name = name
        logger.info(f"CodeReviewNode initialized: {name}")
        
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
        iteration = current_file.get("iteration", 1)
        max_iterations = MAX_ITERATIONS_PER_FILE
        
        logger.info(f"Reviewing {filename} (iteration {iteration})")
        
        # Run multiple validation checks
        validation_results = self._validate_gdscript(code_text, filename, instructions)
        
        # Get existing collections or create new ones
        generated_code = state.get("generated_code", {})
        review_status = state.get("review_status", {})
        detailed_reviews = state.get("detailed_reviews", {})
        
        if validation_results["issues"] and iteration < max_iterations:
            logger.info(f"Found {len(validation_results['issues'])} issues in {filename}: {validation_results['issues']}")
            feedback = "Please address the following issues:\n\n" + "\n".join(validation_results["issues"])
            
            # Update for next iteration
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
        else:
            # Either approved or max iterations reached
            if not validation_results["issues"]:
                logger.info(f"Code for {filename} approved with no issues")
                review_message = "Code meets all requirements and follows best practices."
                review_status[filename] = "Approved"
            else:
                logger.warning(f"Code for {filename} not fully approved after {iteration} iterations")
                review_message = f"Not fully approved after {iteration} iterations, but proceeding."
                review_status[filename] = f"Not fully approved (iteration {iteration})"
            
            # Store the code and reviews
            generated_code[filename] = code_text
            detailed_reviews[filename] = {
                "feedback": review_message,
                "issues": validation_results["issues"]
            }
            
            # Move to the next file processor
            return Command(
                goto="file_processor",
                update={
                    "generated_code": generated_code,
                    "review_status": review_status,
                    "detailed_reviews": detailed_reviews,
                    "current_file": None  # Clear current file since we're done with it
                }
            )
    
    def _validate_gdscript(self, code: str, filename: str, instructions: Dict[str, Any]) -> Dict:
        """Perform multiple validation checks on the GDScript code."""
        issues = []
        
        rules = CODE_VALIDATION_RULES
        
        # Check 1: Basic syntax requirements
        if rules["require_extends"] and "extends" not in code:
            issues.append("Missing 'extends' statement. All GDScript files should extend a base class.")
        
        # Check 2: Verify static typing if required
        if rules["enforce_static_typing"] and instructions.get("coding_best_practices", {}).get("static_typing", False):
            # Look for variable declarations without type hints
            var_declarations = re.findall(r'var\s+(\w+)(?!\s*:\s*\w+)', code)
            if var_declarations:
                issues.append(f"Missing type hints for variables: {', '.join(var_declarations)}")

            # Check function parameters too
            func_params = re.findall(r'func\s+\w+\((.*?)\)', code)
            for params in func_params:
                if params.strip() and not all(":" in param for param in params.split(",") if param.strip()):
                    issues.append(f"Missing type hints for some function parameters")
        
        # Check 3: Check for class_name if this is meant to be a reusable script
        if rules["require_class_name_for_reusable"] and filename not in ["Main.gd", "GameManager.gd"] and "class_name" not in code:
            issues.append("Consider adding a class_name for reusable scripts.")
        
        # Check 4: Check for comments/documentation
        if rules["min_comments_ratio"] > 0 and code.count("#") < rules["min_comments_ratio"] and len(code.splitlines()) > 10:
            issues.append("Insufficient comments for code complexity. Add more documentation.")
        
        # Check 5: Check for signal definitions in complex scripts
        if rules["require_signals_for_complex"] and len(code.splitlines()) > 15 and "signal" not in code:
            issues.append("Consider using signals for communication in this complex script.")
        
        # Check 6: Verify proper indentation
        if rules["check_indentation"] and ("\t " in code or "  \t" in code):
            issues.append("Inconsistent indentation. Use either tabs or spaces, not both.")
        
        # Check 7: Make sure there are no placeholders or TODOs left
        if rules["no_todos"] and ("TODO" in code or "PLACEHOLDER" in code):
            issues.append("Code contains TODO or PLACEHOLDER comments that should be resolved.")
            
        # Check 8: Verify _ready function exists in node scripts
        if any(base in filename for base in rules["require_ready_function"]) and "_ready" not in code:
            issues.append("Missing _ready() function which is typically needed for node initialization.")
            
        # Check 9: Check for error handling in critical operations
        if rules["require_error_handling"] and ("load(" in code or "preload(" in code) and not any(x in code for x in ["if not", "try", "assert"]):
            issues.append("Resource loading without error checking detected. Add error handling for resource loading.")
            
        return {
            "issues": issues,
            "filename": filename
        }
