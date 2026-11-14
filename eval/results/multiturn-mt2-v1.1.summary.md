# Multi-turn results (mt2, agent v1.1)

24 conversations (12 ads × runs). Errors: 0.

| Measure | Result |
|---|---|
| Turn 1: decision right | 24/24 |
| Turn 2: offending words removed from the corrected version | 24/24 |
| Turn 2: brand and price kept | 21/24 |
| Turn 2: corrected version with unfilled template text | 0/24 |
| Turn 2: corrected version approved by a separate one-prompt review | 20/24 |
| Turn 2: all three | 17/24 |
| Turn 3: decision right on the advertiser's version | 22/24 |
|   versions that fix everything, approved | 16/18 |
|   versions that still break a rule, rejected | 6/6 |
| Turn 3: exact categories | 22/24 |
| Agent cost per conversation (3 turns) | US$0.0066 |
| Cost of the separate reviews | US$0.0206 total |
| Median time per conversation | 17 s |
