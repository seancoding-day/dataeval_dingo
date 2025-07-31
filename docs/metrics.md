# Data Quality Metrics

This document provides comprehensive information about all quality metrics used in Dingo.

**Note**: All metrics are backed by academic sources to ensure objectivity and scientific rigor.

### Text Quality Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `DATAMAN_ASSESSMENT` | PromptDataManAssessment | Evaluates pre-training data quality using the DataMan methodology (14 standards, 15 domains). Assigns a score (0/1), ... | [DataMan: Data Manager for Pre-training Large Language Models](https://arxiv.org/abs/2502.19363) (Peng et al., 2025) | N/A |
| `QUALITY_BAD_SECURITY` | PromptPolitics | Evaluates whether the text contains politics-related content | Internal Implementation | N/A |
| `TEXT_QUALITY_V4` | PromptTextQualityV4 | Enhanced text quality evaluation covering completeness (formulas, tables, code), effectiveness (garbled text, spacing... | [WanJuanSiLu: A High-Quality Open-Source Webtext Dataset for Low-Resource Languages](https://arxiv.org/abs/2501.14506) (Yu et al., 2025) | [📊 See Results](eval/prompt/redpajama_data_evaluated_by_prompt.md) |

### SFT Data Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `QUALITY_BAD_HALLUCINATION` | PromptHallucination | Evaluates whether the response contains factual contradictions or hallucinations against provided context information | [TruthfulQA: Measuring How Models Mimic Human Falsehoods](https://arxiv.org/abs/2109.07958) (Lin et al., 2021) | N/A |
| `QUALITY_BAD_HALLUCINATION` | RuleHallucinationHHEM | Uses Vectara's HHEM-2.1-Open model for local hallucination detection by evaluating consistency between response and c... | [HHEM-2.1-Open](https://huggingface.co/vectara/hallucination_evaluation_model) (Forrest Bao, Miaoran Li, Rogger Luo, Ofer Mendelevitch) | N/A |
| `QUALITY_HARMLESS` | PromptTextHarmless | Checks if responses avoid harmful content, discriminatory language, and dangerous assistance | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [📊 See Results](eval/prompt/qa_data_evaluated_by_3h.md) |
| `QUALITY_HELPFUL` | PromptTextHelpful | Assesses if responses address questions directly and follow instructions appropriately | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [📊 See Results](eval/prompt/qa_data_evaluated_by_3h.md) |
| `QUALITY_HONEST` | PromptTextHonest | Evaluates if responses provide accurate information without fabrication or deception | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [📊 See Results](eval/prompt/qa_data_evaluated_by_3h.md) |

### Classification Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `CLASSIFY_TOPIC` | PromptClassifyTopic | Classifies text into categories like language processing, writing, code, mathematics, role-play, or knowledge Q&A. Ba... | [BERTopic](https://maartengr.github.io/BERTopic/index.html#quick-start) & [INSTAG](https://arxiv.org/pdf/2308.07074) (Grootendorst, 2022; Wei et al., 2023) | [📊 See Results](eval/prompt/text_data_classified_by_topic.md) |

### Multimodality Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `CLASSIFY_QR` | PromptClassifyQR | Identifies images as CAPTCHA, QR code, or normal images | Internal Implementation | N/A |
| `IMAGE_RELEVANT` | PromptImageRelevant | Evaluates if an image matches reference image in terms of face count, feature details, and visual elements | Internal Implementation | N/A |

### Rule-Based TEXT Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `QUALITY_BAD_COMPLETENESS` | RuleLineEndWithEllipsis, RuleLineEndWithTerminal, RuleSentenceNumber, RuleWordNumber | Checks whether the ratio of lines ending with ellipsis is below threshold; Checks whether the ratio of lines ending w... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_EFFECTIVENESS` | RuleAbnormalChar, RuleAbnormalHtml, RuleAlphaWords, RuleCharNumber, RuleColonEnd, RuleContentNull, RuleContentShort, RuleContentShortMultiLan, RuleEnterAndSpace, RuleEnterMore, RuleEnterRatioMore, RuleHtmlEntity, RuleHtmlTag, RuleInvisibleChar, RuleLatexSpecialChar, RuleLineJavascriptCount, RuleLoremIpsum, RuleMeanWordLength, RuleSpaceMore, RuleSpecialCharacter, RuleStopWord, RuleSymbolWordRatio, RuleOnlyUrl | Detects garbled text and anti-crawling characters by combining special character and invisible character detection; D... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_FLUENCY` | RuleAbnormalNumber, RuleCharSplit, RuleNoPunc, RuleWordSplit, RuleWordStuck | Checks PDF content for abnormal book page or index numbers that disrupt text flow; Checks PDF content for abnormal ch... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_RELEVANCE` | RuleHeadWordAr, RuleHeadWordCs, RuleHeadWordHu, RuleHeadWordKo, RuleHeadWordRu, RuleHeadWordSr, RuleHeadWordTh, RuleHeadWordVi, RulePatternSearch, RuleWatermark | Checks whether Arabic content contains irrelevant tail source information; Checks whether Czech content contains irre... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_SECURITY` | RuleIDCard, RuleUnsafeWords | Checks whether content contains ID card information; Checks whether content contains unsafe words | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_SIMILARITY` | RuleDocRepeat | Evaluates text for consecutive repeated content and multiple occurrences of special characters | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |
| `QUALITY_BAD_UNDERSTANDABILITY` | RuleCapitalWords, RuleCurlyBracket, RuleLineStartWithBulletpoint, RuleUniqueWords | Checks whether the ratio of capital words is above threshold, indicating poor readability; Checks whether the ratio o... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [📊 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) |

### Rule-Based IMG Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `QUALITY_BAD_IMG_EFFECTIVENESS` | RuleImageValid, RuleImageSizeValid, RuleImageQuality | Checks whether image is not all white or black, ensuring visual content validity; Checks whether image ratio of width... | Internal Implementation | N/A |
| `QUALITY_BAD_IMG_RELEVANCE` | RuleImageTextSimilarity | Evaluates semantic similarity between image and text content using CLIP model | [Learning Transferable Visual Representations with Natural Language Supervision](https://arxiv.org/abs/2103.00020) (Radford et al., 2021) | N/A |
| `QUALITY_BAD_IMG_SIMILARITY` | RuleImageRepeat | Detects duplicate images using PHash and CNN methods to ensure data diversity | [ImageNet Classification with Deep Convolutional Neural Networks](https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf) (Krizhevsky et al., 2012) | N/A |

### Text Generation

| Type | Metric | Description | Paper Source | Evaluation Results |
|------|--------|-------------|--------------|-------------------|
| `PromptLongVideoQa` | PromptLongVideoQa | Generate video-related question-answer pairs based on the summarized information of the input long video. | [VRBench: A Benchmark for Multi-Step Reasoning in Long Narrative Videos](https://arxiv.org/abs/2506.108572) (Jiashuo Yu et al., 2025) | N/A |

