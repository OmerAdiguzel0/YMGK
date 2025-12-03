"""LGS sorularını otomatik olarak indirme scripti."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.utils.io import ensure_dir


class DataDownloader:
    """Veri indirme sınıfı."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = ensure_dir(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def download_file(self, url: str, filename: str) -> bool:
        """Bir dosyayı indirir."""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            file_path = self.output_dir / filename
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[green]✓[/green] İndirildi: {filename}")
            return True
        except Exception as e:
            print(f"[red]✗[/red] Hata ({filename}): {e}")
            return False
    
    def download_meb_example_questions(self, year: int = None) -> int:
        """MEB örnek sorularını indirir."""
        print("[bold cyan]MEB Örnek Sorular indiriliyor...[/bold cyan]")
        
        base_url = "https://odsgm.meb.gov.tr/www/ornek-sorular/icerik/listesi"
        
        try:
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # PDF linklerini bul
            pdf_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if ".pdf" in href.lower() and "matematik" in link.text.lower():
                    full_url = urljoin(base_url, href)
                    pdf_links.append((full_url, link.text.strip()))
            
            downloaded = 0
            for url, title in pdf_links:
                # Yıl filtresi
                if year and str(year) not in title:
                    continue
                
                filename = f"MEB_Ornek_{title.replace(' ', '_')}.pdf"
                if self.download_file(url, filename):
                    downloaded += 1
                time.sleep(1)  # Rate limiting
            
            return downloaded
        except Exception as e:
            print(f"[red]Hata:[/red] MEB sitesine erişilemedi: {e}")
            return 0
    
    def download_dersmatematik(self, year: int = None) -> int:
        """DersMatematik.net'ten soruları indirir."""
        print("[bold cyan]DersMatematik.net'ten indiriliyor...[/bold cyan]")
        
        base_url = "https://dersmatematik.net/lgs/"
        
        try:
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # PDF linklerini bul
            pdf_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if ".pdf" in href.lower() and ("matematik" in link.text.lower() or "mat" in link.text.lower()):
                    full_url = urljoin(base_url, href)
                    pdf_links.append((full_url, link.text.strip()))
            
            downloaded = 0
            for url, title in pdf_links:
                # Yıl filtresi
                if year and str(year) not in title:
                    continue
                
                # Dosya adını temizle
                filename = re.sub(r'[^\w\s-]', '', title).strip()
                filename = re.sub(r'[-\s]+', '_', filename)
                filename = f"LGS_{filename}.pdf"
                
                if self.download_file(url, filename):
                    downloaded += 1
                time.sleep(1)
            
            return downloaded
        except Exception as e:
            print(f"[red]Hata:[/red] DersMatematik.net'e erişilemedi: {e}")
            return 0
    
    def download_from_url(self, url: str, filename: str = None) -> bool:
        """Belirli bir URL'den dosya indirir."""
        if filename is None:
            filename = Path(urlparse(url).path).name
        
        return self.download_file(url, filename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LGS sorularını otomatik indir")
    parser.add_argument(
        "--source",
        choices=["meb", "dersmatematik", "url"],
        default="meb",
        help="Veri kaynağı"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Belirli bir yıl (opsiyonel)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Tüm yılları indir"
    )
    parser.add_argument(
        "--url",
        help="Manuel URL (--source url ile kullan)"
    )
    parser.add_argument(
        "--output",
        default="data/raw/lgs_meb_koklu",
        help="İndirme klasörü"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    downloader = DataDownloader(Path(args.output))
    
    if args.source == "meb":
        if args.all:
            # Tüm yılları dene
            years = range(2018, 2025)
            total = 0
            for year in years:
                print(f"\n[bold]Yıl: {year}[/bold]")
                total += downloader.download_meb_example_questions(year)
            print(f"\n[green]Toplam:[/green] {total} dosya indirildi")
        else:
            count = downloader.download_meb_example_questions(args.year)
            print(f"\n[green]Toplam:[/green] {count} dosya indirildi")
    
    elif args.source == "dersmatematik":
        if args.all:
            years = range(2018, 2025)
            total = 0
            for year in years:
                print(f"\n[bold]Yıl: {year}[/bold]")
                total += downloader.download_dersmatematik(year)
            print(f"\n[green]Toplam:[/green] {total} dosya indirildi")
        else:
            count = downloader.download_dersmatematik(args.year)
            print(f"\n[green]Toplam:[/green] {count} dosya indirildi")
    
    elif args.source == "url" and args.url:
        success = downloader.download_from_url(args.url)
        if success:
            print("[green]Başarılı![/green]")
        else:
            print("[red]Başarısız![/red]")
    
    else:
        print("[yellow]Geçersiz kaynak veya eksik parametre.[/yellow]")


if __name__ == "__main__":
    main()

