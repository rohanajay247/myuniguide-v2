"""Harness configuration. Separate from src/myuniguide/config.py on purpose."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class EvalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ground_truth_dir: Path = Path("../corpus-ground-truth")
    results_dir: Path = Path("./eval/results")


eval_settings = EvalSettings()
