import pyodbc
import time

def test_sql_connection():
    """Test SQL Server connection and basic functionality"""
    print("=== Testing SQL Server Connection ===\n")
    
    server = r'DESKTOP-I4EU9RQ\SQLEXPRESS'
    connection_string = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={server};'
        'Trusted_Connection=yes;'
        'TrustServerCertificate=yes;'
    )
    
    try:
        # First connect to master database
        print("Connecting to master database...")
        conn = pyodbc.connect(connection_string + 'DATABASE=master;', autocommit=True)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print("\nConnection successful!")
        print(f"SQL Server Version: {version}\n")
        
        # Create database if it doesn't exist
        print("Checking if database exists...")
        cursor.execute("""
        IF NOT EXISTS (
            SELECT name 
            FROM sys.databases 
            WHERE name = 'DXFProfiles'
        )
        BEGIN
            CREATE DATABASE DXFProfiles
            PRINT 'Database created successfully'
        END
        ELSE
            PRINT 'Database already exists'
        """)
        
        cursor.close()
        conn.close()
        
        # Connect to new database and create schema
        print("\nConnecting to DXFProfiles database...")
        conn = pyodbc.connect(connection_string + 'DATABASE=DXFProfiles;', autocommit=True)
        cursor = conn.cursor()
        
        # Create profiles table
        print("Creating profiles table if it doesn't exist...")
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sys.objects 
            WHERE object_id = OBJECT_ID(N'[dbo].[Profiles]') 
            AND type in (N'U')
        )
        BEGIN
            CREATE TABLE [dbo].[Profiles](
                [ID] [int] IDENTITY(1,1) PRIMARY KEY,
                [SketchNumber] [nvarchar](50) NULL,
                [ProfileNumber] [nvarchar](50) NULL,
                [InputFilename] [nvarchar](255) NULL,
                [Timestamp] [datetime] NULL,
                [ProcessingStatus] [nvarchar](50) NULL
            )
            PRINT 'Table created successfully'
        END
        ELSE
            PRINT 'Table already exists'
        """)
        
        cursor.close()
        conn.close()
        print("\nDatabase setup completed successfully!")
        return True
        
    except pyodbc.Error as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_sql_connection()