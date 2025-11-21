from __future__ import annotations

import argparse
import pathlib
from dataclasses import dataclass
from typing import List

from rich import print

from src.utils.io import ensure_dir, read_yaml


@dataclass
class SourceSpec:
    name: str
    type: str
    pattern: str
    metadata: dict


@dataclass
class IngestConfig:
    raw_data_dir: pathlib.Path
    interim_data_dir: pathlib.Path
    processed_data_dir: pathlib.Path
    sources: List[SourceSpec]

    @classmethod
    def from_dict(cls, data: dict) -> "IngestConfig":
        return cls(
            raw_data_dir=pathlib.Path(data["raw_data_dir"]),
            interim_data_dir=pathlib.Path(data["interim_data_dir"]),
            processed_data_dir=pathlib.Path(data["processed_data_dir"]),
            sources=[
                SourceSpec(
                    name=src["name"],
                    type=src["type"],
                    pattern=src["pattern"],
                    metadata=src.get("metadata", {}),
                )
                for src in data.get("sources", [])
            ],
        )


def ingest_source(source: SourceSpec, raw_dir: pathlib.Path) -> None:
    print(f"[bold cyan]Kaynak taranıyor:[/bold cyan] {source.name}")
    candidate_files = list(raw_dir.glob(source.pattern))
    if not candidate_files:
        print(f"[yellow]Uyarı:[/yellow] {source.pattern} kalıbı için dosya bulunamadı.")
        return

    for file in candidate_files:
        print(f"  • {file.name} ({source.type}) -> işlenmek üzere kuyruğa alındı.")
        # Burada gerçek PDF/JSON ayrıştırma kodu yer alacak.


def run_ingest(cfg: IngestConfig) -> None:
    ensure_dir(cfg.raw_data_dir)
    ensure_dir(cfg.interim_data_dir)
    ensure_dir(cfg.processed_data_dir)

    for source in cfg.sources:
        ingest_source(source, cfg.raw_data_dir)

    print("[green]Tamamlandı:[/green] Veri taraması tamamlandı, ayrıştırma için hazır.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LGS kareköklü ifadeler veri ingest pipeline'ı")
    parser.add_argument("--config", required=True, help="YAML yapılandırma dosyasının yolu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_dict = read_yaml(args.config)
    cfg = IngestConfig.from_dict(config_dict)
    run_ingest(cfg)


if __name__ == "__main__":
    main()

