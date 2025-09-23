import json
import shutil
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/app/data/models")
CURRENT_MODEL_FILE = MODEL_DIR / "current_model.pkl"
MODEL_META_FILE = MODEL_DIR / "model_metadata.json"

class ModelManagementError(Exception):
    """Custom exception for model management related errors."""
    pass

def initialize_model_storage() -> None:
    """
    Initialize the model storage directory structure.
    """
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        if not MODEL_META_FILE.exists():
            save_metadata({
                "versions": [],
                "current_version": None
            })
        logger.info("Model storage initialized")
    except Exception as e:
        logger.error("Failed to initialize model storage: %s", str(e))
        raise ModelManagementError(f"Storage initialization failed: {str(e)}")

def save_metadata(metadata: Dict[str, Any]) -> None:
    """Save model metadata to file."""
    with open(MODEL_META_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_metadata() -> Dict[str, Any]:
    """Load model metadata from file."""
    try:
        with open(MODEL_META_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"versions": [], "current_version": None}
    except json.JSONDecodeError as e:
        raise ModelManagementError(f"Invalid metadata file format: {str(e)}")

def create_model_version(
    model_data: bytes,
    accuracy: float,
    sample_count: int,
    description: Optional[str] = None
) -> str:
    """
    Create a new model version with metadata.
    
    Args:
        model_data: Serialized model data
        accuracy: Model accuracy score
        sample_count: Number of training samples
        description: Optional description of the model version
        
    Returns:
        Version ID string
    """
    try:
        # Initialize if needed
        initialize_model_storage()
        
        # Generate version ID
        version_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version_path = MODEL_DIR / f"model_{version_id}.pkl"
        
        # Save model file
        with open(version_path, 'wb') as f:
            f.write(model_data)
        
        # Update metadata
        metadata = load_metadata()
        version_info = {
            "id": version_id,
            "timestamp": datetime.utcnow().isoformat(),
            "accuracy": accuracy,
            "sample_count": sample_count,
            "description": description,
            "file_path": str(version_path)
        }
        metadata["versions"].append(version_info)
        metadata["current_version"] = version_id
        save_metadata(metadata)
        
        # Update current model symlink
        if CURRENT_MODEL_FILE.exists():
            CURRENT_MODEL_FILE.unlink()
        CURRENT_MODEL_FILE.symlink_to(version_path)
        
        logger.info("Created new model version: %s", version_id)
        return version_id
        
    except Exception as e:
        logger.error("Failed to create model version: %s", str(e))
        raise ModelManagementError(f"Version creation failed: {str(e)}")

def get_model_version(version_id: str) -> Path:
    """
    Get the path to a specific model version.
    
    Args:
        version_id: Version ID string
        
    Returns:
        Path to the model file
    """
    try:
        metadata = load_metadata()
        version = next((v for v in metadata["versions"] if v["id"] == version_id), None)
        if not version:
            raise ModelManagementError(f"Version {version_id} not found")
        return Path(version["file_path"])
    except Exception as e:
        logger.error("Failed to get model version: %s", str(e))
        raise ModelManagementError(f"Failed to get version: {str(e)}")

def get_current_model() -> Optional[Path]:
    """
    Get the path to the current model version.
    
    Returns:
        Path to the current model file or None if no model exists
    """
    if CURRENT_MODEL_FILE.exists():
        return CURRENT_MODEL_FILE
    return None

def backup_model(version_id: str, backup_dir: Path) -> None:
    """
    Create a backup of a specific model version.
    
    Args:
        version_id: Version ID to backup
        backup_dir: Directory to store the backup
    """
    try:
        model_path = get_model_version(version_id)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"model_{version_id}_backup.pkl"
        shutil.copy2(model_path, backup_path)
        
        # Backup metadata
        meta_backup_path = backup_dir / f"metadata_{version_id}.json"
        shutil.copy2(MODEL_META_FILE, meta_backup_path)
        
        logger.info("Created backup of model version %s", version_id)
    except Exception as e:
        logger.error("Failed to create backup: %s", str(e))
        raise ModelManagementError(f"Backup failed: {str(e)}")

def restore_model(backup_dir: Path, version_id: str) -> None:
    """
    Restore a model from backup.
    
    Args:
        backup_dir: Directory containing the backup
        version_id: Version ID to restore
    """
    try:
        backup_path = backup_dir / f"model_{version_id}_backup.pkl"
        meta_backup_path = backup_dir / f"metadata_{version_id}.json"
        
        if not backup_path.exists() or not meta_backup_path.exists():
            raise ModelManagementError(f"Backup files for version {version_id} not found")
            
        # Restore model file
        model_path = MODEL_DIR / f"model_{version_id}.pkl"
        shutil.copy2(backup_path, model_path)
        
        # Restore metadata
        shutil.copy2(meta_backup_path, MODEL_META_FILE)
        
        # Update current model symlink
        if CURRENT_MODEL_FILE.exists():
            CURRENT_MODEL_FILE.unlink()
        CURRENT_MODEL_FILE.symlink_to(model_path)
        
        logger.info("Restored model version %s from backup", version_id)
    except Exception as e:
        logger.error("Failed to restore from backup: %s", str(e))
        raise ModelManagementError(f"Restore failed: {str(e)}")