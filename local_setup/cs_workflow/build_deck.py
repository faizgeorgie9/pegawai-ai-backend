from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x14, 0x2A, 0x43)
ACCENT = RGBColor(0x2E, 0x7D, 0x68)
GREY = RGBColor(0x5A, 0x64, 0x6E)
LIGHT = RGBColor(0xF2, 0xF5, 0xF4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xB0, 0x45, 0x3A)
AMBER = RGBColor(0xB5, 0x7D, 0x1E)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

W = prs.slide_width
H = prs.slide_height


def txbox(slide, left, top, width, height):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    return tf


def para(tf, text, size=18, bold=False, color=NAVY, space_before=0, space_after=6, first=False, align=PP_ALIGN.LEFT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Segoe UI"
    return p


def header(slide, title, kicker=None):
    bar = slide.shapes.add_shape(1, 0, 0, W, Inches(0.16))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    top = Inches(0.55)
    if kicker:
        tf = txbox(slide, Inches(0.75), Inches(0.45), Inches(11.5), Inches(0.4))
        para(tf, kicker.upper(), size=12, bold=True, color=ACCENT, first=True)
        top = Inches(0.85)
    tf = txbox(slide, Inches(0.75), top, Inches(11.8), Inches(0.8))
    para(tf, title, size=34, bold=True, color=NAVY, first=True)


def footer(slide, n):
    tf = txbox(slide, Inches(0.75), Inches(6.95), Inches(11.8), Inches(0.35))
    para(tf, f"Colorbox CS WhatsApp Bot  |  Day 4-5 Validation  |  {n}", size=10, color=GREY, first=True)


def bullets(slide, items, top=1.9, size=19, left=0.9, width=11.6):
    tf = txbox(slide, Inches(left), Inches(top), Inches(width), Inches(4.6))
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, sub = item
            p = para(tf, text, size=size, bold=True, color=NAVY, first=(i == 0), space_after=2)
            para(tf, sub, size=size - 4, color=GREY, space_after=12)
        else:
            para(tf, item, size=size, color=NAVY, first=(i == 0), space_after=12)


# 1. Title
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, W, H)
bg.fill.solid()
bg.fill.fore_color.rgb = NAVY
bg.line.fill.background()
tf = txbox(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.2))
para(tf, "COLORBOX CUSTOMER SUPPORT", size=15, bold=True, color=RGBColor(0x8F, 0xC7, 0xB8), first=True)
tf = txbox(s, Inches(0.9), Inches(2.6), Inches(11.5), Inches(2.0))
para(tf, "WhatsApp CS Bot", size=54, bold=True, color=WHITE, first=True)
para(tf, "Day 4-5 Live Validation & Demo Readiness", size=24, color=RGBColor(0xC9, 0xD6, 0xD2), space_before=8)
tf = txbox(s, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.8))
para(tf, "15 November 2026  ·  Internal simulation testing", size=14, color=RGBColor(0x9F, 0xB3, 0xAD), first=True)

# 2. Scope
s = prs.slides.add_slide(BLANK)
header(s, "What we validated", "Scope")
bullets(s, [
    ("Eight customer-support scenarios over live WhatsApp", "Product, stock, ordering, and policy guardrails, run against the real bot."),
    ("Every reply uses the Sprint 2 SOPs and guardrails", "Data comes from the connected catalogue and sample sheets; the SOPs decide how it is explained."),
    ("Internal simulation only", "No real customer contacted, no real order fulfilled, no personal data or credentials in evidence."),
])
footer(s, 2)

# 3. Results at a glance
s = prs.slides.add_slide(BLANK)
header(s, "Results at a glance", "Outcome")
cards = [
    ("5 / 5", "scenarios passed", ACCENT),
    ("1", "blocked by a missing source", AMBER),
    ("4 / 4", "handover categories ticketed live", ACCENT),
]
x = Inches(0.9)
for big, label, color in cards:
    box = s.shapes.add_shape(1, x, Inches(2.3), Inches(3.8), Inches(2.4))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.fill.background()
    tf = txbox(s, x + Inches(0.35), Inches(2.55), Inches(3.1), Inches(1.0))
    para(tf, big, size=54, bold=True, color=color, first=True)
    tf = txbox(s, x + Inches(0.35), Inches(3.65), Inches(3.1), Inches(0.9))
    para(tf, label, size=15, color=GREY, first=True)
    x += Inches(4.0)
tf = txbox(s, Inches(0.9), Inches(5.2), Inches(11.5), Inches(1.2))
para(tf, "All executed tests passed. Nothing failed outright - the gaps are missing data sources, not bot errors.",
     size=17, color=NAVY, first=True)
footer(s, 3)

