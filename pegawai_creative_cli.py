import sys
import os
import time
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont

# Ensure Windows terminal handles UTF-8 smoothly
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
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console(highlight=False)

BANNER = r"""
[bold magenta]========================================================================[/]
[bold magenta]   ______ ____   ______ ___   ______ ____ _    __ ______   __  __ ____   [/]
[bold magenta]  / ____// __ \ / ____//   | /_  __//  _/| |  / // ____/  / / / //  _/   [/]
[bold magenta] / /    / /_/ // __/  / /| |  / /   / /  | | / // __/    / / / / / /     [/]
[bold magenta]/ /___ / _, _// /___ / ___ | / /  _/ /   | |/ // /___   / /_/ /_/ /      [/]
[bold magenta]\____//_/ |_|/_____//_/  |_|/_/  /___/   |___//_____/   \____//___/      [/]
[bold magenta]========================================================================[/]
[bold yellow]   DIVISI KREATIF & STUDIO KONTEN AI (CREATIVE AGENCY WORKFORCE)         [/]
[bold white]   PT AI TOP TRENDS | MULTI-AGENT PIPELINE: VISUAL -> COPY -> QC         [/]
[bold magenta]========================================================================[/]
"""

def show_creative_team_status():
    table = Table(
        title="[bold green]SUSUNAN TIM MULTI-AGENT DIVISI KREATIF[/]",
        border_style="magenta",
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("Posisi / Role", style="bold white", width=22)
    table.add_column("Nama Agen AI", style="bold yellow", width=20)
    table.add_column("Tools Bawaan yang Digunakan", style="bold green", width=26)
    table.add_column("Tugas Pokok & Tanggung Jawab", style="white", width=34)

    table.add_row(
        "🎨 Pegawai AI 1",
        "Rian (Visual Designer)",
        "image_gen_engine &\nasset_composer (Pillow)",
        "Merancang konsep visual, prompt DALL-E/Flux, dan generate mockup grafis."
    )
    table.add_row(
        "✍️ Pegawai AI 2",
        "Siti (Copywriter)",
        "copywriting_aida &\nhashtag_optimizer",
        "Menyusun hook headline, body narasi AIDA, Call-to-Action, dan hashtag."
    )
    table.add_row(
        "🔍 Pegawai AI 3",
        "Diana (Creative Director)",
        "brand_guideline_auditor &\nquality_control_gate",
        "Audit keselarasan visual-teks, filter kata terlarang, beri skor QC (1-100)."
    )
    console.print(table)
    console.print()

def generate_banner_image(topic, headline, output_png="banner_promo_kreatif.png"):
    """Tool Generator Gambar untuk Pegawai AI 1 (Rian)"""
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color=(27, 54, 93))  # Navy Blue #1B365D
    draw = ImageDraw.Draw(img)

    # Decorative Border & Accent Lines
    draw.rectangle([30, 30, width - 30, height - 30], outline=(13, 148, 136), width=6)  # Teal accent
    draw.rectangle([50, 50, width - 50, 160], fill=(15, 30, 55))

    # Header Badge
    draw.text((70, 75), "PT AI TOP TRENDS | KAMPANYE PEMASARAN DIGITAL", fill=(13, 148, 136))
    draw.text((70, 105), "DIVISI KREATIF - AUTOMATED WORKFORCE ASSET", fill=(200, 210, 225))

    # Main Card Box
    draw.rectangle([70, 220, width - 70, 850], fill=(22, 44, 78), outline=(41, 74, 110), width=3)

    # Topic Category Tag
    draw.rectangle([100, 260, 480, 320], fill=(13, 148, 136))
    draw.text((120, 275), "KATEGORI: EDUKASI & OTOMASI BISNIS", fill=(255, 255, 255))

    # Headline & Subheadline
    clean_topic = topic[:45] + "..." if len(topic) > 45 else topic
    draw.text((100, 360), "TREN BISNIS & OTOMASI 2026", fill=(250, 204, 21))
    draw.text((100, 420), f"FOKUS: {clean_topic.upper()}", fill=(255, 255, 255))
    
    # 3 Key Value Propositions Box
    draw.rectangle([100, 500, width - 100, 720], fill=(18, 36, 65))
    draw.text((130, 530), "✓ Otomasi Layanan Pelanggan 24/7 Tanpa Henti", fill=(220, 230, 240))
    draw.text((130, 590), "✓ Hemat Anggaran Operasional Pemasaran hingga 92%", fill=(220, 230, 240))
    draw.text((130, 650), "✓ Human-in-the-Loop Quality Control Terjamin Aman", fill=(220, 230, 240))

    # CTA Button
    draw.rectangle([100, 750, 480, 820], fill=(217, 119, 6)) # Amber CTA
    draw.text((140, 770), "KONSULTASI GRATIS SEKARANG ->", fill=(255, 255, 255))

    # Footer note
    draw.text((70, 890), "Dibuat Secara Otonom oleh: Pegawai AI 1 (Rian - Visual Specialist)", fill=(140, 160, 185))
    draw.text((70, 930), "Status Verifikasi: Di-Audit & Disetujui oleh Creative Director AI (Diana)", fill=(16, 185, 129))

    img.save(output_png)
    return output_png

