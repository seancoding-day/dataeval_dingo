# RuleQuanliangFieldValidation Label 说明

## 实现位置

[`rule_quanliang.py`](../../dingo/model/rule/scibase/rule_quanliang.py)

## 标签数量统计

| 字段 | 标签数量 |
|---|---:|
| `metadata_type` | 5 |
| `doi` | 6 |
| `isbns` | 4 |
| `isbn13` | 4 |
| `title` | 21 |
| `abstract` | 21 |
| `language` | 4 |
| `author` | 9 |
| `contributors` | 4 |
| `locations` | 6 |
| `access_is_oa` | 4 |
| `access_oa_status` | 4 |
| `access_oa_url` | 4 |
| `access_license` | 4 |
| `publication_published_date` | 5 |
| `publication_published_year` | 3 |
| `publication_venue_issn` | 4 |
| `publication_venue_biblio_volume` | 4 |
| `publication_venue_biblio_issue` | 4 |
| `publication_venue_biblio_pages` | 6 |
| `publication_pages` | 3 |
| `publication_venue_name_unified` | 5 |
| `grade_class` | 4 |
| `grade` | 5 |
| `references` | 23 |
| `related_works` | 23 |
| `citations` | 23 |
| `supplementary_material` | 4 |
| `cited_by_api_url` | 4 |
| `access_xinghe_repository_sha256` | 4 |
| `access_xinghe_repository_origin_path` | 3 |
| `access_xinghe_repository_model_name` | 4 |
| `access_xinghe_repository_model_version` | 5 |
| **合计** | **236** |

## metadata_type

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `metadata_type.missing_field` | 字段缺失 | 检查输入对象中是否存在 `metadata_type` 字段。 |
| `metadata_type.null` | 值为 null | 检查字段值是否为 `null`。 |
| `metadata_type.empty` | 值为空 | 若值为空，则标记。 |
| `metadata_type.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `metadata_type.unsupported_value` | 值不在限定范围内 | 值须属于 2 个限定值之一：`paper`、`ebook`。 |

## doi

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `doi.missing_field` | 字段缺失 | 检查输入对象中是否存在 `doi` 字段。 |
| `doi.empty` | 值为空 | 若论文 DOI 为空，则标记。 |
| `doi.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `doi.not_lowercase` | 不是小写字母 | 若 DOI 不是小写，则标记。 |
| `doi.format_invalid` | 格式不符合要求 | 若DOI 格式错误，包含空白或分隔符，或者输入了 DOI URL，则标记。 |
| `doi.error_prefix` | 前缀不符合要求 | 提取 DOI 的 `/` 前缀；命中 3 个测试前缀 `10.0000`、`10.0001`、`10.5555` 时标记。 |

## isbns

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `isbns.missing_field` | 字段缺失 | 检查输入对象中是否存在 `isbns` 字段。 |
| `isbns.empty` | 值为空 | 若电子书 ISBN 列表为空，则标记。 |
| `isbns.wrong_type` | 字段类型错误 | 值不是字符串列表时标记。 |
| `isbns.invalid_format` | 格式不符合要求 | 若ISBN 格式或校验位错误，则标记。 |

