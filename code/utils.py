import yaml
import os

from paths import CONFIG_FILE_PATH, DATA_DIR, OUTPUTS_DIR
from llm import get_llm


def load_config(config_path: str = CONFIG_FILE_PATH):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



