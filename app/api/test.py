import uuid, re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def make_clean_file_name(name)-> str:
    """Clean filename from special characters, turn file name in string format"""
    file_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_name = file_name.strip().lower()
    file_name = re.sub(r"[^A-Za-z0-9._-]", "_", file_name)
    return file_name



def create_source_key(username:str, file_name:str) ->str:
    """Creates a unique and safe source key for a file based on user_id and file name."""
    unique_file_id = str(uuid.uuid4())
    #To prevent special character that might cause problem for ChromaDB
    safe_file_name = make_clean_file_name(file_name)
    source_key = f"user_{username}/{unique_file_id}_{safe_file_name}"
    return source_key





def create_file_path(user_name, file_name):
    user_dir = BASE_DIR / "upload" /user_name
    user_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file_name).suffix
    file_path = user_dir / f"{create_source_key(username=user_name, file_name=file_name)}{ext}"
    return file_path

print(type(create_file_path("omid84", "insurance.pdf")))