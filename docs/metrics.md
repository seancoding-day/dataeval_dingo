# Data Quality Metrics

This document provides comprehensive information about all quality metrics used in Dingo.

**Note**: All metrics are backed by academic sources to ensure objectivity and scientific rigor.

### RAG Evaluation Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMRAGAnswerRelevancy` | LLMRAGAnswerRelevancy | 璇勪及绛旀鏄惁鐩存帴鍥炵瓟闂锛屾娴嬫棤鍏冲拰鍐椾綑淇℃伅 | [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | N/A | [馃摑 View Example](../examples/rag/dataset_rag_eval_baseline.py) |
| `LLMRAGContextPrecision` | LLMRAGContextPrecision | 璇勪及妫€绱笂涓嬫枃鐨勭簿纭害锛屽寘鎷浉鍏虫€у拰鎺掑簭璐ㄩ噺 | [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | N/A | [馃摑 View Example](../examples/rag/dataset_rag_eval_baseline.py) |
| `LLMRAGContextRecall` | LLMRAGContextRecall | 璇勪及妫€绱笂涓嬫枃鐨勫畬鏁存€э紝鍒ゆ柇涓婁笅鏂囨槸鍚﹁兘鏀寔绛旀涓殑鎵€鏈夐檲杩?| [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | N/A | [馃摑 View Example](../examples/rag/dataset_rag_eval_baseline.py) |
| `LLMRAGContextRelevancy` | LLMRAGContextRelevancy | 璇勪及妫€绱笂涓嬫枃涓庨棶棰樼殑鐩稿叧鎬э紝妫€娴嬪櫔澹颁俊鎭?| [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | N/A | [馃摑 View Example](../examples/rag/dataset_rag_eval_baseline.py) |
| `LLMRAGFaithfulness` | LLMRAGFaithfulness | 璇勪及鐢熸垚绛旀鏄惁蹇犲疄浜庣粰瀹氫笂涓嬫枃锛屾娴嬪够瑙夊拰缂栭€犱俊鎭?| [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217) | N/A | [馃摑 View Example](../examples/rag/dataset_rag_eval_baseline.py) |

### Pretrain Text Quality Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMCodeCompare` | LLMCodeCompare | Compares the effectiveness of two tools in extracting code blocks from HTML to Markdown format by evaluating recognit... | Internal Implementation | N/A | N/A |
| `LLMDatamanAssessment` | LLMDatamanAssessment | Evaluates pre-training data quality using the DataMan methodology (14 standards, 15 domains). Assigns a score (0/1), ... | [DataMan: Data Manager for Pre-training Large Language Models](https://arxiv.org/abs/2502.19363) (Peng et al., 2025) | N/A | N/A |
| `LLMHtmlExtractCompareV2` | LLMHtmlExtractCompareV2 | Compares two HTML main-content extraction tools by computing text diffs and using LLM to judge which preserves more c... | Internal Implementation | N/A | N/A |
| `LLMHtmlExtractCompareV3` | LLMHtmlExtractCompareV3 | Compares two HTML extraction tools using LLM pretraining quality dimensions (completeness, effectiveness, similarity,... | Internal Implementation | N/A | N/A |
| `LLMMathCompare` | LLMMathCompare | Compares the effectiveness of two tools in extracting mathematical formulas from HTML to Markdown format by evaluatin... | Internal Implementation | N/A | N/A |
| `LLMSecurityPolitics` | LLMSecurityPolitics | Evaluates whether the text contains politics-related content | Internal Implementation | N/A | N/A |
| `LLMTableCompare` | LLMTableCompare | Compares the effectiveness of two tools in extracting tables from HTML to Markdown format by evaluating recognition r... | Internal Implementation | N/A | N/A |
| `LLMTextEquation` | LLMTextEquation | Impact-driven text quality evaluation for LLM pretraining, focusing on structural completeness, readability, diversit... | [WanJuanSiLu: A High-Quality Open-Source Webtext Dataset for Low-Resource Languages](https://arxiv.org/abs/2501.14506) (Yu et al., 2025) | [馃搳 See Results](eval/prompt/redpajama_data_evaluated_by_prompt.md) | [馃摑 View Example](../examples/llm_and_rule/llm_local.py) |
| `LLMTextQualityV4` | LLMTextQualityV4 | Enhanced text quality evaluation covering completeness (formulas, tables, code), effectiveness (garbled text, spacing... | [WanJuanSiLu: A High-Quality Open-Source Webtext Dataset for Low-Resource Languages](https://arxiv.org/abs/2501.14506) (Yu et al., 2025) | [馃搳 See Results](eval/prompt/redpajama_data_evaluated_by_prompt.md) | N/A |
| `LLMTextQualityV5` | LLMTextQualityV5 | Impact-driven text quality evaluation for LLM pretraining, focusing on structural completeness, readability, diversit... | [WanJuanSiLu: A High-Quality Open-Source Webtext Dataset for Low-Resource Languages](https://arxiv.org/abs/2501.14506) (Yu et al., 2025) | [馃搳 See Results](eval/prompt/redpajama_data_evaluated_by_prompt.md) | [馃摑 View Example](../examples/llm_and_rule/llm_local.py) |
| `LLMTextTable` | LLMTextTable | Impact-driven text quality evaluation for LLM pretraining, focusing on structural completeness, readability, diversit... | [WanJuanSiLu: A High-Quality Open-Source Webtext Dataset for Low-Resource Languages](https://arxiv.org/abs/2501.14506) (Yu et al., 2025) | [馃搳 See Results](eval/prompt/redpajama_data_evaluated_by_prompt.md) | [馃摑 View Example](../examples/llm_and_rule/llm_local.py) |

### SFT Data Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMFactCheckPublic` | LLMFactCheckPublic | Two-stage factuality evaluation pipeline from GPT-5 | [GPT-5 System Card](https://cdn.openai.com/pdf/8124a3ce-ab78-4f06-96eb-49ea29ffb52f/gpt5-system-card-aug7.pdf) (OpenAI) | N/A | N/A |
| `LLMHallucination` | LLMHallucination | Evaluates whether the response contains factual contradictions or hallucinations against provided context information | [TruthfulQA: Measuring How Models Mimic Human Falsehoods](https://arxiv.org/abs/2109.07958) (Lin et al., 2021) | N/A | N/A |
| `LLMInstructionClarity` | LLMInstructionClarity | Evaluates instruction clarity across four dimensions: self-descriptiveness, consistency, specificity, and completeness | Internal Implementation | [馃搳 See Results](Returns clarity score (0-10) and detailed analysis) | [馃摑 View Example](../examples/sft/evaluate_instruction_quality.py) |
| `LLMTaskDifficulty` | LLMTaskDifficulty | Evaluates task difficulty across cognitive complexity, step complexity, domain knowledge, and constraint density | Internal Implementation | [馃搳 See Results](Returns difficulty level (1-10) with detailed breakdown) | [馃摑 View Example](../examples/sft/evaluate_instruction_quality.py) |
| `LLMText3HHarmless` | LLMText3HHarmless | Checks if responses avoid harmful content, discriminatory language, and dangerous assistance | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [馃搳 See Results](eval/prompt/qa_data_evaluated_by_3h.md) | N/A |
| `LLMText3HHelpful` | LLMText3HHelpful | Assesses if responses address questions directly and follow instructions appropriately | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [馃搳 See Results](eval/prompt/qa_data_evaluated_by_3h.md) | N/A |
| `LLMText3HHonest` | LLMText3HHonest | Evaluates if responses provide accurate information without fabrication or deception | [Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback](https://arxiv.org/pdf/2204.05862) (Bai et al., 2022) | [馃搳 See Results](eval/prompt/qa_data_evaluated_by_3h.md) | N/A |
| `QUALITY_BAD_HALLUCINATION` | RuleHallucinationHHEM | Uses Vectara's HHEM-2.1-Open model for local hallucination detection by evaluating consistency between response and c... | [HHEM-2.1-Open](https://huggingface.co/vectara/hallucination_evaluation_model) (Forrest Bao, Miaoran Li, Rogger Luo, Ofer Mendelevitch) | N/A | N/A |

### Classification Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMClassifyTopic` | LLMClassifyTopic | Classifies text into categories like language processing, writing, code, mathematics, role-play, or knowledge Q&A. Ba... | [BERTopic](https://maartengr.github.io/BERTopic/index.html#quick-start) & [INSTAG](https://arxiv.org/pdf/2308.07074) (Grootendorst, 2022; Wei et al., 2023) | [馃搳 See Results](eval/prompt/text_data_classified_by_topic.md) | N/A |

### Multimodality Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMClassifyQR` | LLMClassifyQR | Identifies images as CAPTCHA, QR code, or normal images | Internal Implementation | N/A | N/A |
| `VLMOCRUnderstanding` | VLMOCRUnderstanding | 璇勪及澶氭ā鎬佹ā鍨嬪鍥剧墖涓枃瀛楀唴瀹圭殑璇嗗埆鍜岀悊瑙ｈ兘鍔涳紝浣跨敤DeepSeek-OCR浣滀负Ground Truth | [DeepSeek-OCR: Contexts Optical Compression](https://github.com/deepseek-ai/DeepSeek-OCR) | [馃搳 See Results](閫氳繃瀵规瘮VLM杈撳嚭涓嶰CR ground truth锛岃瘑鍒枃瀛楅仐婕忋€侀敊璇€佸够瑙夌瓑闂) | N/A |

### Rule-Based TEXT Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `QUALITY_BAD_COMPLETENESS` | RuleLineEndWithEllipsis, RuleLineEndWithTerminal, RuleSentenceNumber, RuleWordNumber | Checks whether the ratio of lines ending with ellipsis is below threshold; Checks whether the ratio of lines ending w... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_EFFECTIVENESS` | RuleAbnormalChar, RuleAbnormalHtml, RuleAlphaWords, RuleAudioDataFormat, RuleCharNumber, RuleColonEnd, RuleContentNull, RuleContentShort, RuleContentShortMultiLan, RuleEnterAndSpace, RuleEnterMore, RuleEnterRatioMore, RuleHtmlEntity, RuleHtmlTag, RuleInvisibleChar, RuleImageDataFormat, RuleLatexSpecialChar, RuleLineJavascriptCount, RuleLoremIpsum, RuleMeanWordLength, RuleNlpDataFormat, RuleSftDataFormat, RuleSpaceMore, RuleSpecialCharacter, RuleStopWord, RuleSymbolWordRatio, RuleVedioDataFormat, RuleOnlyUrl, RuleDictConsistency, RuleDoi, RuleIsbn | Detects garbled text and anti-crawling characters by combining special character and invisible character detection; D... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_FLUENCY` | RuleAbnormalNumber, RuleCharSplit, RuleNoPunc, RuleTextPerplexity, RuleWordSplit, RuleWordStuck | Checks PDF content for abnormal book page or index numbers that disrupt text flow; calculates model-based text perplexity; detects abnormal character and word splitting. | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023); High-quality dataset quality evaluation specification (SAC/TC609) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_RELEVANCE` | RuleHeadWordAr, RuleHeadWordCs, RuleHeadWordHu, RuleHeadWordKo, RuleHeadWordRu, RuleHeadWordSr, RuleHeadWordTh, RuleHeadWordVi, RulePatternSearch, RuleWatermark | Checks whether Arabic content contains irrelevant tail source information; Checks whether Czech content contains irre... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_SECURITY` | RuleIDCard, RuleUnsafeWords, RulePIIDetection | Checks whether content contains ID card information; Checks whether content contains unsafe words; Detects Personal I... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_SIMILARITY` | RuleDocRepeat, RuleDocFormulaRepeat | Evaluates text for consecutive repeated content and multiple occurrences of special characters; Evaluates text for co... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |
| `QUALITY_BAD_TYPE_CONSISTENCY` | RuleDataTypeConsistency | Uses a local zero-shot classifier to check whether content belongs to the type declared in `data.type`. | High-quality dataset classification guide (SAC/TC609) | N/A | N/A |
| `QUALITY_BAD_UNDERSTANDABILITY` | RuleCapitalWords, RuleCurlyBracket, RuleLineStartWithBulletpoint, RuleUniqueWords | Checks whether the ratio of capital words is above threshold, indicating poor readability; Checks whether the ratio o... | [RedPajama: an Open Dataset for Training Large Language Models](https://github.com/togethercomputer/RedPajama-Data) (Together Computer, 2023) | [馃搳 See Results](eval/rule/slimpajama_data_evaluated_by_rule.md) | N/A |

### Rule-Based IMG Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `QUALITY_BAD_IMG_ARTIMUSE` | RuleImageArtimuse | Evaluates image quality in the field of aesthetics using artimuse | Internal Implementation | N/A | N/A |
| `QUALITY_BAD_IMG_EFFECTIVENESS` | RuleImageValid, RuleImageSizeValid, RuleImageQuality | Checks whether image is not all white or black, ensuring visual content validity; Checks whether image ratio of width... | Internal Implementation | N/A | N/A |
| `QUALITY_BAD_IMG_LABEL_OVERLAP` | RuleImageLabelOverlap | Detects overlapping bounding boxes in image annotations, marks full/partial overlap and generates visualization images | Internal Implementation | N/A | N/A |
| `QUALITY_BAD_IMG_LABEL_VISUALIZATION` | RuleImageLabelVisualization | Generates visualization images with bounding boxes and category labels, helping manual check of annotation accuracy | Internal Implementation | N/A | N/A |
| `QUALITY_BAD_IMG_RELEVANCE` | RuleImageTextSimilarity | Evaluates semantic similarity between image and text content using CLIP model | [Learning Transferable Visual Representations with Natural Language Supervision](https://arxiv.org/abs/2103.00020) (Radford et al., 2021) | N/A | N/A |
| `QUALITY_BAD_IMG_SIMILARITY` | RuleImageRepeat | Detects duplicate images using PHash and CNN methods to ensure data diversity | [ImageNet Classification with Deep Convolutional Neural Networks](https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf) (Krizhevsky et al., 2012) | N/A | N/A |

### Audio Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `QUALITY_BAD_EFFECTIVENESS` | RuleAudioDuration | Check whether the audio duration meets the standard | Internal Implementation | N/A | N/A |
| `QUALITY_BAD_EFFECTIVENESS` | RuleAudioSnrQuality | Check whether the audio signal-to-noise ratio meets the standard | Internal Implementation | N/A | N/A |

### Job Hunting Strategy Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMScout` | LLMScout | Strategic job hunting analysis with industry report parsing and person-job matching | Internal Implementation | N/A | N/A |

### Meta Rater Evaluation Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMMetaRaterCleanliness` | LLMMetaRaterCleanliness | Evaluates text formatting, content appropriateness, and completeness, assessing whether text appears human-edited and... | [Meta-rater: A Multi-dimensional Data Selection Method for Pre-training Language Models](https://arxiv.org/pdf/2504.14194) (Zhuang et al., 2025) | N/A | N/A |
| `LLMMetaRaterProfessionalism` | LLMMetaRaterProfessionalism | Evaluates the degree of expertise and prerequisite knowledge required to comprehend text on a 5-point scale | [Meta-rater: A Multi-dimensional Data Selection Method for Pre-training Language Models](https://arxiv.org/pdf/2504.14194) (Zhuang et al., 2025) | N/A | N/A |
| `LLMMetaRaterReadability` | LLMMetaRaterReadability | Evaluates the clarity and coherence of text using appropriate vocabulary and sentence structures on a 5-point scale | [Meta-rater: A Multi-dimensional Data Selection Method for Pre-training Language Models](https://arxiv.org/pdf/2504.14194) (Zhuang et al., 2025) | N/A | N/A |
| `LLMMetaRaterReasoning` | LLMMetaRaterReasoning | Evaluates the reasoning complexity and logical depth of text content, from simple logical judgments to complex multid... | [Meta-rater: A Multi-dimensional Data Selection Method for Pre-training Language Models](https://arxiv.org/pdf/2504.14194) (Zhuang et al., 2025) | N/A | N/A |

### OCR Eval Metric

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMMinerURecognizeQuality` | LLMMinerURecognizeQuality | Evaluate the quality of mineru recognize | Internal Implementation | [馃搳 See Results](error_category and error_label) | N/A |
| `VLMDocumentParsingOCRTrain` | VLMDocumentParsingOCRTrain | Evaluate the quality of mineru recognize | Internal Implementation | [馃搳 See Results](error_category and error_label) | N/A |

### RAG Retrieved Evidence Chunk Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMChunkQuality` | LLMChunkQuality | Assesses retrieved citation chunks referenced by LLM answers, detecting start-boundary truncation and duplicated lead... | Internal Implementation | N/A | [馃摑 View Example](../examples/rag/sdk_chunk_eval.py) |

### Resume Quality Assessment Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMKeywordMatcher` | LLMKeywordMatcher | Semantic keyword matching between resume and job description | Internal Implementation | N/A | N/A |
| `LLMResumeOptimizer` | LLMResumeOptimizer | ATS-focused resume optimization with keyword injection and STAR polishing | Internal Implementation | N/A | N/A |
| `LLMResumeQuality` | LLMResumeQuality | Comprehensive resume quality evaluation covering privacy, contact, format, structure, professionalism, date, and comp... | Internal Implementation | N/A | N/A |

### Rule-Based Metadata Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `QUALITY_BAD_EFFECTIVENESS` | RuleMetadataSimilarity, RuleQuanliangFieldValidation | 妫€鏌ュ厓鏁版嵁瀛楁涓庡熀鍑嗘暟鎹殑鐩镐技搴﹀尮閰嶏紝闃堝€奸粯璁や负0.6; Validate Quanliang metadata fields and report invalid fields | Internal Implementation | N/A | N/A |

### Rule-Based RESUME Quality Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `RESUME_QUALITY_BAD_COMPLETENESS` | RuleResumeEducationMissing, RuleResumeExperienceMissing | Checks if resume contains education background information; Checks if resume contains work experience information | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_CONTACT` | RuleResumeEmailMissing, RuleResumePhoneMissing, RuleResumePhoneFormat | Checks if resume contains a valid email address; Checks if resume contains a valid phone number; Validates phone numb... | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_DATE` | RuleResumeDateFormat | Detects inconsistent date format usage in resume | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_FORMAT` | RuleResumeExcessiveWhitespace, RuleResumeMarkdown | Detects excessive consecutive spaces in resume; Detects common Markdown syntax errors in resume | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_PRIVACY` | RuleResumeIDCard, RuleResumeDetailedAddress | Detects 18-digit Chinese ID card numbers in resume content; Detects detailed address patterns that may leak privacy | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_PROFESSIONALISM` | RuleResumeEmoji, RuleResumeInformal | Detects emoji usage in resume which reduces professionalism; Detects informal or colloquial expressions in resume | Internal Implementation | N/A | N/A |
| `RESUME_QUALITY_BAD_STRUCTURE` | RuleResumeNameMissing, RuleResumeSectionMissing | Checks if resume contains a name in the first 200 characters; Checks if resume contains required sections like educat... | Internal Implementation | N/A | N/A |

### SFT Data Assessment Metrics - Agent-Enhanced

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `AgentHallucination` | AgentHallucination | Agent-based hallucination detection with automatic web search for missing context | Internal Implementation | N/A | N/A |

### Text Generation

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `LLMLongVideoQa` | LLMLongVideoQa | Generate video-related question-answer pairs based on the summarized information of the input long video. | [VRBench: A Benchmark for Multi-Step Reasoning in Long Narrative Videos](https://arxiv.org/abs/2506.108572) (Jiashuo Yu et al., 2025) | N/A | N/A |

### Other Metrics

| Type | Metric | Description | Paper Source | Evaluation Results | Examples |
|------|--------|-------------|--------------|-------------------|----------|
| `AgentFactCheck` | AgentFactCheck | Agent-based hallucination detection with autonomous web search | Internal Implementation | N/A | N/A |
| `ArticleFactChecker` | ArticleFactChecker | Article-level fact checking with autonomous claims extraction and verification | Internal Implementation | N/A | N/A |
| `LLMCustomMetric` | LLMCustomMetric | Unified metric for user customization | Internal Implementation | N/A | N/A |