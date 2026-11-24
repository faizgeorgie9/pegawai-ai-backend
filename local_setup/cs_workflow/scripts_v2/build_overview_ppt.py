from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def title_slide(title, subtitle):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    sl.shapes.title.text = title
    sl.placeholders[1].text = subtitle

def bullet_slide(title, bullets):
    sl = prs.slides.add_slide(prs.slide_layouts[1])
    sl.shapes.title.text = title
    tf = sl.placeholders[1].text_frame
    tf.text = bullets[0]
    for b in bullets[1:]:
        p = tf.add_paragraph()
        p.text = b
        p.level = 0

title_slide("Pegawai AI - Role Templates (Sprint 5)", "What we built, the standard we followed, and each role's specialty\nMansi Bhavsar - v1.2")

bullet_slide("What we did", [
    "Turned 8 Pegawai AI roles into one review-ready template format (v1.2).",
    "Each role now has the same 11 sections, so reviewers can compare apples to apples.",
    "Grounded every claim in source dossiers or labelled as Proposal / Blocker / input required.",
    "No invented owners, dates, budgets, or verified results.",
    "Verified: 1,397 checks, 0 failures.",
])

bullet_slide("The standard we followed (11 components)", [
    "1. Scope of Work & Boundaries  (in / out / cross-dept)",
    "2. Persona, Language & Tone of Voice",
    "3. Triggers & Use Cases",
    "4. Modular Skills & Capabilities",
    "5. SOP & Task Execution Pattern (8 steps)",
    "6. Operating Rules & Prohibitions",
    "7. Tools, Integrations & Permissions",
    "8. Knowledge Base & Memory Needs (5 layers)",
    "9. Input & Expected Output Standards",
    "10. Approval & Escalation Rules (L1/L2/L3)",
    "11. Model Recommendation & KPIs",
])

bullet_slide("Roles after PM revision (6 total)", [
    "CS-01  Omnichannel Customer Service",
    "MKT-01 Marketing Strategist  (absorbs MKT-07 Marketing Performance Analyst)",
    "MKT-02 SEO Specialist",
    "MKT-03 Digital Ads Specialist",
    "MKT-04 Email Marketing Specialist",
    "MKT-05 Sales Development Specialist  (merges Lead Gen + Sales Assistant)",
])

bullet_slide("Specialty per role", [
    "CS-01: WhatsApp ticketing, order status/refund/cancel rules, human handover line.",
    "MKT-01: niche pain research, offer + value equation, 25-ad matrix, Andromeda plan.",
    "MKT-02: SEO keywords, on-page, content briefs, technical checks.",
    "MKT-03: Meta ads setup, creatives, paused-only activation, clone gate.",
    "MKT-04: email campaigns, drafts only, no send without approval.",
    "MKT-05: lead gen + sales assist, draft-only publishing.",
])

bullet_slide("Approval & safety gates", [
    "Level 1 (autonomous): research, drafts, internal analysis.",
    "Level 2 (approval): final docs, task creation, asset handoff.",
    "Level 3 (human only): publish, spend, legal/financial claims, PII.",
    "No bot self-approves; every write/send/publish stays gated.",
])

bullet_slide("What's still open", [
    "Deep-merge review of the two merged roles (MKT-01, MKT-05).",
    "Reviewer sign-off (Marketing, Ops, CS, BE/FE, PM) - still unassigned.",
    "ClickUp shared doc update (read-only here).",
    "Temporary WhatsApp API provider confirmation.",
    "Orders sheet status values need manual fill before retest.",
])

bullet_slide("Next steps", [
    "Reviewer pass on merged role files.",
    "Stage v1.2 folder + zip for upload to Google Drive.",
    "Run final verification (verify_v1_2).",
    "Share CS knowledge package (sanitized) with testers.",
])

prs.save("SPRINT5_ROLE_TEMPLATES_OVERVIEW.pptx")
print("saved")
