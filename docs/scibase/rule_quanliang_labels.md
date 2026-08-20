# RuleQuanliangFieldValidation Label 说明

## 实现位置

[`rule_quanliang.py`](../../dingo/model/rule/scibase/rule_quanliang.py)

## 标签数量统计

| 字段 | 标签数量 |
|---|---:|
| `metadata_type` | 5 |
| `doi` | 7 |
| `isbns` | 4 |
| `isbn13` | 4 |
| `title` | 21 |
| `abstract` | 21 |
| `language` | 4 |
| `author` | 7 |
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
| `references` | 24 |
| `related_works` | 24 |
| `citations` | 24 |
| `supplementary_material` | 4 |
| `cited_by_api_url` | 4 |
| `access_xinghe_repository_sha256` | 4 |
| `access_xinghe_repository_origin_path` | 3 |
| `access_xinghe_repository_model_name` | 4 |
| `access_xinghe_repository_model_version` | 5 |
| **合计** | **238** |

## metadata_type

| Label 名 | 含义 |
|---|---|
| `metadata_type.missing_field` | 缺少字段 |
| `metadata_type.null` | 值为 null |
| `metadata_type.empty` | 值为空 |
| `metadata_type.wrong_type` | 值不是字符串 |
| `metadata_type.unsupported_value` | 元数据类型不受支持 |

## doi

| Label 名 | 含义 |
|---|---|
| `doi.missing_field` | 缺少字段 |
| `doi.empty` | 论文 DOI 为空 |
| `doi.wrong_type` | 值不是字符串 |
| `doi.not_lowercase` | DOI 不是小写 |
| `doi.doi_url` | 值是 DOI URL，不是纯 DOI |
| `doi.placeholder` | 使用了占位 DOI |
| `doi.invalid_format` | DOI 格式错误 |

## isbns

| Label 名 | 含义 |
|---|---|
| `isbns.missing_field` | 缺少字段 |
| `isbns.empty` | 电子书 ISBN 列表为空 |
| `isbns.wrong_type` | 值不是字符串列表 |
| `isbns.invalid_format` | ISBN 格式或校验位错误 |

## isbn13

| Label 名 | 含义 |
|---|---|
| `isbn13.missing_field` | 缺少字段 |
| `isbn13.empty` | 电子书 ISBN13 为空 |
| `isbn13.wrong_type` | 值不是字符串 |
| `isbn13.invalid_format` | ISBN13 格式或校验位错误 |

## title

| Label 名 | 含义 |
|---|---|
| `title.missing_field` | 缺少字段 |
| `title.null` | 值为 null |
| `title.wrong_type` | 值不是字符串 |
| `title.html_tag_layout` | 包含 HTML 排版标签 |
| `title.html_tag_math` | 包含 MathML 标签 |
| `title.html_tag_xml_comment` | 包含 XML 注释 |
| `title.html_tag_cdata` | 包含 CDATA 片段 |
| `title.html_entity_named` | 包含命名 HTML entity |
| `title.html_entity_decimal` | 包含十进制数字 HTML entity |
| `title.html_entity_hex` | 包含十六进制数字 HTML entity |
| `title.special_char_invisible` | 包含不可见字符 |
| `title.special_char_replacement` | 包含 Unicode 替换字符 |
| `title.special_char_control` | 包含控制字符 |
| `title.special_char_markup` | 包含方括号排版标记 |
| `title.empty` | 去除首尾空格后内容为空 |
| `title.too_short` | 去除首尾空格后长度小于 5 个字符 |
| `title.too_long` | 去除首尾空格后长度大于 1000 个字符 |
| `title.likely_placeholder` | 内容可能是标题占位文本 |
| `title.encoding_error` | 包含 Unicode 替换字符或典型乱码组合 |
| `title.likely_conference` | 内容可能是 IEEE 会议名称而非论文标题 |
| `title.likely_identifier` | 标题整体可能是数字标识符、DOI、URL 或 S3 路径 |

