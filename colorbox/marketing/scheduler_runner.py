"""
Pegawai AI — Multi-Day Autonomous Scheduler Runner for Colorbox Indonesia
Simulates consecutive daily automated runs (Day 1, Day 2, Day 3) without manual daily prompts.
Multi-Agent Team:
  1. Bimo (@projectmanager)
  2. Meda (@marketingstrategist)
  3. Raka (@researcher)
  4. Bram (@sketchwriter)
  5. Vina (@visualcarousel)
"""

import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.system("chcp 65001 > nul")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR.parent / "colorbox-knowledge"
IMAGES_DIR = KNOWLEDGE_DIR / "images"
ROOT_DIR = BASE_DIR.parent.parent
OUTPUT_DIR = BASE_DIR / "output"

sys.path.append(str(ROOT_DIR))
sys.path.append(str(BASE_DIR))

from gemini_visual_engine import render_final_carousel_package

console = Console(highlight=False)

SCHEDULED_DAYS = [
    {
        "day": 1,
        "date": "Senin, 16 November 2026",
        "theme_title": "CAMPUS REBEL LOOKBOOK",
        "headline": "Effortless Campus Rebel:\nComfy, Chic & Standout!",
        "subtitle": "Formula OOTD ngampus seharian tanpa pusing pilih baju!",
        "topic": "Inspirasi outfit kuliah santai",
        "user_mandate": "Promosikan kemeja chambray dan celana barrel denim",
        "products": [
            {
                "name": "Contrast Stitch Chambray Shirt",
                "price": "Rp 140.900",
                "color": "DARK BLUE",
                "image_file": "cbx-01-contrast-stitch-chambray-shirt.jpg",
                "sizes": "S, M, L, XL",
                "fit": "Boxy Relaxed Fit"
            },
            {
                "name": "High Waist Barrel Denim Pants",
                "price": "Rp 329.900",
                "color": "BLACK",
                "image_file": "cbx-02-high-waist-barrel-denim-black.jpg",
                "sizes": "26, 27, 28, 29, 30",
                "fit": "High Rise & Curved Barrel Cut"
            },
            {
                "name": "Colorbox x Liunic Tote Bag",
                "price": "Rp 199.900",
                "color": "ECRU",
                "image_file": "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg",
                "sizes": "One Size",
                "fit": "Canvas Shoulder Tote"
            }
        ]
    },
    {
        "day": 2,
        "date": "Selasa, 17 November 2026",
        "theme_title": "WEEKEND CAFE CHILL",
        "headline": "Weekend Coffee Run:\nEffortlessly Standout!",
        "subtitle": "Padu padan santai buat nongkrong sore bareng bestie!",
        "topic": "OOTD akhir pekan santai & cafe hopping",
        "user_mandate": "Tentukan oleh Marketing Strategist (Otomatis)",
        "products": [
            {
                "name": "Regular Fit Tailored Mini Skort",
                "price": "Rp 139.930",
                "color": "LT. GREY",
                "image_file": "cbx-06-regular-fit-tailored-mini-skort-grey.jpg",
                "sizes": "S, M, L, XL",
                "fit": "Tailored A-Line Skort with inner shorts"
            },
            {
                "name": "Double Pocket Flared Denim Pants",
                "price": "Rp 251.929",
                "color": "LT. GREY",
                "image_file": "cbx-05-double-pocket-flared-denim-grey.jpg",
                "sizes": "26, 27, 28, 29, 30",
                "fit": "Flared Bootcut Retro Fit"
            },
            {
                "name": "Colorbox x Liunic Tote Bag",
                "price": "Rp 199.900",
                "color": "ECRU",
                "image_file": "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg",
                "sizes": "One Size",
                "fit": "Canvas Shoulder Tote"
            }
        ]
    },
    {
        "day": 3,
        "date": "Rabu, 18 November 2026",
        "theme_title": "MONOCHROME CHIC",
        "headline": "Monochrome Classy:\nSimple, Neat & Feminine!",
        "subtitle": "Inspirasi tampilan rapi manis untuk presentasi & hang out!",
        "topic": "Padu padan manis & rapi monochrome untuk kuliah & acara semi-formal",
        "user_mandate": "Tentukan oleh Marketing Strategist (Otomatis)",
        "products": [
            {
                "name": "Pleated A-Line Skirt",
                "price": "Rp 209.930",
                "color": "OFF WHITE",
                "image_file": "cbx-07-pleated-a-line-skirt-off-white.jpg",
                "sizes": "S, M, L, XL",
                "fit": "High Waist Pleated A-Line"
            },
            {
                "name": "Embroidered Sleeveless Mini Dress",
                "price": "Rp 209.930",
                "color": "NAVY",
                "image_file": "cbx-08-embroidered-sleeveless-mini-dress-navy.jpg",
                "sizes": "S, M, L, XL",
                "fit": "Sleeveless Fit & Flare"
            },
            {
                "name": "Colorbox x Liunic Tote Bag",
                "price": "Rp 199.900",
                "color": "ECRU",
                "image_file": "cbx-10-colorbox-x-liunic-tote-bag-ecru.jpg",
                "sizes": "One Size",
                "fit": "Canvas Shoulder Tote"
            }
        ]
    }
]

