# Real ads: the arms that run locally

One run per ad. An ad whose published decision found a breach counts as right when it is rejected; an ad that was cleared counts as right when it is approved. The stored outputs hold the ads' words and are not published.

| Arm | Language | Ads | Decision right | Breaching ads rejected | Cleared ads approved |
|---|---|---|---|---|---|
| Word list | English, 30 ASA rulings | 30 | 13/30 | 6/23 | 7/7 |
| Word list | Chinese, 16 published cases | 16 | 11/16 | 10/12 | 1/4 |
| Qwen3Guard-Gen-4B | English, 30 ASA rulings | 30 | 18/30 | 11/23 | 7/7 |
| Qwen3Guard-Gen-4B | Chinese, 16 published cases | 16 | 11/16 | 7/12 | 4/4 |
| Granite Guardian 3.3 8B | English, 30 ASA rulings | 30 | 14/30 | 9/23 | 5/7 |
| Granite Guardian 3.3 8B | Chinese, 16 published cases | 16 | 13/16 | 10/12 | 3/4 |
