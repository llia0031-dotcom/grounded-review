# Multi-turn results (mt3, agent v1.2)

36 conversations (12 ads × runs). Errors: 0.

| Measure | Result |
|---|---|
| Turn 1: decision right | 36/36 |
| Turn 2: offending words removed from the corrected version | 36/36 |
| Turn 2: brand and price kept | 33/36 |
| Turn 2: corrected version with unfilled template text | 0/36 |
| Turn 2: advice fields filled in wrongly (tool markup in a field, empty or one-word caption) | 6/36 |
| Turn 2: advice sent back once by the field check (v1.2 only) | 7/36 |
| Turn 2: corrected version approved by a separate one-prompt review | 31/36 |
| Turn 2: all three | 30/36 |
| Turn 3: decision right on the advertiser's version | 36/36 |
|   versions that fix everything, approved | 27/27 |
|   versions that still break a rule, rejected | 9/9 |
| Turn 3: exact categories | 34/36 |
| Agent cost per conversation (3 turns) | US$0.0077 |
| Cost of the separate reviews | US$0.0303 total |
| Median time per conversation | 23 s |
