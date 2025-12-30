"""Mevcut veri setinden sadece en temiz soruları filtrele."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict

from rich import print
from rich.table import Table


def is_clean_question(question: Dict) -> bool:
    """Soru temiz mi kontrol et (çok sıkı kriterler)."""
    text = question.get("full_text", question.get("raw_text", ""))
    if not text:
        return False
    
    # Temizle
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 1. Uzunluk kontrolü (biraz daha esnek)
    if not (30 <= len(text) <= 500):
        return False
    
    # 2. Soru işareti olmalı
    if '?' not in text:
        return False
    
    # 3. Seçenekler olmalı (en az 2)
    options = re.findall(r'[A-D][\.\)]', text)
    if len(options) < 2:
        return False
    
    # 4. Anlamlı başlangıç (daha esnek)
    text_stripped = text.strip()
    
    # Kötü başlangıçları reddet
    bad_starts = ['sayı olmak', 'ave', 'yay', 'cm', 'br?', 'm?']
    if any(text_stripped.lower().startswith(bs) for bs in bad_starts):
        return False
    
    # İyi başlangıçlar (opsiyonel - varsa bonus)
    meaningful_starts = [
        'Aşağıdaki', 'Yukarıdaki', 'Yukarıda', 'Aşağıda',
        'Bir', 'İki', 'Üç', 'Dört', 'Beş',
        'Kare', 'Dikdörtgen', 'Üçgen', 'Çember',
        'Sayı', 'Tam', 'Alanı', 'Çevresi', 'Kenar', 'Uzunluk',
        'Hangi', 'Kaç', 'Hangisi', 'Buna göre', 'Verilen',
        'Eğer', 'Düzgün', 'Ardışık', 'Doğal', 'Tam sayı',
        'İşlemin', 'Sonucu', 'Arası', 'Arasında'
    ]
    
    starts_well = (
        any(text_stripped.startswith(s) for s in meaningful_starts) or
        (text_stripped and text_stripped[0].isupper() and not text_stripped[0].isdigit() and
         not text_stripped[0] in ['<', '(', '[', '{'])
    )
    
    if not starts_well:
        return False
    
    # 6. Encoding sorunları olmamalı
    if '(cid:' in question.get("full_text", "") or '(cid:' in question.get("raw_text", ""):
        return False
    
    # 7. Sayı sayısı makul olmalı (daha esnek)
    numbers = re.findall(r'\d+', text)
    if len(numbers) < 1 or len(numbers) > 20:
        return False
    
    # 8. Çok fazla özel karakter olmamalı (daha esnek)
    special_chars = len(re.findall(r'[^a-zA-Z0-9\s\.\,\?\(\)\[\]\-\+\=\√]', text))
    if special_chars > 10:
        return False
    
    # 9. Tekrarlanan karakterler olmamalı (daha esnek)
    if re.search(r'(.)\1{6,}', text):  # 6'dan fazla tekrar
        return False
    
    # 10. Türkçe karakterler içermeli
    if not re.search(r'[a-zA-ZçğıöşüÇĞIİÖŞÜ]', text):
        return False
    
    # 11. İlk soru işaretine kadar geçerli bir soru olmalı (daha esnek)
    q_mark_idx = text.find('?')
    if q_mark_idx > 0:
        question_part = text[:q_mark_idx + 1]
        if len(question_part) < 15:  # Daha kısa sorulara izin ver
            return False
        # Soru kısmı anlamlı olmalı (daha esnek)
        question_lower = question_part.lower()
        meaningful_words = ['kaç', 'hangi', 'hangisi', 'nedir', 'olur', 'olur?', 
                          'sonucu', 'sonucu?', 'arasında', 'arasındadır', 'işlemin',
                          'sayı', 'tam', 'kare', 'alan', 'çevre']
        if not any(word in question_lower for word in meaningful_words):
            # Eğer hiçbir anlamlı kelime yoksa, en azından büyük harfle başlamalı
            if not question_part[0].isupper():
                return False
    
    return True


def extract_clean_question_text(question: Dict) -> str:
    """Temiz soru metnini çıkar (tek soru, düzgün format)."""
    text = question.get("full_text", question.get("raw_text", ""))
    
    # Temizle
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # İlk soru işaretine kadar al
    q_mark_idx = text.find('?')
    if q_mark_idx > 0:
        question_part = text[:q_mark_idx + 1]
        
        # Seçenekleri bul
        after_question = text[q_mark_idx + 1:]
        options = []
        
        # Seçenekleri parse et
        option_pattern = re.compile(r'([A-D])[\.\)]\s*([^A-D]{0,50}?)(?=[A-D][\.\)]|$)', re.DOTALL)
        for match in option_pattern.finditer(after_question):
            letter = match.group(1)
            content = match.group(2).strip()
            # Çok uzun seçenekleri atla
            if len(content) < 80:
                options.append(f"{letter}) {content}")
        
        # İlk 4 seçeneği al
        if len(options) >= 2:
            return question_part + ' ' + ' '.join(options[:4])
        else:
            return question_part
    
    return text


def filter_clean_questions(input_path: Path, output_path: Path) -> None:
    """Temiz soruları filtrele ve kaydet."""
    print("[bold cyan]Temiz Sorular Filtreleniyor[/bold cyan]\n")
    
    # Soruları yükle
    with input_path.open("r", encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"[dim]Toplam soru:[/dim] {len(questions)}\n")
    
    # Temiz soruları filtrele
    clean_questions = []
    for q in questions:
        if is_clean_question(q):
            # Temiz soru metnini çıkar
            clean_text = extract_clean_question_text(q)
            if clean_text and len(clean_text) >= 30:
                clean_q = {
                    "question_number": q.get("question_number", "unknown"),
                    "question_text": clean_text,
                    "raw_text": clean_text,
                    "full_text": clean_text,
                    "source_file": q.get("source_file", "unknown"),
                    "source_type": q.get("source_type", "pdf"),
                    "is_koklu": True,
                    "quality": "high"
                }
                clean_questions.append(clean_q)
    
    print(f"[green]✓ Temiz soru:[/green] {len(clean_questions)}/{len(questions)}")
    print(f"[green]✓ Oran:[/green] {len(clean_questions)*100//len(questions) if questions else 0}%\n")
    
    # Kaydet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(clean_questions, f, ensure_ascii=False, indent=2)
    
    print(f"[green]✓ Kaydedildi:[/green] {output_path}")
    
    # Örnek sorular göster
    if clean_questions:
        print("\n[bold cyan]Örnek Temiz Sorular:[/bold cyan]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Sıra", style="dim", width=6)
        table.add_column("Soru Metni", width=100)
        table.add_column("Kaynak", width=20)
        
        for i, q in enumerate(clean_questions[:5], 1):
            table.add_row(
                str(i),
                q["question_text"][:150] + "..." if len(q["question_text"]) > 150 else q["question_text"],
                q["source_file"]
            )
        
        print(table)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Temiz soruları filtrele")
    parser.add_argument("--input", default="models/baseline/questions.json", help="Giriş dosyası")
    parser.add_argument("--output", default="models/baseline/clean_questions.json", help="Çıkış dosyası")
    args = parser.parse_args()
    
    filter_clean_questions(Path(args.input), Path(args.output))

