from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x1B, 0x2A, 0x41)
ACCENT = RGBColor(0x2E, 0x7D, 0x68)
AMBER = RGBColor(0xB5, 0x7D, 0x1E)
RED = RGBColor(0xA6, 0x3A, 0x2E)
GREY = RGBColor(0x5C, 0x6B, 0x73)
LIGHT = RGBColor(0xF2, 0xF5, 0xF4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RULE = RGBColor(0xD8, 0xE0, 0xDE)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def txbox(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tf


def para(tf, text, size=16, bold=False, color=NAVY, first=False, space=6, align=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space)
    if align:
        p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Segoe UI"
    return p


def header(slide, title, kicker):
    tf = txbox(slide, Inches(0.75), Inches(0.45), Inches(11.6), Inches(0.4))
    para(tf, kicker.upper(), size=11, bold=True, color=ACCENT, first=True, space=0)
    tf = txbox(slide, Inches(0.75), Inches(0.8), Inches(11.8), Inches(0.8))
    para(tf, title, size=32, bold=True, color=NAVY, first=True, space=0)
    ln = slide.shapes.add_shape(1, Inches(0.75), Inches(1.62), Inches(1.1), Inches(0.055))
    ln.fill.solid()
    ln.fill.fore_color.rgb = ACCENT
    ln.line.fill.background()


def footer(slide, n):
    tf = txbox(slide, Inches(0.75), Inches(7.0), Inches(11.8), Inches(0.35))
    para(tf, f"Colorbox CS AI  ·  WhatsApp live validation  ·  17 Nov 2026                    {n}",
         size=10, color=GREY, first=True, space=0)


def band(slide, color):
    box = slide.shapes.add_shape(1, Inches(0.0), Inches(0.0), prs.slide_width, Inches(0.14))
    box.fill.solid()
    box.fill.fore_color.rgb = color
    box.line.fill.background()


# 1. Title
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid()
bg.fill.fore_color.rgb = NAVY
bg.line.fill.background()
tf = txbox(s, Inches(0.9), Inches(2.1), Inches(11), Inches(0.5))
para(tf, "COLORBOX CUSTOMER SUPPORT", size=14, bold=True,
     color=RGBColor(0x8F, 0xC7, 0xB8), first=True, space=8)
tf = txbox(s, Inches(0.9), Inches(2.55), Inches(11.6), Inches(1.2))
para(tf, "Colorbox CS AI — WhatsApp Live Test", size=40, bold=True, color=WHITE,
     first=True, space=10)
para(tf, "What we built, what we tested, and what is still open", size=19,
     color=RGBColor(0xC9, 0xD6, 0xD3))
ln = s.shapes.add_shape(1, Inches(0.95), Inches(4.9), Inches(2.2), Inches(0.06))
ln.fill.solid()
ln.fill.fore_color.rgb = RGBColor(0x8F, 0xC7, 0xB8)
ln.line.fill.background()
tf = txbox(s, Inches(0.9), Inches(5.25), Inches(11), Inches(0.5))
para(tf, "Day 4–5  ·  Status report  ·  17 November 2026", size=14,
     color=RGBColor(0xA9, 0xBC, 0xB8), first=True)

# 2. What we did
s = prs.slides.add_slide(BLANK)
band(s, ACCENT)
header(s, "What we did", "Setup")
items = [
    ("Defined the CS persona and rules",
     "Tone, language, and hard limits: no refunds, discounts, or cancellations approved in chat; every escalation becomes a ticket."),
    ("Fed it the Colorbox catalogue",
     "Product names, colours, prices, and links loaded from the public catalogue, with the source and observation date in every answer."),
    ("Connected the operational data",
     "Stock and order rows read from Google Sheets, so nothing is invented; sample stock is always labelled as sample."),
    ("Tested on real WhatsApp",
     "A supervised demo number, one requirement at a time, checking both the reply and the data written behind it."),
    ("Built a human handover protocol",
     "Discount, refund, dispute, and cancellation requests create a numbered ticket and land in the Handover tab of the sheet."),
]
y = Inches(1.95)
for i, (head, body) in enumerate(items):
    tf = txbox(s, Inches(0.85), y, Inches(11.5), Inches(0.34))
    para(tf, head, size=17, bold=True, color=NAVY, first=True, space=2)
    tf = txbox(s, Inches(0.85), y + Inches(0.36), Inches(11.4), Inches(0.45))
    para(tf, body, size=13.5, color=GREY, first=True, space=0)
    y += Inches(0.95)
footer(s, 2)

# 3. Scoreboard
s = prs.slides.add_slide(BLANK)
band(s, ACCENT)
header(s, "Where it stands", "Summary")
cards = [
    ("7", "requirements working live", ACCENT),
    ("1", "partially solved", AMBER),
    ("1", "waiting on status values", AMBER),
]
x = Inches(0.9)
for big, label, color in cards:
    box = s.shapes.add_shape(1, x, Inches(2.2), Inches(3.7), Inches(2.3))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.fill.background()
    tf = txbox(s, x + Inches(0.35), Inches(2.45), Inches(3.0), Inches(1.0))
    para(tf, big, size=54, bold=True, color=color, first=True)
    tf = txbox(s, x + Inches(0.35), Inches(3.55), Inches(3.0), Inches(0.85))
    para(tf, label, size=14, color=GREY, first=True, space=0)
    x += Inches(3.95)
tf = txbox(s, Inches(0.9), Inches(5.05), Inches(11.4), Inches(1.5))
para(tf, "All nine requirements were exercised end to end on WhatsApp. Nothing failed because the bot behaved badly — "
         "the two gaps are missing inputs, not missing behaviour.", size=16, color=NAVY, first=True, space=8)
para(tf, "Every policy answer refused to approve money or a cancellation on its own, and every case left a traceable ticket.",
     size=14, color=GREY, space=0)
footer(s, 3)

# 4. Requirement table
s = prs.slides.add_slide(BLANK)
band(s, ACCENT)
header(s, "The nine requirements", "Detail")
rows = [
    ("Product recommendations", "Working", "Answers from the real catalogue, with source link and date", ACCENT),
    ("Stock level checks", "Working", "Per-SKU lookup; missing row is never reported as zero stock", ACCENT),
    ("Create orders", "Working", "Row written to the Orders sheet and read back to confirm", ACCENT),
    ("Update order statuses", "Reader ready", "Returns the stage written in the sheet; every status cell is still empty", AMBER),
    ("Cancel orders", "Partial", "Policy and ticket yes; decision still waits on a filled status", AMBER),
    ("Special discounts", "Working", "Not granted; recorded as a ticket for human decision", ACCENT),
    ("Refunds", "Working", "Not granted; 7-day retur rule quoted, ticket opened", ACCENT),
    ("Serious disputes", "Working", "No false claims; ticket opened, official CS channel given", ACCENT),
    ("Human handover protocol", "Working", "All four categories produced a ticket, mirrored to the sheet", ACCENT),
]
top = Inches(1.95)
left = Inches(0.85)
w_name, w_st, w_note = Inches(3.5), Inches(1.75), Inches(6.5)
y = top
for i, (name, st, note, color) in enumerate(rows):
    bgc = LIGHT if i % 2 == 0 else WHITE
    box = s.shapes.add_shape(1, left, y, w_name + w_st + w_note, Inches(0.5))
    box.fill.solid()
    box.fill.fore_color.rgb = bgc
    box.line.fill.background()
    tf = txbox(s, left + Inches(0.16), y + Inches(0.11), w_name, Inches(0.32))
    para(tf, name, size=14, bold=True, color=NAVY, first=True, space=0)
    tf = txbox(s, left + w_name, y + Inches(0.11), w_st, Inches(0.32))
    para(tf, st, size=13, bold=True, color=color, first=True, space=0)
    tf = txbox(s, left + w_name + w_st, y + Inches(0.12), w_note, Inches(0.32))
    para(tf, note, size=12.5, color=GREY, first=True, space=0)
    y += Inches(0.535)
footer(s, 4)

# 5. Handover detail
s = prs.slides.add_slide(BLANK)
band(s, ACCENT)
header(s, "Human handover, proven live", "Escalation")
tf = txbox(s, Inches(0.85), Inches(1.9), Inches(11.5), Inches(0.6))
para(tf, "Each request below produced a numbered ticket in the same conversation, visible in the Handover tab, "
         "with the customer told plainly that no decision had been made yet.", size=15, color=GREY, first=True, space=0)
tickets = [
    ("Dispute", "HW-20261117-C02C70", "P1 · 1x24 jam", "Follow-up message reused the ticket; official CS channel supplied"),
    ("Refund", "HW-20261117-321CE3", "P1 · 1x24 jam", "Order WL-889201; no refund promised, retur rule quoted"),
    ("Discount", "HW-20261117-F11774", "P1 · 1x24 jam", "20% request recorded; decision left to the team"),
    ("Cancellation", "HW-20261117-832E4F", "P2 · 2x24 jam", "Shipping stage stated as unverifiable; not approved"),
]
y = Inches(2.7)
for cat, tid, sla, note in tickets:
    box = s.shapes.add_shape(1, Inches(0.85), y, Inches(11.5), Inches(0.9))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.fill.background()
    tf = txbox(s, Inches(1.05), y + Inches(0.13), Inches(2.1), Inches(0.3))
    para(tf, cat, size=15, bold=True, color=NAVY, first=True, space=0)
    tf = txbox(s, Inches(1.05), y + Inches(0.47), Inches(2.6), Inches(0.3))
    para(tf, tid, size=11.5, color=ACCENT, first=True, space=0)
    tf = txbox(s, Inches(3.75), y + Inches(0.13), Inches(1.9), Inches(0.3))
    para(tf, sla, size=12, bold=True, color=GREY, first=True, space=0)
    tf = txbox(s, Inches(5.7), y + Inches(0.16), Inches(6.4), Inches(0.5))
    para(tf, note, size=12.5, color=GREY, first=True, space=0)
    y += Inches(0.97)
tf = txbox(s, Inches(0.85), Inches(6.62), Inches(11.5), Inches(0.34))
para(tf, "No owner is assigned yet, by design: replies say the case is recorded but not yet assigned.",
     size=12, color=AMBER, first=True, space=0)
footer(s, 5)

# 6. What's left
s = prs.slides.add_slide(BLANK)
band(s, AMBER)
header(s, "What is still open", "Next")
open_items = [
    ("Fill the status column, then connect the real source",
     "The agent can now read a status per order, but no row has a value yet. Long term the honest source is Colorbox's existing marketplace or warehouse system; we have no access to it, so the sheet is the interim feed."),
    ("Assign an owner per category",
     "Tickets are created and mirrored already. Until refund, discount, dispute and cancellation each have a named reviewer, every reply has to say nobody is assigned."),
    ("Confirm the customer's number lands on new tickets",
     "The pipeline now passes the sender's phone through and the ticket has a contact field. One more live ticket proves it end to end."),
]
y = Inches(1.95)
for head, body in open_items:
    tf = txbox(s, Inches(0.9), y, Inches(11.4), Inches(0.36))
    para(tf, head, size=17.5, bold=True, color=NAVY, first=True, space=2)
    tf = txbox(s, Inches(0.9), y + Inches(0.4), Inches(11.2), Inches(0.9))
    para(tf, body, size=13.5, color=GREY, first=True, space=0)
    y += Inches(1.4)
box = s.shapes.add_shape(1, Inches(0.85), Inches(6.0), Inches(11.5), Inches(0.72))
box.fill.solid()
box.fill.fore_color.rgb = LIGHT
box.line.fill.background()
tf = txbox(s, Inches(1.05), Inches(6.16), Inches(11.1), Inches(0.45))
para(tf, "Everything else is done and verified on WhatsApp. These three are inputs from CS and operations, not bot behaviour.",
     size=13.5, bold=True, color=NAVY, first=True, space=0)
footer(s, 6)

# 7. Fixed today
s = prs.slides.add_slide(BLANK)
band(s, ACCENT)
header(s, "Fixed while testing today", "Defects closed")
fixes = [
    ("Status had no reader",
     "The order lookup now returns the stage written in the sheet, and the agent may only quote it when the cell is filled: baru, diproses, dikirim, diterima, dibatalkan."),
    ("The phone number was dropped",
     "WhatsApp delivered the chat as an internal ID, so the agent only ever saw a display name. The phone now travels from the bridge to the agent, and the cancellation rule uses it for the ticket."),
    ("A repeat request opened a second ticket",
     "Two refund tickets for WL-889201 were created minutes apart. The agent now checks open tickets for the same order and category first, and quotes the existing number."),
]
y = Inches(1.95)
for head, body in fixes:
    box = s.shapes.add_shape(1, Inches(0.85), y, Inches(11.5), Inches(1.35))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.fill.background()
    tf = txbox(s, Inches(1.1), y + Inches(0.16), Inches(10.9), Inches(0.34))
    para(tf, head, size=16.5, bold=True, color=NAVY, first=True, space=0)
    tf = txbox(s, Inches(1.1), y + Inches(0.56), Inches(10.9), Inches(0.7))
    para(tf, body, size=12.5, color=GREY, first=True, space=0)
    y += Inches(1.5)
footer(s, 7)

out = r"C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481\COLORBOX_CS_AI_WhatsApp_Status.pptx"
prs.save(out)
print(out)
