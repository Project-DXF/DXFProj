"""
Profile Manager for CAD Profiles

Manages CAD profile operations including saving, loading, and organizing profiles.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from .profile_storage import ProfileStorage
from .profile_validator import ProfileValidator


class ProfileManager:
    """Manages CAD profile operations and data."""
    
    def __init__(self, storage_directory: Optional[str] = None):
        """
        Initialize the profile manager.
        
        Args:
            storage_directory: Directory to store profile data (default: ./profiles)
        """
        self.storage_directory = Path(storage_directory or "./profiles")
        self.storage_directory.mkdir(exist_ok=True)
        
        self.storage = ProfileStorage(self.storage_directory)
        self.validator = ProfileValidator()
        
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new CAD profile.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Dictionary containing creation results
        """
        try:
            # Validate profile data
            validation_result = self.validator.validate_profile(profile_data)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': 'Profile validation failed',
                    'validation_errors': validation_result['errors']
                }
            
            # Add metadata
            profile_data['created_at'] = datetime.now().isoformat()
            profile_data['modified_at'] = datetime.now().isoformat()
            profile_data['version'] = '1.0'
            
            # Generate profile ID if not provided
            if 'profile_id' not in profile_data:
                profile_data['profile_id'] = self._generate_profile_id(profile_data)
            
            # Save profile
            save_result = self.storage.save_profile(profile_data)
            
            if save_result['success']:
                return {
                    'success': True,
                    'profile_id': profile_data['profile_id'],
                    'message': 'Profile created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': save_result.get('error', 'Failed to save profile')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating profile: {str(e)}'
            }
    
    def load_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Load a CAD profile by ID.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            Dictionary containing profile data or error information
        """
        try:
            load_result = self.storage.load_profile(profile_id)
            
            if load_result['success']:
                return {
                    'success': True,
                    'profile_data': load_result['profile_data']
                }
            else:
                return {
                    'success': False,
                    'error': load_result.get('error', 'Failed to load profile')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error loading profile: {str(e)}'
            }
    
    def update_profile(self, profile_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing CAD profile.
        
        Args:
            profile_id: Unique identifier for the profile
            updated_data: Dictionary containing updated profile information
            
        Returns:
            Dictionary containing update results
        """
        try:
            # Load existing profile
            load_result = self.load_profile(profile_id)
            if not load_result['success']:
                return load_result
            
            # Merge with updated data
            profile_data = load_result['profile_data']
            profile_data.update(updated_data)
            profile_data['modified_at'] = datetime.now().isoformat()
            
            # Validate updated profile
            validation_result = self.validator.validate_profile(profile_data)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'error': 'Profile validation failed',
                    'validation_errors': validation_result['errors']
                }
            
            # Save updated profile
            save_result = self.storage.save_profile(profile_data)
            
            if save_result['success']:
                return {
                    'success': True,
                    'profile_id': profile_id,
                    'message': 'Profile updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': save_result.get('error', 'Failed to save updated profile')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error updating profile: {str(e)}'
            }
    
    def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Delete a CAD profile.
        
        Args:
            profile_id: Unique identifier for the profile
            
        Returns:
            Dictionary containing deletion results
        """
        try:
            delete_result = self.storage.delete_profile(profile_id)
            
            if delete_result['success']:
                return {
                    'success': True,
                    'message': 'Profile deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': delete_result.get('error', 'Failed to delete profile')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error deleting profile: {str(e)}'
            }
    
    def list_profiles(self, filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List all available CAD profiles.
        
        Args:
            filter_criteria: Optional criteria to filter profiles
            
        Returns:
            Dictionary containing list of profiles
        """
        try:
            list_result = self.storage.list_profiles()
            
            if not list_result['success']:
                return list_result
            
            profiles = list_result['profiles']
            
            # Apply filters if provided
            if filter_criteria:
                profiles = self._filter_profiles(profiles, filter_criteria)
            
            return {
                'success': True,
                'profiles': profiles,
                'count': len(profiles)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error listing profiles: {str(e)}'
            }
    
    def search_profiles(self, search_term: str, search_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for profiles based on a search term.
        
        Args:
            search_term: Term to search for
            search_fields: Fields to search in (default: ['name', 'description', 'tags'])
            
        Returns:
            Dictionary containing search results
        """
        try:
            if not search_fields:
                search_fields = ['name', 'description', 'tags']
            
            list_result = self.list_profiles()
            if not list_result['success']:
                return list_result
            
            profiles = list_result['profiles']
            search_results = []
            
            search_term_lower = search_term.lower()
            
            for profile in profiles:
                match_found = False
                for field in search_fields:
                    if field in profile:
                        field_value = str(profile[field]).lower()
                        if search_term_lower in field_value:
                            match_found = True
                            break
                
                if match_found:
                    search_results.append(profile)
            
            return {
                'success': True,
                'profiles': search_results,
                'count': len(search_results),
                'search_term': search_term
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error searching profiles: {str(e)}'
            }
    
    def export_profile(self, profile_id: str, export_path: str, format: str = 'json') -> Dict[str, Any]:
        """
        Export a profile to a file.
        
        Args:
            profile_id: Unique identifier for the profile
            export_path: Path to export the profile to
            format: Export format ('json', 'csv', 'xml')
            
        Returns:
            Dictionary containing export results
        """
        try:
            # Load profile
            load_result = self.load_profile(profile_id)
            if not load_result['success']:
                return load_result
            
            profile_data = load_result['profile_data']
            
            # Export based on format
            if format.lower() == 'json':
                return self._export_json(profile_data, export_path)
            elif format.lower() == 'csv':
                return self._export_csv(profile_data, export_path)
            elif format.lower() == 'xml':
                return self._export_xml(profile_data, export_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported export format: {format}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error exporting profile: {str(e)}'
            }
    
    def import_profile(self, import_path: str, format: str = 'json') -> Dict[str, Any]:
        """
        Import a profile from a file.
        
        Args:
            import_path: Path to import the profile from
            format: Import format ('json', 'csv', 'xml')
            
        Returns:
            Dictionary containing import results
        """
        try:
            # Import based on format
            if format.lower() == 'json':
                import_result = self._import_json(import_path)
            elif format.lower() == 'csv':
                import_result = self._import_csv(import_path)
            elif format.lower() == 'xml':
                import_result = self._import_xml(import_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported import format: {format}'
                }
            
            if not import_result['success']:
                return import_result
            
            # Create profile from imported data
            return self.create_profile(import_result['profile_data'])
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error importing profile: {str(e)}'
            }
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored profiles.
        
        Returns:
            Dictionary containing profile statistics
        """
        try:
            list_result = self.list_profiles()
            if not list_result['success']:
                return list_result
            
            profiles = list_result['profiles']
            
            # Calculate statistics
            total_profiles = len(profiles)
            
            # Group by creation date
            creation_dates = {}
            for profile in profiles:
                created_at = profile.get('created_at', '')
                if created_at:
                    date = created_at.split('T')[0]  # Extract date part
                    creation_dates[date] = creation_dates.get(date, 0) + 1
            
            # Group by profile type/category
            categories = {}
            for profile in profiles:
                category = profile.get('category', 'Uncategorized')
                categories[category] = categories.get(category, 0) + 1
            
            return {
                'success': True,
                'statistics': {
                    'total_profiles': total_profiles,
                    'creation_dates': creation_dates,
                    'categories': categories,
                    'storage_directory': str(self.storage_directory)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting profile statistics: {str(e)}'
            }
    
    def _generate_profile_id(self, profile_data: Dict[str, Any]) -> str:
        """Generate a unique profile ID."""
        import hashlib
        import time
        
        # Use profile name and timestamp to generate ID
        name = profile_data.get('name', 'unnamed')
        timestamp = str(time.time())
        
        id_string = f"{name}_{timestamp}"
        return hashlib.md5(id_string.encode()).hexdigest()[:12]
    
    def _filter_profiles(self, profiles: List[Dict[str, Any]], 
                        filter_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter profiles based on criteria."""
        filtered_profiles = []
        
        for profile in profiles:
            match = True
            for key, value in filter_criteria.items():
                if key not in profile or profile[key] != value:
                    match = False
                    break
            
            if match:
                filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def _export_json(self, profile_data: Dict[str, Any], export_path: str) -> Dict[str, Any]:
        """Export profile data to JSON format."""
        try:
            with open(export_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            return {
                'success': True,
                'message': f'Profile exported to {export_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error exporting to JSON: {str(e)}'
            }
    
    def _export_csv(self, profile_data: Dict[str, Any], export_path: str) -> Dict[str, Any]:
        """Export profile data to CSV format."""
        try:
            import csv
            
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write headers
                writer.writerow(['Field', 'Value'])
                
                # Write data
                for key, value in profile_data.items():
                    writer.writerow([key, str(value)])
            
            return {
                'success': True,
                'message': f'Profile exported to {export_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error exporting to CSV: {str(e)}'
            }
    
    def _export_xml(self, profile_data: Dict[str, Any], export_path: str) -> Dict[str, Any]:
        """Export profile data to XML format."""
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.Element('profile')
            
            for key, value in profile_data.items():
                element = ET.SubElement(root, key)
                element.text = str(value)
            
            tree = ET.ElementTree(root)
            tree.write(export_path, encoding='utf-8', xml_declaration=True)
            
            return {
                'success': True,
                'message': f'Profile exported to {export_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error exporting to XML: {str(e)}'
            }
    
    def _import_json(self, import_path: str) -> Dict[str, Any]:
        """Import profile data from JSON format."""
        try:
            with open(import_path, 'r') as f:
                profile_data = json.load(f)
            
            return {
                'success': True,
                'profile_data': profile_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error importing from JSON: {str(e)}'
            }
    
    def _import_csv(self, import_path: str) -> Dict[str, Any]:
        """Import profile data from CSV format."""
        try:
            import csv
            
            profile_data = {}
            
            with open(import_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 2:
                        key, value = row[0], row[1]
                        # Try to convert to appropriate type
                        try:
                            profile_data[key] = json.loads(value)
                        except:
                            profile_data[key] = value
            
            return {
                'success': True,
                'profile_data': profile_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error importing from CSV: {str(e)}'
            }
    
    def _import_xml(self, import_path: str) -> Dict[str, Any]:
        """Import profile data from XML format."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(import_path)
            root = tree.getroot()
            
            profile_data = {}
            
            for element in root:
                key = element.tag
                value = element.text
                
                # Try to convert to appropriate type
                try:
                    profile_data[key] = json.loads(value)
                except:
                    profile_data[key] = value
            
            return {
                'success': True,
                'profile_data': profile_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error importing from XML: {str(e)}'
            } 