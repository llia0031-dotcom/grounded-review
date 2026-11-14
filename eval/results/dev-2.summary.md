# Results (dev)

| | oneshot | agent |
|---|---|---|
| Runs scored (items × runs) | 24 | 24 |
| Decision right (approve / reject) | 23/24 (96%) | 23/24 (96%) |
| Violating ads rejected (recall) | 17/17 (100%) | 17/17 (100%) |
| Rejections that were right (precision) | 17/18 (94%) | 17/18 (94%) |
| Traps approved | 4/5 (80%) | 4/5 (80%) |
| Exact set of categories | 19/24 (79%) | 19/24 (79%) |
| Word violations found | 15/15 (100%) | 15/15 (100%) |
| Picture-only violations found | 2/2 (100%) | 2/2 (100%) |
| Missing-element violations found | n/a | n/a |
| Right clause cited (found labels) | 17/17 (100%) | 17/17 (100%) |
| Offending words located (found word labels) | 15/15 (100%) | 14/15 (93%) |
| Ad quotes verbatim | 26/26 (100%) | 27/27 (100%) |
| Policy quotes verbatim (in the cited clause) | 32/32 (100%) | 28/29 (97%) |
| Decision right, Chinese ads | 12/12 (100%) | 12/12 (100%) |
| Decision right, English ads | 11/12 (92%) | 11/12 (92%) |
| Cost per ad (US$) | 0.00103 | 0.00234 |
| Median latency per ad (s) | 10.4 | 15.4 |
| API calls per ad | 1.0 | 3.1 |
| Run 1 vs run 2: same decision | – | – |
| Run 1 vs run 2: same categories | – | – |

## Per category: precision / recall over (ad × run, category) pairs

| Category | oneshot | agent |
|---|---|---|
| ABSOLUTE | 0.67 / 1.00 (tp 4, fp 2, fn 0) | 0.80 / 1.00 (tp 4, fp 1, fn 0) |
| MEDICAL | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) |
| GUARANTEE | 0.57 / 1.00 (tp 4, fp 3, fn 0) | 0.50 / 1.00 (tp 4, fp 4, fn 0) |
| DISPARAGE | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) |
| DATA | – / – (tp 0, fp 0, fn 0) | – / – (tp 0, fp 0, fn 0) |
| ALCOHOL | 1.00 / 1.00 (tp 2, fp 0, fn 0) | 1.00 / 1.00 (tp 2, fp 0, fn 0) |
| WEIGHT | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) |
| BEFORE_AFTER | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) |
| FLAG | 1.00 / 1.00 (tp 1, fp 0, fn 0) | 1.00 / 1.00 (tp 1, fp 0, fn 0) |
