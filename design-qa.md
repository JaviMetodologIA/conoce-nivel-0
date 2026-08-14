# Playbook visual QA · 2026-08-14

## Scope

Playbook ES/EN/PT at 320, 390, 768 and 1440 px, light/dark themes. The source of truth is `src/site.css` plus the playbook renderer in `scripts/build.py`; `dist/` is compiled output.

## Captured evidence

- Before, desktop collision: `qa/playbook-adversarial-before/founders-accepted-1440.png`
- After, desktop: `qa/playbook-adversarial-after/final-founders-1440.png`
- After, mobile: `qa/playbook-adversarial-after/final-founders-390.png`

## Brutally honest audit

1. The founder title used display-scale typography inside a narrow editorial column. At 1440 px it crossed into the portrait grid. This was not expressive tension; it was an untested collision.
2. The original founder layout treated the four portraits as a sidebar, weakening the authorship story and starving both text columns.
3. Nineteen chapters repeated an oversized vertical rhythm. The result looked expensive in isolated screenshots but slow and template-like as a complete document.
4. Spanish alone produced a false sense of safety. The longer English title overflowed at both 320 and 1440 px after the first repair.
5. A decorative `Carta abierta` pseudo-label collided with the real eyebrow on mobile after the structural fix.

## Iterations

1. Split founder heading and body into explicit semantic wrappers.
2. Promoted portraits to a four-column editorial band; preserved a two-column mobile collage.
3. Reduced chapter spacing, index width and heading scale while retaining the A³ hierarchy.
4. Added fail-closed geometry checks for title overflow and copy/card collisions in all three locales at 320/390/768/1440.
5. Added responsive breakpoints for English minimum-content width and removed the decorative label below 600 px.
6. Rebuilt twice and compared the complete output trees byte for byte.

## Final verification

- Full visual/runtime QA: passed across 15 routes.
- Playbook geometry matrix: zero document overflow, section overflow, title overflow or founder collisions.
- Axe WCAG A/AA: 0 violations across ES/EN/PT, light/dark, 390/1440 (12 combinations).
- Build integrity: 25 sources and 50 outputs hash-bound.
- State: `RENDERED_DRAFT`; publication is not authorized.

## Final Result

passed
