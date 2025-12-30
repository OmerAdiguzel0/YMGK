"""Soru üretim modeli - Template-based ve generation yaklaşımı."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from rich import print
from rich.console import Console
from rich.table import Table

from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch


class QuestionGenerator:
    """Kareköklü ifadeler soruları üreten model."""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.console = Console()
        self.templates = []
        self.question_patterns = []
        self.model = None
        self.tokenizer = None
        self.use_llm = False
        
        if model_path and model_path.exists():
            self._load_llm_model(model_path)
    
    def _load_llm_model(self, model_path: Path):
        """LLM modelini yükle (opsiyonel)."""
        try:
            print("[dim]LLM modeli yükleniyor...[/dim]")
            # Türkçe GPT-2 veya fine-tuned model
            self.tokenizer = GPT2Tokenizer.from_pretrained(str(model_path))
            self.model = GPT2LMHeadModel.from_pretrained(str(model_path))
            self.model.eval()
            self.use_llm = True
            print("[green]✓ LLM modeli yüklendi[/green]")
        except Exception as e:
            print(f"[yellow]Uyarı:[/yellow] LLM modeli yüklenemedi: {e}")
            print("[dim]Template-based generation kullanılacak[/dim]")
    
    def extract_templates(self, questions: List[Dict]) -> List[Dict]:
        """Soru şablonlarını çıkar (daha kaliteli)."""
        templates = []
        
        for q in questions:
            text = q.get("full_text", q.get("raw_text", ""))
            if not text or len(text) < 30:
                continue
            
            # Temizlik: Encoding sorunlarını temizle
            text = re.sub(r'\(cid:\d+\)', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Çok kısa veya çok uzun soruları atla
            if len(text) < 30 or len(text) > 2000:
                continue
            
            # Şablon oluştur
            template = self._create_template(text)
            
            if template and len(template) > 30:
                # Şablon kalitesi kontrolü
                # Çok fazla placeholder varsa reddet
                placeholder_ratio = (template.count('<NUM>') + template.count('<VAR>') + template.count('<SQRT>')) / len(template)
                if placeholder_ratio > 0.3:  # %30'dan fazla placeholder varsa
                    continue
                
                templates.append({
                    "template": template,
                    "original": text[:300],
                    "source": q.get("source_file", "unknown"),
                    "quality_score": 1.0 - placeholder_ratio  # Daha az placeholder = daha yüksek kalite
                })
        
        # Kaliteye göre sırala
        templates.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        return templates
    
    def _create_template(self, text: str) -> str:
        """Metinden şablon oluştur (sadece matematiksel değerleri değiştir)."""
        template = text
        
        # Önce karekök ifadelerini koru (sonra değiştirilecek)
        sqrt_patterns = re.findall(r'√\d+|\\sqrt\{[^}]+\}', template)
        for i, pattern in enumerate(sqrt_patterns):
            template = template.replace(pattern, f'<SQRT_{i}>', 1)
        
        # Sadece matematiksel değişkenleri değiştir (x, y, a, b, c, n, m)
        # Kelimelerin içindeki harfleri değil, bağımsız değişkenleri
        math_vars = ['x', 'y', 'a', 'b', 'c', 'n', 'm', 'k', 'p', 'q']
        for var in math_vars:
            # Sadece kelime sınırlarında ve matematiksel bağlamda olanları
            pattern = r'\b' + var + r'\b(?![a-z])'  # Sonrasında küçük harf olmayan
            template = re.sub(pattern, '<VAR>', template, flags=re.IGNORECASE)
        
        # Sayıları değiştir (ama çok fazla değil)
        # Önce seçeneklerdeki sayıları koru
        options_pattern = r'([A-D])[\.\)]\s*(\d+)'
        options_matches = list(re.finditer(options_pattern, template))
        option_numbers = {}
        for i, match in enumerate(options_matches):
            option_numbers[f'<OPT_NUM_{i}>'] = match.group(2)
            template = template[:match.start(2)] + f'<OPT_NUM_{i}>' + template[match.end(2):]
        
        # Kalan sayıları değiştir (ama çok fazla değilse)
        num_count = len(re.findall(r'\d+', template))
        if num_count <= 15:  # Makul sayıda sayı varsa
            template = re.sub(r'\b\d+\b', '<NUM>', template)
        else:
            # Çok fazla sayı varsa, sadece bazılarını değiştir
            numbers = re.findall(r'\b\d+\b', template)
            # İlk 10 sayıyı değiştir
            for num in numbers[:10]:
                template = template.replace(num, '<NUM>', 1)
        
        # Option placeholder'ları geri koy
        for placeholder, num in option_numbers.items():
            template = template.replace(placeholder, num)
        
        # SQRT placeholder'ları geri koy
        for i, pattern in enumerate(sqrt_patterns):
            template = template.replace(f'<SQRT_{i}>', '<SQRT>', 1)
        
        # Çok fazla placeholder varsa reddet
        if template.count('<NUM>') > 12 or template.count('<VAR>') > 8:
            return None
        
        return template
    
    def generate_from_template(self, template: str, num_variations: int = 1) -> List[str]:
        """Şablondan yeni sorular üret (daha akıllı değiştirme)."""
        variations = []
        
        for _ in range(num_variations):
            question = template
            
            # <VAR> yerine rastgele değişken isimleri (tutarlılık için)
            vars_list = ['x', 'y', 'a', 'b', 'c', 'n', 'm']
            var_mapping = {}  # Aynı placeholder için aynı değişkeni kullan
            var_count = 0
            
            while '<VAR>' in question:
                if var_count not in var_mapping:
                    var_mapping[var_count] = random.choice(vars_list)
                var = var_mapping[var_count]
                question = question.replace('<VAR>', var, 1)
                var_count += 1
            
            # <SQRT> yerine rastgele karekök ifadeleri
            sqrt_numbers = []
            while '<SQRT>' in question:
                sqrt_num = random.randint(2, 50)
                sqrt_numbers.append(sqrt_num)
                question = question.replace('<SQRT>', f'√{sqrt_num}', 1)
            
            # <NUM> yerine rastgele sayılar (context'e göre)
            num_count = 0
            while '<NUM>' in question:
                # İlk birkaç sayı için daha küçük aralık (genelde soru başında)
                if num_count < 3:
                    num = random.randint(1, 50)
                else:
                    num = random.randint(1, 100)
                question = question.replace('<NUM>', str(num), 1)
                num_count += 1
            
            # Temizlik: Çift boşlukları düzelt
            question = re.sub(r'\s+', ' ', question)
            question = question.strip()
            
            variations.append(question)
        
        return variations
    
    def generate_with_llm(self, prompt: str, max_length: int = 200, num_return_sequences: int = 1) -> List[str]:
        """LLM ile soru üret."""
        if not self.use_llm:
            return []
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors='pt')
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    num_return_sequences=num_return_sequences,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated = []
            for output in outputs:
                text = self.tokenizer.decode(output, skip_special_tokens=True)
                # Prompt'u çıkar
                text = text[len(prompt):].strip()
                generated.append(text)
            
            return generated
        except Exception as e:
            print(f"[red]Hata:[/red] LLM generation hatası: {e}")
            return []
    
    def _clean_question_text(self, text: str) -> str:
        """Soru metnini temizle ve düzelt."""
        # Encoding sorunlarını temizle
        text = re.sub(r'\(cid:\d+\)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Çok uzun metinleri kısalt (muhtemelen birleşmiş sorular)
        if len(text) > 500:
            # Soru işareti veya seçenek başlangıcına kadar al
            question_end = max(
                text.find('?'),
                text.find('A)'),
                text.find('B)'),
                text.find('C)'),
                text.find('D)')
            )
            if question_end > 100:  # En az 100 karakter olsun
                text = text[:question_end + 1]
        
        return text
    
    def _extract_single_question(self, text: str) -> Optional[str]:
        """Metinden tek bir soru çıkar (birleşmiş soruları ayır) - daha agresif."""
        # Önce temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Soru başlangıçlarını bul (yaygın soru başlangıçları)
        question_starters = [
            r'Aşağıdaki',
            r'Yukarıdaki',
            r'Yukarıda',
            r'Aşağıda',
            r'Bir',
            r'İki',
            r'Üç',
            r'Dört',
            r'Beş',
            r'Kare',
            r'Dikdörtgen',
            r'Üçgen',
            r'Çember',
            r'Sayı',
            r'Tam',
            r'Karekök',
            r'√',
            r'Alanı',
            r'Çevresi',
            r'Kenar',
            r'Uzunluk',
            r'Hangi',
            r'Kaç',
            r'Hangisi',
            r'Buna göre',
            r'Eğer',
            r'Verilen'
        ]
        
        # İlk soru başlangıcını bul
        best_start = -1
        for starter in question_starters:
            pattern = r'\b' + starter + r'\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if match and (best_start == -1 or match.start() < best_start):
                best_start = match.start()
        
        # Soru başlangıcından itibaren al
        if best_start > 0:
            text = text[best_start:]
        
        # İlk soru işaretine kadar al
        first_question_mark = text.find('?')
        if first_question_mark > 20:  # En az 20 karakter olsun
            question_part = text[:first_question_mark + 1]
            
            # Soru kısmının geçerli olup olmadığını kontrol et
            # Çok kısa veya anlamsız olmamalı
            if len(question_part) < 20:
                return None
            
            # Seçenekleri bul (soru işaretinden sonraki ilk 4 seçenek)
            after_question = text[first_question_mark + 1:]
            # Seçenekleri daha iyi parse et
            options = []
            option_pattern = r'([A-D])[\.\)]\s*([^A-D]*?)(?=[A-D][\.\)]|$)'
            for match in re.finditer(option_pattern, after_question):
                letter = match.group(1)
                content = match.group(2).strip()
                # Çok uzun seçenekleri atla (muhtemelen yanlış parse)
                if len(content) < 50:
                    options.append(f"{letter}) {content}")
            
            # İlk 4 seçeneği al
            if len(options) >= 4:
                options_text = ' '.join(options[:4])
                result = (question_part + ' ' + options_text).strip()
                # Son kontrol: çok kısa veya çok uzun olmamalı
                if 30 <= len(result) <= 300:
                    return result
            elif len(options) > 0:
                options_text = ' '.join(options)
                result = (question_part + ' ' + options_text).strip()
                if 30 <= len(result) <= 300:
                    return result
            else:
                # Seçenek yoksa sadece soru kısmını döndür (ama yeterince uzunsa)
                if 30 <= len(question_part) <= 200:
                    return question_part.strip()
        
        return None
    
    def generate_from_original(self, original_text: str, num_variations: int = 1) -> List[str]:
        """Orijinal sorudan sadece sayıları değiştirerek yeni sorular üret (daha güvenli)."""
        variations = []
        
        # Önce soruyu temizle ve tek soru çıkar
        cleaned = self._clean_question_text(original_text)
        single_question = self._extract_single_question(cleaned)
        
        if not single_question or len(single_question) < 30:
            return []
        
        for _ in range(num_variations):
            question = single_question
            
            # Seçenekleri bul ve koru
            option_matches = list(re.finditer(r'([A-D])[\.\)]\s*(\d+)', question))
            
            # Seçenekleri geçici olarak değiştir (ters sırada, index kaymasını önlemek için)
            option_placeholders = {}
            for i, match in enumerate(reversed(option_matches)):
                placeholder = f'__OPT_PLACEHOLDER_{len(option_matches)-1-i}__'
                option_placeholders[placeholder] = match.group(0)
                # Ters sırada değiştir ki index kayması olmasın
                start, end = match.span()
                question = question[:start] + placeholder + question[end:]
            
            # Sayıları değiştir (seçenekler hariç - placeholder'lar sayı içermiyor)
            def replace_number(match):
                num = int(match.group(0))
                # Sayı aralığına göre değiştir
                if num < 10:
                    return str(random.randint(2, 15))
                elif num < 50:
                    return str(random.randint(10, 60))
                elif num < 100:
                    return str(random.randint(50, 120))
                else:
                    return str(random.randint(80, 200))
            
            question = re.sub(r'\b\d+\b', replace_number, question)
            
            # Seçenekleri geri koy (sayıları da değiştir)
            for placeholder, original_opt in option_placeholders.items():
                # Seçenekteki sayıyı değiştir
                opt_match = re.match(r'([A-D])[\.\)]\s*(\d+)', original_opt)
                if opt_match:
                    letter = opt_match.group(1)
                    num = int(opt_match.group(2))
                    # Seçeneklerdeki sayıları biraz değiştir
                    if num < 10:
                        new_num = random.randint(1, 20)
                    elif num < 50:
                        new_num = random.randint(10, 60)
                    else:
                        new_num = random.randint(40, 100)
                    new_opt = f"{letter}) {new_num}"
                    question = question.replace(placeholder, new_opt)
                else:
                    # Eğer parse edilemediyse, orijinalini koy
                    question = question.replace(placeholder, original_opt)
            
            # Final temizlik
            question = re.sub(r'\s+', ' ', question).strip()
            variations.append(question)
        
        return variations
    
    def generate_questions(
        self,
        num_questions: int = 5,
        method: str = "template",  # "template", "original", "llm", "hybrid"
        seed_questions: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Yeni sorular üret."""
        generated = []
        
        # Orijinal sorulardan varyasyon üret (daha güvenli)
        if method in ["original", "hybrid"] and seed_questions:
            # Kaliteli soruları seç (daha sıkı kriterler)
            quality_questions = []
            for q in seed_questions:
                text = q.get("full_text", q.get("raw_text", ""))
                if not text:
                    continue
                
                # Temizle
                text = self._clean_question_text(text)
                
                # Tek soru çıkar (birleşmiş soruları ayır)
                single_q = self._extract_single_question(text)
                if not single_q or len(single_q) < 30:
                    continue
                
                # Kalite kriterleri (çok sıkı)
                has_question_mark = '?' in single_q
                has_options = bool(re.search(r'[A-D][\.\)]', single_q))
                reasonable_length = 40 <= len(single_q) <= 250
                not_too_many_numbers = 2 <= len(re.findall(r'\d+', single_q)) <= 10
                
                # Soru anlamlı başlamalı (yaygın soru başlangıçları)
                meaningful_start = any(
                    single_q.strip().startswith(starter) or 
                    single_q.strip().lower().startswith(starter.lower())
                    for starter in ['Aşağıdaki', 'Yukarıdaki', 'Yukarıda', 'Aşağıda', 
                                   'Bir', 'İki', 'Üç', 'Kare', 'Sayı', 'Tam', 'Alanı', 
                                   'Çevresi', 'Hangi', 'Kaç', 'Buna göre', 'Verilen']
                ) or single_q.strip()[0].isupper()  # Büyük harfle başlamalı
                
                # Anlamsız karakterler çok az olmalı
                special_chars = len(re.findall(r'[^a-zA-Z0-9\s\.\,\?\(\)\[\]\-\+\=\√]', single_q))
                reasonable_special = special_chars <= 5
                
                # Tekrarlanan karakterler olmamalı (ör: "AAAA" veya "1111")
                no_repeated_chars = not re.search(r'(.)\1{4,}', single_q)
                
                # Geçerli Türkçe karakterler içermeli
                has_turkish_chars = bool(re.search(r'[a-zA-ZçğıöşüÇĞIİÖŞÜ]', single_q))
                
                if (has_question_mark and has_options and reasonable_length and 
                    not_too_many_numbers and reasonable_special and 
                    meaningful_start and no_repeated_chars and has_turkish_chars):
                    quality_questions.append({
                        **q,
                        "cleaned_text": single_q
                    })
            
            if quality_questions:
                selected = random.sample(
                    quality_questions,
                    min(num_questions, len(quality_questions))
                )
                
                for q in selected:
                    text = q.get("cleaned_text", q.get("full_text", q.get("raw_text", "")))
                    variations = self.generate_from_original(text, num_variations=1)
                    
                    for var in variations:
                        if var and len(var) > 30:  # Geçerli soru kontrolü
                            generated.append({
                                "question_text": var,
                                "generation_method": "original_variation",
                                "source": q.get("source_file", "unknown")
                            })
        
        if method in ["template", "hybrid"]:
            if not self.templates and seed_questions:
                print("[bold]Şablonlar çıkarılıyor...[/bold]")
                self.templates = self.extract_templates(seed_questions)
                print(f"[green]✓ {len(self.templates)} şablon bulundu[/green]")
            
            if self.templates:
                # En kaliteli şablonları kullan
                quality_templates = sorted(
                    self.templates,
                    key=lambda x: x.get("quality_score", 0),
                    reverse=True
                )[:num_questions]
                
                for template_data in quality_templates:
                    template = template_data["template"]
                    variations = self.generate_from_template(template, num_variations=1)
                    
                    for var in variations:
                        generated.append({
                            "question_text": var,
                            "generation_method": "template",
                            "source_template": template_data["original"][:100]
                        })
        
        if method in ["llm", "hybrid"] and self.use_llm:
            # LLM ile soru üret
            prompts = [
                "Aşağıdaki sayılardan hangisi tam kare sayıdır?",
                "Karekök ifadesi:",
                "Sayı doğrusu üzerinde:",
                "Kareköklü ifadeler sorusu:"
            ]
            
            for prompt in prompts[:num_questions]:
                llm_generated = self.generate_with_llm(prompt, num_return_sequences=1)
                for text in llm_generated:
                    if text and len(text) > 20:
                        generated.append({
                            "question_text": text,
                            "generation_method": "llm",
                            "prompt": prompt
                        })
        
        return generated[:num_questions]
    
    def save_templates(self, output_path: Path):
        """Şablonları kaydet."""
        if self.templates:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            print(f"[green]✓ Şablonlar kaydedildi:[/green] {output_path}")
    
    def load_templates(self, input_path: Path):
        """Şablonları yükle."""
        if input_path.exists():
            with input_path.open("r", encoding="utf-8") as f:
                self.templates = json.load(f)
            print(f"[green]✓ {len(self.templates)} şablon yüklendi[/green]")


