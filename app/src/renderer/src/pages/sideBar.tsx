import React, { useEffect, useRef, useState } from 'react';
import IconFont from '@/components/icon-font';
import logoSvg from '@/assets/electron.svg';
import cls from 'classnames';
import styles from './index.module.scss';
import {
    DEFAULT_SIDEBAR_WIDTH,
    MAX_SIDEBAR_WIDTH,
    MIN_SIDEBAR_WIDTH,
    NARROW_SIDEBAR_WIDTH,
} from '@/constant';
import { useMobileScreen } from '@/utils';
import { useAppConfig } from '@/store/config';

interface SideBarProps {
    // Add any props you might need
    className?: string;
}

interface SideBarContainerProps {
    // Add any props you might need
    className?: string;
    children: React.ReactNode;
}

interface DragSideBarResult {
    onDragStart: (e: React.MouseEvent) => void;
    shouldNarrow: boolean;
}

export function useDragSideBar(): DragSideBarResult {
    const limit = (x: number) =>
        Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, x));

    const config = useAppConfig();
    const startX = useRef(0);
    const startDragWidth = useRef(config.sidebarWidth ?? DEFAULT_SIDEBAR_WIDTH);
    const lastUpdateTime = useRef(Date.now());

    const toggleSideBar = () => {
        config.update(config => {
            config.sidebarWidth =
                config.sidebarWidth < MIN_SIDEBAR_WIDTH
                    ? DEFAULT_SIDEBAR_WIDTH
                    : NARROW_SIDEBAR_WIDTH;
        });
    };

    const onDragStart = (e: React.MouseEvent) => {
        startX.current = e.clientX;
        startDragWidth.current = config.sidebarWidth ?? DEFAULT_SIDEBAR_WIDTH;
        const dragStartTime = Date.now();

        const handleDragMove = (e: MouseEvent) => {
            if (Date.now() < lastUpdateTime.current + 20) {
                return;
            }
            lastUpdateTime.current = Date.now();
            const d = e.clientX - startX.current;
            const nextWidth = limit(startDragWidth.current + d);

            config.update(config => {
                config.sidebarWidth =
                    nextWidth < MIN_SIDEBAR_WIDTH
                        ? NARROW_SIDEBAR_WIDTH
                        : nextWidth;
            });
        };

        const handleDragEnd = () => {
            window.removeEventListener('pointermove', handleDragMove);
            window.removeEventListener('pointerup', handleDragEnd);

            const shouldFireClick = Date.now() - dragStartTime < 240;
            if (shouldFireClick) {
                toggleSideBar();
            }
        };

        window.addEventListener('pointermove', handleDragMove);
        window.addEventListener('pointerup', handleDragEnd);
    };

    const isMobileScreen = useMobileScreen();
    const shouldNarrow =
        !isMobileScreen && (config.sidebarWidth ?? 0) < MIN_SIDEBAR_WIDTH;

    useEffect(() => {
        const barWidth = shouldNarrow
            ? NARROW_SIDEBAR_WIDTH
            : limit(config.sidebarWidth ?? DEFAULT_SIDEBAR_WIDTH);
        const sideBarWidth = isMobileScreen ? '100vw' : `${barWidth}px`;
        document.documentElement.style.setProperty(
            '--sidebar-width',
            sideBarWidth
        );
    }, [config.sidebarWidth, isMobileScreen, shouldNarrow]);

    return {
        onDragStart,
        shouldNarrow,
    };
}
const SideBarContainer: React.FC<SideBarContainerProps> = ({
    className,
    children,
}) => {
    // const { onDragStart, shouldNarrow } = useDragSideBar();

    return (
        <div
            className={cls(
                className,
                styles.sidebar,
                `h-full bg-white shadow-lg transition-all px-4 bg-[#F4F5F9] duration-300`
            )}
        >
            {children}
            <div
                className={styles.sidebarDrag}
                // onPointerDown={e => onDragStart(e as any)}
            >
                <IconFont type="icon-resize" />
            </div>
        </div>
    );
};

const SideListItem = [
    {
        name: 'taskManager',
        icon: 'icon-task-tab',
        title: '评测任务',
    },
];

const SideBar: React.FC<SideBarProps> = () => {
    const [isExpanded, setIsExpanded] = useState(false);

    useEffect(() => {
        if (isExpanded) {
            document.documentElement.style.setProperty(
                '--sidebar-width',
                '240px'
            );
        } else {
            document.documentElement.style.setProperty(
                '--sidebar-width',
                '60px'
            );
        }
    }, [isExpanded]);

    return (
        <SideBarContainer className={styles.sidebar}>
            <div className="flex flex-col h-full">
                {/* Top icon */}
                <div
                    className={cls(
                        'py-4  flex items-center text-gray',
                        !isExpanded && 'justify-center'
                    )}
                >
                    <img src={logoSvg} alt="" />
                    <span
                        className={cls(
                            'ml-2 text-black-1 font-bold opacity-0 w-0 overflow-hidden',
                            isExpanded && 'opacity-100 duration-3000 w-auto'
                        )}
                    >
                        {'dingo'}
                    </span>
                </div>
                <div className="h-[1px] bg-[#EBECF0]"></div>
                <hgroup className="flex flex-grow">
                    {SideListItem.map(item => (
                        <div
                            key={item.name}
                            className="flex items-center justify-center h-12"
                        >
                            <IconFont
                                type={item.icon}
                                className="text-[1.55rem] text-blue"
                            />
                            <span
                                className={cls(
                                    'ml-2 text-blue font-bold hidden whitespace-nowrap',
                                    isExpanded && '!block'
                                )}
                            >
                                {item.title}
                            </span>
                        </div>
                    ))}
                </hgroup>

                {/* Expand/collapse button */}
                <div
                    className={cls(
                        'w-full flex justify-end items-center mb-6',
                        !isExpanded && 'flex-col justify-center'
                    )}
                >
                    <IconFont
                        onClick={() =>
                            window?.open('https://github.com/shijinpjlab/Dingo')
                        }
                        className={cls(
                            'text-[1.25rem] text-gray-2 hover:text-blue ',
                            isExpanded && 'mr-auto',
                            !isExpanded && 'mb-2'
                        )}
                        type={'icon-GithubFilled'}
                    />
                    <IconFont
                        onClick={() => setIsExpanded(!isExpanded)}
                        type={isExpanded ? 'icon-expand' : 'icon-fold'}
                        className="text-[1.25rem] text-gray-2 hover:text-blue"
                    />
                </div>
            </div>
        </SideBarContainer>
    );
};

export default SideBar;
