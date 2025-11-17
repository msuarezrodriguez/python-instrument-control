from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"

def make_data_dir(user: str, device: str) -> Path:
    """
    Returns the path data/user/device and creates it if necessary.
    """
    path = DATA_ROOT / user / device
    path.mkdir(parents=True, exist_ok=True)
    return path