def train_generator(questions_path: Path, output_dir: Path):
    """Soru üretici modeli eğit (şablon çıkarma)."""
    print("[bold cyan]Soru Üretim Modeli Eğitimi[/bold cyan]\n")
    
    # Soruları yükle
    if questions_path.suffix == ".json":
        with questions_path.open("r", encoding="utf-8") as f:
            questions = json.load(f)
    else:
        df = pd.read_csv(questions_path)
        questions = df.to_dict("records")
    
    print(f"[green]Toplam soru:[/green] {len(questions)}")
    
    # Generator oluştur
    generator = QuestionGenerator()
    
    # Şablonları çıkar
    print("\n[bold]Şablon çıkarma...[/bold]")
    templates = generator.extract_templates(questions)
    generator.templates = templates
    
    print(f"[green]✓ {len(templates)} şablon çıkarıldı[/green]")
    
    # Şablonları kaydet
    output_dir.mkdir(parents=True, exist_ok=True)
    templates_path = output_dir / "templates.json"
    generator.save_templates(templates_path)
    
    # Örnek üretim
    print("\n[bold cyan]Örnek Soru Üretimi:[/bold cyan]\n")
    sample_questions = generator.generate_questions(num_questions=3, method="template")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Sıra", style="dim", width=6)
    table.add_column("Üretilen Soru", width=80)
    table.add_column("Yöntem", width=15)
    
    for i, q in enumerate(sample_questions, 1):
        table.add_row(
            str(i),
            q["question_text"][:150] + "..." if len(q["question_text"]) > 150 else q["question_text"],
            q["generation_method"]
        )
    
    print(table)
    
    print(f"\n[bold green]✓ Model hazır![/bold green]")
    print(f"[green]Model dizini:[/green] {output_dir}")
    
    return generator