## abstract

| Label 名 | 含义 |
|---|---|
| `abstract.missing_field` | 缺少字段 |
| `abstract.null` | 值为 null |
| `abstract.wrong_type` | 值不是字符串 |
| `abstract.html_tag_layout` | 包含 HTML 排版标签 |
| `abstract.html_tag_math` | 包含 MathML 标签 |
| `abstract.html_tag_xml_comment` | 包含 XML 注释 |
| `abstract.html_tag_cdata` | 包含 CDATA 片段 |
| `abstract.html_entity_named` | 包含命名 HTML entity |
| `abstract.html_entity_decimal` | 包含十进制数字 HTML entity |
| `abstract.html_entity_hex` | 包含十六进制数字 HTML entity |
| `abstract.special_char_invisible` | 包含不可见字符 |
| `abstract.special_char_replacement` | 包含 Unicode 替换字符 |
| `abstract.special_char_control` | 包含控制字符 |
| `abstract.special_char_markup` | 包含方括号排版标记 |
| `abstract.empty` | 去除首尾空格后内容为空 |
| `abstract.too_short` | 去除首尾空格后长度小于 20 个字符 |
| `abstract.too_long` | 去除首尾空格后长度大于 6000 个字符 |
| `abstract.likely_placeholder` | 内容可能是无摘要占位文本 |
| `abstract.encoding_error` | 包含 Unicode 替换字符或典型乱码组合 |
| `abstract.same_title` | 摘要与标题去除首尾空格并忽略大小写后完全相同 |
| `abstract.likely_identifier` | 摘要整体可能是数字标识符、DOI、URL 或 S3 路径 |

## language

| Label 名 | 含义 |
|---|---|
| `language.missing_field` | 缺少字段 |
| `language.null` | 值为 null |
| `language.wrong_type` | 值不是字符串 |
| `language.unsupported_value` | 语言代码不受支持 |

## author

| Label 名 | 含义 |
|---|---|
| `author.missing_field` | 缺少字段 |
| `author.null` | 值为 null |
| `author.wrong_type` | 作者列表、对象或属性类型错误 |
| `author.invalid_keys` | 作者对象字段不符合要求 |
| `author.empty` | 作者姓名为空 |
| `author.invalid_separator` | 作者姓名包含非法分隔符 |
| `author.invalid_orcid` | ORCID URL 格式错误 |

## contributors

| Label 名 | 含义 |
|---|---|
| `contributors.missing_field` | 缺少字段 |
| `contributors.null` | 值为 null |
| `contributors.wrong_type` | 值不是字符串列表 |
| `contributors.invalid_separator` | 姓名包含非法分隔符 |

## locations

| Label 名 | 含义 |
|---|---|
| `locations.missing_field` | 缺少字段 |
| `locations.null` | 值为 null |
| `locations.wrong_type` | 列表或列表项类型错误 |
| `locations.missing_key` | 位置对象缺少必需字段 |
| `locations.invalid_value` | `type`、`license` 或 `is_oa` 无效 |
| `locations.invalid_url` | URL 格式错误 |

## access_is_oa

| Label 名 | 含义 |
|---|---|
| `access_is_oa.missing_field` | 缺少字段 |
| `access_is_oa.empty` | 论文开放获取标记为空 |
| `access_is_oa.wrong_type` | 值不是字符串 |
| `access_is_oa.unsupported_value` | 值不受支持 |

## access_oa_status

| Label 名 | 含义 |
|---|---|
| `access_oa_status.missing_field` | 缺少字段 |
| `access_oa_status.null` | 值为 null |
| `access_oa_status.wrong_type` | 值不是字符串 |
| `access_oa_status.unsupported_value` | 开放获取状态不受支持 |

## access_oa_url

| Label 名 | 含义 |
|---|---|
| `access_oa_url.missing_field` | 缺少字段 |
| `access_oa_url.null` | 值为 null |
| `access_oa_url.wrong_type` | 值不是字符串列表 |
| `access_oa_url.invalid_url` | 列表中存在无效 URL |

