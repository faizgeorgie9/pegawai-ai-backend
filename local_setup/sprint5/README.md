# Sprint 5 final deliverables

This folder is the current, organised entry point for Sprint 5 role-template work.

## Current status

- `role_templates_final/` is authoritative: 6 DOCX files + 6 Markdown sources after the PM role merge on 2026-11-24.
- Final roles: CS-01, MKT-01, MKT-02, MKT-03, MKT-04, MKT-05 (Sales Development Specialist).
- `notes/PM_ROLE_MERGE_NOTE.md` records the merge and supersedes older role-count wording.
- `review_packet_v1_2/` is retained for audit. It predates the PM merge and still describes the earlier 8-role review scope.
- Raw Karyawan.AI `.mhtml` files are intentionally not committed because of their size. The 13 `.txt` extracts and `extract_mhtml.py` are committed under `sources/karyawan_dossiers/`.

## Folder map

- `role_templates_final/` — final upload-ready templates.
- `review_packet_v1_2/` — v1.2 review packet, BE/FE handover, source register, shared-doc links.
- `sources/master_catalog/` — supplied catalog DOCX, extracted catalog text, depth standard, 11-component checklist.
- `sources/karyawan_dossiers/` — 13 plain-text source extracts and the extractor script.
- `scripts/` — build, catalog/depth application, deep-merge, and verification scripts.
- `notes/` — PM decision note.

Related folders elsewhere in `local_setup/`:

- `cs_workflow/` — CS validation and backlog evidence.
- `backend_template/context/sops/` — runtime SOPs.
- `sprint5_review_handover/` — historical v1/v1.1/v1.2 review material.
- `sprint5_mkt_templates/` — earlier v1 MKT template upload set (historical).

## Verification

From the repo root:

```powershell
cd bff
uv run pytest
cd ..\frontend
npm run build
```

The final DOCX set was also checked with `scripts/verify_v1_2.py` against the 11-component depth standard.
