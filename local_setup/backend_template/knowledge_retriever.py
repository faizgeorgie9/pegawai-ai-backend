"""
knowledge_retriever.py - Colorbox Knowledge Loading & Simple Retrieval Engine
Sprint 3 Day 2 (November 6, 2026) - Intern 1 (Backend & Platform Lead)

Features:
- Incremental versioned markdown loading from context/knowledge/
- Department-specific isolation (Marketing vs Customer Service)
- Truthful absent/missing data behavior (Zero Hallucination / Honest Fallback)
- Conflict resolution (Department-specific SOP takes precedence over Shared Brand)
- Strict source labeling ([VERIFIED_FACT], [ASSUMED_POLICY], [DUMMY_SIMULATION])
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
        self.reload()

    def reload(self):
        """Scans and reloads all versioned knowledge markdown files."""
        self.registry.clear()
        if not self.base_dir.exists():
            return

        for filepath in self.base_dir.glob("*.md"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract header metadata
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

            # Detect verified / assumed / dummy labels
            labels = []
            if "[VERIFIED_FACT]" in sec:
                labels.append("VERIFIED_FACT")
            if "[ASSUMED_POLICY]" in sec:
                labels.append("ASSUMED_POLICY")
            if "[DUMMY_SIMULATION]" in sec:
                labels.append("DUMMY_SIMULATION")

            # Extract specific SOP codes like SOP-CBX-RET-01
            sop_codes = re.findall(r"\[(SOP-[A-Z0-9\-]+|MKT-[A-Z0-9\-]+)\]", sec)

            sections.append({
                "section_id": f"{source_key}_sec_{idx}",
                "title": title,
                "body": body,
                "labels": labels or ["VERIFIED_FACT"],
                "sop_codes": sop_codes
            })
        return sections

    def get_agent_knowledge(self, department: str) -> str:
        """
        Returns isolated knowledge context tailored exclusively to the requested department.
        - Marketing: shared_brand_knowledge_v1 + colorbox_marketing_knowledge_v1
        - Customer Service: shared_brand_knowledge_v1 + colorbox_cs_sop_v1
        """
        dept_norm = department.lower().strip()
        shared_text = self.registry.get("shared_brand_knowledge_v1", {}).get("raw_content", "")

        if dept_norm in ["marketing", "kreatif", "creative"]:
            mkt_text = self.registry.get("colorbox_marketing_knowledge_v1", {}).get("raw_content", "")
            return f"=== PANDUAN BERSAMA BRAND COLORBOX ===\n{shared_text}\n\n=== PANDUAN KHUSUS MARKETING & KREATIF ===\n{mkt_text}"
        
        elif dept_norm in ["customer_service", "cs", "customer_support", "support"]:
            cs_text = self.registry.get("colorbox_cs_sop_v1", {}).get("raw_content", "")
            return f"=== PANDUAN BERSAMA BRAND COLORBOX ===\n{shared_text}\n\n=== STANDAR OPERASIONAL PROSEDUR (SOP) CUSTOMER SERVICE ===\n{cs_text}"

        return shared_text

    def retrieve(self, query: str, department: str = "cs") -> Dict[str, Any]:
        """
        Performs simple, grounded keyword & token search against department-authorized sections.
        Returns truthful absent behavior if no grounded match is found.
        """
        query_lower = query.lower().strip()
        dept_norm = department.lower().strip()

        # Determine authorized files based on department
        if dept_norm in ["marketing", "creative"]:
            allowed_files = ["shared_brand_knowledge_v1", "colorbox_marketing_knowledge_v1"]
        else:
            allowed_files = ["shared_brand_knowledge_v1", "colorbox_cs_sop_v1"]

        # Tokens to match (filter out single letters/stop words, common verbs and brand names)
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
        for file_key in allowed_files:
            file_data = self.registry.get(file_key)
            if not file_data:
                continue

            is_department_specific = "sop" in file_key or "marketing" in file_key

            for sec in file_data["sections"]:
                text_to_search = (sec["title"] + " " + sec["body"]).lower()
                score = 0
                matched_tokens = []

                for token in tokens:
                    if re.search(r"\b" + re.escape(token) + r"\b", text_to_search):
                        score += 1
                        matched_tokens.append(token)

                # Prioritize department-specific SOP over general shared info (Conflict Resolution)
                if is_department_specific and score > 0:
                    score += 0.5

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

        # Sort by score descending
        scored_sections.sort(key=lambda x: x["score"], reverse=True)

        # TRUTHFUL ABSENT BEHAVIOR: If no grounded match with score >= 1
        if not scored_sections:
            return {
                "status": "KNOWLEDGE_ABSENT",
                "grounded": False,
                "query": query,
                "department": department,
                "message": "Informasi atau kebijakan spesifik terkait pertanyaan ini tidak ditemukan dalam SOP resmi Colorbox.",
                "fallback_action": "ESCALATE_TO_SUPERVISOR",
                "suggested_response": "Mohon maaf Kak, untuk pertanyaan atau permintaan khusus terkait hal ini, tim kami perlu melakukan konfirmasi langsung ke Customer Service Team Lead kami untuk memastikan informasi yang akurat. Kami telah membuatkan tiket tindak lanjut ya Kak.",
                "results": []
            }

        top_matches = scored_sections[:2]
        return {
            "status": "KNOWLEDGE_FOUND",
            "grounded": True,
            "query": query,
            "department": department,
            "match_count": len(top_matches),
            "primary_source": top_matches[0]["ref_code"],
            "results": top_matches
        }


# Global singleton instance
knowledge_engine = KnowledgeRetriever()
