"""Скачивает набор ronantakizawa/github-codereview с Hugging Face и сохраняет только Python в data/raw/."""
import io
import re
from pathlib import Path

import pandas as pd
import requests

BASE = "https://huggingface.co/datasets/ronantakizawa/github-codereview/resolve/main/data"
SPLITS = ["test", "validation"]
TARGET = Path(__file__).parent / "raw" / "github_codereview_python.csv"

# в открытом коде встречаются настоящие ключи облака: в наших файлах их быть не должно
AWS_KEY_ID = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
AWS_SECRET = re.compile(r"(?i)(secret[\w'\"]*\s*[:=]\s*['\"])[A-Za-z0-9/+]{40}(?=['\"])")


def mask_cloud_keys(df: pd.DataFrame) -> pd.DataFrame:
    text = df.select_dtypes("object").columns
    df[text] = df[text].apply(
        lambda s: s.str.replace(AWS_KEY_ID, "<AWS_ACCESS_KEY>", regex=True)
        .str.replace(AWS_SECRET, r"\1<AWS_SECRET_KEY>", regex=True)
    )
    return df


def load_split(split: str) -> pd.DataFrame:
    r = requests.get(f"{BASE}/{split}/{split}-00000-of-00001.parquet", timeout=(10, 300))
    r.raise_for_status()
    return pd.read_parquet(io.BytesIO(r.content)).assign(split=split)


def main() -> None:
    if TARGET.exists():
        print(f"уже есть: {TARGET.name}")
        return
    df = pd.concat([load_split(s) for s in SPLITS], ignore_index=True)
    df = mask_cloud_keys(df[df.language == "Python"].reset_index(drop=True))
    TARGET.parent.mkdir(exist_ok=True)
    df.to_csv(TARGET, index=False)
    print(f"{TARGET.name}: {len(df)} строк, {df.shape[1]} колонок")


if __name__ == "__main__":
    main()
