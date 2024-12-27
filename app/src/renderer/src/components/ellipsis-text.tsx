import React, {
    useState,
    useRef,
    useEffect,
    ReactNode,
    forwardRef,
    useImperativeHandle,
} from 'react';

import cls from 'classnames';

interface EllipsisTextProps {
    children: ReactNode;
    lines?: number;
    width?: number | string;
    className?: string;
    expandable?: boolean;
    onExpandChange?: (val?: boolean) => void;
    controlIsExpanded?: boolean;
}

export interface EllipsisTextRef {
    toggleExpand: () => void;
}

const EllipsisText = forwardRef<EllipsisTextRef, EllipsisTextProps>(
    (
        {
            children,
            lines = 1,
            width,
            className = '',
            expandable = true,
            onExpandChange,
            controlIsExpanded,
        },
        ref
    ) => {
        const [isExpanded, setIsExpanded] = useState(false);
        const [showEllipsis, setShowEllipsis] = useState(false);
        const textRef = useRef<HTMLDivElement>(null);
        const containerRef = useRef<HTMLDivElement>(null);

        useImperativeHandle(ref, () => ({
            toggleExpand: () => {
                if (expandable) {
                    setIsExpanded(prev => !prev);
                }
            },
        }));

        useEffect(() => {
            const checkOverflow = () => {
                if (textRef.current && containerRef.current) {
                    const isOverflowing =
                        textRef.current.scrollHeight >
                        containerRef.current.clientHeight;
                    setShowEllipsis(isOverflowing);
                }
            };

            checkOverflow();
            window.addEventListener('resize', checkOverflow);
            return () => window.removeEventListener('resize', checkOverflow);
        }, [children, lines]);

        const handleClick = () => {
            if (expandable) {
                setIsExpanded(!isExpanded);
            }
        };

        const containerStyle: React.CSSProperties = {
            width: width || '100%',
            maxWidth: '100%',
            overflow: 'hidden',
        };

        const textStyle: React.CSSProperties = {
            display: '-webkit-box',
            WebkitLineClamp: isExpanded ? 'unset' : lines,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
        };

        useEffect(() => {
            onExpandChange?.(isExpanded);
        }, [isExpanded, onExpandChange]);

        useEffect(() => {
            setIsExpanded(!!controlIsExpanded);
        }, [controlIsExpanded]);

        return (
            <div
                ref={containerRef}
                style={containerStyle}
                className={`relative ${className}`}
            >
                <div
                    ref={textRef}
                    style={textStyle}
                    className={cls(
                        `${expandable ? 'cursor-select' : ''}`,
                        'select-text'
                    )}
                    onClick={handleClick}
                >
                    {children}
                </div>
            </div>
        );
    }
);

// 添加显示名称以便调试
EllipsisText.displayName = 'EllipsisText';

export default EllipsisText;
