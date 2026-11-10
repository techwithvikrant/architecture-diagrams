# Clarifying Questions

Goal: one short round of questions (at most 3, via `ask_user_input_v0`) only when the answer changes the
output. If the request, screenshot or conversation already answers a question, don't ask it. If a
sensible default exists, use it and state it in one line.

## Ask when unclear (in priority order)

| # | Question | Typical options | Ask when |
|---|----------|-----------------|----------|
| 1 | Which pages do you need? | Current state only · Target only · Current + target · Full story (current, roadmap, phases, target) | The scope isn't stated |
| 2 | How should the migration be phased? | Big-bang · Parallel run, then retire · By signal/component · By application wave | A phased story is wanted but the order isn't given |
| 3 | Unreadable or ambiguous parts of the source | Show the specific item: "Is X pushing to Y, or Y pulling from X?" | The screenshot is blurry or an arrow direction is unclear |
| 4 | Audience | Customer / executive · Engineering | It changes the density of detail |
| 5 | Branding | Customer name/logo on the cover · Neutral | A customer-facing deck and the name is unknown |
| 6 | Components to add or drop | e.g. "Include Kubernetes for stateless tiers?" | The user hinted at it but didn't confirm |

## Defaults (state, don't ask)

- Deliverables: `.drawio` (all pages) + PNG per page + one combined PDF.
- Canvas 16:9 (1920x1080), white background, legend top right, "why" panel on every slide.
- Arrows show the direction of data flow (pull-based scrapes still point toward the collector/store).
- Status colours: existing / new / changed / retiring (see SKILL.md).
- Cover page included for multi-page customer decks; omitted for a single diagram.
- Brand icons from Simple Icons; generic icons for LBs, servers, databases without a brand.

## Example round

> Before I draw, three quick choices:
> 1. Pages: full story (current → roadmap → phases → target) or current + target only?
> 2. Phase order: by signal (traces → logs → metrics → agents) or by application wave?
> 3. Cover: put the customer's name on it, or keep it neutral?

Then proceed immediately after the answers. Don't ask a second round unless something is truly blocking.
