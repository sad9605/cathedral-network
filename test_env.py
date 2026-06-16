from dotenv import load_dotenv
import os

load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

print(f"EIA_API_KEY: {EIA_API_KEY}")
print(f"FRED_API_KEY: {FRED_API_KEY}")
print("✅ Environment variables loaded successfully!")