## access_license

| Label 名 | 含义 |
|---|---|
| `access_license.missing_field` | 缺少字段 |
| `access_license.null` | 值为 null |
| `access_license.wrong_type` | 值不是字符串 |
| `access_license.unsupported_value` | 许可协议不受支持 |

## publication_published_date

| Label 名 | 含义 |
|---|---|
| `publication_published_date.missing_field` | 缺少字段 |
| `publication_published_date.null` | 值为 null |
| `publication_published_date.wrong_type` | 值不是字符串 |
| `publication_published_date.invalid_format` | 不符合 YYYY-MM-DD 格式 |
| `publication_published_date.invalid_date` | 不是有效日历日期 |

## publication_published_year

| Label 名 | 含义 |
|---|---|
| `publication_published_year.missing_field` | 缺少字段 |
| `publication_published_year.wrong_type` | 值不是整数 |
| `publication_published_year.out_of_range` | 年份超出有效范围 |

## publication_venue_issn

| Label 名 | 含义 |
|---|---|
| `publication_venue_issn.missing_field` | 缺少字段 |
| `publication_venue_issn.null` | 值为 null |
| `publication_venue_issn.wrong_type` | 值不是字符串列表 |
| `publication_venue_issn.invalid_format` | ISSN 格式或校验位错误 |

## publication_venue_biblio_volume

| Label 名 | 含义 |
|---|---|
| `publication_venue_biblio_volume.missing_field` | 缺少字段 |
| `publication_venue_biblio_volume.null` | 值为 null |
| `publication_venue_biblio_volume.wrong_type` | 值不是字符串 |
| `publication_venue_biblio_volume.invalid_format` | 值不能转换为整数 |

## publication_venue_biblio_issue

| Label 名 | 含义 |
|---|---|
| `publication_venue_biblio_issue.missing_field` | 缺少字段 |
| `publication_venue_biblio_issue.null` | 值为 null |
| `publication_venue_biblio_issue.wrong_type` | 值不是字符串 |
| `publication_venue_biblio_issue.invalid_format` | 值不能转换为整数 |

## publication_venue_biblio_pages

| Label 名 | 含义 |
|---|---|
| `publication_venue_biblio_pages.missing_field` | 缺少字段 |
| `publication_venue_biblio_pages.null` | 值为 null |
| `publication_venue_biblio_pages.wrong_type` | 值不是字符串 |
| `publication_venue_biblio_pages.invalid_format` | 不符合 `<起始页>-<结束页>` 格式 |
| `publication_venue_biblio_pages.out_of_range` | 页码不是正数 |
| `publication_venue_biblio_pages.page_order` | 起始页大于结束页 |

## publication_pages

| Label 名 | 含义 |
|---|---|
| `publication_pages.missing_field` | 缺少字段 |
| `publication_pages.wrong_type` | 值不是整数 |
| `publication_pages.out_of_range` | 页数不大于 0 |

## publication_venue_name_unified

| Label 名 | 含义 |
|---|---|
| `publication_venue_name_unified.missing_field` | 缺少字段 |
| `publication_venue_name_unified.null` | 值为 null |
| `publication_venue_name_unified.wrong_type` | 当前字段或依赖字段类型错误 |
| `publication_venue_name_unified.missing_dependency` | 缺少期刊原始名称，无法校验 |
| `publication_venue_name_unified.mismatch` | 与预期统一名称不一致 |

## grade_class

| Label 名 | 含义 |
|---|---|
| `grade_class.missing_field` | 缺少字段 |
| `grade_class.null` | 值为 null |
| `grade_class.wrong_type` | 值不是字符串 |
| `grade_class.unsupported_value` | 教育类型不受支持 |

## grade

| Label 名 | 含义 |
|---|---|
| `grade.missing_field` | 缺少字段 |
| `grade.null` | 值为 null |
| `grade.wrong_type` | 当前字段或 `grade_class` 类型错误 |
| `grade.unsupported_value` | 年级值不受支持 |
| `grade.grade_mismatch` | 非 K12 类型设置了年级 |

