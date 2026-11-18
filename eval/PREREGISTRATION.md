# Held-out evaluation: plan fixed before the run

Written 13 November 2026, frozen at 01:24 MYT, before any model saw the test split. After the run, nothing in the test set, policy library, prompts or scoring rules below changes. Any later fix to the scorer is listed under "Changes after the run" with its reason, and the run is re-scored from the stored outputs with no new model calls.

## Question

When an ad is reviewed against a written policy, does an agent that reads the image, looks up clauses and checks its own quotes do better than one prompt with everything in it, and how do both compare with a banned-word list and zero-shot image models? "Better" means: right decision, right violation type, right clause, the offending words located, and quotes that are verbatim, at a known cost and latency.

## Test set

`testset/items_zh.yaml` and `testset/items_en.yaml`. Brands are fictional. Answers were fixed when each item was written.

- **Policies.** Chinese ads: the Advertising Law of the PRC (2021) and the SAMR enforcement guide on absolute terms (2023). English ads: five TikTok Advertising Policies pages, global sections only. 32 clauses in `policies/clauses.yaml`, 12 of which no item is labelled with (they are there to be wrongly retrieved).
- **Nine violation types:** absolute claims, medical claims, guaranteed outcomes, disparaging competitors, data without a source (Chinese law only), alcohol rules, weight and body image (TikTok only), before-and-after comparisons (TikTok only), national flag (Chinese law only).
- **Test split, 96 ads:** 48 Chinese (19 text, 29 image), 48 English (20 text, 28 image). 62 break at least one rule (65 labels: 56 located in words, 8 only in the picture, 1 a missing required statement); 34 are compliant, 30 of them traps that look risky but are allowed, each with the clause that says so.
- **Images** are drawn by `testset/render.py`: posters, banners, before-and-after panels, the national flag drawn to its published geometry (once large, once small in a corner), lanterns, small print at the bottom, and three illustrated scenes for alcohol (people drinking; a drunken party). The words of every image are known, so OCR and quotes can be checked exactly. OCR (RapidOCR, PP-OCRv6 medium) on all images: see `testset/ocr.json`.
- **16 harder test items** (`zh-t41`–`zh-t48`, `en-t41`–`en-t48`) were added after the dev runs showed both model arms at 23–24 of 24, and before any model saw the test split: a digit-zero "N0.1", Unicode bold "𝗯𝗲𝘀𝘁", testimonials that imply treatment, small print, a claim split between caption and image, risky words inside a negation, "治愈系" as a style word, "Number 1 fan", and a small flag.
- **Multi-turn:** 12 test items carry an advertiser's revised version with its own answers (7 fix everything, 5 still break a rule) and the facts a corrected version must keep.
- **Dev split, 24 ads**, used to debug the harness and prompts; reported separately.

## Arms

| Arm | What it gets | Output |
|---|---|---|
| one prompt | the whole policy library of the ad's jurisdiction, the image, the caption and the OCR text, in one request | review schema (structured output) |
| agent | the image and the caption; tools: `read_image_text` (OCR), `search_policy` (BM25 over clauses), `get_clause`, `check_quotes` (evidence-check script 0.2.0), `submit_review`; up to 10 rounds | the same schema |
| word list | caption + OCR text; Chinese: sdhack/ecommerce-content-review rules v4.10 (block groups); English: AdLint signal lists (high/critical) | categories and matched words; no clauses |
| CLIP, SigLIP 2 | the image only; zero-shot, top prompt among 9 categories and "ordinary ad" | one category or approve |
| ShieldGemma 2 | NOT RUN: downloading it requires signing in and accepting the model's terms of use | — |

Both model arms: `claude-haiku-5-5`, effort `medium`, adaptive thinking by default, the same category list and the same output schema (category, clause id, ad quote, picture evidence, policy quote, explanation). Category `OTHER` (another rule in the library) rejects but counts for no category.

Changes made on the dev split before this plan: the `OTHER` category and clearer category descriptions (the agent had put a "false advertising" finding under FLAG for lack of a better option), and one line telling the model the ad's language.

## What is measured (rules in `eval/score.py`)

1. **Decision right**: reject if any violation is named; the answer is reject if the item has labels. Also recall on violating ads, precision of rejections, and the share of traps approved.
2. **Per category**: precision and recall over (ad × run, category) pairs.
3. **Right clause**: for each labelled violation whose category was found, a violation of that category cites one of the accepted clause ids.
4. **Located**: for each found violation with labelled words, the ad quote overlaps the labelled words (one contains the other, or they share 4 Chinese / 8 other characters).
5. **Quotes verbatim**: evidence-check's script on every ad quote, against the true words of the ad, and on every policy quote, against the text of the clause it cites (each clause is its own source file).
6. **Cost** per ad from token counts at list price, **median latency** (including OCR time), API calls per ad.
7. **Noise**: each model arm runs twice; agreement between the two runs on the decision and on the set of categories.
8. **Multi-turn** (`eval/multiturn.py`, agent only, 12 items × 2 runs): turn 2 corrected version removes every labelled offending span, keeps brand and price, and is approved by a separate one-prompt review (image re-rendered with the corrected words, OCR run on it); turn 3 decision on the advertiser's version.
9. **Failure attribution**: every miss and every wrong flag of the model arms is read and put in one cause: OCR did not read the words; the picture was not understood; trap wrongly flagged; defensible extra flag (a reading a reviewer could also take, under a clause in the library); wrong category for a real problem; clause confusion; missed outright.

Image-only results are also reported for all arms on the 57 image ads, since CLIP and SigLIP 2 see images only.

## Expectations, written down before the run

1. Both model arms will get at least 85% of decisions right and reject at least 90% of ads whose violation is in words. Differences of one or two ads between them are noise.
2. Misses will concentrate in the harder items: small print, the small flag and the illustrated drinking scenes. At least one model arm will miss at least one of them in at least one run.
3. The model arms will approve at least 75% of traps; the word list will approve fewer than 60%.
4. The word list will reject fewer than half of the violating ads: it has nothing for disparagement, data without a source, pictures, or missing statements.
5. CLIP and SigLIP 2 will be close to useless at naming the category; they may catch some flags, before-and-after panels and drinking scenes.
6. The agent will cost about twice as much as one prompt and take longer. Its policy quotes will be verbatim at least as often as the one-prompt arm's, because it checks them.
7. In the multi-turn task the agent's corrected version will remove the offending words in at least 10 of 12 conversations per run, and at least 8 of 12 will pass the separate review.

Expectations that do not hold are reported as not holding.

## Budget

Model calls for the whole project stay under US$3. Estimated from the dev runs: test split, two arms × 96 ads × 2 runs ≈ US$0.65; multi-turn ≈ US$0.2.

## Run

