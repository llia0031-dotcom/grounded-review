# Ad review agent: evaluation brief

*13 November 2026 · 96 held-out ads (48 Chinese, 48 English), and 24 harder ads on 14 November, with answers fixed when the ads were written (synthetic ads, fictional brands) · 46 real ads on 14 November, with answers from regulator and court decisions · a memory test of 24 new ads on 16 November · this is not a measurement on live traffic*

## Question

An ad reviewer has to say more than "reject": which rule the ad breaks and which words break it, so that a second reviewer can check the call quickly and the advertiser knows what to change. Does an agent that reads the image, looks up the clauses and checks its own quotes do this better than one prompt that is given everything at once? And how do both compare with a banned-word list, with zero-shot image models and with open guardrail models?

## Where this fits

This project belongs to a set built on one idea: an AI should show its evidence. It is the set's judgment scenario: a call on an ad, backed by the ad's words and the clause's words. It uses [evidence-check](https://github.com/llia0031-dotcom/evidence-check) as its checking tool, and every quote below was run through that script. It is also the core of the [evidence-backed labelling pipeline](https://github.com/llia0031-dotcom/grounded-labelling-pipeline). The pipeline routes ads that fail the check, or that the agent is unsure about, to review, and turns reviewed ads into new test items.

## Setup