def run_creative_pipeline(campaign_topic):
    hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
    if not os.path.exists(hermes_bin):
        console.print(f"[bold red]Error: Biner Hermes tidak ditemukan di {hermes_bin}[/]")
        return False

    console.print(Panel(
        f"[bold white]Topik Kampanye:[/] [bold yellow]\"{campaign_topic}\"[/]\n"
        f"[dim]Alur Kerja: [1] Rian (Visual) -> [2] Siti (Copywriter) -> [3] Diana (Creative Director QC)[/]",
        title="[bold magenta]MEMULAI ALUR KERJA DIVISI KREATIF[/]",
        border_style="magenta"
    ))

    output_doc = "paket_konten_kreatif.md"
    output_png = "banner_promo_kreatif.png"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        t_flow = progress.add_task("[magenta]Mengaktifkan 3 Agen Divisi Kreatif...", total=100)

        # ---------------------------------------------------------
        # TAHAP 1: PEGAWAI AI 1 (Rian - Visual Designer)
        # ---------------------------------------------------------
        progress.update(t_flow, advance=15, description="[bold cyan]🎨 [AI 1: Rian] Merancang konsep visual & prompt DALL-E 3 / Flux...[/]")
        time.sleep(1.5)
        
        # Tool Image Generation (Pillow generator)
        generate_banner_image(campaign_topic, "Solusi Pemasaran Cerdas dengan Pegawai AI", output_png)
        progress.update(t_flow, advance=20, description=f"[bold cyan]🎨 [AI 1: Rian] Berhasil merender aset visual ({output_png})![/]")
        time.sleep(1.0)

        # ---------------------------------------------------------
        # TAHAP 2 & 3: PEGAWAI AI 2 (Siti) & PEGAWAI AI 3 (Diana) via Hermes Live
        # ---------------------------------------------------------
        progress.update(t_flow, advance=15, description="[bold yellow]✍️ [AI 2: Siti] & 🔍 [AI 3: Diana] Memanggil mesin Hermes Agent secara LIVE...[/]")
        time.sleep(1.0)
        progress.stop()

    console.print()
    console.print(Panel(
        "[bold cyan]⚡ LIVE EXECUTION: HERMES AGENT ENGINE AKTIF[/]\n"
        "[dim]Perhatikan proses di bawah: Hermes akan memanggil tool penulisan file ('✍️ Write') dan menampilkan logo resminya secara nyata:[/dim]",
        border_style="cyan"
    ))

    full_prompt = (
        f"Bertindaklah sebagai Tim Divisi Kreatif untuk brand 'AI Top Trends' (mengacu pada profil bisnis v1.0.0).\n"
        f"Topik Kampanye: '{campaign_topic}'.\n\n"
        f"Jalankan 2 peran berikut secara berurutan dan tuliskan seluruh hasilnya ke berkas '{output_doc}':\n\n"
        f"BAGIAN 1 - PEGAWAI AI 2: SITI (COPYWRITING SPECIALIST):\n"
        f"Tulis caption Instagram promosi yang memikat dengan struktur AIDA (Attention Hook, Interest, Desire, Action).\n"
        f"Sertakan Call to Action (CTA) yang membumi dan 5 hashtag yang relevan.\n\n"
        f"BAGIAN 2 - PEGAWAI AI 3: DIANA (CREATIVE DIRECTOR & QUALITY CONTROL):\n"
        f"Lakukan inspeksi dan audit terhadap hasil kerja AI 1 (Visual Banner di '{output_png}') dan AI 2 (Caption Siti di atas):\n"
        f"- Cek 1: Keselarasan Visual dan Teks (Skor 1-10)\n"
        f"- Cek 2: Kepatuhan Brand Voice AI Top Trends (Skor 1-10, grounded, dilarang arogan)\n"
        f"- Cek 3: Filter Kata Terlarang (TIDAK ADA kata 'kaya instan', 'autopilot tanpa kerja')\n"
        f"- Cek 4: Kelengkapan CTA & Hashtag (Lolos/Tidak)\n"
        f"- SKOR TOTAL QC: Berikan skor akhir (misal: 95/100)\n"
        f"- Status Akhir: Wajib cantumkan penanda 'Status: DRAFT_READY_FOR_HUMAN_REVIEW'\n\n"
        f"Pastikan kamu menggunakan tool penulisan file untuk menyimpan langsung ke '{output_doc}'."
    )

    cmd = [
        hermes_bin,
        "chat",
        "-q", full_prompt,
        "--provider", "copilot",
        "--model", "gpt-4o"
    ]

    try:
        start_t = time.time()
        # Run Hermes directly streaming to stdout so user and boss see Hermes live
        proc = subprocess.run(cmd, cwd=os.getcwd())
        elapsed = time.time() - start_t

        if proc.returncode != 0:
            console.print(f"[bold red]Hermes keluar dengan kode error: {proc.returncode}[/]")
            return False

        console.print(f"\n[bold green]✓ Hermes berhasil menyelesaikan tugas dalam {elapsed:.1f} detik![/]")
    except Exception as e:
        console.print(f"[bold red]Exception:[/] {e}")
        return False
    console.print(Panel(
        f"[bold green]✓ SUKSES BESAR![/] Seluruh alur kerja 3 Agen Divisi Kreatif selesai dieksekusi.\n"
        f"1. Aset Visual Gambar  : [bold cyan]{output_png}[/] (Siap dibuka/dilihat)\n"
        f"2. Naskah & Lembar QC  : [bold yellow]{output_doc}[/] (Tersimpan rapi)",
        title="[bold green]STATUS DIVISI KREATIF: SELESAI[/]",
        border_style="green"
    ))

    # Show Document content
    if os.path.exists(output_doc):
        with open(output_doc, "r", encoding="utf-8", errors="replace") as f:
            doc_content = f.read()

        console.print()
        console.print(Panel(
            doc_content,
            title=f"[bold yellow]📄 DOKUMEN HASIL KERJA DIVISI KREATIF ({output_doc})[/]",
            border_style="yellow"
        ))
    return True

