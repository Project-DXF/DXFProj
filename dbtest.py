from src.dxf_analyzer.database.profile_database import ProfileDatabase
from datetime import datetime

def test_database():
    try:
        # Initialize database
        db = ProfileDatabase()
        
        # Test saving a profile
        metadata = {
            'Sketch Number': 'TEST001',
            'Profile Number': 'P001',
            'Input Filename': 'test.dxf',
            'Timestamp': datetime.now(),
            'Processing Status': 'Completed'
        }
        
        parameters = {
            'Geometry': {
                'number of loops': {'value': 1},
                'profile area': {'value': 100.5}
            }
        }
        
        success, message = db.save_profile(metadata, parameters)
        print(f"Save result: {message}")
        
        # Test retrieving the profile
        profile = db.get_profile('TEST001', 'P001')
        print("\nRetrieved profile:", profile)
        
        # List all profiles
        profiles = db.list_profiles()
        print("\nTotal profiles:", len(profiles))
        
    except Exception as e:
        print(f"Test error: {str(e)}")

if __name__ == "__main__":
    test_database()