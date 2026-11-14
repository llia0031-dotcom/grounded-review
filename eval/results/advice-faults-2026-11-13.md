# Advice fields filled in wrongly

Fault = tool markup inside an advice field, or a corrected caption that is empty or one word (`common.advice_problems`).
For v1.2 the stored advice is the one finally accepted. "After cleanup" applies `common.clean_advice` (agent v1.3) offline.

| Run | Conversations stored | With markup | Caption empty or one word | Fault after cleanup |
|---|---|---|---|---|
| multiturn-2026-11-13 | 24 | 2 | 1 | 0 |
| multiturn-mt2-v1 | 24 | 2 | 1 | 0 |
| multiturn-mt2-v1.1 | 24 | 3 | 3 | 0 |
| multiturn-mt3-v1.1 | 36 | 4 | 3 | 0 |
| multiturn-mt3-v1.2 | 36 | 6 | 3 | 0 |
| *first five runs (read before writing the check and the cleanup)* | 144 | 17 | 11 | 0 |
| multiturn-mt4-v1.1 | 36 | 6 | 2 | 0 |
| multiturn-mt4-v1.3 | 36 | 0 | 0 | 0 |
| **all** | **216** | **23** | **13** | **0** |

| Run | Item | Run no. | Fault | Cleanup | Fault after cleanup |
|---|---|---|---|---|---|
| multiturn-2026-11-13 | en-t38 | 2 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-2026-11-13 | zh-t27 | 2 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt2-v1 | en-m02 | 2 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt2-v1 | en-m06 | 2 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt2-v1.1 | en-m03 | 2 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt2-v1.1 | en-m06 | 2 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt2-v1.1 | zh-m04 | 1 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.1 | en-n01 | 2 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt3-v1.1 | en-n06 | 1 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.1 | zh-n06 | 1 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.1 | zh-n06 | 3 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.2 | en-n04 | 3 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.2 | zh-n01 | 1 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt3-v1.2 | zh-n01 | 2 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt3-v1.2 | zh-n01 | 3 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt3-v1.2 | zh-n03 | 3 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt3-v1.2 | zh-n04 | 1 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt4-v1.1 | en-p03 | 3 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt4-v1.1 | en-p06 | 2 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt4-v1.1 | zh-p02 | 1 | answer contains tool markup | answer cut at tool markup | none |
| multiturn-mt4-v1.1 | zh-p04 | 3 | answer contains tool markup; revised_caption is empty | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt4-v1.1 | zh-p06 | 1 | answer contains tool markup; revised_caption is a single word | answer cut at tool markup; caption taken from the markup | none |
| multiturn-mt4-v1.1 | zh-p06 | 2 | answer contains tool markup | answer cut at tool markup | none |