## isbn13

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `isbn13.missing_field` | 字段缺失 | 检查输入对象中是否存在 `isbn13` 字段。 |
| `isbn13.empty` | 值为空 | 若电子书 ISBN13 为空，则标记。 |
| `isbn13.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `isbn13.invalid_format` | 格式不符合要求 | 若ISBN13 格式或校验位错误，则标记。 |

## title

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `title.missing_field` | 字段缺失 | 检查输入对象中是否存在 `title` 字段。 |
| `title.null` | 值为 null | 检查字段值是否为 `null`。 |
| `title.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `title.html_tag_layout` | 包含 HTML 标签-排版标签 | 若包含 HTML 排版标签，则标记。 |
| `title.html_tag_math` | 包含 HTML 标签-数学标签 | 若包含 MathML 标签，则标记。 |
| `title.html_tag_xml_comment` | 包含 HTML 标签-XML 注释 | 若包含 XML 注释，则标记。 |
| `title.html_tag_cdata` | 包含 HTML 标签-CDATA 内容 | 若包含 CDATA 片段，则标记。 |
| `title.html_entity_named` | 包含 HTML 实体-命名实体 | 若包含命名 HTML entity，则标记。 |
| `title.html_entity_decimal` | 包含 HTML 实体-十进制数字实体 | 若包含十进制数字 HTML entity，则标记。 |
| `title.html_entity_hex` | 包含 HTML 实体-十六进制数字实体 | 若包含十六进制数字 HTML entity，则标记。 |
| `title.special_char_invisible` | 包含特殊字符-不可见字符 | 若包含不可见字符，则标记。 |
| `title.special_char_replacement` | 包含特殊字符-Unicode 替换字符 | 若包含 Unicode 替换字符，则标记。 |
| `title.special_char_control` | 包含特殊字符-控制字符 | 若包含控制字符，则标记。 |
| `title.special_char_markup` | 包含特殊字符-排版标记 | 若包含方括号排版标记，则标记。 |
| `title.empty` | 值为空 | 若去除首尾空格后内容为空，则标记。 |
| `title.too_short` | 内容过短 | 若去除首尾空格后长度小于 5 个字符，则标记。 |
| `title.too_long` | 内容过长 | 若去除首尾空格后长度大于 1000 个字符，则标记。 |
| `title.likely_placeholder` | 疑似占位内容 | 若内容可能是标题占位文本，则标记。 |
| `title.encoding_error` | 编码错误 | 若包含 Unicode 替换字符或典型乱码组合，则标记。 |
| `title.likely_conference` | 疑似会议名称 | 若内容可能是 IEEE 会议名称而非论文标题，则标记。 |
| `title.likely_identifier` | 疑似标识符或链接 | 若标题整体可能是数字标识符、DOI、URL 或 S3 路径，则标记。 |

## abstract

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `abstract.missing_field` | 字段缺失 | 检查输入对象中是否存在 `abstract` 字段。 |
| `abstract.null` | 值为 null | 检查字段值是否为 `null`。 |
| `abstract.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `abstract.html_tag_layout` | 包含 HTML 标签-排版标签 | 若包含 HTML 排版标签，则标记。 |
| `abstract.html_tag_math` | 包含 HTML 标签-数学标签 | 若包含 MathML 标签，则标记。 |
| `abstract.html_tag_xml_comment` | 包含 HTML 标签-XML 注释 | 若包含 XML 注释，则标记。 |
| `abstract.html_tag_cdata` | 包含 HTML 标签-CDATA 内容 | 若包含 CDATA 片段，则标记。 |
| `abstract.html_entity_named` | 包含 HTML 实体-命名实体 | 若包含命名 HTML entity，则标记。 |
| `abstract.html_entity_decimal` | 包含 HTML 实体-十进制数字实体 | 若包含十进制数字 HTML entity，则标记。 |
| `abstract.html_entity_hex` | 包含 HTML 实体-十六进制数字实体 | 若包含十六进制数字 HTML entity，则标记。 |
| `abstract.special_char_invisible` | 包含特殊字符-不可见字符 | 若包含不可见字符，则标记。 |
| `abstract.special_char_replacement` | 包含特殊字符-Unicode 替换字符 | 若包含 Unicode 替换字符，则标记。 |
| `abstract.special_char_control` | 包含特殊字符-控制字符 | 若包含控制字符，则标记。 |
| `abstract.special_char_markup` | 包含特殊字符-排版标记 | 若包含方括号排版标记，则标记。 |
| `abstract.empty` | 值为空 | 若去除首尾空格后内容为空，则标记。 |
| `abstract.too_short` | 内容过短 | 若去除首尾空格后长度小于 20 个字符，则标记。 |
| `abstract.too_long` | 内容过长 | 若去除首尾空格后长度大于 6000 个字符，则标记。 |
| `abstract.likely_placeholder` | 疑似占位内容 | 若内容可能是无摘要占位文本，则标记。 |
| `abstract.encoding_error` | 编码错误 | 若包含 Unicode 替换字符或典型乱码组合，则标记。 |
| `abstract.same_title` | 内容与标题重复 | 若摘要与标题去除首尾空格并忽略大小写后完全相同，则标记。 |
| `abstract.likely_identifier` | 疑似标识符或链接 | 若摘要整体可能是数字标识符、DOI、URL 或 S3 路径，则标记。 |

## language

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `language.missing_field` | 字段缺失 | 检查输入对象中是否存在 `language` 字段。 |
| `language.null` | 值为 null | 检查字段值是否为 `null`。 |
| `language.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `language.unsupported_value` | 值不在限定范围内 | 值须属于 ISO 639 映射表中的 8038 个语言代码之一，例如 `zh`、`en`、`fr`、`de`。 |