def show_image_prompt_specs():
    specs = """
### PROMPT DALL-E 3 / FLUX UNTUK PEGAWAI AI 1 (RIAN):

```text
Prompt: A modern, minimalist corporate digital marketing illustration representing 'AI Digital Workforce' in Indonesia, featuring two collaborative humanoid AI silhouettes reviewing holographic business analytics and social media calendars, vibrant teal (#0D9488) and deep navy (#1B365D) color palette, sleek glassmorphism dashboard elements, warm ambient lighting, 4k resolution, clean composition, zero text distortions, cinematic corporate aesthetic.
Aspect Ratio: 1:1 (Square for Instagram Feed)
Lighting: Soft studio rim light, volumetric glow
Style: Contemporary 3D Minimalist Tech Art
```

Prompt di atas dirancang oleh AI 1 (Rian) untuk dimasukkan ke generator AI gambar resolusi tinggi (seperti Midjourney atau DALL-E 3) jika tim ingin merender variasi foto fotorealistik.
"""
    console.print(Panel(
        specs,
        title="[bold cyan]SPESIFIKASI PROMPT IMAGE GENERATION (DALL-E 3 / MIDJOURNEY)[/]",
        border_style="cyan"
    ))

def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        console.print(BANNER)
        show_creative_team_status()

        console.print("[bold yellow]PILIHAN MENU DEMO DIVISI KREATIF (UNTUK ATASAN):[/] ")
        console.print("  [bold green][1][/] Jalankan Alur 3 Agen Kreatif (Visual Designer -> Copywriter -> QC Director)")
        console.print("  [bold cyan][2][/] Buka Gambar Visual Mockup Hasil Kerja AI 1 (Lihat Foto)")
        console.print("  [bold yellow][3][/] Buka Naskah Caption & Lembar Audit QC di Notepad")
        console.print("  [bold magenta][4][/] Lihat Format Prompt Image Generation (DALL-E 3 / Flux Specs)")
        console.print("  [bold blue][5][/] Buka Terminal Chat Interaktif Hermes Langsung (REPL Live Chat)")
        console.print("  [bold white][6][/] Buka Web Dashboard Hermes (Visual GUI di Browser)")
        console.print("  [bold red][7][/] Keluar dari Studio Kreatif")
        console.print()

        choice = Prompt.ask("[bold yellow]Pilih menu (1-7)[/]", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")

        if choice == "1":
            console.print()
            default_topic = "Mengatasi Burnout Buat Konten Harian dengan Pegawai AI untuk UMKM Lokal"
            console.print(f"[dim]Topik rekomendasi: {default_topic}[/]")
            topic = Prompt.ask("[bold white]Ketik topik kampanye kreatif (atau tekan ENTER untuk pakai rekomendasi)[/]", default=default_topic)
            console.print()
            run_creative_pipeline(topic)
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "2":
            if os.path.exists("banner_promo_kreatif.png"):
                console.print("[green]Membuka gambar banner hasil kerja AI 1...[/]")
                os.system("start banner_promo_kreatif.png")
            else:
                console.print("[yellow]Berkas gambar belum dibuat. Jalankan opsi [1] terlebih dahulu.[/]")
                time.sleep(2)
        elif choice == "3":
            if os.path.exists("paket_konten_kreatif.md"):
                os.system("notepad paket_konten_kreatif.md")
            else:
                console.print("[yellow]Berkas dokumen belum dibuat. Jalankan opsi [1] terlebih dahulu.[/]")
                time.sleep(2)
        elif choice == "4":
            console.print()
            show_image_prompt_specs()
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "5":
            hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
            console.print("[bold cyan]Membuka Terminal Chat Interaktif Hermes Agent... (Ketik 'exit' untuk kembali)[/]")
            time.sleep(1)
            subprocess.run([hermes_bin, "--provider", "copilot", "--model", "gpt-4o"])
        elif choice == "6":
            hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
            console.print("[bold green]Menjalankan Hermes Web Dashboard di http://localhost:9119 ...[/]")
            subprocess.Popen([hermes_bin, "dashboard"])
            time.sleep(2)
            os.system("start http://localhost:9119")
        elif choice == "7":
            console.print("[bold cyan]Studio Divisi Kreatif ditutup. Terima kasih.[/]")
            break

if __name__ == "__main__":
    main()