## references

| Label 名 | 含义 |
|---|---|
| `references.missing_field` | 缺少字段 |
| `references.null` | 值为 null |
| `references.wrong_type` | 列表或列表项类型错误 |
| `references.invalid_keys` | 列表项字段不符合要求 |
| `references.empty` | `id_type` 或非 DOI 标识符为空 |
| `references.title_null` | 标题为 null |
| `references.title_wrong_type` | 标题类型错误 |
| `references.title_html_tag_layout` | 标题包含 HTML 排版标签 |
| `references.title_html_tag_math` | 标题包含 MathML 标签 |
| `references.title_html_tag_xml_comment` | 标题包含 XML 注释 |
| `references.title_html_tag_cdata` | 标题包含 CDATA 片段 |
| `references.title_html_entity_named` | 标题包含命名 HTML entity |
| `references.title_html_entity_decimal` | 标题包含十进制数字 HTML entity |
| `references.title_html_entity_hex` | 标题包含十六进制数字 HTML entity |
| `references.title_special_char_invisible` | 标题包含不可见字符 |
| `references.title_special_char_replacement` | 标题包含 Unicode 替换字符 |
| `references.title_special_char_control` | 标题包含控制字符 |
| `references.title_special_char_markup` | 标题包含方括号排版标记 |
| `references.id_empty` | DOI 为空 |
| `references.id_wrong_type` | DOI 类型错误 |
| `references.id_not_lowercase` | DOI 不是小写 |
| `references.id_doi_url` | DOI 是 URL |
| `references.id_placeholder` | 使用了占位 DOI |
| `references.id_invalid_format` | DOI 格式错误 |

## related_works

| Label 名 | 含义 |
|---|---|
| `related_works.missing_field` | 缺少字段 |
| `related_works.null` | 值为 null |
| `related_works.wrong_type` | 列表或列表项类型错误 |
| `related_works.invalid_keys` | 列表项字段不符合要求 |
| `related_works.empty` | `id_type` 或非 DOI 标识符为空 |
| `related_works.title_null` | 标题为 null |
| `related_works.title_wrong_type` | 标题类型错误 |
| `related_works.title_html_tag_layout` | 标题包含 HTML 排版标签 |
| `related_works.title_html_tag_math` | 标题包含 MathML 标签 |
| `related_works.title_html_tag_xml_comment` | 标题包含 XML 注释 |
| `related_works.title_html_tag_cdata` | 标题包含 CDATA 片段 |
| `related_works.title_html_entity_named` | 标题包含命名 HTML entity |
| `related_works.title_html_entity_decimal` | 标题包含十进制数字 HTML entity |
| `related_works.title_html_entity_hex` | 标题包含十六进制数字 HTML entity |
| `related_works.title_special_char_invisible` | 标题包含不可见字符 |
| `related_works.title_special_char_replacement` | 标题包含 Unicode 替换字符 |
| `related_works.title_special_char_control` | 标题包含控制字符 |
| `related_works.title_special_char_markup` | 标题包含方括号排版标记 |
| `related_works.id_empty` | DOI 为空 |
| `related_works.id_wrong_type` | DOI 类型错误 |
| `related_works.id_not_lowercase` | DOI 不是小写 |
| `related_works.id_doi_url` | DOI 是 URL |
| `related_works.id_placeholder` | 使用了占位 DOI |
| `related_works.id_invalid_format` | DOI 格式错误 |

## citations

