# Postmortem — <title>  (<date> · induced | real)

> Blameless. Copy to `docs/reliability/postmortems/<date>-<slug>.md`. A postmortem is a proof-catalog
> entry — the clearest "operate under failure" signal.

## Summary
_One paragraph: what happened, user/business impact, duration._

## SLO impact
_Which SLI breached · error budget burned · **MTTR**._

## Timeline
_`Detect → Diagnose → Mitigate → Recover` with timestamps._

## Root cause
_The actual layer + why (state the hypothesis + the evidence) — not the symptom._

## What worked
_The controls/automation that helped (alert fired, canary aborted, selfHeal, outbox drained…)._

## What didn't
_Gaps: missing alert, slow/unclear runbook, a wrong assumption, a mock that hid the bug._

## Action items
_Each a concrete fix + owner + issue link._

## Evidence
_Graphs, logs, `kubectl` output, the restore proof, before/after metrics._
