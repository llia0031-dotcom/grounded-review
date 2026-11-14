# Failure attribution

Every miss and wrong flag of the two model arms, two runs each. Causes are defined in `eval/attribution.py`.

| Cause | oneshot | agent |
|---|---|---|
| extra:defensible | 23 | 13 |
| extra:wrong | 7 | 3 |
| missed | 1 | 0 |
| trap | 1 | 5 |
| wrong_category | 0 | 1 |

| Arm | Item | Run | Category | Cause | Detail |
|---|---|---|---|---|---|
| oneshot | en-t02 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "No more insulin!" — The ad promises that users can stop insulin because of the tea, which promises and exaggerates a health result the product cannot guarantee. |
| oneshot | en-t02 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "No more insulin!" — The ad promises that users will stop needing insulin after drinking the tea. This is an exaggerated promise of a product effect that could lead diabetic viewers |
| agent | en-t03 | 2 | DATA | extra:wrong | TT-DEC-FINREP: "Zero risk, withdraw anytime." — Claiming zero risk for an investment is misleading. The ad does not disclose any investment risk, which the policy requires. |
| agent | en-t05 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Lose 10 kg in 7 days with Slimora drops." — The specific promise of 10 kg lost in 7 days exaggerates the product's effect and presents it as a guaranteed result, which misleads viewers. |
| agent | en-t05 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Lose 10 kg in 7 days with Slimora drops." — The specific promised result of 10 kg in 7 days is an exaggerated promise of the product's effect and is not supported by any evidence. |
| oneshot | en-t05 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Lose 10 kg in 7 days with Slimora drops." — The ad promises a specific, exaggerated result (10 kg lost in 7 days) from the product's effect. This is the same kind of promised result as the policy's 'Get s |
| oneshot | en-t05 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Lose 10 kg in 7 days with Slimora drops." — The ad promises an exaggerated, specific result for the product within a short time frame, which misleads viewers about what the product can do. |
| agent | en-t06 | 1 | BEFORE_AFTER | extra:wrong | TT-WM-BODY: "Tired of being the fat friend?" — The ad uses the insulting label "the fat friend" to shame viewers about their body and suggests that being overweight is a problem to escape. This breaks the bo |
| oneshot | en-t06 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "gets you beach-body ready" — The ad promises a guaranteed physical result from a shake, which exaggerates what the product can achieve. |
| oneshot | en-t06 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Oakline Shake gets you beach-body ready." — Saying the shake "gets you" beach-body ready promises a definite physical result from the product. |
| agent | en-t13 | 1 | GUARANTEE | trap | TT-MIS-CLAIMS: "Guaranteed delivery by Friday on all Verdi orders over $30." — The ad promises an absolute, guaranteed delivery date ('Guaranteed delivery by Friday') with no stated conditions. This is an absolute term about the product's  |
| agent | en-t13 | 2 | GUARANTEE | trap | TT-MIS-CLAIMS: "Guaranteed delivery by Friday on all Verdi orders over $30." — The ad makes an unconditional promise that every qualifying Verdi order will arrive by Friday, with no stated cut-off time, delivery region, or exceptions. This |
| agent | en-t19 | 2 | OTHER | trap | TT-MIS-INCONSISTENT: "Lumeo Daily Set $42" — The ad sells a three-step 'Daily Set' for $42 but shows only one product, so viewers cannot tell what the price includes. The ad's product presentation is incon |
| agent | en-t21 | 1 | ABSOLUTE | extra:defensible | TT-MIS-CLAIMS: "Clears psoriasis for good" — The phrase "for good" is an absolute term about the product's effect over time, implying a permanent result that cannot be substantiated. |
| oneshot | en-t21 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Clears psoriasis for good" — The phrase 'for good' promises a permanent, guaranteed result from the product that is not supported. |
| oneshot | en-t21 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Clears psoriasis for good" — The phrase 'for good' promises a permanent, guaranteed result of the product's effect on psoriasis, which is exaggerated and not substantiated. |
| agent | en-t22 | 1 | ABSOLUTE | extra:wrong | TT-MIS-CLAIMS: "Reverses arthritis in 30 days" — The phrase 'in 30 days' is an absolute time-bound claim about the product's effect, which the policy does not allow. |
| agent | en-t22 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Reverses arthritis in 30 days" — The ad promises a specific, guaranteed effect (reversing arthritis) within a fixed 30-day period, which exaggerates the product's results. |
| oneshot | en-t22 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Reverses arthritis in 30 days" — The ad promises a specific, time-bound effect on a disease that the product cannot reliably deliver, which exaggerates the product's results. |
| oneshot | en-t26 | 1 | ABSOLUTE | extra:wrong | TT-MIS-CLAIMS: "Wrinkles gone in 3 days." — The phrase "gone in 3 days" is an absolute claim about the product's effect in relation to time, which the policy does not allow. |
| oneshot | en-t26 | 2 | ABSOLUTE | extra:wrong | TT-MIS-CLAIMS: "Wrinkles gone in 3 days." — The ad uses an absolute time-bound claim that wrinkles are completely gone in 3 days, which the policy does not allow for a product's effect. |
| oneshot | en-t27 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Melt belly fat while you sleep" — The ad promises a fast, specific result (belly fat melting overnight) from a capsule. This exaggerates the product's effect and is misleading. |
| oneshot | en-t27 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Melt belly fat while you sleep" — The ad promises a specific, fast and effortless fat-loss result from a supplement overnight, which exaggerates the product's effect and is similar to the prohib |
| oneshot | en-t28 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Drop 3 dress sizes in 2 weeks" — The ad promises a specific, fast result from the Slimora plan, which exaggerates the product's effect and may mislead viewers. |
| oneshot | en-t28 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Drop 3 dress sizes in 2 weeks" — The ad promises a fast, specific result from the Slimora plan within a set time frame, which exaggerates the product's effect. |
| agent | en-t30 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "See the difference." — The caption and images promise that the serum removes spots entirely, which exaggerates the product's effect. Such results claims are not allowed. |
| oneshot | en-t30 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "See the difference." — The ad implies that the serum completely removes spots, which exaggerates the product's effect on skin. |
| agent | en-t31 | 1 | WEIGHT | extra:defensible | TT-WM-WEIGHT: "Slimora 30-day plan" — The 30-day plan is presented as producing a visibly dramatic weight loss, implying the product alone delivers the result, which is an exaggerated weight-loss cl |
| agent | en-t31 | 2 | WEIGHT | extra:defensible | TT-WM-WEIGHT: "Slimora 30-day plan" — The ad implies that a 30-day plan produces dramatic weight loss, without any healthy lifestyle context. This is an exaggerated and unrealistic weight-loss claim |
| oneshot | en-t31 | 1 | WEIGHT | extra:defensible | TT-WM-WEIGHT: "Slimora 30-day plan" — The ad implies a dramatic weight loss in 30 days, which is unrealistic and is not tied to a healthy lifestyle. |
| oneshot | en-t31 | 2 | WEIGHT | extra:defensible | TT-WM-WEIGHT: "Slimora 30-day plan" — The ad implies that a 30-day plan produces a dramatic weight loss, without any reference to diet or exercise, which is an unrealistic weight loss claim. |
| agent | en-t43 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Results in weeks" — 'Results in weeks' promises a specific timeframe for product effects without any substantiation, which is an exaggerated and misleading promise of results. |
| agent | en-t43 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Results in weeks" — 'Results in weeks' promises a specific timeframe for the product's effect, which is an exaggerated and unsubstantiated promise of results. |
| oneshot | en-t43 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Results in weeks" — "Results in weeks" promises a specific, time-bound effect from the product with no evidence or qualification, which exaggerates the product's results. |
| oneshot | en-t43 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Results in weeks" — The headline promises visible results within weeks for a product with no evidence or disclaimer. This is a promised outcome about the product's effect and is no |
| agent | en-t44 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Clinically shown to cure eczema in 2 weeks." — The ad uses an absolute, time-bound promise of results ("cure ... in 2 weeks") that exaggerates the product's effect and is not allowed. |
| oneshot | en-t44 | 1 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Clinically shown to cure eczema in 2 weeks." — The ad promises a specific, time-bound result from the product, which exaggerates its effect and is not supported by any stated study or source. |
| oneshot | en-t44 | 2 | DATA | extra:wrong | TT-MIS-CLAIMS: "Clinically shown" — The ad cites clinical evidence but gives no source, study, or sponsor, so viewers cannot verify the claim and it may be misleading. |
| oneshot | en-t44 | 2 | GUARANTEE | extra:defensible | TT-MIS-CLAIMS: "Clinically shown to cure eczema in 2 weeks." — The ad promises a specific result, curing eczema within 2 weeks. This is a promised product effect with a fixed timeframe, which exaggerates what the cream can  |
| oneshot | zh-t07 | 1 | ABSOLUTE | missed |  |
| oneshot | zh-t17 | 2 | GUARANTEE | extra:wrong | CN-AL-28: "24 小时不凉" — 广告以“24小时不凉”作为确定的保温效果承诺，但画面和文字均未提供测试依据或适用条件，容易让消费者误认为任何情况下都能保温24小时，存在误导风险。 |
| agent | zh-t21 | 1 | OTHER | trap | CN-AL-28: "国家级非物质文化遗产代表性项目" — 广告将“龙泉青瓷烧制技艺”这一非遗项目的国家级荣誉与所售“木朴手作茶具”并置，并未说明该商品或其生产者是否属于该非遗项目传承范围，容易让消费者误认为该商品曾获得国家级荣誉，构成引人误解的虚假广告。 |
| agent | zh-t21 | 2 | ABSOLUTE | trap | CN-AL-9-3: "国家级非物质文化遗产代表性项目" — 广告将“国家级”非遗称号置于所售木朴茶具的商品信息上方，使消费者认为该茶具本身具有国家级非遗的品质或地位。该称号授予的是“龙泉青瓷烧制技艺”这一技艺，而非木朴品牌或这件商品，广告未说明二者的关系，属于对商品使用“国家级”绝对化用语。 |
| oneshot | zh-t21 | 2 | ABSOLUTE | trap | CN-AL-9-3: "国家级非物质文化遗产代表性项目" — 广告在商品标题下使用“国家级”用语，并将其与木朴手作茶具一同展示，使消费者误以为该茶具具有国家级非遗代表性项目的地位。广告未说明该认定与本商品的关系，也不符合执法指南第六条第（五）项“依据国家有关规定评定的称号”的豁免情形，因此构成违规。 |
| oneshot | zh-t22 | 2 | GUARANTEE | extra:wrong | CN-AL-18: "一贴改善失眠 降血压" — 广告以“一贴改善失眠 降血压”作出功效断言，属于对产品功效的断言性表述，且未有依据。若该产品被视为保健类产品，同样违反保健食品广告的功效断言禁令。 |
| oneshot | zh-t23 | 1 | GUARANTEE | extra:wrong | CN-AL-28: "三天见效" — 护手霜在没有依据的情况下承诺"三天见效"，并与治疗湿疹相联系，容易让消费者误以为产品能治疗疾病，构成引人误解的效果承诺。 |
| oneshot | zh-t23 | 2 | GUARANTEE | extra:wrong | CN-AL-28: "三天见效" — “三天见效”对产品效果作出时限性承诺，且无任何依据或检测结果支持，容易误导消费者，构成引人误解的内容。 |
| agent | zh-t24 | 1 | GUARANTEE | extra:defensible | CN-AL-18: "增强免疫力" — 保健食品广告以断言方式宣称“增强免疫力”的功效，属于表示功效的断言，违反广告法第十八条第（一）项。 |
| agent | zh-t24 | 2 | GUARANTEE | extra:defensible | CN-AL-18: "增强免疫力抗癌防癌" — 广告以断言方式表示产品“增强免疫力”“抗癌防癌”的功效，违反广告法第十八条第（一）项。 |
| oneshot | zh-t24 | 1 | GUARANTEE | extra:defensible | CN-AL-18: "增强免疫力" — 广告以肯定语气断言该保健食品“增强免疫力”，属于对产品功效的断言，不符合保健食品广告的规定。 |
| agent | zh-t41 | 1 | DATA | extra:defensible | CN-AL-11-2: "全网销量 N0.1" — “全网销量第一”属于销售数据排名类引证内容，画面中未表明统计出处、统计时间和范围，不符合引证内容应表明出处的要求。 |
| oneshot | zh-t41 | 1 | DATA | extra:defensible | CN-AL-11-2: "全网销量 N0.1" — “全网销量第一”是基于销量数据的排名类统计结论，广告未表明数据来源或统计范围，不符合引证内容须表明出处的要求。 |
| oneshot | zh-t41 | 2 | DATA | extra:defensible | CN-AL-11-2: "全网销量 N0.1" — “全网销量第一”是销量统计结论，广告未标明统计数据的来源或统计依据，不符合引证内容须表明出处的要求。 |
| agent | zh-t45 | 1 | GUARANTEE | wrong_category | flagged as OTHER |