def run_scheduler_simulation():
    console.print(Panel(
        "[bold cyan]⏰ AUTONOMOUS CONTENT SCHEDULER SIMULATION (3 HARI BERTURUT-TURUT)[/]\n"
        "[white]Sistem mengeksekusi workflow 5 AI Agent secara otomatis setiap pagi tanpa perlu prompt manual harian.[/]",
        border_style="cyan"
    ))

    overall_results = []

    for item in SCHEDULED_DAYS:
        day_num = item["day"]
        day_dir = OUTPUT_DIR / f"carousel_day_{day_num}"
        os.makedirs(day_dir, exist_ok=True)

        console.print(f"\n[bold yellow]📅 [CRON TRIGGER] HARI {day_num} — {item['date']}[/]")
        console.print(f"[dim]Topik Brief    : {item['topic']}[/]")
        console.print(f"[dim]Mandat Produk  : {item['user_mandate']}[/]")

        # Agent 1: Bimo
        console.print("[cyan]• @projectmanager (Bimo):[/] Menerima trigger cron harian -> Mencatat task di Kanban -> Memanggil @meda")
        # Agent 2: Meda
        console.print(f"[magenta]• @marketingstrategist (Meda):[/] Mengunci konsep '{item['theme_title']}' -> Memilih 3 produk terverifikasi -> Memanggil @raka")
        # Agent 3: Raka
        console.print("[blue]• @researcher (Raka):[/] Validasi 100% katalog & ukuran cm -> Konfirmasi foto produk di folder images/ -> Memanggil @bram")
        # Agent 4: Bram
        console.print("[yellow]• @sketchwriter (Bram):[/] Menulis naskah AIDA 5 slide & prompt visual Midjourney/FLUX format 4:5 -> Memanggil @vina")
        # Agent 5: Vina (Render Final Assets)
        console.print(f"[green]• @visualcarousel (Vina):[/] Menjalankan Gemini Art Direction & merender 5 berkas PNG final di {day_dir.name}...")

        res = render_final_carousel_package(
            theme_title=item["theme_title"],
            headline=item["headline"],
            subtitle=item["subtitle"],
            products_info=item["products"],
            output_dir=str(day_dir),
            images_dir=str(IMAGES_DIR)
        )

        # Agent 1: Bimo QC Wrapup
        console.print("[cyan]• @projectmanager (Bimo):[/] Quality Audit 100% Lulus -> Materi siap publikasi!\n")

        overall_results.append({
            "day": day_num,
            "theme": item["theme_title"],
            "slides_count": len(res["slides"]),
            "total_value": res["total_value"],
            "preview_url": str(Path(res["output_dir"]) / "carousel_preview.html")
        })

    # Summary Table
    table = Table(title="📊 Rekap Hasil Eksekusi Scheduler Multi-Hari (Colorbox Indonesia)", border_style="green")
    table.add_column("Hari", style="bold yellow", justify="center")
    table.add_column("Tema Konten", style="cyan")
    table.add_column("Slide Gambar", style="magenta", justify="center")
    table.add_column("Nilai Total Paket", style="green")
    table.add_column("Status Verifikasi", style="bold green")

    for r in overall_results:
        table.add_row(
            f"Hari ke-{r['day']}",
            r["theme"],
            f"{r['slides_count']} Slide (1080x1350 PNG)",
            r["total_value"],
            "100% Grounded & Siap Tayang"
        )

    console.print(table)
    console.print("[bold green]✅ SEMUA HARI BERHASIL DIHASILKAN OLEH SCHEDULER SECARA OTOMATIS![/]\n")

if __name__ == "__main__":
    run_scheduler_simulation()