## author

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `author.missing_field` | 字段缺失 | 检查输入对象中是否存在 `author` 字段。 |
| `author.null` | 值为 null | 检查字段值是否为 `null`。 |
| `author.wrong_type` | 字段类型错误 | 检查值是否为作者对象列表，并逐项检查对象属性类型。 |
| `author.invalid_keys` | key 不符合要求 | 若作者对象字段不符合要求，则标记。 |
| `author.empty` | 值为空 | 若作者列表为空，则标记。 |
| `author.empty_name` | 名称为空 | 若至少一个作者姓名去除首尾空格后为空，则标记。 |
| `author.duplicated_name` | 名称重复 | 若标准化后的非空作者姓名存在重复，则标记。 |
| `author.invalid_separator` | 包含非法分隔符 | 若作者姓名包含竖线、分号或连续两个逗号，则标记。 |
| `author.invalid_orcid` | ORCID 不合法 | 若ORCID URL 格式或校验位错误，则标记。 |

## contributors

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `contributors.missing_field` | 字段缺失 | 检查输入对象中是否存在 `contributors` 字段。 |
| `contributors.null` | 值为 null | 检查字段值是否为 `null`。 |
| `contributors.wrong_type` | 字段类型错误 | 值不是字符串列表时标记。 |
| `contributors.invalid_separator` | 包含非法分隔符 | 若姓名包含非法分隔符，则标记。 |

## locations

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `locations.missing_field` | 字段缺失 | 检查输入对象中是否存在 `locations` 字段。 |
| `locations.null` | 值为 null | 检查字段值是否为 `null`。 |
| `locations.wrong_type` | 字段类型错误 | 检查值是否为列表，并逐项检查列表项类型。 |
| `locations.missing_key` | key 缺失 | 若位置对象缺少必需字段，则标记。 |
| `locations.invalid_value` | 值不合法 | 逐项检查位置对象：`type` 共 4 个限定值，`license` 共 27 个限定值，`is_oa` 共 3 个限定值；例如 `type=download`、`license=cc-by`、`is_oa=true`。 |
| `locations.invalid_url` | URL 不合法 | 若URL 格式错误，则标记。 |

## access_is_oa

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_is_oa.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_is_oa` 字段。 |
| `access_is_oa.empty` | 值为空 | 若论文开放获取标记为空，则标记。 |
| `access_is_oa.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `access_is_oa.unsupported_value` | 值不在限定范围内 | 值须属于 3 个限定值之一：`true`、`false`、`unknown`。 |

## access_oa_status

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_oa_status.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_oa_status` 字段。 |
| `access_oa_status.null` | 值为 null | 检查字段值是否为 `null`。 |
| `access_oa_status.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `access_oa_status.unsupported_value` | 值不在限定范围内 | 值须属于 7 个限定值之一，例如 `diamond`、`gold`、`green`、`closed`，也允许空字符串。 |

