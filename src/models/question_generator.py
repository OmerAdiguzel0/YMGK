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
    
    def generate_from_original(self, original_text: str, num_variations: int = 1) -> List[str]:
        """Orijinal sorudan sadece sayıları değiştirerek yeni sorular üret (daha güvenli)."""
        variations = []
        
        for _ in range(num_variations):
            question = original_text
            
            # Temizlik
            question = re.sub(r'\(cid:\d+\)', '', question)
            question = re.sub(r'\s+', ' ', question).strip()
            
            # Sadece sayıları değiştir (seçeneklerdeki sayıları koru)
            # Seçenekleri koru: A) 12, B) 34 gibi
            option_pattern = r'([A-D])[\.\)]\s*(\d+)'
            
            def replace_number(match):
                letter = match.group(1)
                num = int(match.group(2))
                # Seçeneklerdeki sayıları biraz değiştir (ama mantıklı aralıkta)
                if num < 10:
                    new_num = random.randint(1, 20)
                elif num < 50:
                    new_num = random.randint(10, 60)
                else:
                    new_num = random.randint(40, 100)
                return f"{letter}) {new_num}"
            
            # Seçeneklerdeki sayıları değiştir
            question = re.sub(option_pattern, replace_number, question)
            
            # Diğer sayıları değiştir (ama daha dikkatli)
            # Soru metnindeki sayıları bul ve değiştir
            def replace_other_number(match):
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
            
            # Seçenekler dışındaki sayıları değiştir
            # Önce seçenekleri koru
            options_text = ' '.join(re.findall(r'[A-D][\.\)]\s*\d+', question))
            question_without_options = question
            
            # Seçenekleri geçici olarak değiştir
            temp_question = re.sub(r'[A-D][\.\)]\s*\d+', '<OPT>', question_without_options)
            # Sayıları değiştir
            temp_question = re.sub(r'\b\d+\b', replace_other_number, temp_question)
            # Seçenekleri geri koy
            option_matches = re.findall(r'[A-D][\.\)]\s*\d+', question)
            for opt in option_matches:
                temp_question = temp_question.replace('<OPT>', opt, 1)
            question = temp_question
            
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
            # Kaliteli soruları seç
            quality_questions = [
                q for q in seed_questions 
                if q.get("full_text", q.get("raw_text", "")) and 
                   len(q.get("full_text", q.get("raw_text", ""))) > 50 and
                   len(q.get("full_text", q.get("raw_text", ""))) < 500
            ]
            
            if quality_questions:
                selected = random.sample(
                    quality_questions,
                    min(num_questions, len(quality_questions))
                )
                
                for q in selected:
                    text = q.get("full_text", q.get("raw_text", ""))
                    variations = self.generate_from_original(text, num_variations=1)
                    
                    for var in variations:
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

