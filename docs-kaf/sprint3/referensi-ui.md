# Phase A: UI reference and inspiration notes (7 November 2026)

Method: each site's text was read with WebFetch, and Malika and pegawAI were also looked at as screenshots in the built-in browser. I did not log in or test any app. Feature claims are marketing copy and have not been verified. The Phase A reference video on YouTube has not been reviewed yet, because Claude cannot watch videos; Kevin reviews it himself.

| Platform | URL | Note |
|---|---|---|
| Malika Agent | https://malika.ai/ (demo at `#demo`) | The main visual reference |
| pegawAI | https://pegawai.biz.id/ (app at `#app`) | The second visual reference |
| Solvion | https://solvion.id/ | Landing page only, no app UI |
| Officeverse | https://officeverse.id/ | Not released yet; virtual office |

## Malika: interactive demo, labelled "bukan AI beneran, cuma simulasi"

- **Layout:** three columns.
  - **Left:** search and an agent list. Each agent has an avatar, name, role, and a "running" badge.
  - **Centre:** chat with the active agent's identity ("Kazhim · Project Manager") in the header, and timestamped bubbles.
  - **Right:** a "running" panel showing the agent's screen, KPI cards, a chart, and a step-by-step activity log ("CRM · Menarik data…").
- **Look:** light and airy, white with a mint-to-blue gradient as the accent, rounded cards, soft shadows, and 3D robot mascots on the landing page.
- **Patterns:**
  - Suggestion chips above the input.
  - Answers rendered as report cards (tables, analysis, recommendations, action buttons).
  - A routines (scheduler) panel ordered by time.
  - The demo is labelled honestly as a simulation. That fits our rule: "mock harus berlabel".

## pegawAI: "One app, all your employees"

- **Views:** Wall (all employees and channels), Chat, Call, and Phone pairing.
- **Channels:** sidebar channels such as `#toko-online`, `#gudang` and `#pribadi`.
- **Look:**
  - Dark, warm palette with large serif italic display type ("all your employees").
  - A coral avatar with a mascot face.
  - Pill tabs.
- **Patterns:**
  - Employee cards with a role and a clear text status: "sedang bekerja", "menunggu izin Anda", "sedang berpikir", "selesai".
  - An approval card inside the chat with "Izinkan" / "Tolak" buttons.
  - Routine cards with a time ("Sen 08.00").
  - Example roles: Nara (CS), Kiara (content and promo).

## Solvion and Officeverse

- **Solvion:** one named persona per job (Sari.AI for CS, Joko.AI for sales), with an avatar and an "Online 24/7" status. There is no dashboard; reporting happens in chat. Nothing to copy for app structure.
- **Officeverse:** a virtual office with a floor plan and desks shared by AI and humans. It matches the "Kantor" idea that was **deferred** (stage 6). Not a Sprint 3 priority.

## Decisions for Pegawai AI

1. **Keep three columns:** sidebar, chat, and a side panel. Our app already has this shape (the Berpikir/Token/Aktivitas/Info panel), so we refine it rather than rebuild it.
2. **Status is text, not only a dot:** "Sedang berpikir", "Sedang bekerja: web_search", "Menunggu izin", "Siap". Shown in the agent list and on the agent card.
3. **Structured results as cards in the chat:** Marketing's brief, ideas, calendar, drafts, review and revision, and CS's classification, sources, draft, summary and escalation. Each is a card component inside the message, so chat stays primary and the structure is kept, as ClickUp requires.
4. **An honest mock label:** a "Contoh data" / "Simulasi" badge, as in the Malika demo, on every fixture.
5. **Approval card inside the chat** for Tools or Computer Use, if the backend opens them.
6. **Scheduler as a time-ordered list** of routine cards.
7. **Visual direction:** stay light like Malika, keep the raspberry `#b8336a` and DM Sans identity we already have, and borrow pegawAI's status labels and avatar character. Do not copy any mascot, logo or palette one to one.
8. **Avoid:** pricing tiers and quotas (out of PRD scope) and the virtual office (deferred).
