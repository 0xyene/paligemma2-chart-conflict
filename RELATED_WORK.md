# Related work

Found by four search agents from different angles, then each paper checked against its abstract page (title, authors, year, venue, and that the finding below matches the abstract). Venues as of October 2026; arXiv-only papers are not peer reviewed.

**Gap:** none of the searches found a benchmark that keeps the marks pixel-identical and changes only text printed *inside* the chart (labels, ticks, legend, readouts), with a no-text baseline, across question types and two languages. That's a statement about what the searches found, not proof that nothing exists.

## The original paper: what it measures and what it doesn't

**Steiner et al., "PaliGemma 2: A Family of Versatile VLMs for Transfer", arXiv 2412.03555 (Dec 2024)** — checked against the PDF text.

- **Chart / text benchmarks evaluated:** ChartQA (aug, human), AI2D, DocVQA, InfoVQA, TextVQA, TextCaps, OCR-VQA, ST-VQA, plus screen
  tasks (Screen2Words, WidgetCap) and SciCap. Multilingual: XM3600 (35 languages, captioning), xGQA (7 languages), MARVL, COCO-35L.
  No Turkish-specific evaluation and no multilingual chart questions.
- **3B numbers, 224 → 448 px (Table 13):** ChartQA aug 74.4 → 89.2 · ChartQA human 42.0 → 54.0 · DocVQA 39.9 → 73.6 ·
  InfoVQA 25.2 → 37.5 · AI2D 74.7 → 76.0.
- **Resolution finding (Sec. 4.1.1, Fig. 3):** text, document, screen and chart tasks gain mainly from higher resolution, while
  reasoning and multilingual tasks gain mainly from a bigger language model.
- **Protocol:** every benchmark is fine-tuned separately (learning-rate sweep per model size and task). The generalist `mix`
  checkpoints used in this experiment are not evaluated in the paper.
- **Not in the paper:** any robustness, counterfactual, typographic-attack, misleading-chart or text-vs-image conflict test. The only
  evaluation beyond task accuracy is the ethics/safety appendix (toxicity, representational harms). Accuracy alone can't tell which
  cue a model used: when a chart prints its values, reading the bar and reading the label give the same answer.

## Closest to our design

