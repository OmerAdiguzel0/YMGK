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
        """Soru şablonlarını çıkar."""
        templates = []
        
        for q in questions:
            text = q.get("full_text", q.get("raw_text", ""))
            if not text or len(text) < 20:
                continue
            
            # Sayıları ve değişkenleri placeholder'a çevir
            template = self._create_template(text)
            
            if template and len(template) > 30:
                templates.append({
                    "template": template,
                    "original": text[:200],
                    "source": q.get("source_file", "unknown")
                })
        
        return templates
    
    def _create_template(self, text: str) -> str:
        """Metinden şablon oluştur (sayıları ve değişkenleri değiştir)."""
        # Sayıları placeholder'a çevir
        template = re.sub(r'\d+', '<NUM>', text)
        
        # Karekök ifadelerini placeholder'a çevir
        template = re.sub(r'√\d+', '<SQRT>', template)
        template = re.sub(r'\\sqrt\{[^}]+\}', '<SQRT>', template)
        
        # Değişken isimlerini placeholder'a çevir
        template = re.sub(r'\b[a-z]\b', '<VAR>', template, flags=re.IGNORECASE)
        
        # Çok fazla placeholder varsa temizle
        if template.count('<NUM>') > 10 or template.count('<VAR>') > 10:
            return None
        
        return template
    
    def generate_from_template(self, template: str, num_variations: int = 1) -> List[str]:
        """Şablondan yeni sorular üret."""
        variations = []
        
        for _ in range(num_variations):
            # Placeholder'ları rastgele değerlerle değiştir
            question = template
            
            # <NUM> yerine rastgele sayılar
            while '<NUM>' in question:
                num = random.randint(1, 100)
                question = question.replace('<NUM>', str(num), 1)
            
            # <SQRT> yerine rastgele karekök ifadeleri
            while '<SQRT>' in question:
                sqrt_num = random.randint(2, 50)
                question = question.replace('<SQRT>', f'√{sqrt_num}', 1)
            
            # <VAR> yerine rastgele değişken isimleri
            vars_list = ['x', 'y', 'a', 'b', 'c', 'n', 'm']
            while '<VAR>' in question:
                var = random.choice(vars_list)
                question = question.replace('<VAR>', var, 1)
            
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
    
    def generate_questions(
        self,
        num_questions: int = 5,
        method: str = "template",  # "template" veya "llm" veya "hybrid"
        seed_questions: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Yeni sorular üret."""
        generated = []
        
        if method in ["template", "hybrid"]:
            if not self.templates and seed_questions:
                print("[bold]Şablonlar çıkarılıyor...[/bold]")
                self.templates = self.extract_templates(seed_questions)
                print(f"[green]✓ {len(self.templates)} şablon bulundu[/green]")
            
            if self.templates:
                # Şablonlardan soru üret
                templates_to_use = random.sample(
                    self.templates,
                    min(num_questions, len(self.templates))
                )
                
                for template_data in templates_to_use:
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