From `ad-review-agent/`, with `PY` the project's Python:

```
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/run.py --split test --repeat 2 --out test-2026-11-13 --budget 1.2
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/multiturn.py --repeat 2 --out multiturn-2026-11-13
PY baselines/wordlist.py --split test
PY baselines/clip_zeroshot.py --split test
PY eval/score.py eval/results/test-2026-11-13.jsonl eval/results/wordlist-test.jsonl --split test --out eval/results/test-2026-11-13.summary.md
PY eval/score.py eval/results/test-2026-11-13.jsonl eval/results/wordlist-test.jsonl eval/results/clip-test.jsonl eval/results/siglip2-test.jsonl --split test --kind image --out eval/results/test-2026-11-13.images.summary.md
```

## Frozen files (sha256, first 12 characters)

Hashes are of the file contents with line endings normalised to LF. `check_evidence.py` is evidence-check's script 0.2.0, called in place.

| File | sha256 |
|---|---|
| `testset/items_zh.yaml` | `f2b3804c4ad0` |
| `testset/items_en.yaml` | `2b30055e67c8` |
| `testset/load.py` | `321aa7691169` |
| `testset/render.py` | `3eb39011c340` |
| `testset/ocr.json` | `ff0e3d7339b4` |
| `policies/clauses.yaml` | `27cd8a53cea1` |
| `policies/library.py` | `27bb9ac4d470` |
| `policies/sources/cn-advertising-law-2021.md` | `c1276c64ede8` |
| `policies/sources/cn-samr-absolute-terms-guide-2023.md` | `9758864bc338` |
| `policies/sources/tiktok-alcohol.md` | `ea67e7b95784` |
| `policies/sources/tiktok-deceptive-practices.md` | `9477c6304a50` |
| `policies/sources/tiktok-financial-services.md` | `3126fd4becac` |
| `policies/sources/tiktok-misleading-and-false-content.md` | `4fcf3c83f08d` |
| `policies/sources/tiktok-weight-management.md` | `9ea07c449000` |
| `agent/common.py` | `5ea74497d86c` |
| `agent/oneshot.py` | `10add0142f10` |
| `agent/review_agent.py` | `e895154eaa80` |
| `agent/ocr.py` | `28272c9275f8` |
| `eval/run.py` | `d8b48b365fcb` |
| `eval/score.py` | `284941b328a8` |
| `eval/multiturn.py` | `ecbc72a25618` |
| `baselines/wordlist.py` | `eb79ffdb8dcb` |
| `baselines/clip_zeroshot.py` | `fe4b6ba68bdb` |
| `../evidence-check/skills/evidence-check/scripts/check_evidence.py` | `f820b173a356` |
| `testset/images/` (73 PNG files, names and bytes in name order) | `15220b51bd2b` |

## Changes after the run

The run started at 01:24 MYT, after the hashes were written. Test set, policy library, prompts and `eval/score.py` did not change.

