import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)

class FileDedupTracker:
    """
    Helper class to track files and ensure they don't get reprocessed.
    """
    @staticmethod
    def normalize_filename(filename: str) -> str:
        """Normalize a filename for consistent comparison."""
        return filename.lower().strip().replace('\\', '/').split('/')[-1]
    
    @staticmethod
    def is_duplicate_file(filename: str, 
                        existing_files: List[str], 
                        pending_files: List[Dict[str, Any]],
                        processed_files: set) -> bool:
        """
        Check if a file is already being tracked in any form.
        
        Args:
            filename: The filename to check
            existing_files: List of filenames in generated_code
            pending_files: List of pending file definitions
            processed_files: Set of filenames that have been processed
            
        Returns:
            bool: True if the file is a duplicate
        """
        norm_filename = FileDedupTracker.normalize_filename(filename)
        
        # Check existing files (normalize them too)
        for existing_file in existing_files:
            if FileDedupTracker.normalize_filename(existing_file) == norm_filename:
                return True
        
        # Check pending files
        for pending_file in pending_files:
            pending_filename = pending_file.get("filename", "")
            if FileDedupTracker.normalize_filename(pending_filename) == norm_filename:
                return True
        
        # Check processed files
        for proc_file in processed_files:
            if FileDedupTracker.normalize_filename(proc_file) == norm_filename:
                return True
                
        return False
    
    @staticmethod
    def deduplicate_dependencies(dependencies: List[Dict[str, Any]], 
                               existing_files: List[str],
                               pending_files: List[Dict[str, Any]], 
                               processed_files: set) -> List[Dict[str, Any]]:
        """
        Deduplicate dependencies against all tracking systems.
        
        Args:
            dependencies: List of dependency file definitions
            existing_files: List of filenames in generated_code
            pending_files: List of pending file definitions
            processed_files: Set of filenames that have been processed
            
        Returns:
            List[Dict[str, Any]]: Deduplicated list of dependencies
        """
        unique_deps = []
        
        for dep in dependencies:
            filename = dep.get("filename", "")
            if filename and not FileDedupTracker.is_duplicate_file(
                filename, existing_files, pending_files, processed_files
            ):
                unique_deps.append(dep)
                logger.debug(f"Adding unique dependency: {filename}")
            else:
                logger.debug(f"Skipping duplicate dependency: {filename}")
                
        return unique_deps
    
    @staticmethod
    def get_processed_filenames(processed_files: set) -> Set[str]:
        """Convert processed files to a set of normalized filenames."""
        return {FileDedupTracker.normalize_filename(f) for f in processed_files}
