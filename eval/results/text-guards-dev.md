# Text ads only (dev split): decision by language

12 text ads: 9 break a rule, 3 compliant (3 of them traps). Counts are over (ad, run) pairs; the model arms ran twice, the others once.

| Arm | Language | Ad × run | Decision right | Violating ads rejected | Traps approved | Median latency (s) |
|---|---|---|---|---|---|---|
| oneshot | zh | 6 | 6/6 (100%) | 4/4 | 2/2 | 8.8 |
| oneshot | en | 6 | 5/6 (83%) | 5/5 | 0/1 | 4.5 |
| **oneshot** | all | 12 | 11/12 (92%) | 9/9 | 2/3 | 6.3 |
| agent | zh | 6 | 6/6 (100%) | 4/4 | 2/2 | 10.7 |
| agent | en | 6 | 5/6 (83%) | 5/5 | 0/1 | 8.1 |
| **agent** | all | 12 | 11/12 (92%) | 9/9 | 2/3 | 10.3 |
| wordlist | zh | 6 | 4/6 (67%) | 3/4 | 1/2 | 0.0 |
| wordlist | en | 6 | 3/6 (50%) | 2/5 | 1/1 | 0.0 |
| **wordlist** | all | 12 | 7/12 (58%) | 5/9 | 2/3 | 0.0 |
| qwen3guard | zh | 3 | 0/3 (0%) | 0/3 | 0/0 | 22.4 |
| qwen3guard | en | 0 | 0/0 (0%) | 0/0 | 0/0 | — |
| **qwen3guard** | all | 3 | 0/3 (0%) | 0/3 | 0/0 | 22.4 |
| qwen3guard (Unsafe only) | zh | 3 | 0/3 (0%) | 0/3 | 0/0 | 22.4 |
| qwen3guard (Unsafe only) | en | 0 | 0/0 (0%) | 0/0 | 0/0 | — |
| **qwen3guard (Unsafe only)** | all | 3 | 0/3 (0%) | 0/3 | 0/0 | 22.4 |

## Every answer of the two guardrail models

| Ad | Answer is | qwen3guard | granite-guardian |
|---|---|---|---|
| zh-d01 | reject (ABSOLUTE) | Safe / None | — |
| zh-d02 | reject (MEDICAL) | Safe / None | — |
| zh-d03 | reject (GUARANTEE) | Safe / None | — |
| zh-d04 | approve (trap) | — | — |
| zh-d05 | approve (trap) | — | — |
| zh-d06 | reject (GUARANTEE) | — | — |
| en-d01 | reject (ABSOLUTE) | — | — |
| en-d02 | reject (MEDICAL) | — | — |
| en-d03 | reject (WEIGHT) | — | — |
| en-d04 | approve (trap) | — | — |
| en-d05 | reject (GUARANTEE) | — | — |
| en-d06 | reject (ALCOHOL) | — | — |
