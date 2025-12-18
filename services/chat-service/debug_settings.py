import os
os.environ['GOOGLE_API_KEY'] = 'dummy'
from main import Settings
try:
    s = Settings()
    print("Settings instantiated successfully")
    print(s.model_dump())
except Exception as e:
    print(f"Error: {e}")
