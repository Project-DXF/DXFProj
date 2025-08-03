import os
import pyodbc
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

class ProfileDatabase:    
    PARAMETER_COLUMNS = {
        'Number of Loops': '',
        'Profile Type': '',
        'Profile Area': 'mm²',
        'Outer Area': 'mm²',
        'Inner Area': 'mm²',
        'Hollow Ratio': '',
        'Outer Perimeter': 'mm',
        'Total Perimeter': 'mm',
        'Number of Mandrels': '',
        
        'Bounding Box Width': 'mm',
        'Bounding Box Height': 'mm',
        'Bounding Box Area': 'mm²',
        'Max Width': 'mm',
        'Max Height': 'mm',
        'Aspect Ratio': '',
        
        'ER for P22': '',
        'ER for P40': '',
        'ER for P55': '',
        'Holes for P22': '',
        'Holes for P40': '',
        'Holes for P55': '',
        
        'Compactness': '',
        'Solidity': '',
        'Circumscribing Circle Diameter': 'mm',
        'Min Radius (Outer)': 'mm',
        'Max Radius (Outer)': 'mm',
        
        'Max Wall Thickness': 'mm',
        'Min Wall Thickness': 'mm',
        'Average Wall Thickness': 'mm',
        'Wall Thickness Variability': 'mm',
        
        'Moment of Inertia (Ix)': 'mm⁴',
        'Moment of Inertia (Iy)': 'mm⁴',
        'Polar Moment of Inertia': 'mm⁴',
        'Product of Inertia': 'mm⁴',
        
        'Euclidean Distance': '',
        'Cosine Similarity': '',
        
        'Mass Vector Top-Left': '',
        'Mass Vector Top-Right': '',
        'Mass Vector Bottom-Left': '',
        'Mass Vector Bottom-Right': '',
        
        'Complexity Factor C1': '',
        'Complexity Factor C2': '',
        'Complexity Factor C3': '',
        'Complexity Factor C4': '',
        'Complexity Factor C5': '',
        
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
    
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database connection"""
        if connection_string is None:
            self.connection_string = (
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=DESKTOP-I4EU9RQ\\SQLEXPRESS;'
                'DATABASE=DXFProfiles;'
                'Trusted_Connection=yes;'
                'TrustServerCertificate=yes;'
            )
        else:
            self.connection_string = connection_string
        
        self._ensure_db_exists()


    def get_connection(self) -> pyodbc.Connection:
        """Get a database connection for custom queries"""
        return pyodbc.connect(self.connection_string)
    
    def _ensure_db_exists(self):
        """Ensure database and table exist"""
        try:
            with pyodbc.connect(self.connection_string, autocommit=True) as conn:
                cursor = conn.cursor()
                
                # Drop existing table if it exists
                cursor.execute("""
                    IF OBJECT_ID('Profiles', 'U') IS NOT NULL
                        DROP TABLE Profiles
                """)
                
                # Create columns for main data
                columns = [
                    "ID INT IDENTITY(1,1) PRIMARY KEY",
                    "SketchNumber NVARCHAR(50)",
                    "ProfileNumber NVARCHAR(50)",
                    "InputFilename NVARCHAR(255)",
                    "Timestamp DATETIME",
                    "ProcessingStatus NVARCHAR(50)"
                ]
                
                # Add parameter columns with proper types
                for param_name in self.PARAMETER_COLUMNS.keys():
                    safe_name = param_name.replace(" ", "").replace("(", "").replace(")", "")
                    safe_name = ''.join(c for c in safe_name if c.isalnum())
                    
                    # Special handling for Profile Type
                    if param_name == "Profile Type":
                        columns.append(f"{safe_name} NVARCHAR(100)")
                    else:
                        columns.append(f"{safe_name} FLOAT NULL")
            
                # Create table
                create_table_sql = f"""
                CREATE TABLE Profiles (
                    {','.join(columns)}
                )
                """
                cursor.execute(create_table_sql)
                
        except pyodbc.Error as e:
            print(f"Database initialization error: {str(e)}")
            raise

    def save_profile(self, metadata: Dict[str, Any], parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Save profile to database with parameter logging"""
        try:
            # Debug print
            print("\n=== Debug: Parameter Values ===")
            print("Metadata:", metadata)
            print("\nParameters by category:")
            for category, params in parameters.items():
                print(f"\n{category}:")
                for param_name, param_data in params.items():
                    print(f"  {param_name}: {param_data}")

            if self.profile_exists(metadata['Sketch Number'], metadata['Profile Number']):
                return False, f"Profile already exists"
            
            # Prepare column names and values with logging
            columns = ['SketchNumber', 'ProfileNumber', 'InputFilename', 
                      'Timestamp', 'ProcessingStatus']
            values = [
                str(metadata['Sketch Number']),
                str(metadata['Profile Number']),
                str(metadata['Input Filename']),
                metadata['Timestamp'],
                str(metadata['Processing Status'])
            ]
            
            # Add special handling for Profile Type
            parameter_map = {}
            for category, params in parameters.items():
                for param_name, param_data in params.items():
                    param_value = param_data.get('value')
                    
                    # Find matching column name
                    matched_col = None
                    for col_name in self.PARAMETER_COLUMNS.keys():
                        if param_name.lower() in col_name.lower():
                            safe_name = col_name.replace(" ", "").replace("(", "").replace(")", "")
                            safe_name = ''.join(c for c in safe_name if c.isalnum())
                            matched_col = safe_name
                            break
                    
                    if matched_col:
                        print(f"\nMapping parameter: {param_name}")
                        print(f"  Original value: {param_value}")
                        print(f"  Column name: {matched_col}")
                        
                        # Special handling for Profile Type
                        if param_name == "Profile Type":
                            parameter_map[matched_col] = str(param_value)
                            print(f"  Stored as string: {param_value}")
                        else:
                            # Convert value to float for numeric parameters
                            try:
                                if param_value is not None:
                                    float_value = float(param_value)
                                    parameter_map[matched_col] = float_value
                                    print(f"  Converted value: {float_value}")
                                else:
                                    print("  Value is None, skipping")
                            except (ValueError, TypeError) as e:
                                print(f"  Conversion error: {e}")
            
            # Print final parameter map
            print("\nFinal parameter mappings:")
            for col, val in parameter_map.items():
                print(f"{col}: {val}")
            
            # Add parameters to columns and values
            for col_name, value in parameter_map.items():
                columns.append(col_name)
                values.append(value)
            
            # Create and log SQL query
            query = f"""
                INSERT INTO Profiles ({','.join(columns)})
                VALUES ({','.join(['?' for _ in values])})
            """
            print("\nSQL Query:", query)
            print("Values:", values)
            
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
            
            return True, "Profile saved successfully"
            
        except Exception as e:
            print(f"\nError details: {str(e)}")
            return False, f"Error saving profile: {str(e)}"

    def profile_exists(self, sketch_number: str, profile_number: str) -> bool:
        """Check if profile exists in database"""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM Profiles 
                    WHERE SketchNumber = ? AND ProfileNumber = ?
                """, (sketch_number, profile_number))
                return cursor.fetchone()[0] > 0
        except pyodbc.Error as e:
            print(f"Error checking profile existence: {e}")
            return False
        
    def get_profile(self, sketch_number: str, profile_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve profile from database"""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM Profiles 
                    WHERE SketchNumber = ? AND ProfileNumber = ?
                """, (sketch_number, profile_number))
                
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                return {col: val for col, val in zip(columns, row)}
                
        except pyodbc.Error as e:
            print(f"Error retrieving profile: {e}")
            return None

    def list_profiles(self) -> pd.DataFrame:
        """List all profiles in database"""
        try:
            # Create SQLAlchemy engine for pandas compatibility
            from sqlalchemy import create_engine
            import urllib
            
            params = urllib.parse.quote_plus(self.connection_string)
            engine = create_engine(f'mssql+pyodbc:///?odbc_connect={params}')
            
            query = "SELECT * FROM Profiles"
            return pd.read_sql(query, engine)
        except Exception as e:
            print(f"Error listing profiles: {e}")
            return pd.DataFrame()