import logging
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from instruction import InstructionNode
from code_writer import CodeWriterNode
from code_review import CodeReviewNode
from supervisor import SupervisorNode
from scene_setup import SceneSetupNode
from final_report import FinalReportNode
from file_processor import FileProcessorNode
from state import GodotState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample game instructions
sample_instructions = {
    "game_premise": "A strategy game blending Factorio and Nexus Wars mechanics.",
    "coding_best_practices": {
        "static_typing": True,
        "use_folders": {
            "scripts": "res://scripts/",
            "scenes": "res://scenes/",
            "resources": "res://resources/",
            "autoload": "res://autoload/"
        },
        "godot_version": "Godot 4.x"
    }
}

def test_instruction_node():
    logger.info("Testing InstructionNode...")
    node = InstructionNode("InstructionNode")
    state = {"instructions": {"game_premise": sample_instructions["game_premise"]}, "messages": []}
    result = node.invoke(state)
    logger.info(f"InstructionNode Output: {result}")
    return result

def test_code_writer():
    logger.info("Testing CodeWriterNode...")
    node = CodeWriterNode("CodeWriter")
    state = {
        "instructions": sample_instructions,
        "current_file": {
            "filename": "GameManager.gd",
            "purpose": "Handles game state.",
            "iteration": 1
        },
        "messages": []
    }
    result = node.invoke(state)
    logger.info(f"CodeWriterNode Output: {result}")
    return result

def test_code_review():
    logger.info("Testing CodeReviewNode...")
    node = CodeReviewNode("CodeReviewer")
    state = {
        "current_file": {
            "filename": "GameManager.gd",
            "code": "extends Node\nvar game_state: String = 'idle'",
            "iteration": 1
        },
        "instructions": sample_instructions,
        "generated_code": {},
        "review_status": {},
        "detailed_reviews": {},
        "messages": []
    }
    result = node.invoke(state)
    logger.info(f"CodeReviewNode Output: {result}")
    return result

def test_supervisor():
    logger.info("Testing SupervisorNode...")
    node = SupervisorNode("SupervisorNode", max_iterations=2)
    state = {"instructions": sample_instructions, "messages": []}
    result = node.invoke(state)
    logger.info(f"SupervisorNode Output: {result}")
    return result

def test_file_processor():
    logger.info("Testing FileProcessorNode...")
    node = FileProcessorNode("FileProcessorNode")
    state = {
        "instructions": sample_instructions,
        "generated_code": {
            "GameManager.gd": "extends Node\nvar game_state: String = 'idle'"
        },
        "pending_files": [
            {"filename": "ResourceManager.gd", "purpose": "Manages resources"}
        ],
        "messages": []
    }
    result = node.invoke(state)
    logger.info(f"FileProcessorNode Output: {result}")
    return result

def test_scene_setup():
    logger.info("Testing SceneSetupNode...")
    node = SceneSetupNode("SceneSetupNode")
    state = {
        "instructions": sample_instructions,
        "generated_code": {
            "GameManager.gd": "extends Node\nvar game_state: String = 'idle'"
        },
        "messages": []
    }
    result = node.invoke(state)
    logger.info(f"SceneSetupNode Output: {result}")
    return result

def test_final_report():
    logger.info("Testing FinalReportNode...")
    node = FinalReportNode("FinalReportNode")
    state = {
        "instructions": sample_instructions,
        "generated_code": {
            "GameManager.gd": "extends Node\nvar game_state: String = 'idle'"
        },
        "scene_guide": "Create a new scene with a Node root and attach GameManager.gd",
        "messages": []
    }
    result = node.invoke(state)
    logger.info(f"FinalReportNode Output: {result}")
    return result

def run_all_tests():
    test_instruction_node()
    test_code_writer()
    test_code_review()
    test_supervisor()
    test_file_processor()
    test_scene_setup()
    test_final_report()

if __name__ == "__main__":
    run_all_tests()
