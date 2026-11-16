# Spec: simplify the Pegawai AI UI/UX (7 November 2026)

**Goal:** a first-time user (the owner, the Marketing/CS teams, a reviewer) understands what to do within 10 seconds of opening the app. Fewer menus, plain names, one clear path. Every ClickUp requirement must still be met: the Computer Use and Scheduler pages still exist and keep their honest status.

## 1. Sidebar: from 11 flat menus to 3 groups

| Group | Menu (new name) | Old route |
|---|---|---|
| **Kerja** | Beranda | Dashboard `#/` |
| | Chat | `#/chat` (the agent list stays here, with a team header) |
| | Grup | `#/grup` |
| | Marketing | Workspace Marketing `#/marketing` |
| | Customer Service | Workspace CS `#/cs` |
| **Uji** | Uji & nilai | Skenario uji & evaluasi `#/uji` |
| | Log aktivitas | Aktivitas `#/aktivitas` |
| **Pengaturan** | Agen | `#/agen` |
| | Kemampuan | **one page with 3 tabs**: Tools, Computer Use, Scheduler. Routes `#/tools`, `#/computer-use` and `#/scheduler` still work and open the matching tab |

- The **Pengaturan** group can be collapsed, and its state is remembered.
- **Agent rows** in the sidebar show the avatar, the name, and a status line only. Hovering shows the role. Rows are shorter.
- **"Diblokir" becomes "Nonaktif"** everywhere. Explain it in one short sentence: "Dimatikan sementara demi keamanan prototipe. Backend yang memutuskan kapan dibuka."
- **Icons:** each menu gets a consistent line icon from a single set, inline SVG at one stroke width. No emoji.

## 2. Make the purpose of each page clear

- **Beranda:** at the top, a dismissible "Mulai dari sini" card with 3 steps:
  1. Ngobrol dengan agen (Chat)
  2. Jalankan alur kerja (Marketing / Customer Service)
  3. Uji dan nilai hasil (Uji & nilai)

  Each step has one button. Remember the dismissal in localStorage, inside try/catch.
- **Each page header:** a title plus one subtitle sentence:
  - Chat: "Tanya bebas ke satu agen."
  - Marketing: "Alur langkah demi langkah: brief → rencana → konten → review → revisi."
  - Customer Service: "Simulasikan pertanyaan pelanggan dan lihat draf jawaban terstruktur."
  - Uji & nilai: "Jalankan kasus uji dan beri nilai 1–5."
  - Kemampuan: "Apa yang bisa dan belum bisa dipakai agen."
- **Chat vs workflow:**
  - In the chat empty state for Marketing agents, add the link "Butuh alur brief → konten? Buka Marketing". Do the same for CS agents, linking to Customer Service.
  - In the workspace header, add "Untuk tanya bebas, pakai Chat".
- **Data labels:** keep the "Contoh data", "Simulasi" and data-classification labels. Add one small legend, shown once per workspace page, that explains them.

## 3. Small fixes

- **Indonesian validation messages:**
  - Every form uses `noValidate` and its own messages. No English browser bubbles.
  - Required fields are marked "wajib" and the error appears under the field.
- **Deleting an agent is slow (~10 s):** the BFF responds right away after marking the bot deleted (soft delete), and runs the profile deletion in the background. The UI shows the bot removed immediately.
  - If the background deletion fails, log it and show it on the bot's status (or in the activity log).
  - Keep the existing safety checks.
- **Tables at 375 px:** wide tables become stacked cards instead of scrolling sideways, where that is simple to do.

## 4. Visual polish with taste-skill 2.5.0

The skill is installed in `C:\Users\kevin\.agents\skills\design-taste-frontend` and is now aimed at marketing websites. **Use only the parts that fit an app screen:**

| Reference | Apply to |
|---|---|
| `references/system.md` | One set of tokens: spacing scale, radius, type scale, colour roles |
| `references/icons.md` | One icon set, sizes and stroke |
| `references/copy.md` | Plain, short copy |
| `references/motion.md` | Quiet micro-interactions: hover, focus, panel and drawer transitions under 200 ms, `prefers-reduced-motion` |
| `references/cards.md` | Consistent cards for agents, results and stats |

**Do not use** shaders, scenes, moments, background effects, or marketing photography. They do not fit an R&D testing dashboard, and the PRD forbids unnecessary complexity.

- Keep the raspberry `#b8336a` identity, DM Sans, and light and dark themes.
- Fix inconsistent spacing and sizes between the older pages (Chat, Group, Panel) and the new ones (Dashboard, Agen, Workspace, Uji), so they read as one system.
- Contrast must be AA in both themes.

## Acceptance

- `npm run build` and `uv run pytest` pass. `grep -ri "8642\|HERMES_KEY\|API_SERVER_KEY" frontend/src` gives 0 hits.
- In the browser, at desktop width and at 375 px, in light and dark:
  - all routes render;
  - the old routes still work;
  - the sidebar groups and the collapse work;
  - Kemampuan has 3 tabs;
  - "Mulai dari sini" works;
  - Indonesian validation appears;
  - deleting a test agent is fast;
  - no console errors.
- Before and after screenshots: `frontend/screenshots/s3-simple-*.png`.