## access_oa_url

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_oa_url.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_oa_url` 字段。 |
| `access_oa_url.null` | 值为 null | 检查字段值是否为 `null`。 |
| `access_oa_url.wrong_type` | 字段类型错误 | 值不是字符串列表时标记。 |
| `access_oa_url.invalid_url` | URL 不合法 | 若列表中存在无效 URL，则标记。 |

## access_license

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_license.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_license` 字段。 |
| `access_license.null` | 值为 null | 检查字段值是否为 `null`。 |
| `access_license.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `access_license.unsupported_value` | 值不在限定范围内 | 值须属于 27 个限定值之一，例如 `cc-by`、`cc0`、`mit`、`public-domain`，也允许空字符串。 |

## publication_published_date

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_published_date.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_published_date` 字段。 |
| `publication_published_date.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_published_date.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `publication_published_date.invalid_format` | 格式不符合要求 | 若不符合 YYYY-MM-DD 格式，则标记。 |
| `publication_published_date.invalid_date` | 日期不合法 | 若不是有效日历日期，则标记。 |

## publication_published_year

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_published_year.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_published_year` 字段。 |
| `publication_published_year.wrong_type` | 字段类型错误 | 值的类型不是整数时标记。 |
| `publication_published_year.out_of_range` | 数值超出有效范围 | 若年份超出有效范围，则标记。 |

## publication_venue_issn

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_venue_issn.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_venue_issn` 字段。 |
| `publication_venue_issn.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_venue_issn.wrong_type` | 字段类型错误 | 值不是字符串列表时标记。 |
| `publication_venue_issn.invalid_format` | 格式不符合要求 | 若ISSN 格式或校验位错误，则标记。 |

## publication_venue_biblio_volume

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_venue_biblio_volume.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_venue_biblio_volume` 字段。 |
| `publication_venue_biblio_volume.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_venue_biblio_volume.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `publication_venue_biblio_volume.invalid_format` | 格式不符合要求 | 若值不能转换为整数，则标记。 |

## publication_venue_biblio_issue

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_venue_biblio_issue.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_venue_biblio_issue` 字段。 |
| `publication_venue_biblio_issue.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_venue_biblio_issue.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `publication_venue_biblio_issue.invalid_format` | 格式不符合要求 | 若值不能转换为整数，则标记。 |

## publication_venue_biblio_pages

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_venue_biblio_pages.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_venue_biblio_pages` 字段。 |
| `publication_venue_biblio_pages.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_venue_biblio_pages.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `publication_venue_biblio_pages.invalid_format` | 格式不符合要求 | 若不符合 `<起始页>-<结束页>` 格式，则标记。 |
| `publication_venue_biblio_pages.out_of_range` | 数值超出有效范围 | 若页码不是正数，则标记。 |
| `publication_venue_biblio_pages.page_order` | 页码顺序错误 | 若起始页大于结束页，则标记。 |

## publication_pages

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_pages.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_pages` 字段。 |
| `publication_pages.wrong_type` | 字段类型错误 | 值的类型不是整数时标记。 |
| `publication_pages.out_of_range` | 数值超出有效范围 | 若页数不大于 0，则标记。 |

## publication_venue_name_unified

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `publication_venue_name_unified.missing_field` | 字段缺失 | 检查输入对象中是否存在 `publication_venue_name_unified` 字段。 |
| `publication_venue_name_unified.null` | 值为 null | 检查字段值是否为 `null`。 |
| `publication_venue_name_unified.wrong_type` | 字段类型错误 | 检查当前字段及其依赖字段的类型是否符合要求。 |
| `publication_venue_name_unified.missing_dependency` | 缺少依赖字段 | 若缺少期刊原始名称，无法校验，则标记。 |
| `publication_venue_name_unified.mismatch` | 值与预期不一致 | 若与预期统一名称不一致，则标记。 |

