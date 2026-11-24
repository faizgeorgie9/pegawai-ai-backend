# PM role merge note — 2026-11-24

The PM revision reduces the Sprint 5 role set from 8 templates to 6 final templates.

## Final role set

1. CS-01 Omnichannel Customer Service
2. MKT-01 Marketing Strategist — absorbs the former MKT-07 Marketing Performance Analyst scope.
3. MKT-02 SEO Specialist
4. MKT-03 Digital Ads Specialist
5. MKT-04 Email Marketing Specialist
6. MKT-05 Sales Development Specialist — merges the former MKT-05 Lead Generation Specialist and MKT-06 Sales Assistant scopes.

## Retired roles

- MKT-06 Sales Assistant — merged into final MKT-05.
- MKT-07 Marketing Performance Analyst — merged into final MKT-01.

The retired role DOCX files are not present in `role_templates_final/`.

## Exact handover line

The CS handover line is preserved verbatim wherever it applies:

`Petugas customer service akan segera menghubungi Anda. Mohon tetap di chat ini, ya.`

## Relationship to v1.2 review packet

`review_packet_v1_2/` was produced before this PM merge. Statements such as "All 8 roles" or "CS-01 + MKT-01–MKT-07" in that packet are historical review scope and are superseded by this note and by `role_templates_final/`.

The final 6 DOCX files were verified with `scripts/verify_v1_2.py`: 1,397 checks, 0 failures. The two merged MKT files were additionally checked with limited deep-merge verification: 12 numbered section headings in Markdown, and `PM revision 2026-11-24` present in each DOCX.