- **Inside VLM Chart Reading: Tracing Value Reading from Vertical Bar Charts Across Space and Depth** — Tianhao Niu et al., *arXiv (2609.13745)*, 2026. [https://arxiv.org/abs/2609.13745](https://arxiv.org/abs/2609.13745)
  - Finding: Using counterfactual activation patching in Qwen2.5-VL-7B-Instruct and InternVL3.5-8B, the authors find three things: the changed bar-top region restores much more answer preference than the unchanged bar body even though it has fewer visual tokens; legend and series states stop being locally recoverable at earlier layers than bar-geometry and axis-scale states, and that information moves from legend image regions to prompt-series positions in the middle layers; and both models can combine geometry and scale states taken from separate donor charts to favor the combined target, with Qwen less able to do this than InternVL.
  - Relation to ours: Partial overlap, and the closest stimulus design to ours: tick text changes while the marks stay fixed, as in our relabeled and inverted-axis conflicts. Differences: no value labels on the bars, internal patching instead of a behavioral marks-vs-text tally, and different models (not PaliGemma), English only.

- **The Perils of Chart Deception: How Misleading Visualizations Affect Vision-Language Models** — Ridwan Mahbub et al., *IEEE VIS 2025 (Short Papers track; arXiv 2508.09716)*, 2025. [https://arxiv.org/abs/2508.09716](https://arxiv.org/abs/2508.09716)
  - Finding: Across more than 16,000 responses from ten VLMs on eight kinds of misleading chart design, most models were fooled by the designs and read the charts differently even though the underlying data was the same.
  - Relation to ours: partial overlap: closest design to ours (paired charts, same data, only one factor changed, then check if the answer moves). Difference: they change the geometry/scale and keep the text truthful, so the 'correct' answer follows the ticks. We keep the marks pixel-identical and change only the text. Their inverted-axis result is the mirror image of our inverted-axis conflict case.

- **Read or Ignore? A Unified Benchmark for Typographic-Attack Robustness and Text Recognition in Vision-Language Models** — Futa Waseda et al. et al., *ECCV 2026*, 2026. [https://arxiv.org/abs/2512.11899](https://arxiv.org/abs/2512.11899)
  - Finding: On RIO-Bench, a same-scene counterfactual benchmark, representative typographic-attack defenses built for object recognition can gain robustness by suppressing text sensitivity, which costs them text-reading performance; a data-driven defense baseline the authors propose improves both requirements.
  - Relation to ours: Partial overlap. Same controlled design (scene fixed, only in-image text changed), and its central question (read the text or trust the visual?) is ours. It uses natural scenes and object recognition rather than charts with quantitative marks.

## Text vs image conflict (conflicting text given next to the image)

- **Words or Vision: Do Vision-Language Models Have Blind Faith in Text?** — Ailin Deng et al., *CVPR 2025*, 2025. [https://arxiv.org/abs/2503.02199](https://arxiv.org/abs/2503.02199)
  - Finding: Across ten VLMs and four vision-centric tasks with altered text, the models trust the text far more than the image when the two disagree ("blind faith in text"), so performance drops sharply when the text is corrupted; a larger language model reduces this only slightly, token order can make it worse through positional biases carried over from the LLM, and supervised fine-tuning with text augmentation reduces it.
  - Relation to ours: same question (marks vs text, which wins), but their conflicting text is given next to the image in the prompt, while ours is printed inside the chart pixels

- **Mixed Signals: Decoding VLMs' Reasoning and Underlying Bias in Vision-Language Conflict** — Pouya Pezeshkpour et al., *Findings of EMNLP 2025*, 2025. [https://aclanthology.org/2025.findings-emnlp.1351/](https://aclanthology.org/2025.findings-emnlp.1351/)
  - Finding: On five datasets of mismatched image-text pairs (math, science, visual descriptions), VLMs favour the text on simpler queries and shift toward the image as queries get more complex; the bias correlates with model scale, and the image-minus-text preference gap runs from +56.8% (image favoured) to -85.1% (text favoured) depending on task and model, while the three mitigations (simple prompt changes, explicit conflict-handling instructions, and per-modality task decomposition) vary widely in effect, tied to the model's overall task performance and the modality involved.
  - Relation to ours: same question (an image-vs-text preference score like our 'follows marks vs follows text' rate); the conflicting text is in the prompt, not rendered in the image

- **Evaluating and Steering Modality Preferences in Multi-modal LLMs (ICML 2026 title; arXiv title: "Evaluating and Steering Modality Preferences in Multimodal Large Language Model")** — Yu Zhang et al., *ICML 2026 (poster); arXiv 2505.20977 (v1 May 2025, v3 Feb 2026)*, 2026. [https://arxiv.org/abs/2505.20977](https://arxiv.org/abs/2505.20977)
  - Finding: On the MC² benchmark of controlled evidence conflicts, all 20 tested MLLMs show a clear modality preference that is statistically associated with their downstream performance; the preference can be changed by instructions and read from latent representations, and a representation-engineering probe-and-steer method controls it without fine-tuning and improves several multimodal understanding and reasoning tasks.
  - Relation to ours: same question (a benchmark built to measure modality preference under conflict); text is a separate input, not printed in the image

- **Which Source Wins? Task-Dependent Reliance in Vision-Language Models** — Rodela Ghosh et al., *arXiv*, 2026. [https://arxiv.org/abs/2608.17205](https://arxiv.org/abs/2608.17205)
  - Finding: Modality reliance is task-dependent: when one of two conflicting sources is made harder to read, five of six open-weight VLMs on GSM8K/SVAMP arithmetic conflicts move away from degraded text more strongly than from degraded images, but on ChartQA-Conflict all six likelihood-scored models do the reverse and move away from the degraded chart more strongly; this reversal holds after calibrating for unimodal accuracy loss and with plain table images, and GPT-5.6-Luna and Gemini-3.5-Flash reproduce it behaviorally.
  - Relation to ours: partial overlap: the same marks-vs-text question, but here the text is an external report next to the chart. In our setup the conflicting text is printed inside the chart image (labels, ticks, legend), so OCR and marks compete within one image.

## Text printed inside the image (typographic attacks)

- **Multimodal Neurons in Artificial Neural Networks** — Gabriel Goh et al., *Distill*, 2021. [https://distill.pub/2021/multimodal-neurons/](https://distill.pub/2021/multimodal-neurons/)
  - Finding: CLIP contains multimodal neurons that fire for the same concept whether it appears as a photo, a drawing, or the written word, and because they react so strongly to text, handwritten mislabels on real objects ("typographic attacks") often flip CLIP's classification (a Granny Smith apple labelled "iPod" was read as iPod with 99.7% zero-shot probability), while pasting class-name text onto ImageNet validation images reached up to about 97% attack success with roughly 7% of pixels changed.
  - Relation to ours: background (origin of the 'model reads the label instead of looking at the object' idea; our conflict condition is a typographic attack aimed at chart marks instead of objects)

- **Unveiling Typographic Deceptions: Insights of the Typographic Vulnerability in Large Vision-Language Models** — Hao Cheng et al., *ECCV 2024*, 2024. [https://arxiv.org/abs/2402.19150](https://arxiv.org/abs/2402.19150)
  - Finding: Typographic attacks, already known to fool CLIP-style VLMs, are shown to be a widespread threat to well-known commercial and open-source LVLMs; the authors evaluate them on a new large Typographic Dataset covering several multimodal tasks and text factors, derive three findings about why the attacks work, and while validating those findings reduce the attack-induced performance drop from 42.07% to 13.90%.
  - Relation to ours: partial overlap (misleading text inside the image, as in ours, but on natural photos and object/attribute questions, not chart values)

- **SCAM: A Real-World Typographic Robustness Evaluation for Multimodal Foundation Models** — Justus Westerhoff et al., *CVPR 2025 Workshop (EVAL-FoMo-2); also published in Journal of Data-centric Machine Learning Research (DMLR), 2026*, 2025. [https://arxiv.org/abs/2504.04893](https://arxiv.org/abs/2504.04893)
  - Finding: On SCAM (1,162 real photos with misleading handwritten words), typographic attacks still significantly degrade state-of-the-art LVLMs, especially those whose vision encoders are inherently vulnerable; larger LLM backbones reduce this vulnerability and improve typographic understanding, and synthetic attacks closely resemble real handwritten ones.
  - Relation to ours: partial overlap (clean / attacked / synthetic triplet is close to our consistent / conflict design; their result that a bigger LLM resists more is a useful comparison for 3B PaliGemma 2 at 224 vs 448)

## Charts without printed numbers (our no-numbers condition)

- **ChartBench: A Benchmark for Complex Visual Reasoning in Charts** — Zhengzhuo Xu et al., *arXiv*, 2023. [https://arxiv.org/abs/2312.15915](https://arxiv.org/abs/2312.15915)
  - Finding: ChartBench (42 categories, 66.6k charts, 600k QA pairs, many charts without data-point annotations, scored with a new Acc+ metric) shows in tests of 18 open-source and 3 proprietary MLLMs that they are limited at chart comprehension, and the authors add chain-of-thought and supervised fine-tuning baselines to improve results on unannotated charts.
  - Relation to ours: Same question, matching our consistent vs no-numbers contrast. The paper body says the annotated-minus-unannotated gap grows as models get stronger (e.g. GPT-4V about +34 pts): stronger models gain more from reading printed numbers than from reading the marks. It has no conflict condition.

- **Do MLLMs Really Understand the Charts?** — Xiao Zhang et al., *arXiv*, 2025. [https://arxiv.org/abs/2509.04457](https://arxiv.org/abs/2509.04457)
  - Finding: Most MLLMs show alarming hallucinations and a significant drop in performance on charts without annotations. The authors argue this is because the models rely on visual recognition rather than visual reasoning, and they introduce ChartVRBench, which tests value estimation on non-annotated charts, along with ChartVR-3B/7B models trained with VR-RFT that beat strong proprietary models on it and generalize to other chart benchmarks.
  - Relation to ours: Same question, for our no-numbers condition. The paper body reports GPT-4o at about 21% on ChartVRBench against about 88% for humans. Like ChartBench, it removes text but never makes text contradict the marks.

- **Towards Understanding Graphical Perception in Large Multimodal Models** — Kai Zhang et al., *arXiv (2503.10857, v1, "Work in Progress")*, 2025. [https://arxiv.org/abs/2503.10857](https://arxiv.org/abs/2503.10857)
  - Finding: The authors used graphical-perception theory to build an automated framework for testing chart perception in LMMs, and found that leading models including GPT-4o fail to generalize across chart types, fail to understand basic visual elements, and fail to cross-reference values within a chart.
  - Relation to ours: Same question (reliance on annotations). The paper body reports GPT-4o drops from 85.0% on annotated bars to 53.4% without annotations. Without labels, models still find the right region but cannot read the value off the axis. This is the attention-level version of what our no-numbers condition measures.

- **Evaluating Graphical Perception with Multimodal LLMs** — Rami Huu Nguyen et al., *IEEE PacificVis 2025 (arXiv comments field: "IEEE Pacific Visualization 2025 Conference"; arXiv 2504.04221)*, 2025. [https://arxiv.org/abs/2504.04221](https://arxiv.org/abs/2504.04221)
  - Finding: Reproducing Cleveland and McGill's 1984 graphical-perception experiment with fine-tuned and pretrained MLLMs under zero-shot prompting, the authors find that MLLMs outperform human task performance in some cases but not in others.
  - Relation to ours: Background. Classic marks-only perception (angle vs length vs position) with no printed numbers. Useful for justifying why our marks include needle angle, slice size and bar height, and for the expectation that angle/area are harder than position/length.

- **ChartInsights: Evaluating Multimodal Large Language Models for Low-Level Chart Question Answering** — Yifan Wu et al., *Findings of EMNLP 2024 (pp. 12174-12200; arXiv 2405.07001)*, 2024. [https://aclanthology.org/2024.findings-emnlp.710/](https://aclanthology.org/2024.findings-emnlp.710/)
  - Finding: Across 19 MLLMs on 22,347 low-level chart QA samples (10 tasks, 7 chart types), average accuracy is 39.8% with GPT-4o best at 69.17%; the proposed Chain-of-Charts text prompt raises GPT-4o to 83.58% (+14.41%), and adding a visual prompt that points to the relevant chart elements raises it to 84.32%.
  - Relation to ours: Partial overlap, through the label-removal variants. The paper body reports that removing data labels hurts GPT-4o across seven chart types, but improves anomaly detection (+17.5%) and filtering (+5.5%). So printed numbers can pull a model away from comparing marks, which our conflict condition tests directly.

- **Are Large Vision Language Models up to the Challenge of Chart Comprehension and Reasoning? An Extensive Investigation into the Capabilities and Limitations of LVLMs** — Mohammed Saidul Islam et al., *Findings of EMNLP 2024*, 2024. [https://arxiv.org/abs/2406.00257](https://arxiv.org/abs/2406.00257)
  - Finding: In a broad evaluation of closed and open-source LVLMs on chart QA, summarization and fact-checking tasks, the models write fluent text that captures high-level data insights but also hallucinate, make factual errors and show data bias.
  - Relation to ours: partial overlap (ChartQA* matches our no-numbers condition and shows that models lean on printed numbers; it has no conflict condition)

## Misleading charts (our upside-down axis / reversed legend)

- **Chart Deception in Vision-Language Models: From Vulnerability to Mitigation** — Ridwan Mahbub et al., *arXiv (2607.22600)*, 2026. [https://arxiv.org/abs/2607.22600](https://arxiv.org/abs/2607.22600)
  - Finding: On VisDeception (1,600 paired faithful/misleading charts across 8 deception categories), 32,000 responses from 10 VLMs show that even advanced models remain highly vulnerable to deceptive chart designs, particularly axis transformations, misleading encodings and color semantics; a multi-agent framework that grounds reasoning in structured chart metadata reduces deception-induced error for most models (e.g., Gemini 2.5 Pro's Deception Score drops from 0.099 to 0.024, a 76% reduction).
  - Relation to ours: partial overlap: their Deception Score uses the same logic as our consistent/no-numbers baselines (subtract baseline chart-reading error to isolate the effect of the manipulation). They manipulate design, not text.

- **Unmasking Deceptive Visuals: Benchmarking Multimodal Large Language Models on Misleading Chart Question Answering** — Zixin Chen et al., *EMNLP 2025 (Main Conference, pp. 13756-13789; arXiv 2503.18172)*, 2025. [https://arxiv.org/abs/2503.18172](https://arxiv.org/abs/2503.18172)
  - Finding: The paper introduces Misleading ChartQA, a set of 3,026 expert-validated multiple-choice examples covering 21 misleader types and 10 chart types, and uses it to test 24 state-of-the-art MLLMs, which already show strong chart comprehension, on detecting and interpreting misleading charts, a capacity no one had measured before; it also proposes a region-aware reasoning pipeline that improves model accuracy.
  - Relation to ours: partial overlap: the 'misleading distractor' option works much like our 'follows marks' vs 'follows text' scoring, and Deceptive Labeling is close to our label-only conflict. Difference: it uses real misleader designs and four-option MCQ, with no pixel-identical mark control and no multilingual condition.

- **CHARTOM: A Visual Theory-of-Mind Benchmark for LLMs on Misleading Charts** — Shubham Bharti et al., *arXiv*, 2024. [https://arxiv.org/abs/2408.14419](https://arxiv.org/abs/2408.14419)
  - Finding: The authors tested leading multimodal LLMs (GPT, Claude, Gemini, Qwen, Llama and LLaVA series) on CHARTOM, which asks both FACT questions (what the chart actually shows) and MIND questions (would the chart mislead a human reader), and every model found both kinds of question hard.
  - Relation to ours: partial overlap: the FACT questions on paired normal/manipulated charts (including inverted axes and inverted color scales, close to our reversed-legend case) are a small-scale version of our consistent-vs-conflict comparison, with human calibration that we do not have.

- **Protecting multimodal large language models against misleading visualizations** — Jonathan Tonglet et al., *ACL 2026 (Proceedings of the 64th Annual Meeting of the ACL, Volume 1: Long Papers), pp. 8329-8349*, 2026. [https://aclanthology.org/2026.acl-long.377/](https://aclanthology.org/2026.acl-long.377/)
  - Finding: On misleading visualizations (charts that distort the underlying data), MLLM question-answering accuracy drops on average to the random-baseline level; of six inference-time methods compared, table-based QA and redrawing the visualization are effective, improving accuracy by up to 19.6 percentage points.
  - Relation to ours: partial overlap (inverted axis and odd ticks are text-vs-geometry conflicts close to our conflict edits, but they are framed as charts misleading humans, not as a clean marks-vs-text test with a matched consistent version)

- **Is this chart lying to me? Automating the detection of misleading visualizations** — Jonathan Tonglet et al., *ACL 2026 (Main Conference)*, 2026. [https://arxiv.org/abs/2508.21675](https://arxiv.org/abs/2508.21675)
  - Finding: On Misviz (2,604 real-world charts annotated with 12 types of misleaders) and Misviz-synth (57,665 Matplotlib charts built from real data tables), the authors evaluate state-of-the-art MLLMs, rule-based systems and image-axis classifiers, and find that automatically detecting misleading visualizations and identifying which design rules they violate is still highly challenging.
  - Relation to ours: background: the detection side of the field (is this chart misleading?), whereas we measure which channel the answer follows. Useful as a source of synthetic inverted- and truncated-axis charts.

- **An Empirical Evaluation of the GPT-4 Multimodal Language Model on Visualization Literacy Tasks** — Alexander Bendeck et al., *IEEE VIS 2024 (published in IEEE TVCG 31(1), Jan 2025, pp. 1105-1115)*, 2024. [https://ieeevis.org/year/2024/program/paper_v-full-1147.html](https://ieeevis.org/year/2024/program/paper_v-full-1147.html)
  - Finding: On four task sets (VLAT, chart QA, deceptive-design questions, and misaligned-title questions), GPT-4V can recognize trends and extreme values and shows some grasp of visualization design best practices, but struggles with simple value retrieval when it is not given the original dataset, cannot reliably tell chart colors apart, and sometimes hallucinates or answers inconsistently.
  - Relation to ours: background: the misaligned-titles task is an early text-vs-marks conflict (title vs data), and the finding that GPT-4V is weak at value retrieval without printed numbers relates to our no-numbers condition.

## Edited images vs priors

- **HallusionBench: An Advanced Diagnostic Suite for Entangled Language Hallucination and Visual Illusion in Large Vision-Language Models** — Tianrui Guan et al., *CVPR 2024*, 2024. [https://arxiv.org/abs/2310.14566](https://arxiv.org/abs/2310.14566)
  - Finding: Across 15 LVLMs evaluated on 346 expert-made images and 1,129 questions arranged as control groups, the best model, GPT-4V, reached only 31.42% question-pair accuracy and every other model scored below 16%; the observed failure modes included language hallucination and visual illusion.
  - Relation to ours: Partial overlap, and the closest benchmark in spirit: it edits charts/tables and keeps unedited control versions to tell 'reads the image' apart from 'answers from priors'. The conflict there is between edited image and world knowledge. Ours is between printed text and marks inside the same image.

- **Vision Language Models are Biased** — An Vo et al. et al., *ICLR 2026 (poster)*, 2025. [https://arxiv.org/abs/2505.23941](https://arxiv.org/abs/2505.23941)
  - Finding: On counting tasks with counterfactual images of popular subjects across 7 domains, state-of-the-art VLMs average only 17.05% accuracy (for example, they fail to notice a 4th stripe added to a 3-stripe Adidas logo), and removing image backgrounds nearly doubles accuracy (+21.09 points), which suggests contextual visual cues trigger the biased answers.
  - Relation to ours: Partial overlap. Same edited-image method for exposing priors overriding pixels. A search snippet (not the abstract) also says adding text with the subject's name into the image lowers accuracy further, which parallels our printed-text conflict.

- **Vision language models are blind: Failing to translate detailed visual features into words** — Pooyan Rahmanzadehgervi et al. et al., *ACCV 2024 (arXiv 2407.06581)*, 2024. [https://arxiv.org/abs/2407.06581](https://arxiv.org/abs/2407.06581)
  - Finding: On BlindTest, 7 very simple low-level tasks such as checking whether two circles overlap or counting line intersections, four state-of-the-art VLMs average only 58.07% (best: Claude 3.5 Sonnet at 77.84%, against an expected 100% for humans); they struggle most when shapes overlap or sit close together and reach near 100% when the shapes are spaced apart, and linear probes show the vision encoder holds enough information while the language model fails to decode it into correct answers.
  - Relation to ours: Background. It explains why reading bar heights, slice sizes or needle angles without printed numbers (our no-numbers condition) is hard for VLMs, and why they may fall back on text when it is present.

- **Chartographer: Counterfactual Chart Generation for Evaluating Vision-Language Models** — Yifan Jiang et al., *EMNLP 2026 (Main)*, 2026. [https://arxiv.org/abs/2605.27311](https://arxiv.org/abs/2605.27311)
  - Finding: Counterfactual charts, which keep the chart-question task fixed but change the underlying data and answer, reveal failures that single-chart scores hide: VLMs often fail to generalize after answering the original chart correctly, and failures are most common when the updated chart requires a novel visual reasoning pathway.
  - Relation to ours: Partial overlap. A chart-specific counterfactual benchmark testing whether models really read the chart or pattern-match. It changes the data (marks and text together), whereas we keep the marks fixed and change only the text.

- **Disentangling Visual and Factual Correctness in LVLMs' Visualization Literacy** — Soohyun Lee et al., *arXiv (2606.03142; under review at IEEE TVCG, not yet accepted)*, 2026. [https://arxiv.org/abs/2606.03142](https://arxiv.org/abs/2606.03142)
  - Finding: Across 15 LVLMs, near-human VLAT scores may reflect factual recall rather than visual understanding; on the counterfactual CVLAT, most models (9 of 15 by VFRI sign) follow the chart and a minority follow factual priors, while 30 humans overwhelmingly follow the chart; prompting can shift which source a model prioritizes, but the effect is highly model-dependent and asymmetric in direction, and chart-reading skill does not predict how controllable a model is by prompt.
  - Relation to ours: Partial overlap. Same 'which source wins' design and a reliance index similar to a marks-follow rate, but the conflict is chart vs world knowledge, not marks vs printed text inside the same chart. I found no published benchmark that pits pixel-identical marks against contradicting in-chart labels, ticks and legends, let alone bilingually (en/tr). Our setup appears to fill that gap.
