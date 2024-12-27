import { forwardRef, useImperativeHandle, useRef, useState } from 'react';
import { Button, message, Popover } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import EllipsisText from '../ellipsis-text';
import styles from '@/styles/custom-antd.module.scss';
import copy from 'copy-to-clipboard';

interface HighlightTextProps {
    text: string;
    highlight: (string | string[])[];
    showHighlight: boolean;
    width?: string | number;
    onExpandChange?: (bool?: boolean) => void;
    ellipsisTextClassName?: string;
    controlIsExpanded?: boolean;
    expandable?: boolean;
}

export interface HighlightTextRef {
    toggleExpand: () => void;
}

const HighlightText = forwardRef<HighlightTextRef, HighlightTextProps>(
    (
        {
            text,
            highlight,
            showHighlight,
            width,
            onExpandChange,
            controlIsExpanded,
            ellipsisTextClassName = '',
            expandable,
        },
        ref
    ) => {
        if (!showHighlight || !highlight || highlight.length === 0)
            return (
                <EllipsisText
                    width={width}
                    lines={4}
                    controlIsExpanded={controlIsExpanded}
                >
                    {text}
                </EllipsisText>
            );

        // 拍平 highlight 数组
        const flattenedHighlight = highlight.flat();

        // 创建一个函数来检查和高亮文本
        const highlightText = (inputText: string) => {
            let result: React.ReactNode[] = [inputText];
            flattenedHighlight.forEach(highlightStr => {
                result = result.flatMap(part => {
                    if (typeof part !== 'string') return part;
                    const splitText = part.split(highlightStr);
                    return splitText.reduce(
                        (acc: React.ReactNode[], subPart, index) => {
                            if (index !== 0) {
                                acc.push(
                                    <Popover
                                        key={`highlight-${index}`}
                                        overlayInnerStyle={{ padding: 0 }}
                                        overlayClassName={
                                            styles.customConfigCopyPopover
                                        }
                                        align={{
                                            offset: [0, -1],
                                        }}
                                        content={
                                            <Button
                                                type="text"
                                                icon={<CopyOutlined />}
                                                onClick={e => {
                                                    e?.stopPropagation();
                                                    copy(highlightStr);
                                                    message.success('复制成功');
                                                }}
                                            >
                                                复制
                                            </Button>
                                        }
                                        trigger="hover"
                                        placement="top"
                                    >
                                        <mark
                                            style={{
                                                backgroundColor: '#FFE7B5',
                                                cursor: 'pointer',
                                            }}
                                        >
                                            {highlightStr}
                                        </mark>
                                    </Popover>
                                );
                            }
                            if (subPart) {
                                acc.push(subPart);
                            }
                            return acc;
                        },
                        []
                    );
                });
            });
            return result;
        };

        const highlightedText = highlightText(text);
        const textRef = useRef<any>(null);

        useImperativeHandle(ref, () => ({
            toggleExpand: textRef?.current?.toggleExpand?.(),
        }));

        return (
            <EllipsisText
                width={width}
                lines={4}
                ref={textRef}
                onExpandChange={onExpandChange}
                controlIsExpanded={controlIsExpanded}
                className={ellipsisTextClassName}
                expandable={expandable}
            >
                {highlightedText}
            </EllipsisText>
        );
    }
);

HighlightText.displayName = 'HighlightText';

export default HighlightText;
