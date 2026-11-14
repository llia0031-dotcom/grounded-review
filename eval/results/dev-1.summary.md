# Results (dev)

| | oneshot | agent | wordlist |
|---|---|---|---|
| Runs scored (items × runs) | 24 | 24 | 24 |
| Decision right (approve / reject) | 24/24 (100%) | 24/24 (100%) | 11/24 (46%) |
| Violating ads rejected (recall) | 17/17 (100%) | 17/17 (100%) | 6/17 (35%) |
| Rejections that were right (precision) | 17/17 (100%) | 17/17 (100%) | 6/8 (75%) |
| Traps approved | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) |
| Exact set of categories | 21/24 (88%) | 19/24 (79%) | 9/24 (38%) |
| Word violations found | 15/15 (100%) | 15/15 (100%) | 4/15 (27%) |
| Picture-only violations found | 2/2 (100%) | 2/2 (100%) | 0/2 (0%) |
| Missing-element violations found | n/a | n/a | n/a |
| Right clause cited (found labels) | 17/17 (100%) | 17/17 (100%) | n/a |
| Offending words located (found word labels) | 14/15 (93%) | 15/15 (100%) | 4/4 (100%) |
| Ad quotes verbatim | 23/23 (100%) | 27/27 (100%) | n/a |
| Policy quotes verbatim (in the cited clause) | 26/27 (96%) | 30/30 (100%) | n/a |
| Decision right, Chinese ads | 12/12 (100%) | 12/12 (100%) | 5/12 (42%) |
| Decision right, English ads | 12/12 (100%) | 12/12 (100%) | 6/12 (50%) |
| Cost per ad (US$) | 0.00103 | 0.00208 | 0.00000 |
| Median latency per ad (s) | 11.7 | 12.2 | 3.2 |
| API calls per ad | 1.0 | 3.0 | 0.0 |
| Run 1 vs run 2: same decision | – | – | – |
| Run 1 vs run 2: same categories | – | – | – |

## Per category: precision / recall over (ad × run, category) pairs

| Category | oneshot | agent | wordlist |
|---|---|---|---|
| ABSOLUTE | 0.67 / 1.00 (tp 4, fp 2, fn 0) | 0.67 / 1.00 (tp 4, fp 2, fn 0) | 0.33 / 0.25 (tp 1, fp 2, fn 3) |
| MEDICAL | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 0.50 (tp 1, fp 0, fn 1) |
| GUARANTEE | 0.80 / 1.00 (tp 4, fp 1, fn 0) | 1.00 / 1.00 (tp 4, fp 0, fn 0) | 0.50 / 0.25 (tp 1, fp 1, fn 3) |
| DISPARAGE | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) | – / 0.00 (tp 0, fp 0, fn 2) |
| DATA | – / – (tp 0, fp 0, fn 0) | 0.00 / – (tp 0, fp 2, fn 0) | – / – (tp 0, fp 0, fn 0) |
| ALCOHOL | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) | – / 0.00 (tp 0, fp 0, fn 2) |
| WEIGHT | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) |
| BEFORE_AFTER | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) | – / 0.00 (tp 0, fp 0, fn 1) |
| FLAG | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 0.33 / 1.00 (tp 1, fp 2, fn 0) | – / 0.00 (tp 0, fp 0, fn 1) |
