"""
Profile Storage Backend

Handles the actual file storage and retrieval operations for CAD profiles.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class ProfileStorage:
    """Handles file storage operations for CAD profiles."""
    
    def __init__(self, storage_directory: Path):
        """
        Initialize the profile storage.
        
        Args:
            storage_directory: Directory to store profile files
        """
        self.storage_directory = Path(storage_directory)
        self.storage_directory.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        self.profiles_dir = self.storage_directory / "profiles"
        self.backups_dir = self.storage_directory / "backups"
        self.exports_dir = self.storage_directory / "exports"
        
        for directory in [self.profiles_dir, self.backups_dir, self.exports_dir]:
            directory.mkdir(exist_ok=True)
    
    def save_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a profile to storage.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Dictionary containing save results
        """
        try:
            profile_id = profile_data.get('profile_id')
            if not profile_id:
                return {
                    'success': False,
                    'error': 'Profile ID is required'
                }
            
            # Create filename
            filename = f"{profile_id}.json"
            filepath = self.profiles_dir / filename
            
            # Create backup if profile already exists
            if filepath.exists():
                self._create_backup(filepath)
            
            # Save profile data
            with open(filepath, 'w') as f:
                json.dump(profile_data, f, indent=2, default=str)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'message': f'Profile saved to {filename}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error saving profile: {str(e)}'
            }
    
    def load_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Load a profile from storage.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            Dictionary containing profile data or error information
        """
        try:
            filename = f"{profile_id}.json"
            filepath = self.profiles_dir / filename
            
            if not filepath.exists():
                return {
                    'success': False,
                    'error': f'Profile {profile_id} not found'
                }
            
            with open(filepath, 'r') as f:
                profile_data = json.load(f)
            
            return {
                'success': True,
                'profile_data': profile_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error loading profile: {str(e)}'
            }
    
    def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Delete a profile from storage.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            Dictionary containing deletion results
        """
        try:
            filename = f"{profile_id}.json"
            filepath = self.profiles_dir / filename
            
            if not filepath.exists():
                return {
                    'success': False,
                    'error': f'Profile {profile_id} not found'
                }
            
            # Create backup before deletion
            self._create_backup(filepath)
            
            # Delete the file
            filepath.unlink()
            
            return {
                'success': True,
                'message': f'Profile {profile_id} deleted successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error deleting profile: {str(e)}'
            }
    
    def list_profiles(self) -> Dict[str, Any]:
        """
        List all available profiles.
        
        Returns:
            Dictionary containing list of profiles
        """
        try:
            profiles = []
            
            for filepath in self.profiles_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        profile_data = json.load(f)
                    
                    # Extract summary information
                    profile_summary = {
                        'profile_id': profile_data.get('profile_id'),
                        'name': profile_data.get('name', 'Unnamed'),
                        'description': profile_data.get('description', ''),
                        'created_at': profile_data.get('created_at'),
                        'modified_at': profile_data.get('modified_at'),
                        'category': profile_data.get('category', 'Uncategorized'),
                        'file_size': filepath.stat().st_size
                    }
                    profiles.append(profile_summary)
                    
                except Exception as e:
                    print(f"Error reading profile {filepath}: {e}")
                    continue
            
            # Sort by modification date (newest first)
            profiles.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
            
            return {
                'success': True,
                'profiles': profiles
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error listing profiles: {str(e)}'
            }
    
    def profile_exists(self, profile_id: str) -> bool:
        """
        Check if a profile exists in storage.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            True if profile exists, False otherwise
        """
        filename = f"{profile_id}.json"
        filepath = self.profiles_dir / filename
        return filepath.exists()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage system.
        
        Returns:
            Dictionary containing storage information
        """
        try:
            # Count files in each directory
            profile_count = len(list(self.profiles_dir.glob("*.json")))
            backup_count = len(list(self.backups_dir.glob("*.json")))
            export_count = len(list(self.exports_dir.glob("*")))
            
            # Calculate total storage size
            total_size = 0
            for directory in [self.profiles_dir, self.backups_dir, self.exports_dir]:
                for filepath in directory.rglob("*"):
                    if filepath.is_file():
                        total_size += filepath.stat().st_size
            
            return {
                'storage_directory': str(self.storage_directory),
                'profiles_count': profile_count,
                'backups_count': backup_count,
                'exports_count': export_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {
                'error': f'Error getting storage info: {str(e)}'
            }
    
    def _create_backup(self, filepath: Path):
        """Create a backup of an existing profile file."""
        try:
            if not filepath.exists():
                return
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{filepath.stem}_{timestamp}.json"
            backup_filepath = self.backups_dir / backup_filename
            
            # Copy the file
            import shutil
            shutil.copy2(filepath, backup_filepath)
            
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    def cleanup_old_backups(self, max_backups_per_profile: int = 5) -> Dict[str, Any]:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            max_backups_per_profile: Maximum number of backups to keep per profile
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            # Group backups by profile ID
            backup_groups = {}
            for backup_file in self.backups_dir.glob("*.json"):
                # Extract profile ID from filename (before the timestamp)
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:  # profile_id_timestamp
                    profile_id = '_'.join(parts[:-2])  # Everything except last 2 parts
                    if profile_id not in backup_groups:
                        backup_groups[profile_id] = []
                    backup_groups[profile_id].append(backup_file)
            
            # Clean up old backups for each profile
            deleted_count = 0
            for profile_id, backups in backup_groups.items():
                # Sort by modification time (newest first)
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Delete old backups
                for backup_file in backups[max_backups_per_profile:]:
                    backup_file.unlink()
                    deleted_count += 1
            
            return {
                'success': True,
                'deleted_backups': deleted_count,
                'message': f'Cleaned up {deleted_count} old backup files'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error cleaning up backups: {str(e)}'
            } 