## grade_class

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `grade_class.missing_field` | 字段缺失 | 检查输入对象中是否存在 `grade_class` 字段。 |
| `grade_class.null` | 值为 null | 检查字段值是否为 `null`。 |
| `grade_class.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `grade_class.unsupported_value` | 值不在限定范围内 | 值须属于 5 个限定值之一：`k12`、`higher-edu`、`vocational-edu`、`other` 或空字符串。 |

## grade

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `grade.missing_field` | 字段缺失 | 检查输入对象中是否存在 `grade` 字段。 |
| `grade.null` | 值为 null | 检查字段值是否为 `null`。 |
| `grade.wrong_type` | 字段类型错误 | 检查当前字段与 `grade_class` 是否均为字符串。 |
| `grade.unsupported_value` | 值不在限定范围内 | 值须属于 4 个限定值之一：`小学`、`初中`、`高中` 或空字符串。 |
| `grade.grade_mismatch` | 年级与教育类型不匹配 | 若非 K12 类型设置了年级，则标记。 |

## references

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `references.missing_field` | 字段缺失 | 检查输入对象中是否存在 `references` 字段。 |
| `references.null` | 值为 null | 检查字段值是否为 `null`。 |
| `references.wrong_type` | 字段类型错误 | 检查值是否为列表，并逐项检查列表项类型。 |
| `references.invalid_keys` | key 不符合要求 | 若列表项字段不符合要求，则标记。 |
| `references.empty` | 值为空 | 若`id_type` 或非 DOI 标识符为空，则标记。 |
| `references.title_null` | 标题为 null | 检查列表项中的 `title` 是否为 `null`。 |
| `references.title_wrong_type` | 标题类型错误 | 列表项中的 `title` 不是字符串时标记。 |
| `references.title_html_tag_layout` | 标题包含 HTML 标签-排版标签 | 若标题包含 HTML 排版标签，则标记。 |
| `references.title_html_tag_math` | 标题包含 HTML 标签-数学标签 | 若标题包含 MathML 标签，则标记。 |
| `references.title_html_tag_xml_comment` | 标题包含 HTML 标签-XML 注释 | 若标题包含 XML 注释，则标记。 |
| `references.title_html_tag_cdata` | 标题包含 HTML 标签-CDATA 内容 | 若标题包含 CDATA 片段，则标记。 |
| `references.title_html_entity_named` | 标题包含 HTML 实体-命名实体 | 若标题包含命名 HTML entity，则标记。 |
| `references.title_html_entity_decimal` | 标题包含 HTML 实体-十进制数字实体 | 若标题包含十进制数字 HTML entity，则标记。 |
| `references.title_html_entity_hex` | 标题包含 HTML 实体-十六进制数字实体 | 若标题包含十六进制数字 HTML entity，则标记。 |
| `references.title_special_char_invisible` | 标题包含特殊字符-不可见字符 | 若标题包含不可见字符，则标记。 |
| `references.title_special_char_replacement` | 标题包含特殊字符-Unicode 替换字符 | 若标题包含 Unicode 替换字符，则标记。 |
| `references.title_special_char_control` | 标题包含特殊字符-控制字符 | 若标题包含控制字符，则标记。 |
| `references.title_special_char_markup` | 标题包含特殊字符-排版标记 | 若标题包含方括号排版标记，则标记。 |
| `references.id_empty` | 标识符为空 | 若DOI 为空，则标记。 |
| `references.id_wrong_type` | 标识符类型错误 | 当标识符类型为 DOI 时，标识符值不是字符串则标记。 |
| `references.id_not_lowercase` | 标识符字母大小写不符合要求 | 若DOI 不是小写，则标记。 |
| `references.id_format_invalid` | 标识符格式不符合要求 | 若DOI 格式错误，则标记。 |
| `references.id_error_prefix` | 标识符前缀不符合要求 | 当标识符类型为 DOI 时，检查前缀是否命中 3 个测试前缀：`10.0000`、`10.0001`、`10.5555`。 |

## related_works

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `related_works.missing_field` | 字段缺失 | 检查输入对象中是否存在 `related_works` 字段。 |
| `related_works.null` | 值为 null | 检查字段值是否为 `null`。 |
| `related_works.wrong_type` | 字段类型错误 | 检查值是否为列表，并逐项检查列表项类型。 |
| `related_works.invalid_keys` | key 不符合要求 | 若列表项字段不符合要求，则标记。 |
| `related_works.empty` | 值为空 | 若`id_type` 或非 DOI 标识符为空，则标记。 |
| `related_works.title_null` | 标题为 null | 检查列表项中的 `title` 是否为 `null`。 |
| `related_works.title_wrong_type` | 标题类型错误 | 列表项中的 `title` 不是字符串时标记。 |
| `related_works.title_html_tag_layout` | 标题包含 HTML 标签-排版标签 | 若标题包含 HTML 排版标签，则标记。 |
| `related_works.title_html_tag_math` | 标题包含 HTML 标签-数学标签 | 若标题包含 MathML 标签，则标记。 |
| `related_works.title_html_tag_xml_comment` | 标题包含 HTML 标签-XML 注释 | 若标题包含 XML 注释，则标记。 |
| `related_works.title_html_tag_cdata` | 标题包含 HTML 标签-CDATA 内容 | 若标题包含 CDATA 片段，则标记。 |
| `related_works.title_html_entity_named` | 标题包含 HTML 实体-命名实体 | 若标题包含命名 HTML entity，则标记。 |
| `related_works.title_html_entity_decimal` | 标题包含 HTML 实体-十进制数字实体 | 若标题包含十进制数字 HTML entity，则标记。 |
| `related_works.title_html_entity_hex` | 标题包含 HTML 实体-十六进制数字实体 | 若标题包含十六进制数字 HTML entity，则标记。 |
| `related_works.title_special_char_invisible` | 标题包含特殊字符-不可见字符 | 若标题包含不可见字符，则标记。 |
| `related_works.title_special_char_replacement` | 标题包含特殊字符-Unicode 替换字符 | 若标题包含 Unicode 替换字符，则标记。 |
| `related_works.title_special_char_control` | 标题包含特殊字符-控制字符 | 若标题包含控制字符，则标记。 |
| `related_works.title_special_char_markup` | 标题包含特殊字符-排版标记 | 若标题包含方括号排版标记，则标记。 |
| `related_works.id_empty` | 标识符为空 | 若DOI 为空，则标记。 |
| `related_works.id_wrong_type` | 标识符类型错误 | 当标识符类型为 DOI 时，标识符值不是字符串则标记。 |
| `related_works.id_not_lowercase` | 标识符字母大小写不符合要求 | 若DOI 不是小写，则标记。 |
| `related_works.id_format_invalid` | 标识符格式不符合要求 | 若DOI 格式错误，则标记。 |
| `related_works.id_error_prefix` | 标识符前缀不符合要求 | 当标识符类型为 DOI 时，检查前缀是否命中 3 个测试前缀：`10.0000`、`10.0001`、`10.5555`。 |

## citations

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `citations.missing_field` | 字段缺失 | 检查输入对象中是否存在 `citations` 字段。 |
| `citations.null` | 值为 null | 检查字段值是否为 `null`。 |
| `citations.wrong_type` | 字段类型错误 | 检查值是否为列表，并逐项检查列表项类型。 |
| `citations.invalid_keys` | key 不符合要求 | 若列表项字段不符合要求，则标记。 |
| `citations.empty` | 值为空 | 若`id_type` 或非 DOI 标识符为空，则标记。 |
| `citations.title_null` | 标题为 null | 检查列表项中的 `title` 是否为 `null`。 |
| `citations.title_wrong_type` | 标题类型错误 | 列表项中的 `title` 不是字符串时标记。 |
| `citations.title_html_tag_layout` | 标题包含 HTML 标签-排版标签 | 若标题包含 HTML 排版标签，则标记。 |
| `citations.title_html_tag_math` | 标题包含 HTML 标签-数学标签 | 若标题包含 MathML 标签，则标记。 |
| `citations.title_html_tag_xml_comment` | 标题包含 HTML 标签-XML 注释 | 若标题包含 XML 注释，则标记。 |
| `citations.title_html_tag_cdata` | 标题包含 HTML 标签-CDATA 内容 | 若标题包含 CDATA 片段，则标记。 |
| `citations.title_html_entity_named` | 标题包含 HTML 实体-命名实体 | 若标题包含命名 HTML entity，则标记。 |
| `citations.title_html_entity_decimal` | 标题包含 HTML 实体-十进制数字实体 | 若标题包含十进制数字 HTML entity，则标记。 |
| `citations.title_html_entity_hex` | 标题包含 HTML 实体-十六进制数字实体 | 若标题包含十六进制数字 HTML entity，则标记。 |
| `citations.title_special_char_invisible` | 标题包含特殊字符-不可见字符 | 若标题包含不可见字符，则标记。 |
| `citations.title_special_char_replacement` | 标题包含特殊字符-Unicode 替换字符 | 若标题包含 Unicode 替换字符，则标记。 |
| `citations.title_special_char_control` | 标题包含特殊字符-控制字符 | 若标题包含控制字符，则标记。 |
| `citations.title_special_char_markup` | 标题包含特殊字符-排版标记 | 若标题包含方括号排版标记，则标记。 |
| `citations.id_empty` | 标识符为空 | 若DOI 为空，则标记。 |
| `citations.id_wrong_type` | 标识符类型错误 | 当标识符类型为 DOI 时，标识符值不是字符串则标记。 |
| `citations.id_not_lowercase` | 标识符字母大小写不符合要求 | 若DOI 不是小写，则标记。 |
| `citations.id_format_invalid` | 标识符格式不符合要求 | 若DOI 格式错误，则标记。 |
| `citations.id_error_prefix` | 标识符前缀不符合要求 | 当标识符类型为 DOI 时，检查前缀是否命中 3 个测试前缀：`10.0000`、`10.0001`、`10.5555`。 |

## supplementary_material

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `supplementary_material.missing_field` | 字段缺失 | 检查输入对象中是否存在 `supplementary_material` 字段。 |
| `supplementary_material.null` | 值为 null | 检查字段值是否为 `null`。 |
| `supplementary_material.wrong_type` | 字段类型错误 | 检查值是否为列表，并逐项检查列表项及其属性类型。 |
| `supplementary_material.invalid_keys` | key 不符合要求 | 若列表项字段不符合要求，则标记。 |

## cited_by_api_url

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `cited_by_api_url.missing_field` | 字段缺失 | 检查输入对象中是否存在 `cited_by_api_url` 字段。 |
| `cited_by_api_url.null` | 值为 null | 检查字段值是否为 `null`。 |
| `cited_by_api_url.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `cited_by_api_url.invalid_url` | URL 不合法 | 若URL 格式错误，则标记。 |

