# Product plan: Grounded Review

Draft v0.1, 16 November 2026. [中文](PRD.zh-CN.md)

This document describes Grounded Review as a feature of an ad platform: who uses it, what it solves, how it is measured and how it is rolled out. Every number in section 7 comes from an evaluation already run in this repository. **Anything marked [assumption] has not been tested** and should not be quoted as fact. The evidence in section 2 comes from public sources; each has a link, and each page was opened and checked on 16 November 2026.

## 1. In one sentence

Every ad-review decision carries its evidence: the rule that is broken and the words in the ad that break it, with each quote checked word for word before the decision counts. Reviewers use it to decide faster, advertisers use it to fix the ad, policy staff use it to see where a rule is applied unevenly, and the same kind of ad gets the same call each time.

## 2. Background: why this is worth doing

**Review runs at a very large scale, and platforms themselves aim to hold back fewer legitimate advertisers.**

- Google's 2025 Ads Safety Report: over 8.3 billion ads blocked or removed in the year, 24.9 million accounts suspended, and over 99% of policy-violating ads caught before they ran. [Source](https://blog.google/products/ads-commerce/2025-ads-safety-report/) (16 April 2026)
- In November 2025 Google said incorrect advertiser account suspensions were down by over 80%, appeals were handled 70% faster, and 99% of appeals were resolved within 24 hours. [Source](https://blog.google/products/ads-commerce/improved-accuracy-account-suspensions/) (13 November 2025; this is about account suspensions, not single ads)
- The UK Advertising Standards Authority's Active Ad Monitoring system processed 60 million ads in 2025, and 22,383 ads were amended or removed. In the same year it delivered 596,000 pieces of advice, training and answers to advertisers, who want to know before they publish whether the wording is acceptable. [Source](https://www.asa.org.uk/news/annual-report-2025.html) (14 April 2026)

**Advertisers often cannot tell why an ad was rejected or how to fix it.**

- In a Jiemian News report of October 2026, an agency says that even with staff assigned to follow each platform's policies it often cannot tell why a creative was judged non-compliant, and that the speed of appeals is part of a platform's commercial capability. In the same report, a platform-side interviewee says the customers' core pain is the uncertainty that rules and reviews bring. [Source](https://www.jiemian.com/article/15248310.html) (27 October 2026, in Chinese)
- A performance ad buyer interviewed by Digiday in August 2024 describes more ad rejections, including ads that had run for a long time, leading to account suspensions, and a recovery process that is painful and unpredictable. On the cause, the buyer can only speculate. [Source](https://digiday.com/marketing/confessions-of-a-performance-marketing-ad-buyer-on-uptick-in-platforms-ad-rejections-amid-election-advertising) (26 August 2024)

**Uneven decisions hurt legitimate advertisers.**

- A paper on Google's ads content safety work says in its abstract that inconsistent enforcement causes policy friction and a poor experience for advertisers, while bad actors exploit the inconsistency by creating many similar ads. [Source](https://arxiv.org/abs/2409.15343) (10 September 2024, preprint)
- Another paper clusters similar ads, reviews one representative per cluster and passes the decision to the rest of the cluster; this cut the number of reviews by more than three orders of magnitude. Reusing one decision across similar ads already has a precedent on a large platform. [Source](https://arxiv.org/abs/2402.14590) (7 February 2024)

**Platforms are already moving towards stating the reason and offering a fix.**

- TikTok's ad review FAQ: most ads are typically reviewed within 24 hours; the rejection prompt gives details, and advertisers are notified when changes can fix the ad; an advertiser who disagrees can appeal or contact support. [Source](https://ads.tiktok.com/help/article/ad-review-faq) (page marked as updated February 2025)
- Ocean Engine said publicly in October 2025 that 90% of creatives are reviewed within 10 minutes, and that a rejected creative comes with the reason and detailed suggestions, including the time point in the video where the problem is. [Source](https://news.qq.com/rain/a/20251029A05SPO00) (China Economic Weekly, 29 October 2025, in Chinese)

**Reviewing ads and keeping records are legal duties.**

- China's Measures for the Administration of Internet Advertising (in force from 1 May 2023): Article 14 requires advertising operators and publishers to check ad content, to have ad review staff or a review body, and to keep files for at least three years; Article 16 requires internet platform operators to monitor and screen for illegal ads and to keep records of how they were handled. [Source](https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_d93a579afd45413e8576e4623fab348f.html) (in Chinese)

**The gap this fills.** Each practice above covers one stretch: stating the reason, offering a fix, deciding similar ads alike. This project joins the three in one line, and every step can be checked: a decision carries the clause and the ad's words, and a script checks both quotes word for word; the fix is copy that can run as written; confirmed decisions are stored and compared with each new ad. It is an open-source prototype with an evaluation, not any platform's production system.

## 3. Goals, key results, non-goals

**Goal: all three sides gain.**

- Reviewers: each decision arrives with its evidence, so a second look only has to answer "do these words break this clause?"
- Advertisers: they know which words, which clause and how to fix it, with fewer rounds.
- Policy staff: they see which rules are triggered most and where calls are uneven, and old decisions expire when a rule changes.
- The platform: consistent decisions, each with a record.

**Key results (after a first release in one category; all are [assumed targets], and baselines must come from platform data):**

1. Reviewers accept at least 90% of the assistant's decisions, and time per review falls.
2. Rejected ads need fewer submissions on average before they pass.
3. For the same advertiser and the same kind of claim, at least 95% of decisions match the earlier one.
4. Guardrails: the share of rejections overturned on appeal does not rise; the share of violating ads let through does not rise.

**Non-goals (not in the first release):**

- It does not replace the final action. Rejections and penalties stay in the platform's existing process and are confirmed by reviewers.
- It does not help advertisers get around a rule. A fix removes the violating claim or adds the qualifier that makes it lawful; it does not find another way to imply the same thing.
- It is not stricter with an advertiser because of earlier rejections. History is used for consistency only.
- It does not review landing pages, score accounts for risk, or judge whether a licence is genuine.

## 4. Who it is for

| Who | Today | What this gives them |
|---|---|---|
| Reviewers | Machines screen first and people review the hard cases; the reviewer has to find the offending words and the matching clause [assumption; processes differ by platform] | A decision card: the call, the category, the clause, the ad's words and the clause's words, both quotes checked; earlier decisions on similar ads alongside |
| Advertisers and agencies | They get a rejection notice and a policy link, and work out the problem themselves (see the public reports in section 2) | A rejection note that points at the words; corrected copy; a second review that continues from the first |
| Policy operations | Unclear rules surface through sampling and appeals [assumption] | Counts per rule, samples overturned on appeal, pairs of similar ads decided differently; confirming and retiring stored decisions |

## 5. Value proposition

- **For reviewers**: a decision can be checked at a glance. Every quoted phrase is found word for word in the ad, and every quoted clause in the policy text; a quote that is not found is stopped before anyone reads the decision.
- **For advertisers**: said once and in full. Which words, which clause, why, and what to write instead; the second review looks at the change and does not start over.
- **For policy staff**: decisions become data that can be counted. Each one lands on a clause id, so a vague rule shows up as similar ads decided differently.
- **For the platform**: a handle on consistency. The earlier decision on the same claim appears next to the new ad, and a different call has to say why.

## 6. Solution

### 6.1 What reviewers see

- A decision card: approve or reject; one line per violation with the category, the clause, the ad's words (text in images is read by OCR; a problem in the picture is described in words), the clause's words, and a sentence or two of explanation.
- A check mark: "checked" appears only when both quotes are found word for word; a decision whose quotes fail gets no card and goes to a person.
- Earlier decisions on similar ads: the 3 most similar, plus the same advertiser's 2 most recent, each with its call and reason.
- The reviewer can accept, change the call, or mark "the earlier decision does not apply"; a confirmed decision enters the store.

### 6.2 What advertisers see

- A rejection note that points at the offending words, names the clause and links to the policy page.
- "How to fix it": the reason and copy that can run as written (including the words in the image), keeping the brand, the specification and the price.
- Resubmission: the second review is made against the first; if a problem remains, the note says which one.
- Not shown: other advertisers' ads, and the internal store of earlier decisions.

### 6.3 What policy operations see

- For each rule: how often it was triggered, how often reviewers changed the call, how often an appeal overturned it.
- Pairs decided differently: ads with similar claims and opposite calls, grouped by clause.
- Managing stored decisions: confirm and retire; when a rule changes, decisions citing the old clause are marked for another look, in bulk.

### 6.4 Memory: earlier confirmed decisions

- **What is stored**: the ad's words, the decision, each violation's category, clause and quoted words, a one-line reason, the advertiser, the date.
- **Who writes**: the program, after a decision is confirmed. The model only reads: an ad's words are written by someone else and must not get a chance to become instructions for later reviews.
- **How it is looked up**: the 3 most similar stored ads of the same language by text similarity (BM25, the same search used for clauses), plus the same advertiser's 2 most recent. No embedding model and no extra model call.
- **How it is used**: when the new ad makes the same claim in the same way, decide the same way and cite the same clause; when the wording, a qualifier, a source or the product differs, decide from the clauses and say which earlier decision was not followed and why. The clauses decide; earlier decisions only keep calls consistent.
- **When it should not be applied**: the advertiser has fixed the problem; a qualifier now makes the claim lawful; the advertiser's earlier rejections were for other ads; the ad passed before only because of a qualifier that is now missing. The evaluation has test ads for each case (section 7.5).
- **Existing options not adopted**: general memory libraries mostly have a model rewrite what is stored into "facts", and a rewritten quote can no longer be checked word for word; the model API's own memory tool lets the model decide what to write, which does not suit a review setting where the content comes from a third party.

### 6.5 How it works (the offline version in this repository)

1. Read the image: OCR reads the words in the image; the model also looks at the image, because some problems are only in the picture.
2. Look up earlier decisions: see 6.4.
3. Look up clauses: search the policy library for clauses that may apply. The library has 32 clauses cut from the official texts by script; rules and guidance on when a rule does not apply are marked separately.
4. Check the quotes: the ad's words and the clause's words go to [evidence-check](https://github.com/Jason-d-e/evidence-check)'s script, and a failed quote is redone.
5. Decide; when the advertiser asks, give the fix and corrected copy, then review the version the advertiser submits.

The model is `claude-haiku-5-5`. Large, non-urgent runs go through the Message Batches API at half price.

## 7. Offline evaluation (numbers already in this repository)

The plan, expectations and file hashes are frozen before each run (`eval/PREREGISTRATION.md`); the full report is `eval/EVALUATION.md`. Two methods use the same model: one prompt given everything at once, and the agent with tools.

### 7.1 Are the decisions right?

| Set | One prompt | Agent |
|---|---|---|
| Held-out: 96 synthetic text and image ads, 30 of them traps | 191/192 decisions right | 187/192 |
| Harder: 24 ads with long captions, video frames, implied claims | 48/48 | 48/48 |
| Real, English: 30 published rulings of the UK ASA | 49/60 | 51/60 |
| Real, Chinese: 16 published cases | 27/32 | 26/32 |

On written ads both methods reach the ceiling; on real ads they stay close and the agent is stricter. Most remaining errors come from rules, not from reading: a regulator judges under its own code, which differs from the policy library.

### 7.2 Does the evidence hold up?

On the held-out set, 98% of ad quotes and all but one of 425 clause quotes passed the word-for-word check. The ad quotes that failed were real words too short for the checker.

### 7.3 Fix suggestions

The advice step was tested version by version: v1.1 removed template placeholders from rewrites (3 of 24 had them, then 0); v1.3 fixed corrected copy written into the wrong field (6 of 36, then 0); v1.2 did not help and was not adopted.

### 7.4 Cost

The agent costs more than one prompt: 2.2 times on the held-out set, and 2.4 to 3.1 times on the real ads.

### 7.5 Memory

24 new text ads (12 Chinese, 12 English) and a store of 36 confirmed earlier decisions; each new ad was written against one earlier decision from the same advertiser, with the answer fixed at writing. The agent ran three times without memory and three times with it.

| | No memory | With memory |
|---|---|---|
| Decisions right, 72 runs | 69 | 72 |
| Earlier decision applies: 6 rejected claims in other words (18 runs) | 18 | 18 |
| Earlier decision applies: 6 grey cases approved before (18 runs) | 15 | 18 |
| Earlier decision should not be applied: 12 ads (36 runs) | 36 | 36 |
| Earlier decision repeated when it should not be (36 runs) | 0 | 0 |
| Ads on which all three runs agree | 24/24 | 24/24 |
| Cost per review, batch price | US$0.00116 | US$0.00103 |

- **Memory settled the one grey case the agent gets wrong by itself.** "Order by 3pm for guaranteed next-day delivery" was rejected in all three runs without memory. With the same advertiser's earlier approved delivery guarantee in front of it, the agent approved it in all three, for the earlier reason: the guarantee is about the delivery service, not an effect of the product.
- **An earlier decision never misled it.** The advertiser fixed the problem; the claim gained its qualifiers; a clean ad came from an advertiser with rejected ads; a qualifier was dropped; an approved ad came back with a violation added. Across these 12 ads, all 36 runs were right.
- **It did not cost more.** With memory the agent searched the clauses less, and a review cost 0.89 times a review without.
- **How far this goes.** The benefit comes from one ad of 24, so it shows the mechanism and gives no rate. Lookup found the matching earlier decision for all 24 ads (checked before the run, without a model), so retrieval from a large store is untested; so are a stored decision that is itself wrong, image ads, and decisions the agent wrote itself (NOT RUN).

## 8. Metrics

**North star: the share of decisions that are grounded and accepted.** A decision counts only when its quotes pass the check, the reviewer accepts it, and no appeal overturns it.

| Metric | How it is computed | What it shows |
|---|---|---|
| Quote check pass rate | quotes that pass ÷ all quotes | whether the evidence is reliable (offline: 98%) |
| Acceptance rate | decisions reviewers accept as they are ÷ all decisions | whether decisions are useful [online only] |
| Consistency rate | same advertiser, same kind of claim: share of calls that match the earlier one | whether memory works (offline, see 7.5) |
| Misapplied earlier decisions | times an earlier decision is repeated when it should not be | whether memory misleads (offline, see 7.5) |
| Rounds to approval | average submissions before a rejected ad passes | whether advertisers get there sooner [online only] |
| Guardrails: overturn rate, miss rate | rejections overturned on appeal ÷ all rejections; violating ads found in sampling ÷ sample size | consistency and speed must not cost accuracy [online only] |
| Cost and time per ad | model cost; end-to-end time | whether it can run at volume (offline) |

## 9. Rollout

| Stage | What happens | Condition to move on [assumption] |
|---|---|---|
| 0. Offline | Rerun the section 7 evaluation on the platform's own past decisions, with the policy library replaced by the platform's current policy | Decision accuracy and quote pass rate no lower than the offline results |
| 1. Shadow | One category; the assistant runs alongside live review, its decisions are not shown and are only compared with reviewers' calls | Agreement with reviewers reaches the bar; every disagreement is read |
| 2. Reviewer assist | Reviewers see the decision card; confirmed decisions enter the store | Acceptance at least 90%, time per review down, guardrails no worse |
| 3. Advertiser-side notes | Rejection notes point at the words and the clause; "how to fix it" opens | Fewer rounds to approval; appeals do not rise |
| 4. More categories and languages | For each new category, add its clauses and trap ads first, then repeat stages 0 to 3 | As above |

Each stage can be switched off to fall back to the one before; the final action stays with reviewers throughout.

## 10. Risks and responses

| Risk | Response |
|---|---|
| A clause or a quote that does not exist | Quotes are checked word for word; a decision whose quotes fail gets no card |
| Compliant ads rejected | The policy library marks "when the rule does not apply" separately; the evaluation includes trap ads; the overturn rate is a guardrail |
| An earlier decision misleads: it was wrong, or it does not apply | Only confirmed decisions are stored; clauses come before earlier decisions; not following one requires a reason; decisions can be retired and are re-examined in bulk when a rule changes. The evaluation tests the "does not apply" cases; **a wrong stored decision has not been tested** (NOT RUN) |
| Instructions hidden in ad copy to steer the review | The model does not write memory; ad copy is only ever the thing under review; every decision must land on a clause |
| A suggested fix is read as "guaranteed to pass" | The note says corrected copy is reviewed again; the corrected copy and the advertiser's own revision go through the same review |
| Rules differ from a regulator's code (the main source of error on real ads, 7.1) | The library follows the platform's current policy, with versioned clauses; market-specific requirements are separate libraries |
| Cost | Screen with one prompt first and send only uncertain, rejected or queried ads to the agent [assumption, to be tested]; the batch API is half price |
| Test ads differ from live ads | Written ads only show a floor; rerun on the platform's past decisions before launch (stage 0) |

## 11. Assumptions and open questions

- How reviewers split machine and human review today, and how long a second look takes: this differs by platform, is not public, and has to come from inside the platform.
- The targets in section 3 are assumptions and need baselines.
- Whether text similarity is still enough when the store grows large, or whether vector search is needed: not tested.
- Whether the assistant follows a stored decision that is itself wrong: not tested, and the next thing to test.
- How to look up earlier decisions for image and video ads (this memory test has text ads only): not built.
- Other languages and market-specific requirements: the library covers Chinese (the Advertising Law and the enforcement guide) and English (the global sections of a platform's policy) only.
- The user-feedback evidence here is public reporting and platforms' public statements, with no first-hand research; interviews with reviewers and advertisers should be added before launch.
