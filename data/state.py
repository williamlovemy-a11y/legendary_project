from typing import Any
from pandas import pd
from config import STORAGE_DIR

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

datasets_registry: dict[str, dict[str, Any]] = {}
dataframes_cache: dict[str, pd.DataFrame] = {}