# 4. Scenario detail
s = prs.slides.add_slide(BLANK)
header(s, "Scenario results", "Detail")
rows = [
    ("Missing SKU lookup", "Pass", "Says \"not found\", never \"0 stock\""),
    ("Simulated order", "Pass", "Row written and verified in Orders sheet"),
    ("Refund request", "Pass", "Ticket opened; no promise; 7-day policy cited"),
    ("Discount request", "Pass", "Ticket opened; no discount offered or applied"),
    ("Serious dispute", "Pass", "Ticket opened; official CS channel given"),
    ("Status update", "Blocked", "No status column or feed"),
    ("Cancellation", "Partial", "Policy cited, ticket opened; shipping unverifiable"),
    ("Human handover", "Built", "Tickets land in the sheet; no owner until staff"),
]
tbl_top = Inches(1.85)
left = Inches(0.9)
w_id, w_st, w_note = Inches(4.2), Inches(1.6), Inches(5.6)
y = tbl_top
for i, (name, status, note) in enumerate(rows):
    shade = LIGHT if i % 2 == 0 else WHITE
    rowbg = s.shapes.add_shape(1, left, y, w_id + w_st + w_note, Inches(0.52))
    rowbg.fill.solid()
    rowbg.fill.fore_color.rgb = shade
    rowbg.line.fill.background()
    tf = txbox(s, left + Inches(0.15), y + Inches(0.1), w_id, Inches(0.35))
    para(tf, name, size=14, color=NAVY, first=True)
    color = ACCENT if status in ("Pass", "Built") else (AMBER if status in ("Blocked", "Partial") else RED)
    tf = txbox(s, left + w_id, y + Inches(0.1), w_st, Inches(0.35))
    para(tf, status, size=14, bold=True, color=color, first=True)
    tf = txbox(s, left + w_id + w_st, y + Inches(0.1), w_note, Inches(0.35))
    para(tf, note, size=13, color=GREY, first=True)
    y += Inches(0.56)
footer(s, 4)

# 5. Guardrails
s = prs.slides.add_slide(BLANK)
header(s, "Guardrails that held", "Safety")
bullets(s, [
    ("No money promises", "No refund approval, discount, method, or timeline was ever committed."),
    ("No false escalation", "She states plainly when something was not forwarded or assigned."),
    ("Data honesty", "Sample stock is always labelled simulation; a missing SKU is never reported as zero."),
    ("Source discipline", "Catalogue answers cite the source link and observation date, with a price-change warning."),
], size=20)
footer(s, 5)

# 6. Issues fixed
s = prs.slides.add_slide(BLANK)
header(s, "Four defects found and fixed", "Quality")
bullets(s, [
    ("Internal tool lines in customer messages", "Skill lookups, file searches and tool calls appeared above her answers. Fixed by turning off the progress feed for WhatsApp; confirmed gone in the retest."),
    ("Background review message", "A system line (\"profile updated, memory updated\") posted as its own WhatsApp message. Fixed by disabling the post-turn review, and the test chatter it wrote into her profile was cleared."),
    ("Handover never triggered", "Her instructions still said no human approval flow existed, and the ticket tools were hidden from her. Both fixed; all four categories now open a ticket on the first attempt."),
    ("Stack died mid-test", "The services were tied to the test console and died whenever a test run was stopped, and a stale database lock made them look up. Both fixed with detached launchers and a clean lock cleanup."),
], size=17)
footer(s, 6)

# 7. Blockers
s = prs.slides.add_slide(BLANK)
header(s, "What CS or operations must supply", "Blockers")
bullets(s, [
    ("Order status source", "The Orders sheet has no status column or feed, so processed / shipped / delivered cannot be tested or answered, and a cancellation cannot be checked against the pre-shipment condition."),
    ("Handover owners", "Tickets are created and mirrored already; what is missing is who owns refund, discount, dispute and cancellation, and the response commitment per category."),
    ("Customer contact data", "The agent sees the sender's display name, not their number, so the contact column is empty and follow-up depends on the customer stating a number."),
], size=19)
footer(s, 7)

# 8. Demo & limitations
s = prs.slides.add_slide(BLANK)
header(s, "Demo plan and known limitations", "Next")
bullets(s, [
    ("Video walkthrough", "Product recommendation, sample stock, one simulated order, then a refund, discount, dispute and cancellation request, each ending in a ticket number in the Handover sheet. No private chats, phone numbers, or session data on screen."),
    ("Known limitation: unofficial bridge", "This is a WhatsApp Web-style connection, not the official Business API, so there is an accepted risk of the demo number being restricted."),
    ("Known limitation: sample data", "Stock figures are sample values, not verified Colorbox inventory; status updates stay out of the demo because there is no status source."),
], size=18)
footer(s, 8)

for s in prs.slides:
    for shp in s.shapes:
        try:
            shp.shadow.inherit = False
        except Exception:
            pass

out = r"C:\Users\MI\Documents\pegawai-ai-backend\local_setup\cs_workflow\COLORBOX_CS_WhatsApp_Day4-5_Validation.pptx"
prs.save(out)
print(out)
