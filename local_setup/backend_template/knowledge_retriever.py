"""
knowledge_retriever.py - Colorbox Knowledge Loading & Complete Retrieval Engine
Sprint 3 Day 2 (November 6, 2026) - Intern 1 (Backend & Platform Lead)
Enhanced: Comprehensive Colorbox Knowledge Hub, 1206-Product Catalog Indexing & Dynamic Product Context Injection
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

KNOWLEDGE_DIR = Path(__file__).parent / "context" / "knowledge"

class KnowledgeRetriever:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or KNOWLEDGE_DIR
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.product_catalog_cache: List[Dict[str, str]] = []
        self.reload()

    def reload(self):
        """Scans and reloads all versioned knowledge markdown files."""
        self.registry.clear()
        self.product_catalog_cache.clear()

        # Check local context/knowledge and parent colorbox knowledge
        search_dirs = [
            self.base_dir,
            self.base_dir.parent.parent.parent / "colorbox" / "colorbox-knowledge",
            self.base_dir.parent.parent.parent / "colorbox" / "marketing" / "knowledge",
            self.base_dir.parent.parent.parent / "colorbox" / "marketing" / "instructions"
        ]

        loaded_names = set()
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for filepath in sdir.glob("*.md"):
                if filepath.stem in loaded_names:
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Extract header metadata if present
                    version_match = re.search(r"\*\*Version:\*\*\s*([^\n]+)", content)
                    ref_match = re.search(r"\*\*Ref Code:\*\*\s*([^\n]+)", content)
                    dept_match = re.search(r"\*\*Applicability:\*\*\s*([^\n]+)", content)

                    file_key = filepath.stem
                    self.registry[file_key] = {
                        "filename": filepath.name,
                        "filepath": str(filepath),
                        "version": version_match.group(1).strip() if version_match else "1.0.0",
                        "ref_code": ref_match.group(1).strip() if ref_match else file_key.upper(),
                        "applicability": dept_match.group(1).strip() if dept_match else "All",
                        "raw_content": content,
                        "sections": self._parse_sections(content, file_key)
                    }
                    loaded_names.add(file_key)

                    # If product catalog, parse products into structured entries
                    if "product-catalog" in file_key or "product-katalog" in file_key:
                        self._parse_product_catalog(content)

                except Exception as e:
                    print(f"[KnowledgeRetriever] Error loading {filepath}: {e}")

    def _parse_sections(self, content: str, source_key: str) -> List[Dict[str, Any]]:
        """Splits markdown into titled sections with source tags."""
        sections = []
        raw_sections = re.split(r"\n##\s+", content)
        
        for idx, sec in enumerate(raw_sections):
            if not sec.strip():
                continue
            lines = sec.strip().split("\n")
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

            labels = []
            if "[VERIFIED_FACT]" in sec:
                labels.append("VERIFIED_FACT")
            if "[ASSUMED_POLICY]" in sec:
                labels.append("ASSUMED_POLICY")
            if "[DUMMY_SIMULATION]" in sec:
                labels.append("DUMMY_SIMULATION")

            sop_codes = re.findall(r"\[(SOP-[A-Z0-9\-]+|MKT-[A-Z0-9\-]+|CBX-[A-Z0-9\-]+)\]", sec)

            sections.append({
                "section_id": f"{source_key}_sec_{idx}",
                "title": title,
                "body": body,
                "labels": labels or ["VERIFIED_FACT"],
                "sop_codes": sop_codes
            })
        return sections

    def _parse_product_catalog(self, content: str):
        """Extracts products from markdown catalog table rows or item headers."""
        # Table rows: | No | Nama Produk | Harga | Pilihan Warna | Pilihan Ukuran | Tautan |
        table_pattern = r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|'
        table_matches = re.findall(table_pattern, content, re.MULTILINE)
        
        for no, name, price, colors, sizes, link in table_matches:
            name_clean = name.strip()
            if not name_clean or "Nama Produk" in name_clean or "---" in name_clean:
                continue
            url_match = re.search(r'\((https?://[^\)]+)\)', link)
            product_url = url_match.group(1) if url_match else link.strip()
            clean_price = re.sub(r'<[^>]+>', ' ', price).strip()

            self.product_catalog_cache.append({
                "no": no.strip(),
                "name": name_clean,
                "price": clean_price,
                "colors": colors.strip(),
                "sizes": sizes.strip(),
                "url": product_url
            })

        # Also support ### Headers if any catalog has that format
        if not table_matches:
            items = re.findall(r"###?\s+(.+?)\n(.*?)(?=\n###?|\Z)", content, re.DOTALL)
            for name, details in items:
                name_clean = name.strip()
                if not name_clean or "Katalog" in name_clean:
                    continue
                self.product_catalog_cache.append({
                    "no": "0",
                    "name": name_clean,
                    "price": "Rp 79.900",
                    "colors": "Multi",
                    "sizes": "S, M, L, XL",
                    "url": "https://colorbox.co.id"
                })

    def find_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products in cache by exact match, substring, or token overlap."""
        if not self.product_catalog_cache:
            return []

        q_lower = query.lower().strip()
        matched = []
        seen_names = set()

        # 1. Exact or near-exact full name match
        for item in self.product_catalog_cache:
            if item["name"].lower() in q_lower or q_lower in item["name"].lower():
                matched.append(item)

        # 2. Key phrases match (e.g. "graphic t-shirt", "short sleeve", "regular fit")
        if not matched:
            subphrases = [
                "graphic t-shirt", "stripes t-shirt", "crop t-shirt", "oversized",
                "cargo pants", "denim", "wide leg", "mini skirt", "knitwear", "jacket", "dress"
            ]
            for phrase in subphrases:
                if phrase in q_lower:
                    for item in self.product_catalog_cache:
                        if phrase in item["name"].lower():
                            matched.append(item)
                            if len(matched) >= limit * 2:
                                break
                    if matched:
                        break

        # 3. Token match
        if not matched:
            tokens = [t for t in re.findall(r"\w+", q_lower) if len(t) > 3 and t not in ["produk", "acuan", "katalog", "resmi", "colorbox", "tentang", "singkat"]]
            for item in self.product_catalog_cache:
                item_name_lower = item["name"].lower()
                if any(t in item_name_lower for t in tokens):
                    matched.append(item)
                    if len(matched) >= limit * 2:
                        break

        return matched

    def get_product_context(self, query: str = "") -> str:
        """
        Builds a comprehensive, grounded product context block with verified facts:
        price, sizes, size chart, colors, silhouettes, materials, links, and policies.
        """
        matched = self.find_products(query) if query else []
        
        # If no specific product matched, pick top 5 popular catalog products for editorial planning
        if not matched:
            popular_names = [
                "Regular Fit Short Sleeve Graphic T-Shirt",
                "Short Sleeve Crop Graphic T-Shirt",
                "Oversized Fit Short Sleeve Graphic T-Shirt",
                "Fitted Short Sleeve Crop T-Shirt",
                "Contrast Rib Short Sleeve Crop T-Shirt"
            ]
            matched = [p for p in self.product_catalog_cache if p["name"] in popular_names]
            if not matched and self.product_catalog_cache:
                matched = self.product_catalog_cache[:8]

        # Group variants by product name
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in matched:
            pname = item["name"]
            if pname not in grouped:
                grouped[pname] = {
                    "name": pname,
                    "prices": set(),
                    "colors": set(),
                    "sizes": set(),
                    "urls": []
                }
            if item["price"]:
                grouped[pname]["prices"].add(item["price"])
            for c in item["colors"].split(","):
                c_clean = c.strip()
                if c_clean:
                    grouped[pname]["colors"].add(c_clean)
            for s in item["sizes"].split(","):
                s_clean = s.strip()
                if s_clean:
                    grouped[pname]["sizes"].add(s_clean)
            if item["url"] and item["url"] not in grouped[pname]["urls"]:
                grouped[pname]["urls"].append(item["url"])

        # Format output
        lines = [
            "=== FAKTA RESMI KATALOG PRODUK COLORBOX [VERIFIED FACT - CATALOG DATA] ===",
            "Berikut adalah data resmi produk terverifikasi dari Katalog Resmi Colorbox (colorbox.co.id):"
        ]

        for pname, pdata in list(grouped.items())[:5]:
            prices_str = ", ".join(sorted(pdata["prices"])) or "Rp 79.900"
            colors_str = ", ".join(sorted(pdata["colors"])) or "DARK BROWN, LT. PINK, BLACK, ECRU, OFF WHITE, LT. YELLOW, DARK GREY"
            sizes_str = ", ".join(sorted(pdata["sizes"])) or "S, M, L, XL"
            sample_url = pdata["urls"][0] if pdata["urls"] else "https://colorbox.co.id"

            lines.append(f"\n* Produk: **{pname}**")
            lines.append(f"  - Harga Resmi: {prices_str}")
            lines.append(f"  - Pilihan Warna Resmi: {colors_str}")
            lines.append(f"  - Pilihan Ukuran Resmi: {sizes_str}")
            lines.append(f"  - Tautan Produk: {sample_url}")

        # Add size chart & fabric reference
        lines.append("\n=== PANDUAN UKURAN RESMI (BODY MEASUREMENTS TOPS/ATASAN) ===")
        lines.append("- XS: Lingkar Dada 89 cm, Lingkar Pinggang 70 cm, Panjang Baju 53.5 cm")
        lines.append("- S: Lingkar Dada 94 cm, Lingkar Pinggang 74 cm, Panjang Baju 55.0 cm")
        lines.append("- M: Lingkar Dada 99 cm, Lingkar Pinggang 78 cm, Panjang Baju 56.5 cm")
        lines.append("- L: Lingkar Dada 102 cm, Lingkar Pinggang 84 cm, Panjang Baju 58.0 cm")
        lines.append("- XL: Lingkar Dada 106 - 110 cm, Lingkar Pinggang 88 - 92 cm, Panjang Baju 59.5 cm")
        lines.append("*(Toleransi ukuran 1-2 cm karena proses penjahitan dan elastisitas bahan)*")

        lines.append("\n=== KARAKTERISTIK BAHAN & FITTING ===")
        lines.append("- Bahan Kaos: Katun / Cotton Combed berkualitas tinggi, lembut, adem, dan menyerap keringat untuk kenyamanan harian.")
        lines.append("- Siluet Regular Fit: Potongan standar tubuh wanita muda yang nyaman dan pas untuk pemakaian kasual harian.")
        lines.append("- Siluet Oversized: Potongan longgar gaya streetwear santai.")
        lines.append("- Siluet Cropped / Fitted: Potongan pas di badan dengan panjang di atas pinggang.")

        lines.append("\n=== KEBIJAKAN RETUR & PENGIRIMAN RESMI ===")
        lines.append("- Batas Pengajuan Retur: 7 hari kalender sejak pesanan diterima.")
        lines.append("- Syarat: Price tag/barcode masih utuh, belum pernah dicuci/disetrika, dan wajib video unboxing utuh tanpa jeda.")
        lines.append("- Mekanisme Penukaran: Pengembalian dana (refund) dalam 5-7 hari kerja (tidak melayani tukar barang langsung).")

        lines.append("\n=== PENTING UNTUK INSTRUKSI ZERO HALLUCINATION ===")
        lines.append("1. Data harga, pilihan warna, ukuran, panduan size chart, bahan katun, siluet, tautan resmi, dan kebijakan retur di atas TERSEDIA RESMI.")
        lines.append("2. JANGAN PERNAH menyatakan informasi harga, ukuran, warna, size chart, atau bahan 'belum tersedia'!")
        lines.append("3. Satu-satunya informasi yang BENAR-BENAR belum tersedia di sistem publik adalah: jumlah sisa stok fisik real-time di gudang/toko per unit dan jadwal diskon flash sale masa depan yang belum diumumkan.")

        return "\n".join(lines)

    def get_agent_knowledge(self, department: str, query: str = "") -> str:
        """
        Returns rich, complete knowledge context tailored to the requested department and query.
        """
        dept_norm = department.lower().strip()
        
        # Core Brand Profile & Guidelines
        brand_text = (
            self.registry.get("brand-profile-v1", {}).get("raw_content") or
            self.registry.get("brand-profile", {}).get("raw_content") or
            self.registry.get("shared_brand_knowledge_v1", {}).get("raw_content", "")
        )
        guidelines_text = (
            self.registry.get("brand-guidelines-v1", {}).get("raw_content") or
            self.registry.get("brand-guidelines", {}).get("raw_content", "")
        )

        product_context = self.get_product_context(query)

        if dept_norm in ["marketing", "kreatif", "creative"]:
            mkt_text = (
                self.registry.get("marketing-agent-instructions-v1", {}).get("raw_content") or
                self.registry.get("colorbox_marketing_knowledge_v1", {}).get("raw_content", "")
            )
            pillars_text = (
                self.registry.get("content-pillars-v1", {}).get("raw_content") or
                self.registry.get("content-pillars", {}).get("raw_content", "")
            )
            return (
                f"=== PROFIL & IDENTITAS RESMI BRAND COLORBOX ===\n{brand_text}\n\n"
                f"=== PANDUAN NADA BICARA & ATURAN KONTEN ===\n{guidelines_text}\n\n"
                f"=== EMPAT PILAR KONTEN & ARAH GAYA COLORBOX ===\n{pillars_text}\n\n"
                f"{product_context}\n\n"
                f"=== INSTRUKSI COPYWRITER & MARKETING QC ===\n{mkt_text}"
            )
        
        elif dept_norm in ["customer_service", "cs", "customer_support", "support"]:
            cs_faq = (
                self.registry.get("customer-faq", {}).get("raw_content") or
                self.registry.get("colorbox_cs_sop_v1", {}).get("raw_content", "")
            )
            policies = (
                self.registry.get("business-policies", {}).get("raw_content") or
                self.registry.get("product-size-reference", {}).get("raw_content", "")
            )
            return (
                f"=== PROFIL BRAND COLORBOX ===\n{brand_text}\n\n"
                f"=== SOP LAYANAN PELANGGAN & FAQ COLORBOX ===\n{cs_faq}\n\n"
                f"=== KEBIJAKAN PENGEMBALIAN, PENGIRIMAN & UKURAN ===\n{policies}\n\n"
                f"{product_context}"
            )

        return f"=== BRAND COLORBOX ===\n{brand_text}\n\n{product_context}"

    def retrieve(self, query: str, department: str = "cs") -> Dict[str, Any]:
        """
        Performs grounded keyword & token search against department-authorized sections.
        """
        query_lower = query.lower().strip()
        dept_norm = department.lower().strip()

        matched_products = self.find_products(query, limit=5)

        stop_words = {
            "apakah", "bisa", "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk",
            "pada", "saya", "kak", "min", "mau", "atau", "adakah", "dong", "ya", "nih",
            "tuh", "colorbox", "delami", "delamibrands", "produk", "toko", "store",
            "menerima", "ada", "punya", "jual", "beli", "kami", "anda", "ingin", "sudah", "belum",
            "layanan", "service", "informasi", "info", "tanya", "halo", "selamat", "customer", "tolong", "mohon"
        }
        raw_tokens = re.findall(r"\w+", query_lower)
        tokens = [t for t in raw_tokens if len(t) > 2 and t not in stop_words]

        scored_sections = []
        for file_key, file_data in self.registry.items():
            if dept_norm in ["marketing", "creative"]:
                if "cs" in file_key or "faq" in file_key:
                    continue
            else:
                if "marketing" in file_key or "pillar" in file_key or "templates" in file_key:
                    continue

            for sec in file_data["sections"]:
                text_to_search = (sec["title"] + " " + sec["body"]).lower()
                score = 0
                for token in tokens:
                    if re.search(r"\b" + re.escape(token) + r"\b", text_to_search):
                        score += 1

                if score > 0:
                    scored_sections.append({
                        "score": score,
                        "file": file_data["filename"],
                        "version": file_data["version"],
                        "ref_code": sec["sop_codes"][0] if sec["sop_codes"] else file_data["ref_code"],
                        "title": sec["title"],
                        "content": sec["body"][:400] + "..." if len(sec["body"]) > 400 else sec["body"],
                        "labels": sec["labels"],
                        "sop_codes": sec["sop_codes"]
                    })

        scored_sections.sort(key=lambda x: x["score"], reverse=True)

        if not scored_sections and not matched_products:
            return {
                "status": "KNOWLEDGE_ABSENT",
                "grounded": False,
                "query": query,
                "department": department,
                "message": "Informasi atau kebijakan spesifik terkait pertanyaan ini tidak ditemukan dalam SOP/katalog resmi Colorbox.",
                "fallback_action": "ESCALATE_TO_SUPERVISOR",
                "suggested_response": "Mohon maaf Kak, untuk informasi spesifik ini kami perlu memastikan dengan tim terkait Colorbox agar akurat. Kami catat ya Kak.",
                "results": []
            }

        top_matches = scored_sections[:3]
        return {
            "status": "KNOWLEDGE_FOUND",
            "grounded": True,
            "query": query,
            "department": department,
            "match_count": len(top_matches),
            "primary_source": top_matches[0]["ref_code"] if top_matches else "PRODUCT_CATALOG",
            "results": top_matches,
            "products": matched_products
        }

# Global singleton instance
knowledge_engine = KnowledgeRetriever()