| Label 名 | 含义 |
|---|---|
| `citations.missing_field` | 缺少字段 |
| `citations.null` | 值为 null |
| `citations.wrong_type` | 列表或列表项类型错误 |
| `citations.invalid_keys` | 列表项字段不符合要求 |
| `citations.empty` | `id_type` 或非 DOI 标识符为空 |
| `citations.title_null` | 标题为 null |
| `citations.title_wrong_type` | 标题类型错误 |
| `citations.title_html_tag_layout` | 标题包含 HTML 排版标签 |
| `citations.title_html_tag_math` | 标题包含 MathML 标签 |
| `citations.title_html_tag_xml_comment` | 标题包含 XML 注释 |
| `citations.title_html_tag_cdata` | 标题包含 CDATA 片段 |
| `citations.title_html_entity_named` | 标题包含命名 HTML entity |
| `citations.title_html_entity_decimal` | 标题包含十进制数字 HTML entity |
| `citations.title_html_entity_hex` | 标题包含十六进制数字 HTML entity |
| `citations.title_special_char_invisible` | 标题包含不可见字符 |
| `citations.title_special_char_replacement` | 标题包含 Unicode 替换字符 |
| `citations.title_special_char_control` | 标题包含控制字符 |
| `citations.title_special_char_markup` | 标题包含方括号排版标记 |
| `citations.id_empty` | DOI 为空 |
| `citations.id_wrong_type` | DOI 类型错误 |
| `citations.id_not_lowercase` | DOI 不是小写 |
| `citations.id_doi_url` | DOI 是 URL |
| `citations.id_placeholder` | 使用了占位 DOI |
| `citations.id_invalid_format` | DOI 格式错误 |

## supplementary_material

| Label 名 | 含义 |
|---|---|
| `supplementary_material.missing_field` | 缺少字段 |
| `supplementary_material.null` | 值为 null |
| `supplementary_material.wrong_type` | 列表、列表项或属性类型错误 |
| `supplementary_material.invalid_keys` | 列表项字段不符合要求 |

## cited_by_api_url

| Label 名 | 含义 |
|---|---|
| `cited_by_api_url.missing_field` | 缺少字段 |
| `cited_by_api_url.null` | 值为 null |
| `cited_by_api_url.wrong_type` | 值不是字符串 |
| `cited_by_api_url.invalid_url` | URL 格式错误 |

## access_xinghe_repository_sha256

| Label 名 | 含义 |
|---|---|
| `access_xinghe_repository_sha256.missing_field` | 缺少字段 |
| `access_xinghe_repository_sha256.null` | 值为 null |
| `access_xinghe_repository_sha256.wrong_type` | 当前字段或全文标记类型错误 |
| `access_xinghe_repository_sha256.required` | 存在全文时 SHA256 不能为空 |

## access_xinghe_repository_origin_path

| Label 名 | 含义 |
|---|---|
| `access_xinghe_repository_origin_path.missing_field` | 缺少字段 |
| `access_xinghe_repository_origin_path.wrong_type` | 当前字段或全文标记类型错误 |
| `access_xinghe_repository_origin_path.required` | 存在全文时原始路径不能为空 |

## access_xinghe_repository_model_name

| Label 名 | 含义 |
|---|---|
| `access_xinghe_repository_model_name.missing_field` | 缺少字段 |
| `access_xinghe_repository_model_name.wrong_type` | 值不是字符串 |
| `access_xinghe_repository_model_name.required` | 处理成功时模型名称不能为空 |
| `access_xinghe_repository_model_name.unsupported_value` | 模型名称不受支持 |

## access_xinghe_repository_model_version

| Label 名 | 含义 |
|---|---|
| `access_xinghe_repository_model_version.missing_field` | 缺少字段 |
| `access_xinghe_repository_model_version.wrong_type` | 值不是字符串 |
| `access_xinghe_repository_model_version.required` | 当前条件下模型版本不能为空 |
| `access_xinghe_repository_model_version.unsupported_value` | 模型版本不受支持 |
| `access_xinghe_repository_model_version.model_mismatch` | 模型版本与模型名称不匹配 |

## 其他

| Label 名 | 含义 |
|---|---|
| `<field>.unsupported_field` | 配置了规则不支持的字段 |
| `QUALITY_GOOD` | 所有选中字段均通过校验 |
