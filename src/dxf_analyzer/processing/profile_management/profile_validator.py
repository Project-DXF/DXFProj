"""
Profile Validator for CAD Profiles

Validates profile data to ensure consistency and completeness.
"""

from typing import Dict, List, Any, Optional
import re
from datetime import datetime


class ProfileValidator:
    """Validates CAD profile data."""
    
    def __init__(self):
        """Initialize the profile validator."""
        self.required_fields = [
            'name',
            'profile_id'
        ]
        
        self.optional_fields = [
            'description',
            'category',
            'tags',
            'created_at',
            'modified_at',
            'version',
            'geometric_features',
            'dimensions',
            'material_properties',
            'manufacturing_info',
            'quality_metrics'
        ]
        
        self.field_validators = {
            'name': self._validate_name,
            'profile_id': self._validate_profile_id,
            'description': self._validate_description,
            'category': self._validate_category,
            'tags': self._validate_tags,
            'created_at': self._validate_datetime,
            'modified_at': self._validate_datetime,
            'version': self._validate_version,
            'geometric_features': self._validate_geometric_features,
            'dimensions': self._validate_dimensions,
            'material_properties': self._validate_material_properties,
            'manufacturing_info': self._validate_manufacturing_info,
            'quality_metrics': self._validate_quality_metrics
        }
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a complete profile.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Dictionary containing validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in profile_data:
                errors.append(f"Required field '{field}' is missing")
            elif not profile_data[field]:
                errors.append(f"Required field '{field}' is empty")
        
        # Validate individual fields
        for field, value in profile_data.items():
            if field in self.field_validators:
                validation_result = self.field_validators[field](value)
                if not validation_result['valid']:
                    errors.extend(validation_result.get('errors', []))
                warnings.extend(validation_result.get('warnings', []))
        
        # Check for unknown fields
        known_fields = set(self.required_fields + self.optional_fields)
        unknown_fields = set(profile_data.keys()) - known_fields
        if unknown_fields:
            warnings.append(f"Unknown fields detected: {', '.join(unknown_fields)}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'field_count': len(profile_data),
            'required_fields_present': all(field in profile_data for field in self.required_fields)
        }
    
    def _validate_name(self, value: Any) -> Dict[str, Any]:
        """Validate profile name."""
        errors = []
        warnings = []
        
        if not isinstance(value, str):
            errors.append("Profile name must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(value.strip()) == 0:
            errors.append("Profile name cannot be empty")
        elif len(value) > 100:
            warnings.append("Profile name is very long (>100 characters)")
        elif len(value) < 3:
            warnings.append("Profile name is very short (<3 characters)")
        
        # Check for invalid characters
        if re.search(r'[<>:"/\\|?*]', value):
            errors.append("Profile name contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_profile_id(self, value: Any) -> Dict[str, Any]:
        """Validate profile ID."""
        errors = []
        warnings = []
        
        if not isinstance(value, str):
            errors.append("Profile ID must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(value.strip()) == 0:
            errors.append("Profile ID cannot be empty")
        elif len(value) > 50:
            errors.append("Profile ID is too long (>50 characters)")
        elif len(value) < 3:
            errors.append("Profile ID is too short (<3 characters)")
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            errors.append("Profile ID can only contain letters, numbers, underscores, and hyphens")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_description(self, value: Any) -> Dict[str, Any]:
        """Validate profile description."""
        errors = []
        warnings = []
        
        if value is not None and not isinstance(value, str):
            errors.append("Description must be a string")
        elif value and len(value) > 1000:
            warnings.append("Description is very long (>1000 characters)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_category(self, value: Any) -> Dict[str, Any]:
        """Validate profile category."""
        errors = []
        warnings = []
        
        valid_categories = [
            'Structural', 'Mechanical', 'Architectural', 'Electrical',
            'Piping', 'HVAC', 'Custom', 'Uncategorized'
        ]
        
        if value is not None:
            if not isinstance(value, str):
                errors.append("Category must be a string")
            elif value not in valid_categories:
                warnings.append(f"Category '{value}' is not in standard categories: {', '.join(valid_categories)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_tags(self, value: Any) -> Dict[str, Any]:
        """Validate profile tags."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, list):
                errors.append("Tags must be a list")
            else:
                for i, tag in enumerate(value):
                    if not isinstance(tag, str):
                        errors.append(f"Tag {i} must be a string")
                    elif len(tag.strip()) == 0:
                        warnings.append(f"Tag {i} is empty")
                
                if len(value) > 20:
                    warnings.append("Too many tags (>20)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_datetime(self, value: Any) -> Dict[str, Any]:
        """Validate datetime fields."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, str):
                errors.append("Datetime must be a string")
            else:
                try:
                    # Try to parse ISO format
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("Datetime must be in ISO format")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_version(self, value: Any) -> Dict[str, Any]:
        """Validate version field."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, str):
                errors.append("Version must be a string")
            elif not re.match(r'^\d+\.\d+(\.\d+)?$', value):
                warnings.append("Version should follow semantic versioning (e.g., 1.0.0)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_geometric_features(self, value: Any) -> Dict[str, Any]:
        """Validate geometric features data."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, dict):
                errors.append("Geometric features must be a dictionary")
            else:
                # Check for expected structure
                expected_keys = ['lines', 'arcs', 'circles', 'polylines', 'splines', 'overall']
                for key in expected_keys:
                    if key not in value:
                        warnings.append(f"Missing geometric feature category: {key}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_dimensions(self, value: Any) -> Dict[str, Any]:
        """Validate dimensions data."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, dict):
                errors.append("Dimensions must be a dictionary")
            else:
                # Check for numeric values
                for key, val in value.items():
                    if val is not None and not isinstance(val, (int, float)):
                        errors.append(f"Dimension '{key}' must be numeric")
                    elif isinstance(val, (int, float)) and val < 0:
                        warnings.append(f"Dimension '{key}' has negative value")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_material_properties(self, value: Any) -> Dict[str, Any]:
        """Validate material properties data."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, dict):
                errors.append("Material properties must be a dictionary")
            else:
                # Check for common material properties
                numeric_properties = ['density', 'young_modulus', 'yield_strength', 'tensile_strength']
                for prop in numeric_properties:
                    if prop in value and value[prop] is not None:
                        if not isinstance(value[prop], (int, float)):
                            errors.append(f"Material property '{prop}' must be numeric")
                        elif value[prop] <= 0:
                            warnings.append(f"Material property '{prop}' should be positive")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_manufacturing_info(self, value: Any) -> Dict[str, Any]:
        """Validate manufacturing information."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, dict):
                errors.append("Manufacturing info must be a dictionary")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_quality_metrics(self, value: Any) -> Dict[str, Any]:
        """Validate quality metrics data."""
        errors = []
        warnings = []
        
        if value is not None:
            if not isinstance(value, dict):
                errors.append("Quality metrics must be a dictionary")
            else:
                # Check for quality score
                if 'quality_score' in value:
                    score = value['quality_score']
                    if not isinstance(score, (int, float)):
                        errors.append("Quality score must be numeric")
                    elif not (0 <= score <= 100):
                        errors.append("Quality score must be between 0 and 100")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_validation_schema(self) -> Dict[str, Any]:
        """
        Get the validation schema for profiles.
        
        Returns:
            Dictionary describing the validation schema
        """
        return {
            'required_fields': self.required_fields,
            'optional_fields': self.optional_fields,
            'field_descriptions': {
                'name': 'Human-readable name for the profile',
                'profile_id': 'Unique identifier (alphanumeric, underscore, hyphen)',
                'description': 'Optional description of the profile',
                'category': 'Profile category (Structural, Mechanical, etc.)',
                'tags': 'List of tags for categorization',
                'created_at': 'Creation timestamp (ISO format)',
                'modified_at': 'Last modification timestamp (ISO format)',
                'version': 'Version number (semantic versioning)',
                'geometric_features': 'Geometric analysis results',
                'dimensions': 'Dimensional measurements',
                'material_properties': 'Material characteristics',
                'manufacturing_info': 'Manufacturing-related data',
                'quality_metrics': 'Quality assessment results'
            }
        } 