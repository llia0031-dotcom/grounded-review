# Multi-turn results (mt4, agent v1.3)

36 conversations (12 ads × runs). Errors: 0.

| Measure | Result |
|---|---|
| Turn 1: decision right | 36/36 |
| Turn 2: offending words removed from the corrected version | 36/36 |
| Turn 2: brand and price kept | 36/36 |
| Turn 2: corrected version with unfilled template text | 0/36 |
| Turn 2: advice fields filled in wrongly (tool markup in a field, empty or one-word caption) | 0/36 |
| Turn 2: advice sent back once by the field check (v1.2 only) | 0/36 |
| Turn 2: advice as submitted, fields filled in wrongly (before the v1.3 cleanup) | 0/36 |
| Turn 2: advice repaired by the v1.3 cleanup | 0/36 |
| Turn 2: corrected version approved by a separate one-prompt review | 35/36 |
| Turn 2: all three | 35/36 |
| Turn 3: decision right on the advertiser's version | 36/36 |
|   versions that fix everything, approved | 27/27 |
|   versions that still break a rule, rejected | 9/9 |
| Turn 3: exact categories | 32/36 |
| Agent cost per conversation (3 turns) | US$0.0068 |
| Cost of the separate reviews | US$0.0284 total |
| Median time per conversation | 22 s |
