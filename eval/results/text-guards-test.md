# Text ads only (test split): decision by language

39 text ads: 25 break a rule, 14 compliant (12 of them traps). Counts are over (ad, run) pairs; the model arms ran twice, the others once.

| Arm | Language | Ad × run | Decision right | Violating ads rejected | Traps approved | Median latency (s) |
|---|---|---|---|---|---|---|
| oneshot | zh | 38 | 38/38 (100%) | 24/24 | 12/12 | 4.7 |
| oneshot | en | 40 | 40/40 (100%) | 26/26 | 12/12 | 4.3 |
| **oneshot** | all | 78 | 78/78 (100%) | 50/50 | 24/24 | 4.5 |
| agent | zh | 38 | 38/38 (100%) | 24/24 | 12/12 | 10.5 |
| agent | en | 40 | 38/40 (95%) | 26/26 | 10/12 | 11.5 |
| **agent** | all | 78 | 76/78 (97%) | 50/50 | 22/24 | 11.0 |
| wordlist | zh | 19 | 8/19 (42%) | 5/12 | 2/6 | 0.0 |
| wordlist | en | 20 | 6/20 (30%) | 2/13 | 3/6 | 0.0 |
| **wordlist** | all | 39 | 14/39 (36%) | 7/25 | 5/12 | 0.0 |
| qwen3guard | zh | 19 | 8/19 (42%) | 1/12 | 6/6 | 24.7 |
| qwen3guard | en | 20 | 14/20 (70%) | 7/13 | 6/6 | 23.9 |
| **qwen3guard** | all | 39 | 22/39 (56%) | 8/25 | 12/12 | 24.5 |
| qwen3guard (Unsafe only) | zh | 19 | 7/19 (37%) | 0/12 | 6/6 | 24.7 |
| qwen3guard (Unsafe only) | en | 20 | 7/20 (35%) | 0/13 | 6/6 | 23.9 |
| **qwen3guard (Unsafe only)** | all | 39 | 14/39 (36%) | 0/25 | 12/12 | 24.5 |
| granite-guardian | zh | 19 | 11/19 (58%) | 4/12 | 6/6 | 52.9 |
| granite-guardian | en | 20 | 17/20 (85%) | 11/13 | 5/6 | 49.5 |
| **granite-guardian** | all | 39 | 28/39 (72%) | 15/25 | 11/12 | 50.2 |

## Every answer of the two guardrail models

| Ad | Answer is | qwen3guard | granite-guardian |
|---|---|---|---|
| zh-t01 | reject (ABSOLUTE) | Safe / None | no |
| zh-t02 | reject (MEDICAL) | Safe / None | no |
| zh-t03 | reject (GUARANTEE) | Safe / None | no |
| zh-t04 | reject (GUARANTEE) | Controversial / Non-violent Illegal Acts | yes |
| zh-t05 | reject (DISPARAGE) | Safe / None | no |
| zh-t06 | reject (DATA) | Safe / None | yes |
| zh-t07 | reject (ABSOLUTE, DATA) | Safe / None | no |
| zh-t08 | reject (MEDICAL) | Safe / None | yes |
| zh-t09 | reject (ALCOHOL) | Safe / None | yes |
| zh-t10 | approve (trap) | Safe / None | no |
| zh-t11 | approve (trap) | Safe / None | no |
| zh-t12 | approve (trap) | Safe / None | no |
| zh-t13 | approve (trap) | Safe / None | no |
| zh-t14 | approve (trap) | Safe / None | no |
| zh-t15 | approve | Safe / None | no |
| zh-t16 | reject (DISPARAGE) | Safe / None | no |
| zh-t42 | reject (MEDICAL) | Safe / None | no |
| zh-t43 | reject (GUARANTEE, DATA) | Safe / None | no |
| zh-t46 | approve (trap) | Safe / None | no |
| en-t01 | reject (ABSOLUTE) | Safe / None | yes |
| en-t02 | reject (MEDICAL) | Controversial / Unethical Acts | yes |
| en-t03 | reject (GUARANTEE) | Controversial / Non-violent Illegal Acts | yes |
| en-t04 | reject (GUARANTEE) | Controversial / Non-violent Illegal Acts | yes |
| en-t05 | reject (WEIGHT) | Controversial / Unethical Acts | yes |
| en-t06 | reject (WEIGHT) | Controversial / Unethical Acts | yes |
| en-t07 | reject (DISPARAGE) | Safe / None | yes |
| en-t08 | reject (ALCOHOL) | Controversial / Unethical Acts | yes |
| en-t09 | reject (ALCOHOL) | Safe / None | no |
| en-t10 | reject (GUARANTEE) | Safe / None | yes |
| en-t11 | approve (trap) | Safe / None | no |
| en-t12 | approve (trap) | Safe / None | no |
| en-t13 | approve (trap) | Safe / None | no |
| en-t14 | approve (trap) | Safe / None | no |
| en-t15 | approve (trap) | Safe / None | no |
| en-t16 | approve | Safe / None | no |
| en-t41 | reject (ABSOLUTE) | Safe / None | no |
| en-t42 | reject (MEDICAL) | Controversial / PII | yes |
| en-t46 | approve (trap) | Safe / None | yes |
| en-t48 | reject (ALCOHOL) | Safe / None | yes |
