# Frontend spec (stages 2-5)

App: `pegawai-ai-backend/frontend/` (React 19, Vite, TypeScript). The stage 1 chat is `src/Chat.tsx`, `src/hermes.ts` and `src/chat.css`. The backend contract is `docs/bff-spec.md` section 5: every call goes to `/bff/api/...`, and the Vite proxy adds the key. Decisions: `docs/keputusan-frontend.md`. All UI text is in Indonesian, short and plain. Company name: "AI Top Trends" (never "PT").

Use the `design-taste-frontend` skill (app-screen rules) and keep the existing visual language from stage 1: the accent ladder around raspberry `#b8336a`, DM Sans, and light and dark themes. Extend `chat.css`; do not restyle from scratch.

## Remove

- The "Tugas tim" tab and everything only it used: the old `src/api.ts` calls to `/api` on 8080, `src/mock/`, `reading.tsx` and the `mock` Vite mode, if nothing else imports them. Check with grep before deleting.
- `src/hermes.ts` direct Hermes calls. Replace it with `src/bff.ts`, a typed client for the BFF contract, including an SSE helper built on `EventSource` with reconnect (the browser does that natively; also handle `onerror` with a visible "Menyambung ulang…" state).

## App shell

The sidebar has these parts, top to bottom:

- **Grup**: the group list, each with a member avatar stack and a live dot when a discussion is running. "+ Grup baru" button.
- **Bot**: grouped by team, each with a status dot (idle, working, discussing) and the current activity on hover. "+ Bot baru" button.
- **Riwayat <bot>**: the session list, as in stage 1, when a bot is open.
- Footer:
  - A quota meter: plan name, tokens used out of the monthly limit, and bot and group counts. Clicking it opens the "Paket" dialog: plan cards, a demo switch, and a note "Pembayaran belum tersedia".
  - Links to "Aktivitas" and "Kantor". "Kantor" is a placeholder route for now, built in a later step, so render "Segera hadir".
- "Sedang dikerjakan": a small pill showing the number of active runs, which opens a popover listing them (bot, short input, elapsed time, Stop). Data comes from `/api/runs?status=active` plus the `/api/events` stream.

Routing: a hash router (`#/bot/<id>/<session?>`, `#/grup/<id>`, `#/aktivitas`, `#/kantor`), so refresh and back work. No new dependency is needed for this.

## Bot chat (rework of stage 1)

- Sending: `POST /api/bots/{id}/runs`, then open `/api/runs/{id}/stream`.
- Leaving the page or refreshing must not lose the run. On load, reattach to an active run for the open session from `/api/runs?status=active`.
- Keep the existing pieces: markdown answer, tool chips, the "Proses berpikir" block with the global toggle (reasoning now arrives in `done.reasoning` or from the session messages), and the quiet token display.
- Stop now calls `/api/runs/{id}/stop`; it is a real stop.
- While a run is active the composer stays usable:
  - Enter or "Kirim" queues the message. It shows as a pending bubble labelled "Antre" and is sent automatically after the run ends.
  - A secondary button "Arahkan sekarang" calls `/steer`. On a 409 it falls back to the queue.
- Approval: an `approval` event shows an inline card with the description and buttons "Izinkan sekali" and "Tolak", which call `/approval`.

## Group chat (new)

- Messenger feel: user bubbles on the right; bot bubbles on the left with avatar, name, role and team colour; system messages as centred small text.
- Live updates come from `/api/events` (`group_message`, `group_typing`, `group_send`). Show a typing row, "Rian sedang mengetik…", using the bot's colour.
- Composer: an `@` autocomplete of the members.
  - While a discussion runs, Enter queues (the pending chip shows "Antre, dikirim setelah ronde selesai"), and "Arahkan sekarang" sends `mode: "steer"`.
  - A Stop button calls `/api/groups/{id}/stop`.
- Header: the group name (editable inline), member avatars, and "Atur anggota" (the same dialog as creation).
- Paging: load the latest 50 messages, and older ones when scrolled to the top.

## Dialogs

- **Bot baru**: two tabs.
  - "Dari template": cards for the five personas.
  - "Buat sendiri": name, role, team (choose an existing one or type a new one), colour swatches, and a persona textarea with a 2000-character counter.
  - Show creation progress ("Menyiapkan bot… bisa sampai 40 detik"). On a 402, show the upgrade message with a button to the Paket dialog.
- **Grup baru**: a name, and a member picker grouped by team with 2-6 members and a counter. Picking bots from more than one team shows a small note "Grup lintas tim".
- **Delete a bot**: from the bot's context menu, with confirmation. It is hidden for builtin bots.

## Aktivitas page

- A table from `/api/activity`: time, bot, tool, status, duration, a summary (the redacted preview, expandable), and the chat or group link. Filters: bot and status. A "Muat lagi" button for paging.
- A note at the top: "Bot tidak memiliki akses terminal. Data sensitif disensor otomatis."

## Notifications

- When a run or group send finishes while `document.hidden`, show a browser Notification ("Rian selesai: <first 60 chars>"). Request permission once, on the first send, with a small inline prompt rather than on page load.
- Always show an in-app toast as well. Clicking either opens the chat.

## Quality bar

- `npm run build` passes, and TypeScript has no errors.
- No key or Hermes URL appears in `src/` (`grep -ri "8642\|HERMES_KEY\|API_SERVER_KEY" src` gives 0 hits).
- Mobile: the sidebar becomes a drawer, as in stage 1, and the dialogs are full screen under 640 px.
- Empty, loading and error states exist for every list.