## access_xinghe_repository_sha256

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_xinghe_repository_sha256.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_xinghe_repository_sha256` 字段。 |
| `access_xinghe_repository_sha256.null` | 值为 null | 检查字段值是否为 `null`。 |
| `access_xinghe_repository_sha256.wrong_type` | 字段类型错误 | 检查当前字段的类型，并检查相关全文状态标记的类型。 |
| `access_xinghe_repository_sha256.required` | 必填值为空 | 若存在全文时 SHA256 不能为空，则标记。 |

## access_xinghe_repository_origin_path

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_xinghe_repository_origin_path.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_xinghe_repository_origin_path` 字段。 |
| `access_xinghe_repository_origin_path.wrong_type` | 字段类型错误 | 检查当前字段的类型，并检查相关全文状态标记的类型。 |
| `access_xinghe_repository_origin_path.required` | 必填值为空 | 若存在全文时原始路径不能为空，则标记。 |

## access_xinghe_repository_model_name

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_xinghe_repository_model_name.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_xinghe_repository_model_name` 字段。 |
| `access_xinghe_repository_model_name.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `access_xinghe_repository_model_name.required` | 必填值为空 | 若处理成功时模型名称不能为空，则标记。 |
| `access_xinghe_repository_model_name.unsupported_value` | 值不在限定范围内 | 值须属于 2 个限定值之一：`mineru`、`llm-web-kit`。 |

## access_xinghe_repository_model_version

| Label 名 | 含义 | 实现逻辑 |
|---|---|---|
| `access_xinghe_repository_model_version.missing_field` | 字段缺失 | 检查输入对象中是否存在 `access_xinghe_repository_model_version` 字段。 |
| `access_xinghe_repository_model_version.wrong_type` | 字段类型错误 | 值的类型不是字符串时标记。 |
| `access_xinghe_repository_model_version.required` | 必填值为空 | 若当前条件下模型版本不能为空，则标记。 |
| `access_xinghe_repository_model_version.unsupported_value` | 值不在限定范围内 | 值须属于 4 个限定值之一：`1.3.1`、`2`、`2.5`、`4.1.1`。 |
| `access_xinghe_repository_model_version.model_mismatch` | 模型版本与模型名称不匹配 | 若模型版本与模型名称不匹配，则标记。 |