**Policies.** Chinese ads are reviewed against the Advertising Law of the PRC (2021 amendment; text from the Beijing municipal market regulator, checked article by article against the Shanghai regulator's copy) and the national regulator's 2023 enforcement guide on absolute terms, which says when words such as 最 or 第一 are allowed. English ads are reviewed against the global sections of five TikTok Advertising Policies pages (misleading and false content, weight management, alcohol, deceptive practices, financial services; the policy text is used locally and not reproduced here). The library has 32 clauses; 12 of them match no test item and are there to be retrieved by mistake.

**Test set.** 96 ads (39 text, 57 image), written for this evaluation with the answers fixed at the time of writing; dev set of 24 ads used to build the harness. 62 ads break at least one rule (65 labelled violations, 71 after the answer-key audit of 18 November described below, in nine categories: absolute claims, medical claims, guaranteed outcomes, disparaging competitors, data without a source, alcohol, weight and body image, before-and-after comparisons, national flag). 56 violations are in the words, 8 only in the picture (national flag, people drinking, before-and-after panels), 1 is a missing required statement. 34 ads are compliant, 30 of them traps: words that look risky but are allowed, each with the clause or guide item that allows them (最佳饮用温度 as a serving tip, a brand's comparison with its own older model, a sales ranking limited to one platform and month with its source, "the cure for boring commutes", "Before & After School Club"). 16 harder ads were added after the dev runs and before any model saw the test split: a zero for an O in "N0.1", Unicode bold letters, a patient testimonial that implies a cure, small print at the bottom of an image, a claim split between caption and image, risky words inside a negation, a small flag in a corner.

Images are drawn by a script: posters and banners with a product drawing, before-and-after panels, the national flag drawn to its published geometry, and three illustrated drinking scenes. Because the words in every image are known, OCR and quotes are checked against the true text. OCR (RapidOCR, PP-OCRv6 medium models) on the 73 dev and test images: character error rate 1.2% over 2,749 characters, mostly reading order (the brand printed on the pack read into a line of ad text); real misreads on 2 images (焕 read as 煥; a price read as "6L夫"). Median OCR time 4.4 s per image on CPU.

**Arms.**

| Arm | Input | Method |
|---|---|---|
| One prompt | image, caption, OCR text, whole policy library | one request, structured output |
| Agent | image and caption | tools: OCR, clause search (BM25), get clause, quote check, submit; up to 10 rounds |
| Word list | caption + OCR text | Chinese: an open e-commerce compliance rule list (2,104 rules, block-level groups); English: the signal lists of AdLint (MIT) |
| CLIP ViT-B/32, SigLIP 2 base | image only | zero-shot: the nearest of nine category prompts and an "ordinary ad" prompt |
| SafeGuard-VL-RL (open image guardrail, 8B, Apache-2.0) | image only | the nine categories written as its policy; it answers Safe / Unsafe with a category; greedy decoding, one run on CPU |
| ShieldGemma 2 | — | **NOT RUN**: downloading it requires signing in and accepting the model's terms of use; SafeGuard-VL-RL takes its place |
| Qwen3Guard-Gen-4B (open text guardrail, Apache-2.0) | text ads, caption | fixed general safety categories; it cannot take a custom policy; Unsafe or Controversial counts as reject; greedy decoding, one run on CPU |
| Granite Guardian 3.3 8B (open text guardrail, Apache-2.0) | text ads, caption | the nine categories written as its criterion; it answers yes / no; its model card says it was trained on English only; greedy decoding, one run on CPU |
| gpt-oss-safeguard-20b | — | **NOT RUN**: its model card asks for a 16 GB GPU; this laptop has 8 GB |

Both model arms use Claude Haiku 5.5 at effort `medium`, the same category list and the same output: category, clause id, the ad's words, what the picture shows, the clause's words, and an explanation. The one-prompt arm also gets the OCR text, so the difference between the two arms is the agent's way of working (looking clauses up, checking its own quotes, more steps), not access to the image text. Quotes are checked with the evidence-check script: the ad's words against the true words of the ad, the clause's words against the text of the clause the answer cites. Each model arm ran twice. The plan, predictions and file hashes were fixed before the run in [`PREREGISTRATION.md`](PREREGISTRATION.md).

## Results

**All 96 ads, two runs each** (word list: one run; it is deterministic). For the two model arms every count in the tables of this report is over decisions, two per ad: 96 ads give 192 decisions, and the 62 violating ads give 124. If every ad were rejected, 65% of decisions would be right.

| | one prompt | agent | word list |
|---|---|---|---|
| Decision right (approve / reject) | 191/192 (99%) | 187/192 (97%) | 41/96 (43%) |
| Violating ads rejected | 124/124 | 124/124 | 16/62 (26%) |
| Traps approved | 59/60 (98%) | 55/60 (92%) | 21/30 (70%) |
| Exactly the labelled categories, nothing more | 161/192 (84%) | 173/192 (90%) | 38/96 (40%) |
| Violations found in a picture only | 16/16 | 16/16 | 0/8 |
| Right clause cited, when the category was found | 129/129 | 129/129 | n/a |
| Offending words located, when found | 111/111 | 110/111 | 12/14 |
| Ad quotes passing the checker | 182/186 (98%) | 175/178 (98%) | n/a |
| Clause quotes passing the checker (within the cited clause) | 224/225 | 200/200 | n/a |
| Cost per ad | US$0.0010 | US$0.0023 | 0 |
| Median time per ad, including OCR | 7.9 s | 14.2 s | 3.8 s |
| API calls per ad | 1.0 | 3.1 | 0 |
| Same decision in both runs | 95/96 | 95/96 | |
| Same categories in both runs | 88/96 | 87/96 | |

**The 57 image ads, all arms.** The model arms ran twice (114 decisions); the other arms ran once (57). Always rejecting would get 65% right here too.

| | one prompt | agent | word list | CLIP | SigLIP 2 | SafeGuard-VL |
|---|---|---|---|---|---|---|
| Decision right | 113/114 (99%) | 111/114 (97%) | 27/57 (47%) | 36/57 (63%) | 35/57 (61%) | 49/57 (86%) |
| Violating ads rejected | 74/74 | 74/74 | 9/37 | 23/37 | 26/37 | 32/37 |
| Traps approved | 35/36 | 33/36 | 16/18 | 11/18 | 7/18 | 15/18 |
| Exactly the labelled categories | 90/114 (79%) | 101/114 (89%) | 26/57 (46%) | 26/57 (46%) | 21/57 (37%) | 41/57 (72%) |
| Picture-only violations found | 16/16 | 16/16 | 0/8 | 4/8 | 4/8 | 5/8 |
| Median time per ad | 9.4 s | 16.6 s | 4.4 s | 0.1 s | 0.2 s | 178.3 s |

Times for the local arms are on a laptop CPU (16 threads); the word list's time is the OCR. SafeGuard-VL reads images at up to 640×640 pixels.

**The 39 text ads, every arm that reads text** (19 Chinese, 20 English; 25 violating, 12 traps). Always rejecting would get 64% right.

| | one prompt | agent | word list | Qwen3Guard | Granite Guardian |
|---|---|---|---|---|---|
| Decision right | 78/78 (100%) | 76/78 (97%) | 14/39 (36%) | 22/39 (56%) | 28/39 (72%) |
| Decision right, Chinese | 38/38 | 38/38 | 8/19 | 8/19 | 11/19 |
| Decision right, English | 40/40 | 38/40 | 6/20 | 14/20 | 17/20 |
| Violating ads rejected | 50/50 | 50/50 | 7/25 | 8/25 | 15/25 |
| Traps approved | 24/24 | 22/24 | 5/12 | 12/12 | 11/12 |
| Median time per ad | 4.5 s | 11.0 s | <0.1 s | 24.5 s | 50.2 s |

Qwen3Guard answered Unsafe for none of the 39 ads; all its rejections are Controversial. Counting Unsafe only, it rejects nothing (14/39 right). Every answer of both guardrails: [`results/text-guards-test.md`](results/text-guards-test.md).

Per-category precision and recall: [`results/test-2026-11-13.summary.md`](results/test-2026-11-13.summary.md) and [`results/test-2026-11-13.images.summary.md`](results/test-2026-11-13.images.summary.md).

**Multi-turn task** (agent only; 12 ads with a revision written in advance, 2 runs). After its review, the advertiser asks what is wrong and how to fix it; the agent answers and writes a corrected caption and image text. The advertiser then submits a version of their own, which the agent reviews.

| | 24 conversations |
|---|---|
| Turn 1 decision right | 24/24 |
| Corrected version drops every labelled offending phrase | 24/24 |
| Corrected version keeps brand and price | 24/24 |
| Corrected version approved by a separate one-prompt review (image redrawn with the new words, OCR run again) | 19/24 (9 and 10 per run) |
| Advertiser's version: decision right | 22/24 |
| Agent cost per three-turn conversation / median time | US$0.0065 / 24 s |

## What the results show

1. **On these ads both model arms are at the ceiling for the decision.** Every violating ad was rejected by both, in both runs, including all eight picture-only violations, the small print, the small flag and the 16 harder ads (32/32 decisions right for each arm). The decision gap between them is four runs out of 192, and both agree with themselves on 95 of 96 ads across runs. The test set does not separate the two arms on catching violations.
2. **They differ on precision.** The one-prompt arm adds a second category to the same words more often: 30 extra categories against 16 for the agent, most of them "guaranteed outcome" next to a weight or medical claim. Read one by one, 23 of the one-prompt arm's 30 and 13 of the agent's 16 are defensible under a clause in the library (TikTok's "Misleading claims" section covers both absolute terms and promised results), 7 and 3 are wrong (for example a performance claim on a vacuum flask treated as false advertising with no evidence that it is false). The agent, in turn, rejected 5 trap runs against 1: twice a delivery-time guarantee, twice "国家级非物质文化遗产代表性项目" (a state heritage listing of the craft, shown above the brand's teaware), once a reading that a three-product set shown as one product is inconsistent. The heritage item is a weak trap: the guide's exemption covers titles the product holds, and the ad does not say the maker holds this one; both arms raised that point. [Attribution table](results/attribution-2026-11-13.md).
3. **Quotes are verbatim; the checker's minimum length is the only thing that fails.** Of 7 ad quotes that did not pass, all were verbatim but shorter than the checker accepts (降血脂, "12% APY"). One clause quote from the one-prompt arm joined two list items into one sentence. Both arms cited an accepted clause for every violation they found. With the OCR text in its prompt, the one-prompt arm quotes as accurately as the agent that checks its quotes; checking adds little when the text is already given.
4. **The agent costs 2.2 times as much and takes 1.8 times as long.** It makes about three calls per ad and reads clause text through tools; the one-prompt arm sends the library each time (about 6,600 input tokens) in one call. At these prices both are under a quarter of a cent per ad.
5. **The multi-turn task shows where the agent is weak.** It always removed the offending words and kept the product facts, but in 3 of 24 conversations its corrected version contained template placeholders ("Licensed by [licensing authority, licence number]", "Win [non-alcohol prize]"), which the separate review rejected as unfinished. In 2 more, the separate review objected to the product name 稳盈计划 ("steady gain plan") as implying guaranteed returns, while the agent itself approved the same name in turn 3. In turn 3 it caught all 10 advertiser versions that still broke a rule. Its 2 wrong decisions came from an error in the test set: that revision changed the image text but kept the old product name in the caption, and the agent flagged the mismatch.
6. **The word list and the zero-shot image models are below "always reject".** The word list rejected 16 of 62 violating ads. It found none of the disparagement, unsourced-data, alcohol or flag violations: flags and drinking scenes are pictures, its disparagement and alcohol patterns (吊打, 劝酒 and the like) do not occur in these ads, and the English signals have no entry for "best" or "#1". It also flagged 9 of 30 traps (最佳 in a serving tip, 最好 inside a negation, 治愈系 as a style word, "cure" in "the cure for boring commutes"). CLIP and SigLIP 2 each found 4 of the 8 picture-only violations (both before-and-after panels; CLIP the two large flags, SigLIP 2 one flag and one drinking scene) but cannot read ad copy; as reviewers they score 61–63%, under the 65% of rejecting everything.
7. **The open guardrail model is the best arm that runs without an API, and still well short of the model arms.** Given the nine categories as its policy, SafeGuard-VL-RL got 49 of 57 image ads right (86%; Chinese 27/29, English 22/28). Its reasoning quotes the words in the images, and it found all 3 drinking scenes and both large flags. It approved 5 violating ads: the small flag in a corner, the beer ad with no alcohol strength, the small-print eczema cure, "Principal protected. No risk." on a savings banner, and one before-and-after panel, which it described and then judged allowed. It rejected 3 of 18 traps: a midsole rebound figure printed with its test centre and year ("no source"), "2x the battery of our previous model" and "Number 1 fan?" (both as absolute claims). On 8 ads it rejected for the wrong category, 5 of them as ABSOLUTE (three medical claims, "Win every bet", a disparaging comparison). It names no clause and gives no quote, so a second reviewer has nothing to check its call against, and it took a median 178.3 s per image.
8. **A general safety guardrail does not cover ad rules; a guardrail given the rules works in English only.** Qwen3Guard-Gen-4B, which has its own fixed categories, marked 8 text ads as Controversial: 7 English ones (a herbal tea that "cures type 2 diabetes", "guaranteed 20% monthly returns", "$100 into $10,000 in one week", "Lose 10 kg in 7 days", "the fat friend", "Drink till you drop!", a testimonial about stopping blood-pressure medicine) and one Chinese (投资 5 万，年回报 30%，稳赚不赔). It passed every trap only because it passed almost everything: the other 17 violating ads, including every absolute claim and every disparagement, were Safe. Granite Guardian 3.3, given the nine categories as its criterion, rejected 11 of 13 violating English ads and approved 5 of 6 English traps. It missed the Unicode-bold "𝗯𝗲𝘀𝘁" and a free case of lager as a prize, and rejected "We'll never promise you'll lose weight overnight". On Chinese ads, outside the English-only training its model card states, it rejected 4 of 12 violating ads (98% of users without a source, fish oil that lowers blood lipids, guaranteed returns, a liquor ad) and missed both absolute claims, both disparagements, two medical claims and two guarantees. At 72% it is the only arm without an API above always-reject on text ads. It takes about 50 s per ad on CPU and, like the image guardrail, gives no clause or quote.

## v1.1: corrected versions without template text

The multi-turn task showed one concrete weakness: 3 of 24 corrected versions left template text for the advertiser to fill in. v1.1 changes only the "how do I fix it" turn: a system message says the corrected version must be ready to run, and a fact the advertiser has not given is left out and named in the answer; a `check_revision` tool lists brackets, blanks and quoted words still present. Review turns are unchanged. Because the first 12 conversations were used to find the problem, v1 and v1.1 were compared on 12 new text ads written for this check (plan and hashes in the preregistration, v1.1 section), two runs each.

| 24 conversations per version | v1 | v1.1 |
|---|---|---|
| Corrected version with template text | 3 | **0** |
| Corrected version approved by a separate review | 19 | 20 |
| Offending words gone / brand and price kept | 24 / 23 | 24 / 21 |
| Advertiser's own version: decision right | 22 | 22 |
| Cost per three-turn conversation | US$0.0061 | US$0.0066 |

v1 wrote "[X]% ABV" for a beer ad that gave no strength and "Licensed by [regulator name], licence no. [number]" for a savings ad; v1.1 left those statements out and told the advertiser what to add. The separate review still rejected the beer ad without a strength, which is right: that ad cannot run until the advertiser supplies it. The run also showed a second, different fault: in 4 conversations (1 with v1, 3 with v1.1) the "corrected caption" field came back empty or as a single word ("x", "ignored") while the corrected text sat inside the answer, after tool-call markup (`…</answer> <parameter name="revised_caption">…`). Those are the conversations where brand and price count as lost. The next two versions address this fault (below).

## v1.2 and v1.3: advice fields filled in wrongly

Across the 144 advice turns stored from the four multi-turn runs, 17 show the same fault: at the end of the long `answer` field the model writes tool-call markup into the field (`…</answer> <parameter name="revised_caption">…`), and in 11 of them the corrected-caption field itself is empty or one word. Strict tool use cannot require a minimum string length, so any check has to run in the agent's own loop.

**v1.2** sends a malformed `submit_advice` back once with an error result naming the problem. Compared with v1.1 on 12 new text ads (5 with two violations), three runs each:

| 36 conversations per version | v1.1 | v1.2 |
|---|---|---|
| Advice fields filled in wrongly, in the advice finally accepted | 4 | 6 |
| Advice sent back by the check | – | 7 |
| Brand and price kept | 33 | 33 |
| Corrected version approved by a separate review | 32 | 31 |
| Advertiser's own version: decision right | 36 | 36 |
| Cost per three-turn conversation | US$0.0069 | US$0.0077 |

Sending the call back does not fix the fault: in 6 of the 7 second calls the model repeated the same markup. v1.2 is dropped.

**v1.3** asks for the corrected caption and image words before the answer (strict tool use fills the fields in schema order, and every stored turn has the answer first), and repairs leaked markup in code: the answer is cut where the markup starts, and a caption found in the markup is used only when the field is empty or one word. The repair was written after reading the 144 stored turns, so v1.3 was compared with v1.1 on 12 more new text ads (plan and hashes in the preregistration, v1.3 section), three runs each. The run was interrupted once when the API account's credit ran out and resumed with the same commands; no file changed in between.

| 36 conversations per version | v1.1 | v1.3 |
|---|---|---|
| Advice as submitted, fields filled in wrongly | 6 | **0** |
| Advice changed by the repair | – | 0 |
| Brand and price kept | 34 | **36** |
| Offending words gone | 36 | 36 |
| Corrected version approved by a separate review | 35 | 35 |
| Advertiser's own version: decision right | 36 | 36 |
| Cost per three-turn conversation | US$0.0069 | US$0.0068 |

With the corrected version asked for first, the fault did not occur in any of the 36 v1.3 conversations, so the repair never had anything to do; applied offline to the 6 faulty v1.1 conversations, it fixes all 6 ([table](results/advice-faults-2026-11-13.md)). The 2 v1.1 conversations that lost brand and price are two of those 6. Cost did not change: the order of the fields adds no call.

## Harder set: long captions, video frames, implied claims

The test split did not separate the two model arms on the decision. So 24 harder ads were written after the test run, before any model saw them: 12 Chinese and 12 English. 17 of them break a rule (19 labels), and 7 are traps. The plan, six expectations and file hashes are in the preregistration (Harder set).

**What makes them harder.**

- **Long captions.** 12 ads are text with long captions. The violation sits in the middle, among claims that are allowed.
- **Video frames.** 8 ads are three-frame screenshots of a short video. The violation is either in one frame's subtitle or only in the picture: people toasting with baijiu; people drunk, one lying on the floor; a wide body on day 1 and a slim one on day 30.
- **Single images.** 4 ads are single images, one with its claim in small print.
- **Implied claims.** Several claims are implied, not stated: a parent's comment that a child's allergic rhinitis never came back; a customer who "came off my medication"; "never lost a cent since we were founded"; a job-or-refund promise; "no more hiding at the back of photos".
- **Traps.** These use risky words that are allowed:
  - a sales ranking limited to one platform, category and month, with its source;
  - 一级, a grade set by a national standard;
  - 最佳火候 and 第一步 in a cooking video;
  - "Nothing here is guaranteed";
  - "Best before";
  - two alcohol ads that state the strength and carry the required lines.

**How the requests were sent.** The model arms were sent through the Message Batches API instead of the standard Messages API; model and parameters are unchanged. Cost is counted at the batch price, half the list price. Time per ad is not measured, because it would be queue time. Each round of the agent's tool loop, across all ads, went out as one batch. There were 6 batches of about 2 minutes each, and every request succeeded. Both arms, two runs each over the 24 ads, took 12.7 minutes and cost US$0.092.

**All 24 ads**, two runs each (48 decisions per model arm); the word list ran once. Always rejecting would get 71% right.

| | one prompt | agent | word list |
|---|---|---|---|
| Decision right | 48/48 | 48/48 | 8/24 (33%) |
| Violating ads rejected | 34/34 | 34/34 | 5/17 |
| Traps approved | 14/14 | 14/14 | 3/7 |
| Exactly the labelled categories | 43/48 (90%) | 42/48 (88%) | 7/24 (29%) |
| Violations in the words found | 31/32 | 32/32 | 4/16 |
| Picture-only violations found | 6/6 | 6/6 | 0/3 |
| Right clause cited, when the category was found | 37/37 | 37/38 | n/a |
| Ad quotes passing the checker | 45/47 | 46/47 | n/a |
| Clause quotes passing the checker | 53/53 | 51/51 | n/a |
| Cost per ad, batch price | US$0.00058 | US$0.00133 | 0 |
| API calls per ad | 1.0 | 3.2 | 0 |
| Same decision in both runs | 24/24 | 24/24 | |
| Same categories in both runs | 22/24 | 21/24 | |

**The 12 image ads**, all image arms; the local arms ran once. Always rejecting would get 75% right.

| | one prompt | agent | word list | CLIP | SigLIP 2 | SafeGuard-VL |
|---|---|---|---|---|---|---|
| Decision right | 24/24 | 24/24 | 3/12 | 10/12 | 7/12 | 10/12 |
| Violating ads rejected | 18/18 | 18/18 | 1/9 | 8/9 | 6/9 | 7/9 |
| Traps approved | 6/6 | 6/6 | 2/3 | 2/3 | 1/3 | 3/3 |
| Exactly the labelled categories | 19/24 | 19/24 | 3/12 | 5/12 | 2/12 | 6/12 |
| Picture-only violations found | 6/6 | 6/6 | 0/3 | 2/3 | 0/3 | 2/3 |

**The 12 text ads**, all text arms. Always rejecting would get 67% right.

| | one prompt | agent | word list | Qwen3Guard | Granite Guardian |
|---|---|---|---|---|---|
| Decision right | 24/24 | 24/24 | 5/12 | 4/12 | 5/12 |
| Violating ads rejected | 16/16 | 16/16 | 4/8 | 0/8 | 1/8 |
| Traps approved | 8/8 | 8/8 | 1/4 | 4/4 | 4/4 |

The full results are in separate files:

- every ad and every arm: [`results/hard-2026-11-14.ads.md`](results/hard-2026-11-14.ads.md);
- all ads: [`results/hard-2026-11-14.summary.md`](results/hard-2026-11-14.summary.md);
- image ads: [`results/hard-2026-11-14.images.summary.md`](results/hard-2026-11-14.images.summary.md);
- text ads: [`results/hard-2026-11-14.text.summary.md`](results/hard-2026-11-14.text.summary.md).

**What the harder set shows.**

1. **The model arms are still at the ceiling.** Long captions, video frames, implied claims and these traps changed nothing on the decision. Each arm got 48 of 48 right, and its two runs agreed on every ad. The one-prompt arm, given the OCR text, found every subtitle violation that the agent found by calling OCR. This set does not separate the two arms either.
2. **The differences are small, and only in categories and clauses.** Each arm made one mistake:
   - One prompt missed one medical claim: in one run it filed the small print "Clinically shown to cure acne in 7 days*" as a guaranteed result.
   - The agent once cited the general misleading-claims clause for "$5,000 a month, zero risk", instead of the financial-services clauses.

   Both arms also named categories that are not in the labels: 7 for one prompt and 6 for the agent, over 48 runs each.
   - All four runs filed "Ours don't." (after "Other cases crack.") as an absolute claim or a guarantee.
   - Both arms added weight loss next to the day-1 and day-30 frames. One prompt also called those frames a guarantee.
   - The agent once added a guarantee for the allergic-rhinitis testimonial.
   - The agent once filed the trading app's missing risk statement under data.

   Outside the nine categories, one prompt flagged the trading app's missing risk and licence statements in both runs. This is not counted.
3. **Quotes fail only on the before-and-after video.**
   - Two ad quotes were "Day 1", which is verbatim but too short for the checker.
   - One was "Day 1 / Day 30": the one-prompt arm joined two frames' subtitles into one quote, and that string is not in the ad.

   Every clause quote passed.
4. **At the batch price both arms cost less per ad than in the test run, though the ads cost more to review.** At the list price, the per-ad cost would be 11% and 17% above the test run, mostly because the answers are longer: about 30% and 20% more output tokens per ad.
5. **Every arm without an API does worse here than on the test split.**
   - **Qwen3Guard** answered Safe for all 12 text ads. On the test split, its 8 rejections were blunt claims, 7 of them in English; here the claims are mostly implied.
   - **Granite Guardian** rejected only the body-shame line ("no more hiding at the back of photos"). In English it missed the "most comfortable ever" claim, the medication testimonial and the job-or-refund promise.
   - **SafeGuard-VL-RL** got 10 of 12 image ads right and approved all three traps. It found both drinking scenes. It missed the small-print acne cure, as it missed the small-print eczema cure on the test split, and it missed "Other cases crack.". Of the 7 ads it rejected, 3 were under the wrong category: the gout testimonial as before-and-after, the day-1 and day-30 frames as weight, and "never lost a cent" as an absolute claim.
   - **CLIP** also got 10 of 12 right, but by rejecting 9 of the 12 ads. For 4 of its 8 rejections of violating ads it named the wrong category, and it saw a national flag in a gout testimonial and in a cooking video.
   - **The word list** rejected 5 of 17 violating ads and 4 of 7 traps. The traps it rejected were:
     - 销量第一 in the qualified sales ranking;
     - "guaranteed" inside "Nothing here is guaranteed";
     - 最佳 and 治愈 in the cooking video;
     - 未成年人 in the compliant baijiu ad, where the word is part of the required warning to minors.
6. **Expectations: four of six held.**
   - Held: the model arms caught at least 14 of 16 violating text runs, and at least 5 of 6 picture-only runs.
   - Held: the word list rejected fewer than half of the violating ads.
   - Held, but only through the batch price: the cost per ad fell below the test run.
   - Did not hold: the share of decisions right did not drop.
   - Did not hold: the agent did not approve fewer traps than one prompt, because both approved all of them.

## Real ads: regulator and court decisions

Both written sets hit the ceiling, so the last check uses real ads whose answers were fixed by someone else.

- **English: 30 rulings of the UK Advertising Standards Authority (ASA).** 23 are Upheld (the ad broke the UK code; answer reject) and 7 are Not upheld (answer approve). The Upheld rulings are the most recent ones from 2026 in six groups, at most four per group: medical claims, weight and body image, investment returns, comparisons, ratings and superlatives, and alcohol. The Not upheld rulings are every one from 2024 to 2026 whose issue falls in the nine categories.
- **Chinese: 16 published cases.** 12 ads were penalised by market regulators, taken from the national regulator's typical-case releases of January and July 2026 (answer reject). 4 claims looked like breaches but were found lawful by a regulator or a court, in cases from 2015 to 2019 (answer approve): an award name with 最佳, 最好选择 meaning the best of the bank's own three products, 打造……第一品牌 as an aim, and 完美 as artistic exaggeration.
- **What the arms read.** The input is the published description of the ad, with brand and person names replaced by placeholders. For ASA rulings this is the ruling's "Ad description" section: the ad's words plus the ASA's description of any picture or video. For the Chinese cases it is the product type plus the ad words the release quotes, so the penalised items are easier than whole ads.
- **Plan and sources.** The selection rules, expectations and file hashes were fixed before any model saw these ads (preregistration, "Real ads" sections). The source texts are not reproduced here; the build scripts list the links.

**What this can and cannot show.** The answer is a regulator's or court's decision under its own rules: the UK code for the English ads, and decisions made before the 2023 enforcement guide for the four lawful Chinese ads. The arms apply this project's policy library, so some disagreement comes from the rulebook, not from reading the ad. For 8 English and 3 Chinese ads, the decision turned on evidence the ad does not show (whether a rating, statistic or award was real); results are given with and without them.

The requests were sent through the Message Batches API, as for the harder set.

**30 English ads (ASA)**, two runs each (60 decisions per model arm: 46 on the 23 upheld ads, 14 on the 7 not upheld); the local arms ran once. Always rejecting would get 77% right.

| | one prompt | agent | word list | Qwen3Guard | Granite Guardian |
|---|---|---|---|---|---|
| Decision right | 49/60 (82%) | 51/60 (85%) | 13/30 (43%) | 18/30 (60%) | 14/30 (47%) |
| Upheld ads rejected | 43/46 | 46/46 | 6/23 | 11/23 | 9/23 |
| Not upheld ads approved | 6/14 | 5/14 | 7/7 | 7/7 | 5/7 |
| Decision right, without the 8 evidence-dependent ads | 37/44 (84%) | 38/44 (86%) | | | |
| Exactly the labelled categories | 23/60 (38%) | 26/60 (43%) | 8/30 | | |
| Ad quotes passing the checker | 168/173 | 200/200 | | | |
| Clause quotes passing the checker | 205/206 | 210/210 | | | |
| Cost per ad, batch price | US$0.00097 | US$0.00301 | 0 | 0 | 0 |
| API calls per ad | 1.0 | 4.0 | 0 | 0 | 0 |
| Same decision in both runs | 29/30 | 29/30 | | | |

**16 Chinese ads**, two runs each (32 decisions per model arm: 24 on the 12 penalised ads, 8 on the 4 lawful ones); the local arms ran once. Always rejecting would get 75% right.

| | one prompt | agent | word list | Qwen3Guard | Granite Guardian |
|---|---|---|---|---|---|
| Decision right | 27/32 (84%) | 26/32 (81%) | 11/16 (69%) | 11/16 (69%) | 13/16 (81%) |
| Penalised ads rejected | 24/24 | 24/24 | 10/12 | 7/12 | 10/12 |
| Lawful ads approved | 3/8 | 2/8 | 1/4 | 4/4 | 3/4 |
| Exactly the labelled categories | 20/32 (62%) | 14/32 (44%) | | | |
| Ad quotes passing the checker | 65/65 | 74/74 | | | |
| Clause quotes passing the checker | 68/68 | 76/76 | | | |
| Cost per ad, batch price | US$0.00068 | US$0.00163 | 0 | 0 | 0 |
| API calls per ad | 1.0 | 3.4 | 0 | 0 | 0 |
| Same decision in both runs | 15/16 | 16/16 | | | |

The model arms' scores are in `results/real-2026-11-14.summary.md` (with the word list on the English ads) and `results/real-zh-2026-11-14.summary.md`. The counts for the word list and the two text guardrails on both languages are in `results/real-local-arms-2026-11-15.md`. The stored outputs of these runs hold the ads' words and are not published, and neither are the per-ad tables, which tie each item to its ruling or case; `testset/real-sources.md` gives the selection rules and source pages.

**What the real ads show.**

1. **The decision is off the ceiling, but the arms are still close.** On the decision, one prompt got 76 of 92 runs right across both languages and the agent 77. With 46 ads, a difference of one or two runs is noise.
2. **Where the arms differ, the agent is stricter.**
   - **Missed ads.** In English the agent rejected all 46 Upheld runs, and one prompt approved 3 of them. Two of the 3 were an awareness campaign built on a statistic with no source. One prompt noticed that the statistic had no source, but approved the ad in both runs because the English library has no clause for data. The agent filed the statistic under misleading claims and rejected it in both runs. The third was one run of a health-testing service's post that presented its tests as preventive care.
   - **Lawful ads.** The agent also rejected one more lawful ad than one prompt in each language. In English it was a loyalty-card comparison, rejected once for the scope of its headline. In Chinese it was the award name with 最佳.
3. **Most of the remaining errors come from the rulebook, not from misreading.**
   - **English.** Both arms rejected four ads that the ASA cleared: three alcohol ads built around artwork or animation, and a phone deal billed as the best value in the UK. The ASA had only been asked whether the alcohol ads appealed to under-18s. The arms rejected them mostly because TikTok's alcohol policy requires the drink's strength and a responsible-drinking line, which the descriptions do not show. They rejected the cider ad also for youth appeal in three of its four runs. The phone deal was rejected as a superlative, although its small print gave the basis of the comparison.
   - **Chinese.** Both arms rejected 最好选择 for an investment product: the 2023 guide says superlatives in investment ads are judged strictly. They also rejected 完美变频·唯有[品牌]. Both arms approved 打造花生行业第一品牌, citing the guide's exception for aims, in every run.
4. **Categories agree less than on written ads.** Only 38% to 62% of runs named exactly the labelled categories. The labels cover only the issues the regulator ruled on, while the arms add others. In English each arm added a guarantee 14 times, for example next to medical claims, and an absolute claim 14 to 16 times. Neither arm named the medicinal claim in a supplement-patch ad that borrowed the name of a prescription weight-loss drug, which the ASA upheld; both filed it under weight.
5. **Quotes still pass.** Every clause quote passed the checker except one of one prompt's 206. Every ad quote from the agent passed, and 5 of one prompt's 173 English ad quotes failed.
6. **On these ads the agent costs 3.1 times as much in English and 2.4 times as much in Chinese.** It made 4.0 calls per English ad, against 3.2 on the harder set. Both runs together cost US$0.31 at the batch price.
7. **Arms without an API.**
   - **The word list** rejected 6 of 23 Upheld English ads. In Chinese, the disease words caught 10 of 12 penalised ads, but the list also rejected 3 of the 4 lawful ones.
   - **Qwen3Guard** rejected 11 of 23 Upheld English ads: 6 of the 7 medical and body-image ads, 2 of the 4 alcohol ads, but only 1 of 4 investment ads and 1 of 5 rating ads. It approved all 7 Not upheld ones. In Chinese it rejected 7 of the 12 penalised ads and approved all 4 lawful ones.
   - **Granite Guardian**, given the nine categories as its criteria, rejected 9 of 23 Upheld English ads and 2 of the 7 Not upheld ones: 47% right, below always rejecting and below its 72% on the held-out text ads. It missed the lung-cleansing supplement, the therapy app and every comparison and rating ad. In Chinese it got 13 of 16, level with the agent, because the penalised items are only the phrases the regulator quoted; it approved 3 of the 4 lawful ones.
8. **Expectations: 7 of 7 held for the English ads and 3 of 4 for the Chinese ads.** The one that failed: the arms disagreed on only 1 of the 32 Chinese pairs, against at least 2 expected.

## Memory: earlier decisions shown to the agent

A platform sees the same advertisers and the same claims again and again. Without memory each review starts from the clauses alone, so a grey case can be decided one way for one ad and another way for the next. This test asks two things: when the agent is shown earlier confirmed decisions on similar ads, does it decide grey cases the way they were decided before, and how often does an earlier decision mislead it?

**Memory.** `agent/memory.py` keeps a store of confirmed decisions: the ad's words, the decision, each violation's category, clause and quoted words, a one-line reason, the advertiser and the date. For a new ad it returns the 3 most similar stored ads of the same language (BM25, the search already used for clauses) and up to 2 more of the same advertiser's most recent decisions. They are appended to the review request, and one step is added to the system prompt: decide the same way when the ad makes the same claim in the same way; the clauses decide when anything differs. Records are written by the program once a decision is confirmed. The model only reads the store, so an ad's words cannot become instructions for later reviews. There is no embedding model and no extra model call.

**Set.** 24 new fictional text ads (12 Chinese, 12 English) and a store of 36 earlier decisions, written together before any model saw them, answers fixed at writing. Each ad was written against one stored decision from the same advertiser.

- **Follow (12 ads): the earlier decision applies.** 6 repeat a rejected claim in other words or for another product. 6 are grey cases an earlier decision approved: a registered trademark with a superlative in it, a comparison with the advertiser's own products, a dated first release, a delivery guarantee, a refund trial.
- **Distinguish (12 ads): applying the earlier decision gives the wrong call.** 4 where the advertiser has removed the problem; 2 where a rejected claim now carries the qualifiers and the source that make it lawful; 2 clean ads from an advertiser with rejected ads; 2 where the qualifier or the required statement behind an approval is gone; 2 where an approved ad returns with a violation added.

**Arms.** The agent (v1.3) without and with memory: same model, tools and output format, three runs each through the Message Batches API. Both arms are told the advertiser account. The plan, six expectations and file hashes were fixed before the run (preregistration, "Memory").

| | Agent, no memory | Agent with memory |
|---|---|---|
| Decisions right, 72 runs | 69 | 72 |
| Follow: 6 rejected claims repeated (18 runs) | 18 | 18 |
| Follow: 6 grey cases approved before (18 runs) | 15 | 18 |
| Distinguish: 12 ads (36 runs) | 36 | 36 |
| The earlier decision repeated when it should not be (36 runs) | 0 | 0 |
| Ads on which all three runs agree | 24/24 | 24/24 |
| Earlier clause cited on the repeated claims (18 runs) | 18 | 18 |
| Cost per review, batch price | US$0.00116 | US$0.00103 |
| Model calls per review | 3.0 | 2.7 |

What it shows:

1. **Memory settled the one grey case the agent gets wrong by itself.** "Order by 3pm for guaranteed next-day delivery" was rejected in all three runs without memory, each time under TT-MIS-CLAIMS and each time in a different category (guaranteed outcome, absolute claim, other). With the earlier approval of a delivery guarantee from the same advertiser in front of it, the agent approved it in all three and gave the earlier reason: the guarantee is about the delivery service, not an effect of the product. This is the same mistake the held-out set found ("Guaranteed delivery by Friday"). The other five grey cases were approved by both arms.
2. **An earlier decision never misled it.** On the 12 ads where the earlier decision should not be applied, the memory arm was right in 36 of 36 runs and repeated the earlier decision in none. In 26 of those 36 runs its notes or explanations refer to an earlier decision, usually to say why it does not apply ("This ad omits both, so I did not follow [1]; the clause decides"). This count is a keyword search; the same search matches 2 of 36 runs in the arm without memory.
3. **Memory did not cost more.** A review with memory cost 0.89 times a review without. The earlier decisions add text to the request, but the agent then searched the policy library less: 2.0 searches per review against 2.6.
4. **Run-to-run agreement was already complete.** Both arms reached the same decision in all three runs of every ad. The agent without memory is consistent on the delivery guarantee too: consistently wrong. What memory changed is agreement with the earlier decision, not agreement between runs.

**How far this goes.** The benefit rests on one ad of 24, so it shows the mechanism and gives no rate. The test puts a relevant earlier decision in front of the agent every time: lookup returned the paired record for 24 of 24 ads, which was checked before the run without a model. It does not test lookup on a large store, a stored decision that is itself wrong, image ads, or decisions the agent wrote itself. Those are NOT RUN. Per-ad table: `results/memory-2026-11-16.report.md`.

## Answer-key audit (18 November)

Two clauses require a statement in the ad, not only the absence of bad words: an alcohol ad must state the drink's strength and carry a responsible drinking disclaimer (TT-ALC), and a health-food ad must show 「本品不能代替药物」 (CN-AL-18). The held-out key labelled a missing statement only where it was an ad's sole problem. When another evaluation reused these ads, six more turned up that lack a required statement with no label for it: two health-food ads and four alcohol ads. The frozen key is left as it is and the numbers above are scored against it, as preregistered. Scored again with the six labels added:

| | One prompt, frozen key | One prompt, corrected | Agent, frozen key | Agent, corrected |
|---|---|---|---|---|
| Decisions right | 191/192 | 191/192 | 187/192 | 187/192 |
| Exactly the labelled categories | 161/192 | 161/192 | 173/192 | 173/192 |
| Missing-element labels found | 2/2 | 14/14 | 2/2 | 14/14 |
| Right clause cited, when the category was found | 129/129 | 141/141 | 129/129 | 141/141 |

Nothing at the level of the decision changes: all six ads were already rejected, and the added labels bring no new category. The scorer counts a label as found when any violation of its category is listed, so the arms' own words were also read: on the six ads, each arm named the missing statement in 11 of 12 runs, and on the four alcohol ads that carry both statements neither arm ever claimed one was missing. Audit table: `results/key-audit-2026-11-18.md`; rescoring: `results/test-2026-11-13.corrected-key.md`; the labels: `testset/key_corrections_2026-11-18.yaml`.

## Expectations written before the run

| Expectation | Outcome |
|---|---|
| Both model arms ≥85% decisions right, ≥90% of word violations found | Held: 99% and 97%; 111/112 each |
| Misses concentrate in small print, small flag and drawn drinking scenes | Did not hold: none of these was missed in any run |
| Model arms approve ≥75% of traps; word list <60% | Model arms held (98%, 92%); the word list approved 70%, so that part did not hold |
| Word list rejects fewer than half of violating ads | Held: 26% |
| CLIP and SigLIP 2 close to useless on categories, may catch flags, before-and-after and drinking | Held: exact categories 46% and 37%; before-and-after 2/2 each, flags 2/3 and 1/3, drinking scenes 0/3 and 1/3 |
| Agent about twice the cost, slower, clause quotes at least as often verbatim | Held: 2.2×, 1.8×, 200/200 against 224/225 |
| Multi-turn: offending words removed in ≥10/12 per run, ≥8/12 pass the separate review | Held: 12/12 and 12/12; 9/12 and 10/12 |

SafeGuard-VL-RL was chosen after the plan was frozen, so no expectation was written for it.

For the memory test, five of six expectations held; the one that did not was cost, expected at 1.1 to 1.6 times and measured at 0.89 times (preregistration, "Memory").

The two text guardrails were also added after the freeze. Four expectations were written before their run (preregistration, change 6), and all four held. Qwen3Guard rejected 8 of 25 violating text ads, just under a third. Granite Guardian rejected 15. Granite was right on 85% of English and 58% of Chinese text ads. Both stayed below the model arms: 56% and 72%, against 100% and 97%.

## Limits

- The real ads (46) are judged by regulators and courts under their own rules, which differ from this project's policy library (the UK code against TikTok's ad policy; Chinese decisions from before the 2023 guide). The arms read published descriptions of the ads, not the ads; the Chinese penalised items keep only the words the regulator quoted; only 11 of the 46 are compliant. Rulings from 2024 and 2025 may be in the model's training data.
- The memory test has 24 ads and a store of 36 decisions written by the same author; the measured benefit comes from one ad. Lookup always found the paired decision, so the test says nothing about retrieval at scale, and a wrong stored decision was not tested.
- The ads are synthetic, short and written by the same author as the labels; real ads are longer, noisier and more varied. Answers were fixed at writing; there is no second labeller, six answers missed a required statement (corrected after the run, see the answer-key audit), and one trap (the heritage listing) and one revision (old caption kept) turned out to be flawed.
- Images are drawn, not photographed. The drinking scenes are illustrations; three photographic scenes were planned with an image model and not made.
- The v1.1 check uses 12 new text ads, two runs per version; with these counts a difference of one or two conversations is noise.
- The v1.2 and v1.3 checks each use 12 new text ads, three runs per version; 0 against 6 of 36 is a clear difference, but these are short text ads and one model.
- One model at one effort level, two runs, one day. With 96 ads, differences of a few runs between arms are within noise.
- The policy library is a curated excerpt (32 clauses), not a platform's full policy set; market-specific TikTok rules are left out.
- ShieldGemma 2 was not run: downloading it requires signing in and accepting the model's terms of use. SafeGuard-VL-RL, which takes its place, was chosen and run after the plan was frozen, once, on image ads only and without the caption (as for CLIP); another wording of its policy could change its numbers.
- The harder set has 24 ads, written by the same author as the labels after the test results were known. With both model arms at 48 of 48, it shows a ceiling, not a difference between them. Ads that are hard for these arms would need other sources: real ads, longer videos, or rules the model has not seen.
- The two text guardrails were also added after the freeze and run once, with one wording of the criterion. Granite Guardian's model card says it was trained on English only, so its Chinese numbers test it outside its stated range. gpt-oss-safeguard-20b, which is built to follow a written policy, was not run: it needs a 16 GB GPU.
- Rate limits interrupted 13 of 384 runs, which were run again; the multi-turn runner was made to store and retry failures after one such interruption (listed in the preregistration).
