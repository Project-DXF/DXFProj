"""
Profile Database Manager

Handles all operations related to storing and retrieving profile data from an Excel database.
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path


class ProfileDatabase:
    """Manages profile data storage in an Excel file."""
    
    # Define all possible parameters and their units
    PARAMETER_COLUMNS = {
        # Basic Properties
        'Number of Loops': '',
        'Profile Type': '',
        'Profile Area': 'mm²',
        'Outer Area': 'mm²',
        'Inner Area': 'mm²',
        'Hollow Ratio': '',
        'Outer Perimeter': 'mm',
        'Total Perimeter': 'mm',
        'Number of Mandrels': '',
        
        # Dimensions
        'Bounding Box Width': 'mm',
        'Bounding Box Height': 'mm',
        'Bounding Box Area': 'mm²',
        'Max Width': 'mm',
        'Max Height': 'mm',
        'Aspect Ratio': '',
        
        # Extrusion Ratios
        'ER for P22': '',
        'ER for P40': '',
        'ER for P55': '',
        'Holes for P22': '',
        'Holes for P40': '',
        'Holes for P55': '',
        
        # Geometric Properties
        'Compactness': '',
        'Solidity': '',
        'Circumscribing Circle Diameter': 'mm',
        'Min Radius (Outer)': 'mm',
        'Max Radius (Outer)': 'mm',
        
        # Wall Thickness
        'Max Wall Thickness': 'mm',
        'Min Wall Thickness': 'mm',
        'Average Wall Thickness': 'mm',
        'Wall Thickness Variability': 'mm',
        
        # Moments of Inertia
        'Moment of Inertia (Ix)': 'mm⁴',
        'Moment of Inertia (Iy)': 'mm⁴',
        'Polar Moment of Inertia': 'mm⁴',
        'Product of Inertia': 'mm⁴',
        
        # Distance Metrics
        'Euclidean Distance': '',
        'Cosine Similarity': '',
        
        # Mass Vectors
        'Mass Vector Top-Left': '',
        'Mass Vector Top-Right': '',
        'Mass Vector Bottom-Left': '',
        'Mass Vector Bottom-Right': '',
        
        # Complexity Factors
        'Complexity Factor C1': '',
        'Complexity Factor C2': '',
        'Complexity Factor C3': '',
        'Complexity Factor C4': '',
        'Complexity Factor C5': '',
        
        # Fourier Descriptors
        'Fourier Descriptor 1': '',
        'Fourier Descriptor 2': '',
        'Fourier Descriptor 3': '',
        'Fourier Descriptor 4': '',
        'Fourier Descriptor 5': '',
        'Fourier Descriptor 6': '',
        'Fourier Descriptor 7': '',
        'Fourier Descriptor 8': '',
        'Fourier Descriptor 9': '',
        'Fourier Descriptor 10': '',
    }
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the profile database.
        
        Args:
            db_path: Optional path to the Excel database file. If not provided,
                    will use a default location in the user's Downloads folder.
        """
        if db_path is None:
            # Use default location in user's Downloads folder
            downloads_path = str(Path.home() / "Downloads")
            db_path = os.path.join(downloads_path, 'profile_database.xlsx')
        
        self.db_path = Path(db_path)
        self._ensure_db_exists()
    
    def set_db_path(self, new_path: str) -> bool:
        """
        Change the database file path.
        
        Args:
            new_path: New path for the database file
            
        Returns:
            bool: True if path was changed successfully, False otherwise
        """
        try:
            new_path = Path(new_path)
            # Create directory if it doesn't exist
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If database exists, move it to new location
            if self.db_path.exists():
                import shutil
                shutil.move(str(self.db_path), str(new_path))
            
            self.db_path = new_path
            return True
        except Exception as e:
            print(f"Error changing database path: {e}")
            return False
    
    def _ensure_db_exists(self):
        """Ensure the database file exists with proper structure."""
        if not self.db_path.exists():
            # Create directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create empty database with proper structure
            columns = ['Sketch Number', 'Profile Number', 'Input Filename', 'Timestamp', 'Processing Status']
            columns.extend(self.PARAMETER_COLUMNS.keys())
            
            pd.DataFrame(columns=columns).to_excel(self.db_path, sheet_name='Profiles', index=False)
    
    def profile_exists(self, sketch_number: str, profile_number: str) -> bool:
        """
        Check if a profile with given sketch and profile numbers exists.
        
        Args:
            sketch_number: The sketch number to check
            profile_number: The profile number to check
            
        Returns:
            bool: True if profile exists, False otherwise
        """
        try:
            df = pd.read_excel(self.db_path)
            return any(
                (df['Sketch Number'] == sketch_number) & 
                (df['Profile Number'] == profile_number)
            )
        except Exception as e:
            print(f"Error checking profile existence: {e}")
            return False
    
    def save_profile(self, metadata: Dict[str, Any], parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save a new profile to the database.
        
        Args:
            metadata: Dictionary containing profile metadata
            parameters: Dictionary containing profile parameters
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check if profile already exists
            if self.profile_exists(metadata['Sketch Number'], metadata['Profile Number']):
                return False, f"Profile with sketch number {metadata['Sketch Number']} and profile number {metadata['Profile Number']} already exists"
            
            # Read existing data
            df = pd.read_excel(self.db_path)
            
            # Create new row
            new_row = {
                'Sketch Number': metadata['Sketch Number'],
                'Profile Number': metadata['Profile Number'],
                'Input Filename': metadata['Input Filename'],
                'Timestamp': metadata['Timestamp'],
                'Processing Status': metadata['Processing Status']
            }
            
            # Add parameters
            for category, params in parameters.items():
                for param_name, param_data in params.items():
                    # Find matching column name
                    for col_name in self.PARAMETER_COLUMNS.keys():
                        if param_name.lower() in col_name.lower():
                            new_row[col_name] = param_data['value']
                            break
            
            # Add new row to DataFrame
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save updated data
            df.to_excel(self.db_path, sheet_name='Profiles', index=False)
            
            return True, "Profile saved successfully"
            
        except Exception as e:
            return False, f"Error saving profile: {str(e)}"
    
    def get_profile(self, sketch_number: str, profile_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a profile from the database.
        
        Args:
            sketch_number: The sketch number to retrieve
            profile_number: The profile number to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Profile data if found, None otherwise
        """
        try:
            df = pd.read_excel(self.db_path)
            
            # Get profile data
            profile_data = df[
                (df['Sketch Number'] == sketch_number) & 
                (df['Profile Number'] == profile_number)
            ]
            
            if profile_data.empty:
                return None
            
            # Convert to dictionary
            return profile_data.iloc[0].to_dict()
            
        except Exception as e:
            print(f"Error retrieving profile: {e}")
            return None
    
    def list_profiles(self) -> pd.DataFrame:
        """
        List all profiles in the database.
        
        Returns:
            pd.DataFrame: DataFrame containing all profiles
        """
        try:
            return pd.read_excel(self.db_path)
        except Exception as e:
            print(f"Error listing profiles: {e}")
            return pd.DataFrame() 