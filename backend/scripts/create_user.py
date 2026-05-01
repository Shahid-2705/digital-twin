import argparse
import json
import sys
from pathlib import Path

# Ensure the backend module is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from passlib.context import CryptContext
from backend import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    parser = argparse.ArgumentParser(description="Create a user for the AI Clone API")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--role", default="owner", help="User role (default: owner)")
    
    args = parser.parse_args()
    
    users_file = config.DATA_DIR / "users.json"
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    users = []
    if users_file.exists():
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)
        except json.JSONDecodeError:
            users = []
            
    # Check if user exists and remove it to update
    users = [u for u in users if u.get("username") != args.username]
            
    users.append({
        "username": args.username,
        "hashed_password": pwd_context.hash(args.password),
        "role": args.role
    })
        
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)
        
    print(f"Successfully created user '{args.username}' with role '{args.role}'.")

if __name__ == "__main__":
    main()
