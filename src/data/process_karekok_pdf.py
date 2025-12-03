"""karekokcikmis.pdf dosyasını özel olarak işleme scripti."""

from __future__ import annotations

import json
from pathlib import Path

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.data.pdf_extractor import extract_questions_from_pdf
from src.data.pdf_ocr_extractor import extract_questions_with_ocr
from src.data.koklu_filter import is_koklu_question
from src.utils.io import ensure_dir, write_json


def process_karekok_pdf(
    pdf_path: Path,
    output_path: Path,
    use_ocr: bool = True,
    use_text_extraction: bool = True,
    strict_filter: bool = False
) -> None:
    """karekokcikmis.pdf dosyasını işler (hibrit yaklaşım: metin + OCR)."""
    print(f"[bold cyan]Kareköklü İfadeler PDF İşleniyor:[/bold cyan] {pdf_path.name}\n")
    
    if not pdf_path.exists():
        print(f"[red]Hata:[/red] Dosya bulunamadı: {pdf_path}")
        return
    
    all_questions = []
    
    # Yöntem 1: Metin çıkarma (hızlı, ama şekilli soruları kaçırabilir)
    if use_text_extraction:
        print("[bold]1. Metin Çıkarma Yöntemi:[/bold]")
        # Önce filtreleme olmadan TÜM soruları çıkar
        print("   [dim]Tüm sorular çıkarılıyor (filtreleme kapalı)...[/dim]")
        all_text_questions = extract_questions_from_pdf(pdf_path, filter_keywords=False)
        print(f"   [dim]Toplam soru bulundu:[/dim] {len(all_text_questions)}")
        
        # Bu PDF zaten sadece kareköklü ifadeler sorularını içeriyor
        # Filtreleme yapmadan tüm soruları al, sadece geçersiz olanları temizle
        # Önce tüm soruları temizle
        cleaned_questions = []
        
        for q in all_text_questions:
            raw_text = q.get("raw_text", "").strip()
            full_text = q.get("full_text", "").strip()
            question_num = q.get("question_number", "")
            
            # Çok kısa veya geçersiz soruları atla
            if len(raw_text) < 30:
                continue
            
            # Sayfa başlıkları ve metadata'yı atla
            if "Kareköklü İfadeler LGS ÇIKMIŞ SORULAR" in raw_text:
                if len(raw_text) < 150:  # Sadece başlık, soru yok
                    continue
            if "--- Sayfa" in raw_text:
                continue
            if "S G L" in raw_text and len(raw_text) < 50:  # Yıl bilgisi
                continue
            
            # Soru numarası kontrolü
            if question_num == "0":
                # Soru numarası 0 olanlar genelde başlık, ama kontrol et
                if "?" not in raw_text and not any(opt in raw_text for opt in ["A)", "B)", "C)", "D)"]):
                    continue
                # Eğer gerçekten soru gibi görünüyorsa, numarayı düzelt
                # (Muhtemelen parse hatası)
            
            # Geçerli soru - temizleme sonrası ekle
            q["is_koklu"] = True
            cleaned_questions.append(q)
        
        # Duplikasyon kontrolü: Aynı soru numarası için en iyi versiyonu seç
        questions_by_num = {}
        for q in cleaned_questions:
            q_num = q.get("question_number", "unknown")
            raw_text = q.get("raw_text", "")
            options = q.get("options", [])
            
            # Soru numarası kontrolü - çok yüksek sayıları atla (muhtemelen parse hatası)
            if q_num.isdigit():
                num = int(q_num)
                if num > 100:  # Çok yüksek sayılar (muhtemelen parse hatası)
                    continue
            
            # Aynı numaralı soru varsa, daha iyi olanı seç
            if q_num not in questions_by_num:
                questions_by_num[q_num] = q
            else:
                existing = questions_by_num[q_num]
                # Daha uzun ve daha çok seçenek içeren olanı seç
                if len(raw_text) > len(existing.get("raw_text", "")) or \
                   len(options) > len(existing.get("options", [])):
                    questions_by_num[q_num] = q
        
        # Sonuç listesine ekle
        text_questions = list(questions_by_num.values())
        
        print(f"   [green]Geçerli sorular:[/green] {len(text_questions)}\n")
        all_questions.extend(text_questions)
    
    # Yöntem 2: OCR (yavaş ama şekilli soruları yakalar)
    if use_ocr:
        print("[bold]2. OCR Yöntemi (Şekilli Sorular):[/bold]")
        ocr_questions = extract_questions_with_ocr(pdf_path, filter_koklu=True)
        print(f"   [green]Bulundu:[/green] {len(ocr_questions)} soru\n")
        
        # OCR sorularını ekle (duplikasyon kontrolü yap)
        # Soru numarasına göre kontrol et, ama her iki versiyonu da değerlendir
        existing_nums = {q.get("question_number", "") for q in all_questions}
        existing_texts = {q.get("full_text", "")[:150].lower().strip() for q in all_questions}
        
        for q in ocr_questions:
            q_num = q.get("question_number", "")
            q_text = q.get("full_text", "")[:150].lower().strip()
            
            # Aynı numaralı soru varsa, OCR verilerini mevcut soruya ekle
            if q_num in existing_nums:
                # Mevcut soruyu bul
                for existing_q in all_questions:
                    if existing_q.get("question_number") == q_num:
                        # OCR verilerini ekle
                        existing_q["raw_text_ocr"] = q.get("raw_text", "")
                        existing_q["full_text_ocr"] = q.get("full_text", "")
                        if q.get("options"):
                            existing_q["options_ocr"] = q.get("options", [])
                        existing_q["extraction_method"] = "hybrid"
                        existing_q["note"] = "Metin ve OCR versiyonları birleştirildi"
                        # OCR versiyonu daha temizse kullan
                        if "(cid:" not in q.get("raw_text", "") and "(cid:" in existing_q.get("raw_text", ""):
                            existing_q["raw_text"] = q.get("raw_text", "")
                            existing_q["question_text"] = q.get("raw_text", "")
                            existing_q["has_encoding_issues"] = False
                        break
            else:
                # Yeni soru, ekle
                q["extraction_method"] = "ocr"
                all_questions.append(q)
                existing_nums.add(q_num)
                existing_texts.add(q_text)
    
    # Her soruya kaynak bilgisi ekle ve yeni nesil soru formatına uyarla
    for q in all_questions:
        q["source_file"] = pdf_path.name
        q["source_type"] = "pdf_karekok"
        if "extraction_method" not in q:
            q["extraction_method"] = "text"
        
        # Yeni nesil soru formatı için ek alanlar
        q["question_type"] = "yeni_nesil"  # Varsayılan olarak yeni nesil
        q["has_image"] = q.get("extraction_method") == "ocr"  # OCR ile çıkarıldıysa görsel var
        q["has_table"] = "tablo" in q.get("full_text", "").lower() or "tablo" in q.get("raw_text", "").lower()
        q["has_graph"] = "grafik" in q.get("full_text", "").lower() or "grafik" in q.get("raw_text", "").lower()
        
        # Soru metnini temizle ve yapılandır
        raw_text = q.get("raw_text", "")
        full_text = q.get("full_text", "")
        
        # (cid:...) karakter kodlarını temizle (mümkünse)
        # Bu kodlar PDF font encoding sorunlarından kaynaklanıyor
        import re
        cleaned_text = re.sub(r'\(cid:\d+\)', '', raw_text)
        if cleaned_text != raw_text:
            q["raw_text_cleaned"] = cleaned_text
            q["has_encoding_issues"] = True
        else:
            q["has_encoding_issues"] = False
        
        # Soru uzunluğuna göre tip belirle
        if len(full_text) > 500:
            q["complexity"] = "yüksek"
        elif len(full_text) > 200:
            q["complexity"] = "orta"
        else:
            q["complexity"] = "düşük"
    
    # Sonuçları kaydet
    ensure_dir(output_path.parent)
    write_json(all_questions, output_path)
    
    print(f"\n[bold green]✓ Çıkarma Tamamlandı![/bold green]")
    print(f"[green]Toplam kareköklü ifadeler sorusu:[/green] {len(all_questions)}")
    print(f"[green]Kaydedildi:[/green] {output_path}")
    
    # İstatistikler
    text_count = sum(1 for q in all_questions if q.get("extraction_method") == "text")
    ocr_count = sum(1 for q in all_questions if q.get("extraction_method") == "ocr")
    hybrid_count = sum(1 for q in all_questions if q.get("extraction_method") == "hybrid")
    
    print(f"\n[dim]İstatistikler:[/dim]")
    print(f"  • Metin çıkarma: {text_count} soru")
    print(f"  • OCR: {ocr_count} soru")
    if hybrid_count > 0:
        print(f"  • Hybrid: {hybrid_count} soru")
    
    # Doğrulama önerisi
    print(f"\n[bold yellow]💡 Sonraki Adım:[/bold yellow]")
    print(f"  Verileri doğrulamak için çalıştır:")
    print(f"  python3 -m src.data.validate_extraction --file {output_path} --expected <beklenen_soru_sayısı>")


def main():
    """Ana fonksiyon."""
    pdf_path = Path("data/raw/lgs_meb_koklu/karekokcikmis.pdf")
    output_path = Path("data/interim/karekok_questions.json")
    
    process_karekok_pdf(
        pdf_path=pdf_path,
        output_path=output_path,
        use_ocr=True,  # Tesseract yüklü, OCR aktif
        use_text_extraction=True,  # Hızlı metin çıkarma açık
        strict_filter=False  # Esnek filtreleme (tüm soruları kontrol et)
    )


if __name__ == "__main__":
    main()

