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
