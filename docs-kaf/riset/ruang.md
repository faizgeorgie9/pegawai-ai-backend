# Ruang: research notes (4 November 2026)

Repo: https://github.com/yugienugraha/ruang (v0.2.0). License: MIT, "Copyright (c) 2026 yugienugraha".

## Stack

React 19, @react-three/fiber 9.8, three 0.186, Vite 7. No drei, physics or state library. Our frontend already uses React 19, so it is compatible.

## Files to copy

| File | Role |
|---|---|
| `src/pages/Office3D.tsx` | Canvas, camera, OrbitControls, characters, labels, speech span |
| `src/office3d-layout.ts` | Pure layout maths (no React/three) |
| `src/scene3d/environment.tsx` | Building, floors, outdoors |
| `src/scene3d/props.tsx` | Procedural desks, chairs, sofa |
| `src/scene3d/textures.ts` | Procedural canvas textures |
| `src/agents.ts` | Avatar colours (FNV-1a hash of id) |
| `src/types.ts` | Only `OfficeState`, `OfficeRoom`, `OfficeStation` |
| `src/styles.css` | Only the 3D blocks (the file is 72 KB, mixed with the whole app) |

Do not copy `server/*`, `polling.ts`, `request-state.ts` or other pages. Ruang reads Hermes through the CLI (Express on port 3001, polling every 15 s); we replace that with our BFF.

## Data mapping

`OfficeStation`: id, name, role, room (`Workspace` | `Lounge`), state (`Idle` | `Working` | `Reviewing` | `Collaborating` | `Offline` | `Unknown`), currentTask, activity, seat. Positions are computed on the client.

- Our status maps as: idle to `Idle`, working to `Working`, discussing to `Collaborating`.
- Team colours: change `agentLook` in `agents.ts` to accept our colour.
- Teams: no concept in the layout, so we add grouping.
- Conversation: the scene shows no dialogue text, only a short activity label. Message bubbles are our own overlay.

## Assets and performance

No model, texture or font files: everything is primitives and procedural textures. Canvas dpr [1,2], shadows on, no LOD. The 3D code loads only for the 3D view. It imports `three/examples/jsm` OrbitControls and RoundedBoxGeometry.
