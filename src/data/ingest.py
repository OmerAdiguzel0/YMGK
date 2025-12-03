from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass
from typing import List

from rich import print

from src.data.image_ocr import extract_question_from_image
from src.data.pdf_extractor import extract_questions_from_pdf
from src.data.process_karekok_pdf import process_karekok_pdf
from src.utils.io import ensure_dir, read_yaml, write_json


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


def ingest_source(
    source: SourceSpec, 
    raw_dir: pathlib.Path, 
    interim_dir: pathlib.Path
) -> List[dict]:
    """Bir veri kaynağından soruları çıkarır ve yapılandırır."""
    print(f"[bold cyan]Kaynak taranıyor:[/bold cyan] {source.name}")
    candidate_files = list(raw_dir.glob(source.pattern))
    if not candidate_files:
        print(f"[yellow]Uyarı:[/yellow] {source.pattern} kalıbı için dosya bulunamadı.")
        return []

    all_questions = []
    
    for file in candidate_files:
        print(f"  • {file.name} ({source.type}) -> işleniyor...")
        
        if source.type == "pdf":
            # Özel dosya: karekokcikmis.pdf için OCR destekli işleme
            if "karekok" in file.name.lower() and source.metadata.get("use_ocr", False):
                print(f"  [bold yellow]Özel işleme:[/bold yellow] OCR destekli işleme aktif")
                output_file = interim_dir / f"{file.stem}_questions.json"
                process_karekok_pdf(
                    pdf_path=file,
                    output_path=output_file,
                    use_ocr=True,
                    use_text_extraction=True
                )
                # JSON'dan soruları yükle
                try:
                    import json
                    with output_file.open("r", encoding="utf-8") as f:
                        questions = json.load(f)
                    all_questions.extend(questions)
                except Exception as e:
                    print(f"[red]Hata:[/red] JSON yüklenemedi: {e}")
            else:
                # Normal PDF işleme
                questions = extract_questions_from_pdf(file, filter_keywords=True)
                # Her soruya metadata ekle
                for q in questions:
                    q["source_file"] = file.name
                    q["source_type"] = "pdf"
                    q["source_name"] = source.name
                all_questions.extend(questions)
        
        elif source.type == "json":
            # JSON dosyasından soruları oku
            try:
                with file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        questions = data
                    elif isinstance(data, dict) and "questions" in data:
                        questions = data["questions"]
                    else:
                        questions = [data]
                    
                    for q in questions:
                        q["source_file"] = file.name
                        q["source_type"] = "json"
                        q["source_name"] = source.name
                    all_questions.extend(questions)
            except Exception as e:
                print(f"[red]Hata:[/red] {file.name} okunamadı: {e}")
        
        elif source.type == "image":
            # Görsel dosyalarından OCR ile çıkar
            question_data = extract_question_from_image(file)
            if question_data:
                question_data["source_file"] = file.name
                question_data["source_type"] = "image"
                question_data["source_name"] = source.name
                all_questions.append(question_data)
    
    return all_questions


def run_ingest(cfg: IngestConfig) -> None:
    """Ana ingest pipeline'ı çalıştırır."""
    ensure_dir(cfg.raw_data_dir)
    ensure_dir(cfg.interim_data_dir)
    ensure_dir(cfg.processed_data_dir)

    all_questions = []
    
    # Her kaynaktan soruları çıkar
    for source in cfg.sources:
        questions = ingest_source(source, cfg.raw_data_dir, cfg.interim_data_dir)
        all_questions.extend(questions)
    
    # Görsel klasöründen de soruları çıkar
    images_dir = cfg.raw_data_dir / "images"
    if images_dir.exists():
        print(f"[bold cyan]Görsel klasörü taranıyor:[/bold cyan] {images_dir}")
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))
        for img_file in image_files:
            question_data = extract_question_from_image(img_file)
            if question_data:
                question_data["source_file"] = img_file.name
                question_data["source_type"] = "image"
                question_data["source_name"] = "manual_images"
                all_questions.append(question_data)
    
    # Soruları JSON olarak kaydet
    if all_questions:
        output_file = cfg.interim_data_dir / "extracted_questions.json"
        write_json(all_questions, output_file)
        print(f"[green]Tamamlandı:[/green] {len(all_questions)} soru çıkarıldı ve {output_file} dosyasına kaydedildi.")
    else:
        print("[yellow]Uyarı:[/yellow] Hiç soru çıkarılamadı. Veri dosyalarını kontrol edin.")


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