1. **Rate limits.** The main run and the multi-turn run were started together and hit the API limit of 500,000 input tokens per minute. 13 of 384 main-run tasks failed and were stored as failures; running the same command again ran exactly those 13 (the runner skips stored successes). The multi-turn runner stopped after 5 conversations because one exception was not caught. It now stores a failed conversation and retries it on the next run; the conversation logic is unchanged. `eval/multiturn.py` is now ``c9053719bb0c``. The remaining 19 conversations were run afterwards with fewer parallel workers.
2. **Attribution.** `eval/attribution.py` was written while the run was in progress, before the results were read; it applies the causes listed above. Each extra category on a non-trap ad was then read and marked defensible or wrong in `eval/attribution_reading.yaml`, with a one-line reason.
3. **Flaws found in the test set**, left as they are and reported: the trap `zh-t21` (a state heritage listing of a craft shown above a brand's teaware) is weaker than intended, since the guide's exemption covers titles the product itself holds; the revision of `en-t27` changes the image words but keeps the old product name in the caption, so the agent's "inconsistent information" flag on it is arguably right.
4. **v1.1 code, after the v1 run.** `agent/review_agent.py` and `agent/common.py` gained an optional `version` (default `v1`), the `check_revision` tool and the advice rule, both used only by v1.1, and a placeholder detector. With the default, the agent's prompts and tools are exactly those of the v1 run. The v1 results above were not re-run. See the v1.1 section below.
5. **SafeGuard-VL-RL, an arm added after the freeze.** ShieldGemma 2 stays NOT RUN (downloading it requires signing in and accepting the model's terms of use). In its place, `baselines/safeguard_vl.py` (`4e8c4f0889a8`; last changed 02:00 MYT, before its test run) runs tyodd/SafeGuard-VL-RL with the nine categories written as its policy, on image ads only, without the caption, greedy decoding. It was tried on 2 dev images for timing, then run once on the 57 test images (finished 05:09 MYT, no errors). No expectation was written for it. `eval/score.py` (unchanged) scores it with the same rules; it gives no quotes or clause ids, so the clause, located and quote measures do not apply. Results in `results/test-2026-11-13.images.summary.md`.
6. **Two open text guardrail models, arms added after the freeze (written 14 November 2026, 05:25 MYT, before their test run).** The text ads had no open moderation model to compare with. `baselines/text_guards.py` (`90eaa091dfb0`) runs, on the 39 text ads of the test split (19 Chinese, 20 English; 25 violating, 12 traps), once each, greedy decoding, on CPU:
   - **Qwen/Qwen3Guard-Gen-4B** (Apache-2.0, revision `6ec42827da0c`): a general safety classifier with fixed categories; it cannot take a custom policy. The ad copy is the user message, as in the model card's prompt moderation example. Unsafe or Controversial counts as reject; Unsafe only is also reported.
   - **ibm-granite/granite-guardian-3.3-8b** (Apache-2.0, revision `b3421eda4ba6`): takes a custom criterion; its model card says it was trained and tested on English data only. The criterion is the nine categories in the same words the model arms see; thinking off; yes counts as reject.
   - openai/gpt-oss-safeguard-20b, which is built to follow a written policy, is **NOT RUN**: its model card asks for a 16 GB GPU, this machine has 8 GB, and the CPU build of PyTorch cannot hold it in 32 GB of memory.
   - Both were tried on 3 dev ads for timing and parsing (Qwen3Guard about 22 s per ad, Granite about 48 s). Neither names a category of this test set, a clause or a quote, so only the decision measures apply. `eval/text_guards_report.py` (`c2eb5a5d82e5`) gives decisions on text ads by language for all arms, from stored outputs. Test set, policy library and `eval/score.py` hashes are unchanged.
   - Expectations: (a) Qwen3Guard rejects fewer than a third of the 25 violating text ads, even under the stricter reading; (b) Granite Guardian rejects more violating text ads than Qwen3Guard; (c) Granite Guardian gets a larger share of decisions right on English text ads than on Chinese; (d) both get a smaller share of decisions right on text ads than either model arm.
   - **Results** (both runs finished 14 November, 39 ads each, no errors; `results/qwen3guard-test.jsonl`, `results/granite-guardian-test.jsonl`, summary `results/text-guards-test.md`). All four held. (a) Qwen3Guard rejected 8 of 25, just under a third (8.3); it answered Unsafe for none, so all 8 are Controversial. (b) Granite Guardian rejected 15 of 25. (c) Granite Guardian was right on 17/20 English and 11/19 Chinese text ads. (d) Decisions right on text ads: Qwen3Guard 22/39 (56%), Granite Guardian 28/39 (72%), one prompt 78/78, agent 76/78.
7. **Answer-key audit (written 18 November 2026, after every run).** Two clauses require a statement in the ad, not only the absence of bad words: TT-ALC (an alcohol ad states the drink's strength and carries a responsible drinking disclaimer) and CN-AL-18 (a health-food ad shows 「本品不能代替药物」). The frozen key labelled a missing statement only where it was an ad's sole problem (`en-t36`). Six held-out ads also lack a required statement and have no label for it: `zh-t08` and `zh-t24` (health food), and `en-t08`, `en-t09`, `en-t35`, `en-t48` (alcohol). Found when another evaluation reused these ads; checked with `eval/key_audit.py` (`results/key-audit-2026-11-18.md`). The frozen item files are **not** changed. The six labels are in `testset/key_corrections_2026-11-18.yaml`, and `eval/rescore_corrected.py` scores the stored run again with them (`results/test-2026-11-13.corrected-key.md`):
   - Unchanged for both arms: decisions right (191 and 187 of 192), violating ads rejected (124 of 124), traps approved (59 and 55 of 60), exactly the labelled categories (161 and 173 of 192). All six ads were already rejects and the new labels add no category.
   - Changed: missing-element labels go from 2 to 14 over runs, all 14 found by both arms; labels with the right clause cited go from 129 of 129 to 141 of 141 for both arms.
   - The scorer counts a label as found when the arm lists any violation of its category, so a stricter count was made: on the six ads, each arm named the missing statement itself in 11 of 12 runs. On the four ads in the test, harder and memory sets that carry both alcohol statements, neither arm ever claimed one was missing.
   - The harder set and the memory set have no such gap. The multi-turn measures do not use these labels.
   - The reported numbers stay those of the frozen key, as preregistered.

## v1.1: the agent's corrected versions (written 03:07 MYT, before the v1.1 run)

**Why.** In the multi-turn task, 3 of 24 corrected versions from the agent contained unfilled template text ("Licensed by [licensing authority, licence number]", "Win [non-alcohol prize]"), and a separate review rejected them. v1.1 targets only that.

**Change (agent v1.1, selected with `--version v1.1`; v1 is unchanged and stays the default).** When the advertiser asks how to fix the ad, a system message tells the agent that the corrected version must be ready to run, with no blanks or template text; a fact the advertiser has not given is left out and named in the answer instead. A new tool, `check_revision`, lists template text (brackets, 【】, {{}}, XX, blanks) and any of the review's quoted words still present; the agent is told to call it before `submit_advice`. Review turns are untouched.

**New items.** The 12 v1 multi-turn items were used to find the problem, so v1.1 is compared on 12 new text ads in `testset/items_mt2.yaml` (6 Chinese, 6 English), written before any model saw them, answers fixed: 9 advertiser versions fix everything, 3 still break a rule. Several need a fact the ad does not give for a full fix (alcohol strength, a data source, a health-food notice).

**Run.** Both versions, 12 items × 2 runs each: `PY eval/multiturn.py --set mt2 --version v1 --repeat 2 --out multiturn-mt2-v1` and the same with `--version v1.1 --out multiturn-mt2-v1.1`. Same measures as the multi-turn task above, plus "corrected version with unfilled template text" (`common.placeholders`).

**Expectations.**
1. v1.1 leaves template text in 0 of 24 corrected versions; v1 in at least 1 of 24.
2. The separate review approves at least as many v1.1 corrected versions as v1 ones.
3. Offending words removed and brand and price kept: both versions at least 22 of 24.
4. Turn-3 decisions on the advertiser's versions: no difference beyond 2 of 24.
5. v1.1 costs at most 30% more per conversation.

| File | sha256 |
|---|---|
| `testset/items_mt2.yaml` | `c6432795c69a` |
| `agent/review_agent.py` | `72c16268e5f9` |
| `agent/common.py` | `e8fabca2a802` |
| `agent/oneshot.py` | `10add0142f10` |
| `eval/multiturn.py` | `0cd8d4b64e75` |

**v1.1 results** (`eval/results/multiturn-mt2-v1.summary.md`, `multiturn-mt2-v1.1.summary.md`; no file above changed between the plan and the run):
1. Held: template text in 0 of 24 v1.1 corrected versions, 3 of 24 for v1.
2. Held: the separate review approved 20 (v1.1) and 19 (v1).
3. Did not hold for v1.1: offending words removed 24 and 24, but brand and price kept 23 (v1) and 21 (v1.1). In those conversations the corrected-caption field came back empty or as one word ("x"; v1 once "ignored") with the corrected text inside the answer, a fault in how the answer was filled in, not a rewrite that dropped the facts.
4. Held: turn-3 decisions right 22 and 22.
5. Held: US$0.0066 against US$0.0061 per conversation, 8% more.


## v1.2: advice fields filled in wrongly (written 21:58 MYT, before the v1.2 run)

**Why.** In 7 of the 72 stored advice turns (2 of 24 in the first multi-turn run, 2 of 24 for v1 and 3 of 24 for v1.1 on the 12 v1.1 items), tool-call markup was written into the `answer` field (`…</answer> <parameter name="revised_caption">…`), and in 5 of them `revised_caption` came back empty or as one word ("x", "ignored"). Strict tool schemas cannot require a minimum string length, so the check has to run in the agent's loop. `common.advice_problems` flags tool markup in any advice field and an empty or one-word corrected caption; run over the 72 stored turns it flags exactly those 7 and none of the other 65.

**Change (agent v1.2, `--version v1.2`).** v1.1 plus one step: when `submit_advice` fails `advice_problems`, the agent gets an error result naming the problems ("Each field holds only its own content … Call submit_advice again") and must submit again. This happens at most once per conversation; a second submission is accepted as it is. v1 and v1.1 are unchanged (checked offline: same tools, and v1.1 accepts a malformed submission at once).

**New items.** The 72 stored turns were used to find the problem and write the check, so v1.1 and v1.2 are compared on 12 new text ads in `testset/items_mt3.yaml` (6 Chinese, 6 English), written before any model saw them, answers fixed: 5 break two rules (longer answers), 9 advertiser versions fix everything and 3 still break a rule; two need a statement the advertiser has not given (alcohol strength; 本品不能代替药物).

**Run.** Both versions, 12 items × 3 runs each: `PY eval/multiturn.py --set mt3 --version v1.1 --repeat 3 --out multiturn-mt3-v1.1` and the same with `--version v1.2 --out multiturn-mt3-v1.2`. Same measures as before, plus "advice fields filled in wrongly" (`common.advice_problems` on the advice that was finally accepted) and, for v1.2, how often the check sent the advice back. Estimated cost about US$0.55.

**Expectations.**
1. Advice fields filled in wrongly: v1.2 0 of 36; v1.1 at least 1 of 36 (the stored rate is 7 of 72).
2. The check sends back at most 5 of 36 v1.2 advice turns; every sent-back turn is accepted on the second submission.
3. Brand and price kept: v1.2 at least as many as v1.1.
4. Separate review of the corrected version, offending words removed, turn-3 decisions, template text: no difference beyond 2 of 36.
5. v1.2 costs at most 10% more per conversation than v1.1.

| File | sha256 |
|---|---|
| `testset/items_mt3.yaml` | `c674805dac3c` |
| `agent/review_agent.py` | `249fa69f4c29` |
| `agent/common.py` | `66dd3efde143` |
| `agent/oneshot.py` | `10add0142f10` |
| `eval/multiturn.py` | `4e2b9a670b0d` |

**v1.2 results** (`eval/results/multiturn-mt3-v1.1.summary.md`, `multiturn-mt3-v1.2.summary.md`; no file above changed between the plan and the run; 1 of 72 conversations hit the rate limit and was run again with the same command):
1. Did not hold: advice fields filled in wrongly in 6 of 36 v1.2 conversations and 4 of 36 v1.1 ones.
2. Did not hold: the check sent back 7 of 36 advice turns, and 6 of the 7 second submissions had the same fault (tool markup in the answer, in 3 of them the caption empty again). Sending the call back does not fix it: the model repeats the malformed call.
3. Held: brand and price kept 33 and 33.
4. Held: separate review approved 31 (v1.2) and 32 (v1.1); offending words removed 36 and 36; turn-3 decisions right 36 and 36; template text 0 and 0.
5. Did not hold: US$0.0077 against US$0.0069 per conversation, 11% more (the extra call).


## v1.3: corrected version first, markup cleaned (written 22:15 MYT, before the v1.3 run)

**Why.** In all 17 of the 144 stored advice turns with the fault, the markup sits at the end of the `answer` field, where the model moves on to the next field: `…</answer> <parameter name="revised_caption">…`. Strict tool use writes the fields in schema order (`answer` first in every stored turn), so the long free-text answer comes before the short corrected caption. v1.2 showed that sending the call back does not help.

**Change (agent v1.3, `--version v1.3`).** v1.1 with two changes, no send-back: (a) `submit_advice` lists `revised_caption` and `revised_image_lines` before `answer` (same fields and descriptions); (b) `common.clean_advice` repairs a submitted advice: the answer is cut where tool markup starts, and a caption (or image lines) found in the markup is used only when the field itself is empty or one word. (b) was written after reading the stored turns; on all 144 it leaves no fault, so its result on new items is the check. v1, v1.1 and v1.2 are unchanged (checked offline: same tools and field order).

**New items.** `testset/items_mt4.yaml`: 12 new text ads (6 Chinese, 6 English), written before any model saw them, answers fixed: 5 break two rules, 9 advertiser versions fix everything and 3 still break a rule.

**Run.** 12 items × 3 runs each: `PY eval/multiturn.py --set mt4 --version v1.1 --repeat 3 --out multiturn-mt4-v1.1` and the same with `--version v1.3 --out multiturn-mt4-v1.3`. Measures as for v1.2, plus the fault in the advice as submitted (before the cleanup) and how often the cleanup changed something. Estimated cost about US$0.55; project total after it about US$2.45 of the US$3 limit.

**Expectations.**
1. Advice as submitted, fields filled in wrongly: v1.3 at most 1 of 36; v1.1 at least 2 of 36 (stored rate 17 of 144).
2. After the cleanup, fields filled in wrongly: v1.3 0 of 36.
3. Brand and price kept: v1.3 at least as many as v1.1.
4. Separate review of the corrected version, offending words removed, turn-3 decisions, template text: no difference beyond 2 of 36.
5. v1.3 costs at most 5% more per conversation than v1.1.

| File | sha256 |
|---|---|
| `testset/items_mt4.yaml` | `4abd97a18e0b` |
| `agent/review_agent.py` | `7c4949a5d23a` |
| `agent/common.py` | `df110e6027b2` |
| `agent/oneshot.py` | `10add0142f10` |
| `eval/multiturn.py` | `0101d4ef4efa` |

**v1.3 run status (22:20 MYT).** Interrupted: from 22:18 MYT every request returned "credit balance is too low". Stored: 26 of 36 v1.1 conversations (`multiturn-mt4-v1.1.jsonl`), no v1.3 conversation; failed requests are stored as errors and are run again by the same command. No file above has changed. The run resumes with the same commands once the API account has credit. Read so far, outside the expectations above: the frozen `common.clean_advice`, applied with no model call to the 26 stored v1.1 conversations, finds the fault in 4 and leaves it in none (`eval/advice_faults.py`, `results/advice-faults-2026-11-13.md`).

**v1.3 results** (`eval/results/multiturn-mt4-v1.1.summary.md`, `multiturn-mt4-v1.3.summary.md`; resumed on 14 November after the account was topped up, with the hashes above checked unchanged; 2 v1.3 conversations hit the rate limit and were run again by the same command):
1. Held: advice as submitted with fields filled in wrongly, v1.3 0 of 36, v1.1 6 of 36.
2. Held: after the repair, v1.3 0 of 36 (the repair changed nothing; applied offline to v1.1 it leaves 0 of 6).
3. Held: brand and price kept 36 (v1.3) and 34 (v1.1).
4. Held: separate review 35 and 35; offending words removed 36 and 36; turn-3 decisions right 36 and 36; template text 0 and 0.
5. Held: US$0.0068 against US$0.0069 per conversation.

## Harder set (written 14 November 2026, 17:12 MYT, before any model saw these ads)

**Why.** On the test split both model arms reached the ceiling on the decision (99% and 97%), so it could not separate them. The test ads are short and clean. This set is harder in four ways: long captions with the violation in the middle among allowed claims; three-frame screenshots of a short video, with the violation in one frame's subtitle or only in the picture; implied claims (a testimonial, "never lost a cent", a job-or-refund promise, body shame); and traps whose risky words are allowed (a sales ranking limited to one platform and month with its source, a national-standard grade, "Best before", "Nothing here is guaranteed", a compliant alcohol ad).

**Set.** `testset/items_hard_zh.yaml` and `items_hard_en.yaml`, split `hard`: 24 ads, 12 per language, 12 text and 12 image (8 of them three-frame video screenshots). 17 break a rule (19 labels: 16 in the words, 3 only in the picture), 7 are traps. Answers were fixed when the ads were written. The test split is unchanged; the flawed trap `zh-t21` stays as it is, and `zh-h10` is a cleaner trap for the same guide item (a grade set by a national standard). The images were drawn by `testset/render.py` (new `frames` layout; the 73 earlier images are byte for byte unchanged) and read by `testset/ocr_new.py` (same engine; the 73 earlier OCR entries are unchanged). `testset/load.py` now also reads the two new files; the dev and test items it returns are unchanged.

**Arms.** One prompt and the agent as in the test run (v1, the default), two runs each, with the same model, effort, prompts, tools and output format as the test run. **The sending method changes from the standard Messages API to the Message Batches API; model and parameters are unchanged** (`agent/common.py` `BatchPool`, `eval/run.py --batch`). Latency is therefore not measured; cost is counted at the batch price (half the list price). Batch mode was tried on 2 dev ads first (both arms, one run: 3 batches of about 2 minutes, every request succeeded, US$0.0034; `results/batch-smoke-dev.jsonl`). Also run, once each, at no API cost: the word list, CLIP and SigLIP 2 (image ads), SafeGuard-VL-RL (image ads) and the two text guardrails (text ads).

**Measures.** `eval/score.py` with `--split hard`, the same rules as the test run; text and image ads also separately. Per-ad outcomes are read for the long captions, the video frames and the traps.

**Expectations.**
1. Both model arms get a smaller share of decisions right here than on the test split (99% and 97%).
2. On the 8 violating text ads (16 runs per arm), each model arm rejects at least 14 runs.
3. The agent approves fewer of the 14 trap runs than one prompt (as on the test split).
4. The 3 violations only in the picture (`zh-h07`, `en-h06`, `en-h07`; 6 runs per arm): each model arm catches at least 5.
5. The word list rejects fewer than half of the 17 violating ads.
6. Each arm's cost per ad at the batch price is below its cost per ad in the test run (US$0.0010 and US$0.0023).

**Budget.** Estimated from the test run's cost per ad, scaled up by 1.3 to 1.5 for the longer inputs: about US$0.12 at the batch price, at most about US$0.19. The run stops at US$0.25 (`--budget 0.25`); the project cap is US$3.00 and US$2.4593 is spent.

**Run.**
```
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/run.py --split hard --repeat 2 --out hard-2026-11-14 --budget 0.25 --batch
PY baselines/wordlist.py --split hard
PY baselines/clip_zeroshot.py --split hard
PY baselines/safeguard_vl.py --split hard
PY baselines/text_guards.py --model qwen3guard --split hard ; PY baselines/text_guards.py --model granite --split hard
PY eval/score.py eval/results/hard-2026-11-14.jsonl eval/results/wordlist-hard.jsonl --split hard --out eval/results/hard-2026-11-14.summary.md
```

**Frozen files (sha256 of LF-normalised contents, first 12 characters).**

| File | sha256 |
|---|---|
| `testset/items_hard_zh.yaml` | `e9e00acf8fd1` |
| `testset/items_hard_en.yaml` | `163b6b9fabbc` |
| `testset/load.py` | `802e0dd16910` |
| `testset/render.py` | `cde1b50d995a` |
| `testset/ocr_new.py` | `4faed232abe9` |
| `testset/ocr.json` | `cc453f1aa012` |
| `agent/common.py` | `806c01d705da` |
| `agent/oneshot.py` | `10add0142f10` |
| `agent/review_agent.py` | `7c4949a5d23a` |
| `eval/run.py` | `b321fe5fb4b7` |
| `eval/score.py` | `284941b328a8` |
| `baselines/wordlist.py` | `eb79ffdb8dcb` |
| `baselines/clip_zeroshot.py` | `fe4b6ba68bdb` |
| `baselines/safeguard_vl.py` | `4e8c4f0889a8` |
| `baselines/text_guards.py` | `90eaa091dfb0` |
| `policies/clauses.yaml` | `27cd8a53cea1` |
| `policies/library.py` | `27bb9ac4d470` |
| `testset/images/*-h*.png` (12 files; each name, then its bytes, in name order) | `f7357623826a` |

**Results** (run 14 November, 17:12 to 18:35 MYT). Checked against the table above after the run: no frozen file changed.

- **Model arms.** 6 batches of 96, 48, 40, 12, 3 and 2 requests. Each took about 2 minutes, 12.7 minutes in all, and every request succeeded. Cost: US$0.0917 at the batch price. Outputs: `results/hard-2026-11-14.jsonl`. Summary: `results/hard-2026-11-14.summary.md`, with text and image ads separately in `.text.summary.md` and `.images.summary.md`.
- **Local arms.** Each ran once, with no errors.
- **Per-ad table.** `eval/hard_report.py` writes it to `results/hard-2026-11-14.ads.md`, grouped by long caption, video frames and single image. The script was written before the run and only reads stored outputs.

Outcomes of the expectations:

1. Did not hold. Both arms got all 48 decisions right (100%), more than on the test split.
2. Held: 16 of 16 for each arm.
3. Did not hold: both arms approved all 14 trap runs.
4. Held: 6 of 6 for each arm.
5. Held: 5 of 17 (29%).
6. Held, but only because of the batch price: US$0.00058 and US$0.00133 per ad. At the list price these would be US$0.0012 and US$0.0027, 11% and 17% above the test run. The answers are longer: about 980 and 1,370 output tokens per ad, against 750 and 1,130. The agent also reads more: 19,800 input tokens per ad against 17,200.

## Real ads from published regulator rulings (written 14 November 2026, 23:17 MYT, before any model saw these ads)

**Why.** On the test split and on the harder set, both model arms reached the ceiling on the decision, so neither set separates them; both sets were written by the same person. This set uses real ads and an answer fixed by someone else: rulings published by the UK Advertising Standards Authority (ASA), which says either "Upheld" (the ad broke the UK advertising code) or "Not upheld" (it did not).

**Set.** `testset/items_real_en.yaml`, split `real`: 30 English text items, built by `testset/build_real.py` from the "Ad description" section of 30 rulings (the ad's words, plus the ASA's description of any pictures or video). Advertiser, product, competitor and private-person names are replaced with placeholders such as [Brand]; curly quotes become straight quotes; nothing else changes. The ruling text is not redistributed; `build_real.py` lists the ruling links.
- 23 Upheld rulings, the answer is reject. Taken from the 235 Upheld rulings published from 1 January to 11 November 2026, most recent first, at most 4 for each of six groups: medical claims, weight and body image, investment returns, comparisons with competitors, ratings and superlatives, and alcohol. Skipped: same-day near-duplicates; rulings whose issues fall outside the nine categories (prices, environmental claims, less-healthy food placement, prescription-only medicines, gambling, game footage); pet products. The weight group had only 3 eligible rulings.
- 7 Not upheld rulings, the answer is approve. These are all the Not upheld rulings from 1 January 2025 to 11 November 2026 whose issue falls inside the nine categories (4 of 37), plus the 3 such rulings from 2024 (of 14).
- Categories come from the issues the ASA upheld, mapped to the nine categories by a rule fixed before the run (`testset/real-sources.md`). Issues outside the nine categories get no label. 27 labels: MEDICAL 6, ALCOHOL 4, DATA 4, GUARANTEE 4, DISPARAGE 3, WEIGHT 3, ABSOLUTE 2, BEFORE_AFTER 1.
- 8 items are marked *evidence-dependent*: the ruling turned on evidence the ad itself does not show, such as whether a rating, a statistic or a price check was true (`en-r13`, `r14`, `r16`, `r17`, `r18`, `r19`, `r25`, `r27`).

**What this set can and cannot show.** The ASA applies the UK code. The arms apply the English policy library, which is TikTok's ad policy. So the answer is the regulator's decision, not a decision under the arms' own rules, and some disagreement is expected from that alone. The input is the regulator's written description of the ad, not the ad itself. Rulings from 2024 and 2025 may be in the model's training data; the placeholders make a ruling harder to recognise but do not rule this out.

**Arms.** One prompt and the agent as in the test run and the harder set (v1, the default), two runs each, same model, effort, prompts, tools and output format, sent through the Message Batches API as on the harder set. Also run once each at no API cost: the word list and the two text guardrails (Qwen3Guard-Gen-4B, Granite Guardian 3.3 8B). CLIP, SigLIP 2 and SafeGuard-VL are not run: there are no images.

**Measures.** `eval/score.py --split real`, same rules as before. `eval/real_report.py` (written before the run, reads stored outputs only) gives every ad's outcome per arm and per run, grouped by the six groups and by the ASA decision, for all 30 ads and again without the 8 evidence-dependent ones.

**Expectations.**
1. Each model arm gets fewer than 90% of its 60 decisions right (the harder set was 100%).
2. On the 23 Upheld ads (46 runs per arm), each model arm rejects at least 40 runs.
3. On the 7 Not upheld ads (14 runs per arm), each model arm wrongly rejects at least 4 runs.
4. The agent approves fewer Not upheld runs than one prompt (as on the test split).
5. The two model arms reach different decisions on at least 3 of the 60 (ad, run) pairs; on the harder set they agreed on all 48.
6. Each model arm gets a larger share of decisions right without the 8 evidence-dependent ads than with them.
7. The word list and Qwen3Guard each reject fewer than half of the 23 Upheld ads.

**Budget.** The harder set cost US$0.0019 per ad and run for both arms together at the batch price. These inputs are longer, so allowing 1.25 times that: about US$0.14 for 30 ads and 2 runs, at most about US$0.20. The run stops at US$0.25 (`--budget 0.25`). The project cap is US$3.00 and US$2.5510 is spent.

**Run.**
```
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/run.py --split real --repeat 2 --out real-2026-11-14 --budget 0.25 --batch
PY baselines/wordlist.py --split real
PY baselines/text_guards.py --model qwen3guard --split real ; PY baselines/text_guards.py --model granite --split real
PY eval/score.py eval/results/real-2026-11-14.jsonl eval/results/wordlist-real.jsonl eval/results/qwen3guard-real.jsonl eval/results/granite-guardian-real.jsonl --split real --out eval/results/real-2026-11-14.summary.md
PY eval/real_report.py
```

**Frozen files (sha256 of LF-normalised contents, first 12 characters).** `agent/*`, `eval/score.py`, the baselines and the policy files are the same as for the harder set. `testset/load.py` and `eval/run.py` changed only to accept the new split; the dev, test and harder items `load.py` returns are unchanged, and the offline tests pass (8/8).

| File | sha256 |
|---|---|
| `testset/items_real_en.yaml` | `eafbc1de4a04` |
| `testset/build_real.py` | `05458c1864d0` |
| `testset/load.py` | `8b6074f41644` |
| `agent/common.py` | `806c01d705da` |
| `agent/oneshot.py` | `10add0142f10` |
| `agent/review_agent.py` | `7c4949a5d23a` |
| `eval/run.py` | `7419e6baefbc` |
| `eval/score.py` | `284941b328a8` |
| `eval/real_report.py` | `aefa1b1b2186` |
| `baselines/wordlist.py` | `eb79ffdb8dcb` |
| `baselines/text_guards.py` | `90eaa091dfb0` |
| `policies/clauses.yaml` | `27cd8a53cea1` |
| `policies/library.py` | `27bb9ac4d470` |

**Results** (English run 14 November 2026, started 23:18 MYT). Checked against the table above after the run: no frozen file changed.

- **Model arms.** 7 batches of 120, 60, 58, 40, 19, 3 and 1 requests. Each took about 2 minutes, and every request succeeded. Cost: US$0.2388 at the batch price. This is above the estimate (US$0.14, at most about US$0.20) and below the US$0.25 stop: the agent made 4.0 calls per ad (3.2 on the harder set) and cost US$0.0030 per ad. Outputs: `results/real-2026-11-14.jsonl`. Summary: `results/real-2026-11-14.summary.md`. Per-ad table: `results/real-2026-11-14.ads.md` (private: it links the rulings next to the arms' answers).
- **Local arms.** The word list, Qwen3Guard and Granite Guardian each ran once with no errors (Granite on the CPU at about two minutes per ad, finished on 15 November). No expectation was written for Granite Guardian. It rejected 9 of 23 Upheld ads and approved 5 of 7 Not upheld ones (14 of 30 right).

Outcomes of the expectations:

1. Held: 49 of 60 (82%) for one prompt and 51 of 60 (85%) for the agent.
2. Held: one prompt rejected 43 of 46 Upheld runs, the agent 46 of 46.
3. Held: one prompt wrongly rejected 8 of 14 Not upheld runs, the agent 9.
4. Held, by one run: the agent approved 5 of 14 Not upheld runs, one prompt 6.
5. Held: the arms differ on 4 of 60 pairs (`en-r03` run 2, `en-r19` both runs, `en-r25` run 2).
6. Held: without the 8 evidence-dependent ads, 37 of 44 (84%) and 38 of 44 (86%).
7. Held: the word list rejected 6 of 23 Upheld ads, Qwen3Guard 11 of 23.

## Real Chinese ads from published enforcement cases (written 14 November 2026, 23:36 MYT, before any model saw these ads)

**Why.** The Chinese counterpart of the ASA set above, with answers fixed by Chinese regulators or courts.

**Set.** `testset/items_real_zh.yaml`, split `real`, 16 Chinese text items, built by `testset/build_real_zh.py`. Every quoted fragment is checked to appear verbatim in the saved source text; brand names are replaced with placeholders. Sources are not redistributed; the script lists the links.
- 12 penalised ads, answer reject: every case in the State Administration for Market Regulation's typical-case releases of 31 January and 21 July 2026 that quotes the ad's words and whose quoted words fall in the nine categories. Each item keeps the product type (for example "普通食品", which matters under the Advertising Law) and the quoted words; the release's own verdict words are left out. Labels: MEDICAL 11, ABSOLUTE 1, DATA 1. These items hold only the words the regulator singled out, so they are easier than whole ads.
- 4 ads found lawful, answer approve: published cases in which a regulator or a court decided that a superlative did not break Article 9(3) (an award name containing "最佳", an internal comparison "最好选择", an aim "打造……第一品牌", and "完美" as artistic exaggeration). They date from 2015 to 2019, before SAMR's 2023 enforcement guide on superlatives, which is in the policy library; the article itself is unchanged.
- 3 items are evidence-dependent (`zh-r11`, `r13`, `r14`).
- The whole release of 13 October 2026 (seven cases on discrimination, vulgarity, superstition and use of state organs' names) falls outside the nine categories and is not used. Details: `testset/real-sources.md`.

**Arms.** As for the English real ads: one prompt and the agent (v1), two runs each, Message Batches API. The word list was run on these items before this section was written (it is deterministic and calls no model), so no expectation is written for it. The two text guardrails run afterwards.

**Expectations.**
1. On the 12 penalised ads (24 runs per arm), each model arm rejects at least 22 runs.
2. On the 4 ads found lawful (8 runs per arm), each model arm wrongly rejects at least 4 runs: all four use a word the policy library flags, and the 2023 guide is stricter than these older decisions.
3. The agent approves no more of the 8 lawful runs than one prompt.
4. The two model arms reach different decisions on at least 2 of the 32 (ad, run) pairs.

**Budget.** On the harder set's Chinese ads the two arms together cost US$0.0016 per ad and run at the batch price; these items are as short. Allowing 1.5 times that: about US$0.08 for 16 ads and 2 runs. The run stops at US$0.15 (`--budget 0.15`), so the project stays under US$3.00: US$2.7898 is spent (the English real ads cost US$0.2388, more than the US$0.14 estimated, mainly because the agent made 4.0 calls per ad there).

**Run.**
```
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/run.py --split real --ids zh-r01,zh-r02,zh-r03,zh-r04,zh-r05,zh-r06,zh-r07,zh-r08,zh-r09,zh-r10,zh-r11,zh-r12,zh-r13,zh-r14,zh-r15,zh-r16 --repeat 2 --out real-zh-2026-11-14 --budget 0.15 --batch
PY eval/score.py eval/results/real-zh-2026-11-14.jsonl --split real --out eval/results/real-zh-2026-11-14.summary.md
PY eval/real_report_zh.py
```
`--ids` limits the run to the 16 Chinese items (the English items share the split).

**Frozen files (sha256 of LF-normalised contents, first 12 characters).** `eval/real_report.py` changed after the English run only to read English items (Chinese items now share the split); its English output is unchanged.

| File | sha256 |
|---|---|
| `testset/items_real_zh.yaml` | `b8c21388c70a` |
| `testset/build_real_zh.py` | `e9d4e9475d6b` |
| `testset/load.py` | `8b6074f41644` |
| `agent/common.py` | `806c01d705da` |
| `agent/oneshot.py` | `10add0142f10` |
| `agent/review_agent.py` | `7c4949a5d23a` |
| `eval/run.py` | `7419e6baefbc` |
| `eval/score.py` | `284941b328a8` |
| `eval/real_report_zh.py` | `e4520ee727a7` |
| `baselines/wordlist.py` | `eb79ffdb8dcb` |
| `baselines/text_guards.py` | `90eaa091dfb0` |
| `policies/clauses.yaml` | `27cd8a53cea1` |
| `policies/library.py` | `27bb9ac4d470` |

**Results** (Chinese run 14 November 2026, started 23:37 MYT). Checked against the table above after the run: no frozen file changed.

- **Model arms.** 5 batches of 64, 32, 31, 10 and 4 requests, each about 2 minutes, every request succeeded. Cost: US$0.0739 at the batch price, within the estimate. The project has spent US$2.8637 of US$3.00. Outputs: `results/real-zh-2026-11-14.jsonl`. Summary: `results/real-zh-2026-11-14.summary.md`. Per-ad table: `results/real-zh-2026-11-14.ads.md` (private).

Outcomes of the expectations:

1. Held: both arms rejected 24 of 24 penalised runs.
2. Held: one prompt wrongly rejected 5 of the 8 lawful runs, the agent 6.
3. Held: the agent approved 2 of 8 lawful runs, one prompt 3.
4. Did not hold: the arms differ on 1 of 32 pairs (`zh-r13` run 1, the award name, which one prompt approved once).

The two text guardrails ran afterwards, once each, with no errors; no expectation was written for them. Qwen3Guard rejected 7 of 12 penalised ads and approved all 4 lawful ones (11 of 16 right); Granite Guardian rejected 10 of 12 and approved 3 of 4 (13 of 16).

## Memory: earlier decisions shown to the agent (written 16 November 2026, 20:34 MYT, before any model saw these ads)

**Why.** A platform reviews the same advertiser's ads again and again, and many ads repeat a claim that was already decided. Without memory, each review starts from the clauses alone, so a grey case can be decided one way today and another way tomorrow. The question: when the agent is shown earlier confirmed decisions on similar ads, does it decide more consistently, and how often does an earlier decision mislead it?

**Memory.** `agent/memory.py`. A store of confirmed decisions (the ad's words, the decision, each violation's category, clause and quoted words, a one-line reason, the advertiser, the date). For a new ad, BM25 over the stored ads of the same language returns the 3 most similar records, and up to 2 more of the same advertiser's most recent records are added. The records are appended to the review request, and one step is added to the system prompt: decide the same way when the ad makes the same claim in the same way; the clauses decide when anything differs. The model only reads the store; nothing in a review writes to it. No embedding model and no extra model call. Why this design and what existing memory libraries were considered: `product/PRD.md`, section 6.4.

**Set.** Split `memory`: `testset/items_memory_zh.yaml` and `items_memory_en.yaml`, 24 fictional text ads (12 Chinese, 12 English), and `testset/precedents.yaml`, a store of 36 earlier decisions (18 per language). Ads, store records, answers and reasons were written together, before any model saw them; answers were fixed at writing. Each ad was written against one store record from the same advertiser.

| Type | Ads | The earlier decision | Right call |
|---|---|---|---|
| follow-reject | 6 | rejected a claim; the new ad makes the same kind of claim in other words or for another product | reject, same clause |
| follow-approve | 6 | approved a grey case (a registered trademark with a superlative in it, a comparison with the advertiser's own products, a dated first release, a delivery guarantee, a refund trial) | approve |
| fixed | 4 | rejected; the advertiser has removed the problem | approve |
| qualified | 2 | rejected an unqualified claim; the new ad adds the qualifiers and the source that make it lawful | approve |
| history | 2 | rejected another ad of this advertiser; the new ad is clean | approve |
| dropped | 2 | approved because of a qualifier or a required statement; the new ad leaves it out | reject |
| new-violation | 2 | approved; the new ad repeats it and adds a violating claim | reject |

The first two types (12 ads) are "follow": the earlier decision applies. The other five (12 ads) are "distinguish": applying the earlier decision gives the wrong call. Answers: 10 reject, 14 approve.

**Arms.** The agent (v1.3) without memory and with memory. Same model (`claude-haiku-5-5`), same tools, same output format. Both arms are told the advertiser account; only the memory arm gets the records and the added step. Three runs each, Message Batches API. The store is fixed for the whole run, so every run of an ad sees the same records.

**Checked before the run, with no model.** `memory.lookup` returns the paired record for 24 of 24 ads (rank 1 for 20, rank 2 for 3, rank 4 for 1). So this test measures what the agent does with a relevant earlier decision in front of it, not how well lookup works on a large store. One practice ad (`en-d01`, split dev) was reviewed once by each arm to check the code path (US$0.0041, standard price); no ad of the memory split was sent to a model.

**What is measured** (`eval/memory_report.py`).
- Decisions right, per arm, for follow and distinguish ads and for each type.
- Consistency: the number of ads on which all three runs reach the same decision.
- Follow-reject ads: how often the clause and the category of the earlier decision are cited.
- Memory misleading the agent: on distinguish ads, how often the arm repeats the earlier decision.
- Cost per review at the batch price, and model calls per review.

**Expectations.**
1. Follow-approve (18 runs per arm): without memory the agent wrongly rejects at least 3 runs; with memory at most 1.
2. Follow-reject (18 runs per arm): both arms reject at least 17. With memory the earlier clause is cited in at least 17 runs, and at least as often as without.
3. Distinguish (36 runs per arm): with memory at least 34 are right, and no more than 1 fewer than without memory; the memory arm repeats the earlier decision in at most 2 runs.
4. All three runs agree on at least as many ads with memory as without.
5. Over all 72 runs per arm, the memory arm has at least 3 more decisions right.
6. A review with memory costs between 1.1 and 1.6 times a review without.

**Not tested.** A wrong record in the store (the agent would probably follow it); retrieval from a large store; image ads; records the agent wrote itself. NOT RUN.

**Budget.** On the practice ad a review cost US$0.0018 without memory and US$0.0023 with, at the standard price. At the batch price, 24 ads and 3 runs of both arms come to about US$0.15; allowing 1.5 times that, US$0.22. The run stops at US$0.30 (`--budget 0.30`). The project has spent US$2.8678; this run takes it past the earlier US$3.00 line, within the US$0.50 allowed for this test.

**Run.**
```
AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env PY eval/run.py --split memory --arms agent,agent_memory --version v1.3 --repeat 3 --out memory-2026-11-16 --budget 0.30 --batch
PY eval/memory_report.py eval/results/memory-2026-11-16.jsonl
PY eval/score.py eval/results/memory-2026-11-16.jsonl --split memory --out eval/results/memory-2026-11-16.summary.md
```

**Frozen files (sha256 of LF-normalised contents, first 12 characters).**

| File | sha256 |
|---|---|
| `testset/items_memory_zh.yaml` | `76259b18ed3c` |
| `testset/items_memory_en.yaml` | `01b7507d3c35` |
| `testset/precedents.yaml` | `3048fd65b24d` |
| `testset/load.py` | `ade9618eb203` |
| `agent/common.py` | `806c01d705da` |
| `agent/review_agent.py` | `6b89f97dd307` |
| `agent/memory.py` | `855260842ef4` |
| `eval/run.py` | `1ba63284f017` |
| `eval/score.py` | `284941b328a8` |
| `eval/memory_report.py` | `accf9f67aeb3` |
| `policies/clauses.yaml` | `27cd8a53cea1` |
| `policies/library.py` | `27bb9ac4d470` |

**Results** (run 16 November 2026, started 20:35 MYT). Checked against the table above after the run: no frozen file changed.

- 6 batches of 144, 144, 88, 29, 5 and 1 requests; the second took 16.9 minutes, the others about 2 minutes each; every request succeeded. Cost: US$0.1575 at the batch price, against about US$0.15 estimated. With the practice ad (US$0.0041) the project has spent US$3.0253. Outputs: `results/memory-2026-11-16.jsonl`. Report: `results/memory-2026-11-16.report.md`. Standard scores: `results/memory-2026-11-16.summary.md`.
- Decisions right: 69 of 72 without memory, 72 of 72 with. The whole difference is one ad, `en-m04` (a next-day delivery guarantee): without memory the agent rejected it in all three runs, with memory it approved it in all three.
- Distinguish ads: 36 of 36 right in both arms; the memory arm repeated the earlier decision in 0 of 36 runs.
- All three runs agreed on 24 of 24 ads in both arms.
- A review cost US$0.00116 without memory (3.0 calls, 17,852 input tokens) and US$0.00103 with (2.7 calls, 15,409 input tokens): with the earlier decisions in front of it the agent searched the policy library less (2.0 searches per review against 2.6).

Outcomes of the expectations:

1. Held: on follow-approve ads the agent without memory wrongly rejected 3 of 18 runs (all `en-m04`); with memory 0.
2. Held: both arms rejected 18 of 18 follow-reject runs, and both cited the earlier decision's clause in 18 of 18.
3. Held: with memory 36 of 36 distinguish runs were right, the same as without; the earlier decision was repeated in 0 runs.
4. Held, with nothing between the arms: 24 of 24 ads in both.
5. Held, at the threshold: 3 more decisions right with memory (72 against 69).
6. Did not hold: a review with memory cost 0.89 times a review without, not 1.1 to 1.6 times.

**Timestamp corrected after the run.** The heading of this section first gave the time of writing as 12:35 MYT; that was the UTC clock. The section was saved at 20:34 MYT, one minute before the run started, and nothing else in it was changed.
