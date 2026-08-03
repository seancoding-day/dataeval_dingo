# SAC/TC609 High-quality Dataset Rules

The following eight TC609 rules are currently registered. Rules whose registration decorators are commented out are not included.

| Rule | Metric Type | Description | Standard Source |
|------|-------------|-------------|-----------------|
| Rule_TC609_0201_FormatCompliance | QUALITY_BAD_TC609_0201 | Checks required fields and types against the configured field schema. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
| Rule_TC609_0202_SafetyCompliance | QUALITY_BAD_TC609_0202 | Combines unsafe-word, PII, and identity-card detection for text items in `data_content`. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
| Rule_TC609_0203_AnnotationCompliance | QUALITY_BAD_TC609_0203 | Checks annotation metadata fields, types, and enumerated values. | TC609-5-2025-02 High-quality dataset format requirements |
| Rule_TC609_0204_StructuralCompleteness | QUALITY_BAD_TC609_0204 | Checks configured fields for missing values. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
| Rule_TC609_0205_ContentAuthenticity | QUALITY_BAD_TC609_0205 | Checks source traceability metadata and validates URL syntax when applicable. | TC609-5-2025-02 High-quality dataset format requirements |
| Rule_TC609_0206_ContentConsistency | QUALITY_BAD_TC609_0206 | Checks consistency among text items in `data_content` using multilingual embeddings and robust-center aggregation. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
| Rule_TC609_0207_DataTypeConsistency | QUALITY_BAD_TC609_0207 | Checks whether text items in `data_content` match the configured dataset type. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
| Rule_TC609_0208_ContentCleanliness | QUALITY_BAD_TC609_0208 | Combines available text cleanliness checks; modality coverage is partial. | TC609-5-2025-04 High-quality dataset quality evaluation specification |
