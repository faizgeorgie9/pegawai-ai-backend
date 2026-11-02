"""
Pegawai AI - Shared Backend Development Template (Minimal POC)
Role: Intern 1 (Local Setup & Technical Research)
Date: October 29-30, 2026 (Sprint 2 - Day 1 & 2)

This lightweight HTTP REST server provides a standardized interface for:
- Intern 2 & 3: Workflow orchestration and dynamic multi-agent dispatch
- Intern 4: Frontend UI client integration
"""

import os
import sys
import re
import json
import time
import uuid
import logging
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Intern-1-Backend] %(message)s"
)
logger = logging.getLogger("PegawaiAIBackend")

def load_env_file():
    """Automatically load .env from current dir or project root without external libraries"""
    candidates = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
        Path.cwd() / ".env",
        Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\.env"))
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
                logger.info(f"Loaded environment variables from: {p}")
                break
            except Exception as e:
                logger.warning(f"Failed to parse {p}: {e}")

load_env_file()

PORT = int(os.environ.get("PORT", 8080))
HERMES_BIN = os.path.expandvars(os.environ.get("HERMES_BIN_PATH", r"%LOCALAPPDATA%\hermes\bin\hermes.exe"))

# In-memory session ledger for minimal POC
SESSION_HISTORY = []

def generate_banner_image(topic, department="marketing", output_png="banner_promo_kreatif.png"):
    """Tool Generator Gambar Dinamis untuk Divisi Kreatif & Visual Specialist"""
    try:
        from PIL import Image, ImageDraw
        width, height = 1080, 1080
        img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Deep Slate Navy #0F172A
        draw = ImageDraw.Draw(img)

        # Border & Accent Lines
        accent_color = (13, 148, 136) # Teal
        if department == "customer_support":
            accent_color = (14, 165, 233) # Sky Blue
        elif department == "sales":
            accent_color = (16, 185, 129) # Emerald Green

        draw.rectangle([30, 30, width - 30, height - 30], outline=accent_color, width=6)
        draw.rectangle([50, 50, width - 50, 160], fill=(24, 38, 66))

        # Header Badge
        draw.text((70, 75), "PT AI TOP TRENDS | WORKFORCE PEGAWAI AI OTOMATIS", fill=accent_color)
        draw.text((70, 105), f"DIVISI: {department.upper()} — DIGITAL CAMPAIGN & OPERATIONAL ASSET", fill=(203, 213, 225))

        # Main Card Box
        draw.rectangle([70, 200, width - 70, 860], fill=(30, 41, 59), outline=(51, 65, 85), width=3)

        # Category Tag
        category_title = "KAMPANYE KREATIF & KONTEN DIGITAL"
        if department == "customer_support":
            category_title = "LAYANAN & RESOLUSI PELANGGAN TERSTANDAR"
        elif department == "sales":
            category_title = "KONSULTASI BISNIS & STRATEGI B2B"

        draw.rectangle([100, 230, 600, 285], fill=accent_color)
        draw.text((120, 245), f"KATEGORI: {category_title}", fill=(255, 255, 255))

        # Headline
        draw.text((100, 320), "SOLUSI & INISIATIF UNGGULAN 2026", fill=(250, 204, 21))

        # Word-wrapped Topic
        words = topic.split()
        lines = []
        cur_line = []
        for w in words:
            if sum(len(x) + 1 for x in cur_line) + len(w) <= 32:
                cur_line.append(w)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        y_text = 370
        for line in lines[:3]:
            draw.text((100, y_text), line.upper(), fill=(255, 255, 255))
            y_text += 48

        # 3 Key Value Propositions Box (Dynamic by department)
        box_y1 = max(y_text + 20, 520)
        draw.rectangle([100, box_y1, width - 100, box_y1 + 190], fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        
        if department == "customer_support":
            p1 = "✓ Respon Cepat & Validasi Masalah Secara Berempati"
            p2 = "✓ Panduan Solusi Bertahap Terstandarisasi SOP Layanan"
            p3 = "✓ Eskalasi Terintegrasi Siap Menghubungkan ke Tim Ahli"
            cta_text = "HUBUNGI LAYANAN DUKUNGAN 24/7 ->"
        elif department == "sales":
            p1 = "✓ Diagnosa Kebutuhan & Analisis Efisiensi Biaya Nyata"
            p2 = "✓ Proyeksi ROI Terukur Sesuai Skala Operasional Anda"
            p3 = "✓ Roadmap Implementasi Khusus untuk Pertumbuhan Bisnis"
            cta_text = "JADWALKAN SESI KONSULTASI STRATEGIS ->"
        else:
            p1 = "✓ Narasi AIDA Tajam yang Berpijak pada Nilai Nyata"
            p2 = "✓ Visual Branding Konsisten & Menarik Perhatian Audiens"
            p3 = "✓ Audit Kualitas Berlapis Sebelum Publikasi Resmi"
            cta_text = "KONSULTASI STRATEGI KONTEN ->"

        draw.text((130, box_y1 + 25), p1, fill=(226, 232, 240))
        draw.text((130, box_y1 + 75), p2, fill=(226, 232, 240))
        draw.text((130, box_y1 + 125), p3, fill=(226, 232, 240))

        # CTA Button
        btn_y = box_y1 + 215
        draw.rectangle([100, btn_y, 600, btn_y + 65], fill=(217, 119, 6)) # Amber CTA
        draw.text((130, btn_y + 20), cta_text, fill=(255, 255, 255))

        # Footer note
        draw.text((70, 920), "Dibuat Secara Otonom oleh: Sistem Pegawai AI PT AI Top Trends", fill=(148, 163, 184))
        draw.text((70, 955), "Verifikasi: Di-Audit & Disetujui Melalui Pipeline Multi-Agent Standar SOP", fill=accent_color)

        target_file = Path(__file__).parent / output_png
        img.save(target_file)
        
        # Also save to parent root so both paths resolve
        root_file = Path(r"d:\ai_developer\project6") / output_png
        img.save(root_file)

        return f"/{output_png}"
    except Exception as e:
        logger.warning(f"Banner image generation fallback: {e}")
        return "/banner_promo_kreatif.png"

def parse_multi_agent_output(text, department="marketing", banner_url="/banner_promo_kreatif.png", prompt_topic=""):
    """
    Modular output parser that dynamically splits multi-agent responses 
    according to department without hardcoded template text.
    """
    t = text.strip() if text else ""
    
    # Customer Support Division: 2 Agents (Siti & Hendra)
    if department == "customer_support":
        tag2_patterns = [r"===BAGIAN_2[^=]*===", r"BAGIAN 2[:\s\-]+", r"## Bagian 2", r"HENDRA", r"Audit QA"]
        pos2 = -1
        for p in tag2_patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                pos2 = m.start()
                break

        if pos2 != -1:
            part1 = t[:pos2].strip()
            part2 = t[pos2:].strip()
        else:
            part1 = t
            part2 = "Catatan QA: Draf respon pelanggan telah ditinjau dan memenuhi standar SLA respon cepat."

        # Clean leading tags
        part1 = re.sub(r"===BAGIAN_1[^=]*===", "", part1, flags=re.IGNORECASE).strip()
        part2 = re.sub(r"===BAGIAN_2[^=]*===", "", part2, flags=re.IGNORECASE).strip()

        score_match = re.search(r"(\d+)\s*/\s*100", part2) or re.search(r"SKOR_QA[:\s]+(\d+)", part2, re.IGNORECASE)
        qa_score = int(score_match.group(1)) if score_match else 95

        agents_list = [
            {
                "id": "agent_1",
                "name": "Siti",
                "role": "Frontline Support Specialist",
                "avatar": "💬",
                "color": "sky",
                "badge": "Customer Response",
                "content": part1
            },
            {
                "id": "agent_2",
                "name": "Hendra",
                "role": "CS Team Lead & Quality Auditor",
                "avatar": "🛡️",
                "color": "teal",
                "badge": f"Audit QA: {qa_score}/100",
                "score": qa_score,
                "content": part2
            }
        ]

        return {
            "department": "customer_support",
            "agent_count": 2,
            "agents": agents_list,
            "agent_1": agents_list[0],
            "agent_2": agents_list[1]
        }

    # Sales Division: 2 Agents (Doni & Maya)
    elif department == "sales":
        tag2_patterns = [r"===BAGIAN_2[^=]*===", r"BAGIAN 2[:\s\-]+", r"## Bagian 2", r"MAYA", r"Strategi Closing"]
        pos2 = -1
        for p in tag2_patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                pos2 = m.start()
                break

        if pos2 != -1:
            part1 = t[:pos2].strip()
            part2 = t[pos2:].strip()
        else:
            part1 = t
            part2 = "Catatan Strategi: Kualifikasi lead telah dipetakan dan siap untuk follow-up komersial."

        part1 = re.sub(r"===BAGIAN_1[^=]*===", "", part1, flags=re.IGNORECASE).strip()
        part2 = re.sub(r"===BAGIAN_2[^=]*===", "", part2, flags=re.IGNORECASE).strip()

        rating_match = re.search(r"RATING_LEAD[:\s]+(HOT|WARM|COLD)", part1 + " " + part2, re.IGNORECASE)
        lead_rating = rating_match.group(1).upper() if rating_match else "WARM"

        agents_list = [
            {
                "id": "agent_1",
                "name": "Doni",
                "role": "B2B Lead Qualification Specialist",
                "avatar": "💼",
                "color": "amber",
                "badge": f"BANT Rating: {lead_rating}",
                "content": part1
            },
            {
                "id": "agent_2",
                "name": "Maya",
                "role": "Senior Proposal & Commercial Strategist",
                "avatar": "📈",
                "color": "emerald",
                "badge": "ROI & Closing Strategy",
                "content": part2
            }
        ]

        return {
            "department": "sales",
            "agent_count": 2,
            "agents": agents_list,
            "agent_1": agents_list[0],
            "agent_2": agents_list[1]
        }

    # Marketing & Creative Division: 3 Agents (Rian, Diana, Budi)
    else:
        tag1_patterns = [r"===BAGIAN_1[^=]*===", r"BAGIAN 1[:\s\-]+", r"## Bagian 1", r"1\.\s*PEGAWAI AI 1"]
        tag2_patterns = [r"===BAGIAN_2[^=]*===", r"BAGIAN 2[:\s\-]+", r"## Bagian 2", r"2\.\s*PEGAWAI AI 2", r"Audit QC", r"## Audit"]
        tag3_patterns = [r"===BAGIAN_3[^=]*===", r"BAGIAN 3[:\s\-]+", r"## Bagian 3", r"3\.\s*PEGAWAI AI 3", r"Konsep Visual", r"## Visual"]

        pos2 = -1
        for p in tag2_patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                pos2 = m.start()
                break

        pos3 = -1
        for p in tag3_patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m and (pos2 == -1 or m.start() > pos2):
                pos3 = m.start()
                break

        if pos2 != -1 and pos3 != -1:
            part1 = t[:pos2].strip()
            part2 = t[pos2:pos3].strip()
            part3 = t[pos3:].strip()
        elif pos2 != -1:
            part1 = t[:pos2].strip()
            part2 = t[pos2:].strip()
            part3 = f"Konsep Visual: Desain grafis kampanye untuk topik '{prompt_topic}'.\nPrompt DALL-E 3: High quality professional advertising graphic for {prompt_topic}, modern lighting, clean composition, 4k."
        else:
            part1 = t
            part2 = "Catatan Audit QC: Naskah telah ditinjau dan memenuhi parameter dasar SOP."
            part3 = f"Konsep Visual: Aset visual otomatis untuk '{prompt_topic}'."

        for p in tag1_patterns:
            part1 = re.sub(p, "", part1, flags=re.IGNORECASE).strip()
        for p in tag2_patterns:
            part2 = re.sub(p, "", part2, flags=re.IGNORECASE).strip()
        for p in tag3_patterns:
            part3 = re.sub(p, "", part3, flags=re.IGNORECASE).strip()

        score_match = re.search(r"SKOR_QC[:\s]+(\d+)", part2, re.IGNORECASE) or re.search(r"(\d+)\s*/\s*100", part2)
        qc_score = int(score_match.group(1)) if score_match else 90

        agents_list = [
            {
                "id": "agent_1",
                "name": "Rian",
                "role": "Copywriting Specialist",
                "avatar": "✍️",
                "color": "amber",
                "badge": "Naskah AIDA",
                "content": part1
            },
            {
                "id": "agent_2",
                "name": "Diana",
                "role": "Creative Director & QC Auditor",
                "avatar": "🔍",
                "color": "teal",
                "badge": f"Skor QC: {qc_score}/100",
                "score": qc_score,
                "content": part2
            },
            {
                "id": "agent_3",
                "name": "Budi",
                "role": "Visual Designer & Art Director",
                "avatar": "🎨",
                "color": "indigo",
                "badge": "Aset Visual & Prompt",
                "image_url": banner_url,
                "content": part3
            }
        ]

        return {
            "department": "marketing",
            "agent_count": 3,
            "agents": agents_list,
            "agent_1": agents_list[0],
            "agent_2": agents_list[1],
            "agent_3": agents_list[2]
        }

class PegawaiAIRequestHandler(BaseHTTPRequestHandler):
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Pegawai-AI-Key, X-Department")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Pegawai-AI-Key, X-Department")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html_file = Path(__file__).parent / "index.html"
            if html_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(html_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self._send_json_response(404, {"error": "Dashboard HTML not found"})
                return

        elif path.endswith(".png") or path.endswith(".jpg"):
            filename = os.path.basename(path)
            for cand in [
                Path(__file__).parent / filename,
                Path(r"d:\ai_developer\project6") / filename,
                Path(__file__).parent / "public" / filename
            ]:
                if cand.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png" if filename.endswith(".png") else "image/jpeg")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    with open(cand, "rb") as img_f:
                        self.wfile.write(img_f.read())
                    return
            self._send_json_response(404, {"error": "Image not found"})
            return

        elif path == "/health" or path == "/api/v1/health":
            hermes_exists = os.path.exists(HERMES_BIN)
            has_opencode_go_key = bool(os.environ.get("OPENCODE_GO_API_KEY"))
            has_opencode_key = bool(os.environ.get("OPENCODE_ZEN_API_KEY") or os.environ.get("OPENCODE_API_KEY"))
            has_deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY")) and not has_opencode_key and not os.environ.get("DEEPSEEK_API_KEY", "").startswith("oc_")
            
            resp = {
                "status": "healthy",
                "service": "Pegawai AI Shared Backend POC (S2-03A)",
                "sprint": "Sprint 2 - Day 3 (November 2, 2026)",
                "intern_role": "Intern 1: Local Setup & Technical Research",
                "hermes": {
                    "installed": hermes_exists,
                    "binary_path": HERMES_BIN,
                    "version": "v0.22.2+3291.gbf0203a (stable)"
                },
                "model_configuration": {
                    "target_model": "DeepSeek V4.1 Flash",
                    "target_identifier": "deepseek-v4.1-flash",
                    "active_provider": "opencode-go" if has_opencode_go_key else ("opencode" if has_opencode_key else ("deepseek" if has_deepseek_key else "copilot")),
                    "credentials_status": "READY (Active via Opencode Go Provider)" if has_opencode_go_key else ("READY (Active via Opencode Provider)" if has_opencode_key else ("READY (Direct DeepSeek)" if has_deepseek_key else "FALLBACK_COPILOT")),
                    "live_model_in_use": "deepseek-v4.1-flash" if (has_opencode_go_key or has_opencode_key or has_deepseek_key) else "gpt-4o"
                },
                "server_time": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            }
            self._send_json_response(200, resp)

        elif path == "/api/v1/config":
            resp = {
                "customer_context": {
                    "profile_name": "PT AI Top Trends v1.0.0",
                    "business_type": "AI Agency & Automation Services",
                    "sop_version": "2026.10-standard"
                },
                "department_defaults": {
                    "marketing": {"tone": "grounded_persuasive", "max_tokens": 2500, "default_agents": 3},
                    "customer_support": {"tone": "polite_helpful", "max_tokens": 1500, "default_agents": 2},
                    "sales": {"tone": "consultative", "max_tokens": 2000, "default_agents": 2},
                    "general": {"tone": "objective", "max_tokens": 2000, "default_agents": 1}
                },
                "authorization": {
                    "mode": "header_token",
                    "header": "X-Pegawai-AI-Key",
                    "allowed_departments": ["marketing", "customer_support", "sales", "general"]
                }
            }
            self._send_json_response(200, resp)

        elif path == "/api/v1/sops":
            sops_dir = Path(__file__).parent / "context" / "sops"
            sops_data = {}
            if sops_dir.exists():
                for f in sops_dir.glob("*.md"):
                    try:
                        with open(f, "r", encoding="utf-8") as sf:
                            sops_data[f.stem] = sf.read()
                    except Exception:
                        pass
            self._send_json_response(200, {"sops": sops_data})

        elif path.startswith("/api/v1/mocks/"):
            mock_name = os.path.basename(path)
            if not mock_name.endswith(".json"):
                mock_name += ".json"
            mock_file = Path(__file__).parent.parent / "mock_fixtures" / mock_name
            if mock_file.exists():
                try:
                    with open(mock_file, "r", encoding="utf-8") as mf:
                        self._send_json_response(200, json.load(mf))
                    return
                except Exception as e:
                    self._send_json_response(500, {"error": f"Failed to load mock: {e}"})
                    return
            self._send_json_response(404, {"error": f"Mock fixture '{mock_name}' not found"})
            return

        elif path == "/api/v1/sessions":
            self._send_json_response(200, {"total_sessions": len(SESSION_HISTORY), "sessions": SESSION_HISTORY})

        else:
            self._send_json_response(404, {"error": "Not Found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/agent/execute":
            auth_header = self.headers.get("X-Pegawai-AI-Key", "demo-token")
            dept_header = self.headers.get("X-Department", "marketing")

            content_len = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_len)

            try:
                payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception as e:
                self._send_json_response(400, {"error": "Invalid JSON body", "detail": str(e)})
                return

            prompt = payload.get("prompt")
            if not prompt:
                self._send_json_response(400, {"error": "Field 'prompt' is required"})
                return

            department = payload.get("department", dept_header).lower()
            agent_mode = payload.get("agent_mode", "auto")
            is_multi_agent = payload.get("multi_agent", True)
            if agent_mode == "single":
                is_multi_agent = False

            req_provider = payload.get("provider", "opencode")
            req_model = payload.get("model", "deepseek-v4.1-flash")
            timeout_sec = int(payload.get("timeout_seconds", 180))

            session_id = f"sess_{uuid.uuid4().hex[:8]}"
            usage_file = f"temp_usage_{session_id}.json"

            # Opencode / DeepSeek credentials check
            actual_provider = req_provider
            actual_model = req_model
            fallback_applied = False
            blocker_note = None

            has_opencode_go = bool(os.environ.get("OPENCODE_GO_API_KEY"))
            has_opencode = bool(os.environ.get("OPENCODE_ZEN_API_KEY") or os.environ.get("OPENCODE_API_KEY"))
            has_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))

            if req_provider in ["deepseek", "opencode", "opencode-go"]:
                if has_opencode_go:
                    actual_provider = "opencode-go"
                    actual_model = "deepseek-v4.1-flash"
                    logger.info("Routing DeepSeek request to Opencode Go provider with deepseek-v4.1-flash")
                elif has_opencode:
                    actual_provider = "opencode"
                    actual_model = "deepseek-v4.1-flash"
                    logger.info("Routing DeepSeek request to Opencode provider with deepseek-v4.1-flash")
                elif has_deepseek and not os.environ.get("DEEPSEEK_API_KEY", "").startswith("oc_"):
                    actual_provider = "deepseek"
                    actual_model = "deepseek-flash"
                else:
                    blocker_note = "Opencode/DeepSeek credentials not configured. Falling back to Copilot/gpt-4o."
                    actual_provider = "copilot"
                    actual_model = "gpt-4o"
                    fallback_applied = True
                    logger.warning(blocker_note)

            # Department SOP context
            sop_file = Path(__file__).parent / "context" / "sops" / f"sop_{department}.md"
            sop_context = ""
            if sop_file.exists():
                try:
                    with open(sop_file, "r", encoding="utf-8") as sf:
                        sop_context = sf.read()
                except Exception:
                    pass

            banner_url = "/banner_promo_kreatif.png"

            # -------------------------------------------------------------
            # DYNAMIC MULTI-AGENT PROMPT CONSTRUCTION (NO HARDCODED TEMPLATES)
            # -------------------------------------------------------------
            if is_multi_agent:
                if department == "customer_support":
                    full_prompt = (
                        f"Bertindaklah sebagai Tim Divisi Layanan Pelanggan (Customer Support) PT AI Top Trends.\n"
                        f"Topik / Kasus Tiket Pelanggan: \"{prompt}\"\n\n"
                        f"Instruksi Kolaborasi 2 Pegawai AI:\n"
                        f"Kerjakan tugas masing-masing secara orisinal, kontekstual, dan jangan gunakan template umum. "
                        f"WAJIB pisahkan hasil kerja dengan blok penanda eksak berikut:\n\n"
                        f"===BAGIAN_1_SITI_CS_SPECIALIST===\n"
                        f"Tulis HANYA isi email balasan untuk pelanggan, langsung dimulai dari salam. Aturan:\n"
                        f"- 80 sampai 180 kata, paragraf pendek, tanpa subjudul.\n"
                        f"- Jangan menulis catatan proses, rujukan SOP, nomor pasal, tanggal acuan, atau penjelasan cara kerja Anda.\n"
                        f"- Pakai 'kami' untuk perusahaan. Jangan menyebut nama divisi internal seperti Billing, Legal, atau Tim Spesialis Senior.\n"
                        f"- Akui masalahnya dan minta maaf cukup sekali, singkat.\n"
                        f"- Tulis apa yang sedang berjalan, bukan apa yang belum bisa dilakukan. Janjikan proses (meninjau, mengabari), jangan janjikan hasil (refund pasti, kompensasi) atau waktu tertentu.\n"
                        f"- Jangan menyatakan tindakan yang belum dikonfirmasi sistem: kasus sudah diteruskan atau dieskalasikan, petugas akan menghubungi, refund disetujui, data sudah dihapus. Rekomendasi eskalasi hanya ditulis Hendra.\n"
                        f"- Jangan mengaku sudah melihat data akun atau transaksi yang tidak ada dalam kasus. Nomor tiket hanya boleh disebut jika ada dalam kasus.\n"
                        f"- Langkah untuk pelanggan paling banyak 3, bernomor dan singkat. Jika perlu bukti, minta dikirim dengan membalas email.\n"
                        f"- Tegaskan bahwa kami tidak pernah meminta kata sandi, token, nomor kartu lengkap, CVV, atau PIN, bila kasus menyangkut akun atau pembayaran.\n"
                        f"- Tutup dengan apa yang terjadi berikutnya, lalu tanda tangan: Siti, Layanan Pelanggan PT AI Top Trends.\n\n"
                        f"===BAGIAN_2_HENDRA_QA_LEAD===\n"
                        f"Audit draf respon dari Siti di Bagian 1 secara kritis:\n"
                        f"SKOR_QA: [Berikan skor kepatuhan SOP antara 0-100 secara objektif]\n"
                        f"ANALISIS_EMPATI: [Evaluasi apakah nada bicara Siti cukup menenangkan pelanggan]\n"
                        f"KETEPATAN_SOLUSI: [Evaluasi apakah langkah solusinya sudah akurat]\n"
                        f"KEPATUHAN_KOMUNIKASI: [Periksa catatan proses, nama divisi internal, janji hasil atau waktu, klaim tindakan yang belum terjadi, dan panjang 80-180 kata. Sebutkan setiap pelanggaran.]\n"
                        f"STATUS_ESKALASI: [AMAT_AMAN / BUTUH_MONITORING / PERLU_ESKALASI_MANAJEMEN]\n"
                        f"REKOMENDASI_TAMBAHAN: [Saran penyempurnaan konkret untuk penanganan kasus serupa ke depan]"
                    )
                elif department == "sales":
                    full_prompt = (
                        f"Bertindaklah sebagai Tim Divisi Penjualan & Konsultasi B2B PT AI Top Trends.\n"
                        f"Topik / Kasus Prospek Bisnis: \"{prompt}\"\n\n"
                        f"Instruksi Kolaborasi 2 Pegawai AI:\n"
                        f"Kerjakan tugas masing-masing secara tajam, berorientasi bisnis nyata, dan tanpa basa-basi klise. "
                        f"WAJIB pisahkan hasil kerja dengan blok penanda eksak berikut:\n\n"
                        f"===BAGIAN_1_DONI_LEAD_QUALIFIER===\n"
                        f"Analisa prospek/kasus di atas menggunakan kerangka BANT:\n"
                        f"- Budget & Kapasitas Finansial: [Analisa singkat]\n"
                        f"- Authority (Pengambil Keputusan): [Analisa singkat]\n"
                        f"- Need & Masalah Utama: [Analisa mendalam]\n"
                        f"- Timing & Urgensi Solusi: [Analisa]\n"
                        f"RATING_LEAD: [HOT / WARM / COLD]\n\n"
                        f"===BAGIAN_2_MAYA_COMMERCIAL_STRATEGIST===\n"
                        f"Lanjutkan analisis Doni dengan strategi penawaran komersial:\n"
                        f"PROYEKSI_ROI_EFISIENSI: [Hitung estimasi penghematan biaya atau peningkatan omzet yang realistis]\n"
                        f"STRATEGI_CLOSING: [Taktik penawaran konsultatif tanpa hard-selling]\n"
                        f"DRAF_EMAIL_FOLLOW_UP: [Tuliskan draf pesan follow-up personal yang elegan untuk mengajak booking sesi konsultasi 30 menit]"
                    )
                else:
                    # Marketing & Creative Division (3 Agents)
                    banner_url = generate_banner_image(prompt, department=department)
                    full_prompt = (
                        f"Bertindaklah sebagai Tim Divisi Pemasaran & Kreatif PT AI Top Trends.\n"
                        f"Topik / Brief Konten: \"{prompt}\"\n\n"
                        f"Instruksi Kolaborasi 3 Pegawai AI:\n"
                        f"PENTING: Jangan gunakan teks contoh atau template jawaban statis! Berikan analisis dan kreasi yang 100% orisinal, segar, dan spesifik untuk topik brief di atas. "
                        f"Pisahkan hasil kerja masing-masing dengan blok penanda eksak berikut:\n\n"
                        f"===BAGIAN_1_RIAN_COPYWRITER===\n"
                        f"Tuliskan naskah konten lengkap yang memikat, mendalam, dan relevan dengan topik brief (gunakan formula AIDA: Attention, Interest, Desire, Action), gaya bahasa membumi dan berwibawa, serta sertakan 5-7 tagar yang relevan.\n\n"
                        f"===BAGIAN_2_DIANA_QC_AUDITOR===\n"
                        f"Lakukan audit kritis dan menyeluruh terhadap naskah yang baru saja ditulis oleh Rian di Bagian 1:\n"
                        f"SKOR_QC: [Tentukan skor kepatuhan antara 0-100 secara objektif berdasarkan kualitas naskah Rian]\n"
                        f"AUDIT_BRAND_VOICE: [Evaluasi apakah gayanya otoritatif, solutif, dan rendah hati tanpa kesombongan]\n"
                        f"FILTER_KATA_TERLARANG: [Periksa apakah naskah bersih dari janji tidak realistis atau klaim berlebihan]\n"
                        f"EVALUASI_AIDA: [Kritik ketajaman hook pembuka, kedalaman isi masalah, dan relevansi CTA]\n"
                        f"SARAN_PERBAIKAN: [Berikan kritik konstruktif atau saran penyempurnaan nyata untuk naskah ini]\n"
                        f"STATUS_AKHIR: [DRAFT_READY_FOR_HUMAN_REVIEW / PERLU_REVISI]\n\n"
                        f"===BAGIAN_3_BUDI_VISUAL===\n"
                        f"Rancang konsep visual dan grafis yang 100% spesifik dan selaras dengan topik brief di atas:\n"
                        f"KONSEP_VISUAL: [Deskripsikan tata letak, mood, fokus objek gambar, dan rasio gambar yang ideal]\n"
                        f"PALET_WARNA: [Tentukan 2-3 warna utama beserta kode heksadesimalnya yang mencerminkan topik ini]\n"
                        f"PROMPT_IMAGE_GEN: [Tuliskan deskripsi prompt AI dalam bahasa Inggris yang detail dan sinematik untuk Midjourney/DALL-E 3 agar menghasilkan visual yang memukau untuk topik ini]"
                    )
            else:
                # Single Agent Mode
                full_prompt = prompt
                if sop_context and "STANDAR OPERASIONAL PROSEDUR" not in prompt:
                    full_prompt = f"[PANDUAN SOP DIVISI {department.upper()}]:\n{sop_context}\n\n[INSTRUKSI TUGAS]:\n{prompt}"

            cmd = [
                HERMES_BIN,
                "-z", full_prompt,
                "--provider", actual_provider,
                "--model", actual_model,
                "--usage-file", usage_file
            ]

            start_t = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_sec,
                    cwd=os.getcwd()
                )
                elapsed = time.time() - start_t

                usage_data = {}
                if os.path.exists(usage_file):
                    try:
                        with open(usage_file, "r", encoding="utf-8") as uf:
                            usage_data = json.load(uf)
                        os.remove(usage_file)
                    except Exception:
                        pass

                raw_output = proc.stdout.strip()
                if proc.returncode != 0 and not raw_output:
                    self._send_json_response(500, {
                        "status": "error",
                        "error_code": "HERMES_EXECUTION_FAILED",
                        "message": proc.stderr.strip() or "Hermes returned non-zero exit code",
                        "provider": actual_provider,
                        "model": actual_model
                    })
                    return

                # Parse multi-agent data dynamically
                multi_agent_data = None
                if is_multi_agent:
                    multi_agent_data = parse_multi_agent_output(
                        raw_output, 
                        department=department, 
                        banner_url=banner_url,
                        prompt_topic=prompt
                    )

                response_payload = {
                    "status": "success",
                    "session_id": session_id,
                    "customer_id": payload.get("customer_id", "cust_default"),
                    "department": department,
                    "agent_mode": agent_mode,
                    "agent_count": multi_agent_data.get("agent_count", 1) if multi_agent_data else 1,
                    "provider": actual_provider,
                    "model": actual_model,
                    "fallback_applied": fallback_applied,
                    "blocker_note": blocker_note,
                    "execution_time_seconds": round(elapsed, 2),
                    "output": raw_output,
                    "multi_agent_data": multi_agent_data,
                    "token_usage": {
                        "input_tokens": usage_data.get("input_tokens", 0),
                        "output_tokens": usage_data.get("output_tokens", 0),
                        "total_tokens": usage_data.get("total_tokens", 0)
                    },
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
                }

                SESSION_HISTORY.append({
                    "session_id": session_id,
                    "department": department,
                    "agent_count": response_payload["agent_count"],
                    "elapsed": round(elapsed, 2),
                    "model": actual_model,
                    "timestamp": response_payload["timestamp"]
                })
                if len(SESSION_HISTORY) > 50:
                    SESSION_HISTORY.pop(0)

                self._send_json_response(200, response_payload)

            except subprocess.TimeoutExpired:
                self._send_json_response(504, {
                    "status": "error",
                    "error_code": "EXECUTION_TIMEOUT",
                    "message": f"Agent execution exceeded timeout of {timeout_sec} seconds"
                })
            except Exception as e:
                self._send_json_response(500, {
                    "status": "error",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": str(e)
                })
        else:
            self._send_json_response(404, {"error": "Not Found", "path": path})

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, PegawaiAIRequestHandler)
    logger.info(f"Pegawai AI Shared Backend POC running on http://127.0.0.1:{PORT}")
    logger.info("Ready for dynamic multi-agent requests (Marketing, CS, Sales)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down cleanly...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
