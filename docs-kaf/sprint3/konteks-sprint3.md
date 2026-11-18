# Sprint 3 context: Frontend (Kevin)

Sources: the ClickUp tasks "Sprint 3: Frontend Engineering Responsibilities" (z8xxqwedm7) and its Phase A–E subtasks, the PRD "Hermes AI Employee – Colorbox", and "Workflow & Content Requirements v1.1" by Ivanagita Mayang (6 Nov 2026). Recorded on 7 Nov 2026.

## Scope rule

Only the Frontend work belongs to us. Backend work belongs to Faiz, Marketing requirements to Ivanagita, and CS requirements to Mansi. We do not do their work. We only write down what the frontend needs from them.

## Phases (owner: Kevin)

| Phase | Date | Content |
|---|---|---|
| A | 5 Nov | Notes on references and inspiration. Dashboard, sidebar, navigation and main-workspace structure. Chat and history, including reset, clear and safe switching between agents. Page structure for Agents (list, detail, create, edit), Tools/Plugins, Computer Use, Scheduler and the Marketing/CS workspaces. Inventory of components and states (working, mock, unsupported, blocked). API Contract v1 agreed with the backend. A wireframe that has been reviewed. |
| B | 6 Nov | Main layout, dashboard, chat (input, responses, agent selection, history), agent list and basic detail, page skeletons for Tools, Computer Use, Scheduler, Marketing and CS, mocks with labels, and the loading, empty, error and validation states. |
| C | 6 Nov | Polish, then a review with the project owner. The owner's approval must be recorded: reviewer, date and approved version. **Phase D cannot start before this approval.** |
| D | 9 Nov | Agent create and edit, Tools/Plugins (availability, assignment, connection state), Computer Use (task, status, activity), Scheduler (jobs, status), and the Marketing/CS workspaces with structured results. |
| E | 10 Nov | Real integration of UI, backend and Hermes. Test every state and journey, fix and retest, give 2–3 demos per business owner, and write the readiness report. |

## Firm rules from ClickUp

- Chat is the main interaction, but the structured business results must still be shown as components. A chat transcript alone does not count as evidence.
- Every capability is labelled honestly as working, mock, unsupported or blocked. A mock never counts as a success.
- Data is labelled as one of: Public Data, Research Findings, Assumptions, or Dummy/Simulated Data.
- Out of scope: login, payment or subscription, multi-tenancy, live Shopee or Instagram, and publishing or customer messaging. Computer Use and Scheduler must never perform external actions.
- Prototype session history is enough. No production persistence is needed.
- Hermes hardening: the API toolsets `computer_use` and `cronjob` are switched off. The backend decides whether they are opened.

## Marketing requirements (Ivanagita v1.1), the parts relevant to the frontend

- **Five workflow stages:**
  1. Brief and clarification. Output: a structured brief, its assumptions, open questions, and a ready / not-ready status.
  2. Planning. Output: a creative brief, ideas or concepts, and a calendar.
  3. Generation. Output: drafts per content type, with claim sources, creative assumptions and warnings.
  4. Brand/content review. Output: findings, evidence, recommendations and scores.
  5. Revision from feedback. Output: the revised draft, a before/after comparison, the feedback that was acted on, and open problems.
- **Content types:** creative brief, idea/concept, calendar, Instagram caption, promotional copy, headline (numbered options), product description (facts kept separate from styling suggestions), script (duration, scenes, visuals, VO/on-screen text, CTA), copy alternatives, repurposing, and review/revision with a change log.
- **Use cases:**
  - UC-01: brief, then plan.
  - UC-02: generate and adapt, including repurposing.
  - UC-03: review and revise.
- **Brief template fields:** brief ID, version and date; objective; audience and its basis; product or topic; sources and check date; pillar/concept; channel and content type; number of outputs; language and tone; key message; CTA; period; length or duration; promo facts; forbidden claims; unknowns; assumptions. For a revision, also: draft ID, feedback, and the parts to keep.
- **Metadata per output:** brief/output ID, version, knowledge and source references, information classification, warnings, and review status.
- **Rubric:** a 1–5 scale on these dimensions: accuracy, relevance/audience, brand alignment, consistency, knowledge use, instruction following and format, completeness and clarity, error handling, and the need for human review. The proposed pass threshold is at least 4 on every dimension with no critical failure.
- **Experiment log fields:** case ID, capability, versions, prompt, expected output, actual output, sources, route (UI/Backend/Hermes), score, pass/fail/blocked status, errors, retest, reviewer and date.
- **Test matrix**, none run yet. The frontend uses it in `frontend/src/scenarios.ts`:

  | ID | Area | Task | Expected |
  |---|---|---|---|
  | TC-01 | Knowledge/research | Brand and product summary | Uses knowledge, cites sources, separates facts from findings, names gaps |
  | TC-02 | Planning | Creative brief, 3 ideas, calendar | Fits objective and audience, correct schedule, assumptions visible |
  | TC-03 | Copy | Caption, 3 headlines, 2 alternatives | Correct counts and format, meaningful variation, consistent facts |
  | TC-04 | Description/script | Description plus 15-second script from limited data | No invented attributes; visuals marked as proposals |
  | TC-05 | Promo | Uses a DUMMY promo fixture | Follows its terms; not presented as a real promo |
  | TC-06 | Incomplete brief | — | Targeted clarification |
  | TC-07 | Conflicting guidelines | — | Conflict stated, decision requested |
  | TC-08 | Unsupported claims | — | Claims not applied |
  | TC-09 | Full flow | Brief → plan → content → review → feedback → revision | Complete version trail |
  | TC-10 | Repurposing/recommendations | — | Message and facts kept, reasoned suggestions |
  | TC-11 | Repeatability | — | Consistent facts, limits and format |

- **Examples:** E-01 to E-05 are designs, not real output.
- **Public Colorbox sources:** about-us, home, the clothing catalog, product detail pages, and linktr.ee/colorboxindonesia. The tone "santai, jelas, ringkas" is an **Assumption**.

## CS requirements (Mansi), delivered as package v2.1 (9 Nov 2026)

- **Source:** `sumber/cs-handover-v2.1/`. The runtime copy is in `bff/knowledge/cs-v2.1/`.
- **Output:** strict v2.1 JSON:
  - 15 intents, with P0–P3 priority;
  - `ticket_summary`;
  - `knowledge_refs` with URL and date;
  - `escalation.handoff_status = recommendation_only`;
  - `human_review_required` always true.
- **Simulation:** `SIM-*` fixtures are used only in test mode.
- **Status:** facilitator-led demo only. CS acceptance (R-01..R-07) is pending with the CS owner.

## Decisions on 10 Nov 2026

- **We took over Faiz's backend part.** The BFF is the only backend. `local_setup/` (the 8080 server) is an archive; see `local_setup/LEGACY.md`.
- **Conflicts:** where the Hub and CS v2.1 disagree (size table, refund timing, shipping ETA), the stricter v2.1 rule applies. These conflicts are for Ivana and Mansi to resolve.
- **Details:**
  - spec: `spec-penyesuaian-knowledge-cs.md`
  - contract: `kontrak-api-bff.md`
  - live results: `phase-e-laporan.md`
