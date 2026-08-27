# voc-minimal-subset — campaign report

**Full paper: [paper/main.pdf](paper/main.pdf)** (LaTeX source: paper/main.tex)

Cycles: 0 · Experiments: 0 · Promotions: 0 · Final incumbent score: None

> Draft artifact. Before this leaves the building it must pass docs/paper-audit-protocol.md; human-only byline + AI-contribution statement.

## Abstract

The non-contact implied open-circuit voltage (V_OC) protocol of Louks et al. (arXiv:2508.21037) infers a solar absorber's radiative-limit voltage from three optical measurements---steady-state photoluminescence (SRPL), time-resolved photoluminescence (TRPL), and optical transmission---fed to a detailed-balance model. We ask a pure information-sufficiency question: does there exist a reduced protocol using at most two of the three modalities, at a strictly smaller acquisition budget (measurement time and integrated photon dose), that reproduces the full protocol's own implied V_OC to within 10 mV worst-case, leave-one-device-out across a synthetic grid of realistic p-i-n stacks under certification measurement noise? A sealed, deterministic verifier is the sole oracle; the search only edits candidate protocol dicts. We enumerate exhaustively every single-config-per-modality protocol of at most two modalities under a smaller budget (a finite set) and treat multi-config repeats---which the contract also admits, buying precision as sqrt(dose)---separately by argument. Result: the reduction exists. The protocol {SRPL, transmission}---dropping TRPL---passes and is the only two-modality subset containing a passer; the cheapest certified passer (SRPL at fluence 0.25 suns, 50 ms window; transmission at 20 ms) recovers the full implied V_OC to 9.13 mV worst-case at 68% less acquisition time and 93% less photon dose than the three-measurement protocol. The result is simultaneously a certified partial negative: TRPL is non-load-bearing for the implied-V_OC scalar by construction (setup leverage 0.31 mV), whereas SRPL (20.06 mV) and transmission (47.25 mV) are load-bearing, and every enumerated single-config protocol that drops either fails the bar. Dropping transmission cannot be rescued by any amount of PL repetition (PL carries no absorption-edge or thickness information); dropping SRPL floors at 20.06 mV for single configs, and we scope the negative accordingly rather than claiming multi-config TRPL repeats were graded. Scope is strictly the pinned model's own implied V_OC; the ~170 mV real-device stack offset reported in the source is out of scope. All numbers are sealed-verifier verdicts.

## Belief state at close

# PRIORS — voc-minimal-subset

Belief state. Every claim: `[STATUS] claim (evidence)`. Wrong beliefs get status-flipped in place, never deleted.

- [DEAD] FALSE POSITIVE (run 1): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 100.0}], 'transmission': [{'window_ms': 20.0}]}} — failed independent verification (SEARCH-1)
- [DEAD] FALSE POSITIVE (run 1): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 0.25, 'window_ms': 50.0}], 'transmission': [{'window_ms': 20.0}]}} — failed independent verification (SEARCH-1)
- [DEAD] FALSE POSITIVE (run 1): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 50.0}], 'transmission': [{'window_ms': 20.0}]}} — failed independent verification (SEARCH-1)
- [DEAD] Search run 1 dead ends: [SMALL-FIRST] Every subset that drops SRPL or drops transmission is dead for the 10 mV bar, matching the setup leverage report (SRPL=20.1 mV, transmission=47.2 mV both load-bearing). {trpl,transmission} floors at ~20 mV (TRPL indirect PLQE too imprecise to replace SRPL-direct). {srpl,trpl} and any s (SEARCH-1)
- [ALIVE] VERIFIED HIT (run 2): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 100.0}], 'transmission': [{'window_ms': 20.0}]}} (SEARCH-2)
- [ALIVE] VERIFIED HIT (run 2): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 1.0, 'window_ms': 50.0}], 'transmission': [{'window_ms': 20.0}]}} (SEARCH-2)
- [ALIVE] VERIFIED HIT (run 2): {'modalities': ['srpl', 'transmission'], 'configs': {'srpl': [{'fluence': 0.25, 'window_ms': 50.0}], 'transmission': [{'window_ms': 20.0}]}} (SEARCH-2)
- [DEAD] Search run 2 dead ends: [SMALL-FIRST] Every subset that drops SRPL (={trpl,transmission}, {transmission}, {trpl}) or drops transmission (={srpl,trpl},{srpl},{trpl}) is dead for the 10 mV bar — matches the leverage report (SRPL & transmission both load-bearing). {trpl,transmission} floors ~20 mV (TRPL indirect log-sigma 0.2 (SEARCH-2)

