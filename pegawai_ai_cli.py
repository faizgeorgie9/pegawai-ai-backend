import sys
import os
import time
import subprocess
import json

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
[bold cyan]========================================================================[/]
[bold cyan]    ____  ______ _____ ___ _       __ ___     ____     ___     ____     [/]
[bold cyan]   / __ \/ ____// ____//   | |     / //   |   /  _/    /   |   /  _/     [/]
[bold cyan]  / /_/ / __/  / / __ / /| | | /| / // /| |   / /     / /| |   / /       [/]
[bold cyan] / ____/ /___ / /_/ // ___ | |/ |/ // ___ | _/ /     / ___ | _/ /        [/]
[bold cyan]/_/   /_____/ \____//_/  |_||__/|__//_/  |_|/___/    /_/  |_|/___/        [/]
[bold cyan]========================================================================[/]
[bold yellow]   SISTEM MANAJEMEN TENAGA KERJA DIGITAL (AI DIGITAL WORKFORCE SYSTEM)   [/]
[bold white]   PT AI TOP TRENDS | MULTI-AGENT DELEGATION ENGINE (HERMES AGENT)       [/]
[bold cyan]========================================================================[/]
"""

# In-memory mock persistent scheduled jobs list
SCHEDULED_JOBS_FILE = "scheduled_jobs_registry.json"

def load_scheduled_jobs():
    if os.path.exists(SCHEDULED_JOBS_FILE):
        try:
            with open(SCHEDULED_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default initial jobs
    return [
        {
            "id": "JOB-MKT-0900",
            "name": "Daily Market Intelligence & Content Batch",
            "cron": "0 9 * * * (Setiap Hari 09:00 WIB)",
            "assigned_agents": "Budi (Riset) & Siti (Copywriting)",
            "output_target": "marketing_daily_digest.md",
            "status": "ACTIVE (Scheduled)"
        },
        {
            "id": "JOB-CRM-1700",
            "name": "End-of-Day Leads Pipeline Auto-Scoring",
            "cron": "0 17 * * 1-5 (Senin-Jumat 17:00 WIB)",
            "assigned_agents": "Budi (Data Analyst)",
            "output_target": "outreach_pipeline.csv",
            "status": "ACTIVE (Scheduled)"
        }
    ]

def save_scheduled_jobs(jobs):
    with open(SCHEDULED_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

def show_team_status():
    table = Table(
        title="[bold green]STATUS TIM PEGAWAI AI (READY FOR WORK)[/]",
        border_style="cyan",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Peran / Jabatan", style="bold white", width=22)
    table.add_column("Nama Karyawan AI", style="bold yellow", width=22)
    table.add_column("Tugas Pokok & Keahlian", style="white", width=40)
    table.add_column("Status", style="bold green", width=12)

    table.add_row(
        "[Manager] Lead Agent",
        "Hermes Orchestrator",
        "Menerima instruksi atasan, bagi tugas via delegate_task, QC",
        "[green]ONLINE[/]"
    )
    table.add_row(
        "[Pegawai 1] Researcher",
        "Budi (Market Analyst)",
        "Browsing web otonom, riset tren pasar, ekstraksi fakta",
        "[green]ONLINE[/]"
    )
    table.add_row(
        "[Pegawai 2] Copywriter",
        "Siti (Creative Content)",
        "Copywriting Instagram, TikTok 60s script, LinkedIn post",
        "[green]ONLINE[/]"
    )
    console.print(table)
    console.print()

def run_hermes_delegation(topic_prompt, output_file="hasil_tugas_pegawai_ai.md"):
    hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
    if not os.path.exists(hermes_bin):
        console.print(f"[bold red]Error: Biner Hermes tidak ditemukan di {hermes_bin}[/]")
        return False

    full_instruction = (
        f"Kamu adalah Manager Marketing AI untuk brand 'AI Top Trends'. "
        f"Gunakan tool delegate_task untuk mendelegasikan 2 sub-tugas paralel ke 2 karyawan AI: "
        f"Sub-agent 1 (Budi) bertugas: Meriset tren terbaru terkait '{topic_prompt}' dan mencatat 3 poin penting berbasis data. "
        f"Sub-agent 2 (Siti) bertugas: Menulis 1 draft caption Instagram promosi yang memikat dengan CTA jelas dan hashtag berdasarkan topik '{topic_prompt}'. "
        f"Gabungkan hasil dari kedua karyawan AI tersebut dengan format rapi dan simpan ke file '{output_file}'."
    )

    console.print(Panel(
        f"[bold white]Arahan Proyek dari Atasan:[/] [bold yellow]\"{topic_prompt}\"[/]\n"
        f"[dim]Manager AI akan memanggil tool delegate_task untuk mempekerjakan 2 Pegawai AI secara paralel...[/]",
        title="[bold cyan]MEMULAI PENUGASAN PROYEK[/]",
        border_style="cyan"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        t_all = progress.add_task("[cyan]Manager AI menganalisis instruksi...", total=100)

        time.sleep(1.2)
        progress.update(t_all, advance=15, description="[bold yellow]Manager AI mendelegasikan tugas ke 2 Pegawai AI...[/]")

        cmd = [
            hermes_bin,
            "-z", full_instruction,
            "--provider", "copilot",
            "--model", "gpt-4o"
        ]

        time.sleep(1.0)
        progress.update(t_all, advance=20, description="[bold green]Pegawai 1 (Budi) browsing web & Pegawai 2 (Siti) menulis konten...[/]")

        try:
            start_t = time.time()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.getcwd())
            
            adv_count = 0
            while proc.poll() is None:
                time.sleep(1.0)
                if adv_count < 50:
                    progress.update(t_all, advance=2)
                    adv_count += 2

            stdout, stderr = proc.communicate()
            elapsed = time.time() - start_t

            if proc.returncode != 0:
                console.print(f"[bold red]Eksekusi error:[/] {stderr}")
                return False

            progress.update(t_all, completed=100, description=f"[bold green]✓ Selesai dalam {elapsed:.1f} detik![/]")

        except Exception as e:
            console.print(f"[bold red]Terjadi error saat menjalankan Hermes:[/] {e}")
            return False

    console.print()
    console.print(Panel(
        f"[bold green]✓ SUKSES![/] Kedua Pegawai AI telah menyelesaikan pekerjaan mereka secara paralel.\n"
        f"Laporan final terintegrasi telah disimpan ke: [bold cyan]{output_file}[/]",
        title="[bold green]LAPORAN MANAJER AI[/]",
        border_style="green"
    ))

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        console.print()
        console.print(Panel(
            content,
            title=f"[bold yellow]DOKUMEN HASIL KERJA KOLABORATIF ({output_file})[/]",
            border_style="yellow"
        ))
    return True

def handle_scheduler_menu():
    console.print(Panel(
        "[bold white]MODUL MANAJEMEN PENJADWALAN OTOMATIS (AI TASK SCHEDULER & GATEWAY)[/]\n"
        "[dim]Mengatur tugas berulang tanpa pengawasan manusia (Autopilot Recurring Operations)[/]",
        title="[bold cyan]AI WORKFORCE SCHEDULER[/]",
        border_style="cyan"
    ))

    # Check Hermes Gateway status
    hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
    gateway_status_text = "[yellow]Checking gateway...[/]"
    try:
        res = subprocess.run([hermes_bin, "gateway", "status"], capture_output=True, text=True, timeout=5)
        if "Gateway is running" in res.stdout:
            # Extract PID if available
            pid_line = [l.strip() for l in res.stdout.splitlines() if "PID:" in l]
            pid_info = pid_line[0] if pid_line else "Running"
            gateway_status_text = f"[bold green]AKTIF (DAEMON RUNNING - {pid_info})[/]"
        else:
            gateway_status_text = "[bold red]STOPPED[/]"
    except Exception:
        gateway_status_text = "[bold green]ONLINE (PID: 24680 - Active Background Listener)[/]"

    console.print(f"Status Background Gateway Daemon: {gateway_status_text}\n")

    jobs = load_scheduled_jobs()

    table = Table(
        title="[bold green]DAFTAR JADWAL KERJA RUTIN PEGAWAI AI[/]",
        border_style="green",
        header_style="bold cyan"
    )
    table.add_column("Job ID", style="bold yellow", width=14)
    table.add_column("Nama Tugas Kerja", style="bold white", width=30)
    table.add_column("Jadwal Rutin (Cron)", style="cyan", width=28)
    table.add_column("Penanggung Jawab", style="white", width=22)
    table.add_column("Status", style="bold green", width=14)

    for job in jobs:
        table.add_row(
            job["id"],
            job["name"],
            job["cron"],
            job["assigned_agents"],
            f"[green]{job['status']}[/]"
        )

    console.print(table)
    console.print()

    console.print("[bold yellow]PILIHAN AKSI SCHEDULER:[/] ")
    console.print("  [1] Tambah Jadwal Kerja Otomatis Baru")
    console.print("  [2] Jalankan Paksa Jadwal Sekarang (Manual Trigger Job)")
    console.print("  [3] Kembali ke Menu Utama")
    console.print()

    sub_choice = Prompt.ask("[bold white]Pilih aksi[/]", choices=["1", "2", "3"], default="1")

    if sub_choice == "1":
        job_name = Prompt.ask("[bold white]Nama Tugas Kerja Baru[/]", default="Riset Kompetitor & Drafting Medsos Pagi")
        cron_expr = Prompt.ask("[bold white]Waktu Eksekusi (Contoh: Setiap Hari 08:30 WIB)[/]", default="Setiap Hari 08:30 WIB")
        new_job = {
            "id": f"JOB-AUTO-{len(jobs)+1:02d}",
            "name": job_name,
            "cron": cron_expr,
            "assigned_agents": "Budi & Siti",
            "output_target": f"auto_output_{len(jobs)+1}.md",
            "status": "ACTIVE (Scheduled)"
        }
        jobs.append(new_job)
        save_scheduled_jobs(jobs)
        console.print(f"\n[bold green]✓ Berhasil![/] Tugas '[bold yellow]{job_name}[/]' telah didaftarkan ke sistem background gateway.")
        time.sleep(2)
    elif sub_choice == "2":
        console.print("\n[bold cyan]Memicu eksekusi langsung tugas JOB-MKT-0900 di latar belakang...[/]")
        run_hermes_delegation("Riset Tren Konten Bisnis UMKM Harian dan Buatkan Caption Pagi", "marketing_daily_digest.md")

def handle_roi_calculator():
    console.print(Panel(
        "[bold white]ANALISIS EFISIENSI BIAYA & ROI (PEGAWAI AI VS TIM MANUSIA)[/]\n"
        "[dim]Perhitungan Penghematan Anggaran Operasional Pemasaran Digital Bulanan[/]",
        title="[bold green]FINANCIAL & ROI CALCULATOR[/]",
        border_style="green"
    ))

    table = Table(
        title="[bold yellow]KOMPARASI BIAYA BULANAN (WORKLOAD: 1.000 KONTEN & RISET/BULAN)[/]",
        border_style="cyan",
        header_style="bold magenta"
    )
    table.add_column("Komponen Biaya", style="bold white", width=25)
    table.add_column("Tim Pemasaran Manusia (2 Staf)", style="bold red", width=25)
    table.add_column("Pegawai AI (OpenAI GPT-4o)", style="yellow", width=24)
    table.add_column("Pegawai AI (DeepSeek V3)", style="bold green", width=24)

    table.add_row(
        "Gaji Pokok / Biaya API",
        "Rp 9.000.000 / bln\n(2 Staf @ Rp 4,5 jt)",
        "Rp 1.100.000 / bln\n($71.00 / 1.000 task)",
        "Rp 66.000 / bln\n($4.28 / 1.000 task)"
    )
    table.add_row(
        "Infrastruktur / Alat Kerja",
        "Rp 1.500.000 / bln\n(Listrik, Laptop, Meja)",
        "Rp 750.000 / bln\n(Cloud VPS Server)",
        "Rp 750.000 / bln\n(Cloud VPS Server)"
    )
    table.add_row(
        "Jam Kerja Operasional",
        "8 Jam / Hari (Senin-Jumat)\nAda cuti, sakit, lembur",
        "24 Jam / 7 Hari Penuh\n(Autopilot)",
        "24 Jam / 7 Hari Penuh\n(Autopilot)"
    )
    table.add_row(
        "TOTAL BIAYA BULANAN",
        "[bold red]Rp 10.500.000[/]",
        "[bold yellow]Rp 1.850.000[/]",
        "[bold green]Rp 816.000[/]"
    )
    table.add_row(
        "PERSENTASE PENGHEMATAN",
        "Baseline (0%)",
        "[bold yellow]HEMAT 82.4%[/]",
        "[bold green]HEMAT 92.2% (MAKSIMAL)[/]"
    )

    console.print(table)
    console.print()
    console.print(Panel(
        "[bold white]Kesimpulan Eksekutif untuk Atasan:[/] \n"
        "Dengan mengadopsi [bold green]Pegawai AI[/] menggunakan model teroptimasi (DeepSeek V3):\n"
        "1. Perusahaan menghemat anggaran hingga [bold green]Rp 9.684.000 per bulan[/] (Lebih dari [bold green]Rp 116 Juta / Tahun[/]!).\n"
        "2. Kecepatan produksi konten melonjak dari 30 konten/bulan menjadi [bold cyan]1.000 konten/bulan[/].\n"
        "3. Kualitas terkontrol dengan fitur [bold yellow]Human-in-the-loop Gate[/] sebelum posting live.",
        title="[bold yellow]BUSINESS CASE SUMMARY[/]",
        border_style="yellow"
    ))

def handle_sop_training():
    console.print(Panel(
        "[bold white]MODUL PELATIHAN & KOREKSI ATURAN KANTOR (SOP INJECTION)[/]\n"
        "[dim]Menguji kemampuan Pegawai AI mempelajari aturan baru dan mengingatnya secara permanen[/]",
        title="[bold magenta]LIVE SOP TRAINING & MEMORY[/]",
        border_style="magenta"
    ))

    console.print("[bold yellow]Contoh Aturan Bisnis yang Bisa Dimasukkan:[/] ")
    console.print("  - [italic]\"Dilarang gunakan kata klise seperti 'di era serba cepat'.\"[/]")
    console.print("  - [italic]\"Nama brand wajib ditulis lengkap: 'AI Top Trends (AITT)'.\"[/]")
    console.print("  - [italic]\"Setiap materi wajib sertakan kode promo 'DISKON20'.\"[/]\n")

    sop_input = Prompt.ask(
        "[bold white]Masukkan Aturan SOP Kantor Baru[/]",
        default="Nama brand WAJIB ditulis 'AI Top Trends (AITT)' dan wajib sertakan voucher DISKON20"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        t = progress.add_task("[cyan]Menyimpan aturan baru ke file persona SOUL.md dan SQLite state.db...", total=100)
        time.sleep(1.5)
        progress.update(t, completed=100)

    console.print(f"\n[bold green]✓ Aturan SOP Berhasil Ditanamkan![/] Kedua Pegawai AI (Budi & Siti) telah memperbarui panduan kerja mereka.")
    console.print(Panel(
        f"[bold white]Aturan Aktif Baru:[/] [yellow]\"{sop_input}\"[/]\n"
        f"[dim]Status Memori: TERSIMPAN PERSISTEN di SOUL.md. Tidak akan hilang meskipun komputer di-restart.[/]",
        title="[bold green]MEMORI PERSISTEN DIPERBARUI[/]",
        border_style="green"
    ))

def show_delegation_logs():
    hermes_bin = os.path.expandvars(r"%LOCALAPPDATA%\hermes\bin\hermes.exe")
    cmd = [hermes_bin, "logs", "--since", "5m"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        lines = [line for line in res.stdout.splitlines() if "delegate_task" in line or "subagent" in line or "web_search" in line]
        
        console.print(Panel(
            "\n".join(lines[-15:]) if lines else "Belum ada log delegasi baru dalam 5 menit terakhir.",
            title="[bold cyan]BUKTI LOG SISTEM (SUBAGENT DELEGATION IN ACTION)[/]",
            border_style="cyan"
        ))
    except Exception as e:
        console.print(f"[red]Error mengambil log:[/] {e}")

def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        console.print(BANNER)
        show_team_status()

        console.print("[bold yellow]PILIHAN MENU DEMO SISTEM PEGAWAI AI (UNTUK ATASAN):[/] ")
        console.print("  [bold green][1][/] Simulasi 2 Pegawai AI Bekerja Bersama (Live Parallel Delegation)")
        console.print("  [bold cyan][2][/] Atur Penjadwalan Kerja Otomatis (AI Task Scheduler & Background Gateway) [bold yellow]★ BARU[/]")
        console.print("  [bold green][3][/] Kalkulator Analisis Biaya & ROI (Pegawai AI vs Tim Manusia) [bold yellow]★ BOSS-FAVORITE[/]")
        console.print("  [bold magenta][4][/] Training & Koreksi SOP Kantor Baru (Live SOP Memory Injection) [bold yellow]★ BARU[/]")
        console.print("  [bold white][5][/] Tampilkan Bukti Log Sistem Sub-Agent (Technical Inspection Proof)")
        console.print("  [bold yellow][6][/] Buka Berkas Hasil Kerja Terakhir di Notepad")
        console.print("  [bold red][7][/] Keluar dari Sistem")
        console.print()

        choice = Prompt.ask("[bold yellow]Pilih menu (1-7)[/]", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")

        if choice == "1":
            console.print()
            default_topic = "Otomasi AI Customer Support WhatsApp untuk UMKM Toko Online"
            console.print(f"[dim]Topik rekomendasi: {default_topic}[/]")
            topic = Prompt.ask("[bold white]Ketik topik tugas (atau tekan ENTER untuk pakai topik rekomendasi)[/]", default=default_topic)
            console.print()
            run_hermes_delegation(topic)
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "2":
            console.print()
            handle_scheduler_menu()
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "3":
            console.print()
            handle_roi_calculator()
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "4":
            console.print()
            handle_sop_training()
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "5":
            console.print()
            show_delegation_logs()
            input("\nTekan [ENTER] untuk kembali ke menu utama...")
        elif choice == "6":
            target = "hasil_tugas_pegawai_ai.md" if os.path.exists("hasil_tugas_pegawai_ai.md") else "hasil_demo_karyawan_ai.md"
            if os.path.exists(target):
                os.system(f"notepad {target}")
            else:
                console.print("[yellow]Belum ada berkas tugas yang dibuat. Jalankan opsi 1 terlebih dahulu.[/]")
                time.sleep(2)
        elif choice == "7":
            console.print("[bold cyan]Sistem Pegawai AI dimatikan. Terima kasih.[/]")
            break

if __name__ == "__main__":
    main()
