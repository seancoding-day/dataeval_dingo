import { Cascader } from 'antd';
import React, { useState, useEffect, useMemo } from 'react';
import IconFont from '@/components/icon-font';
import styles from './index.module.scss';
import { SummaryData } from '@/pages/main-home/components/summary-data-table';
import cls from 'classnames';

interface FilterCascaderProps {
    summary: SummaryData;
    onFilter: (primaryName: string, secondaryName: string) => void;
}

const FilterCascader: React.FC<FilterCascaderProps> = ({
    summary,
    onFilter,
}) => {
    const [firstText, setFirstText] = useState('');
    const [secondText, setSecondText] = useState('');
    const [selectedValue, setSelectedValue] = useState<string[]>(['all']);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    const cascaderOptions = [
        {
            value: 'all',
            label: '全部',
        },
        ...Object.entries(summary?.type_ratio).map(([key, value]) => {
            const primaryOption = {
                value: key,
                label: (
                    <span>
                        {`${key}`}
                        <span className="text-[#2951F2] ml-2">
                            {(value * 100).toFixed(1)}%
                        </span>
                    </span>
                ),
                children: [] as { value: string; label: any }[],
            };

            // 处理二级选项
            Object.entries(summary?.name_ratio).forEach(
                ([nameKey, nameValue]) => {
                    if (nameKey.startsWith(`${key}-`)) {
                        // const secondaryName = nameKey.split('-')[1];
                        primaryOption.children.push({
                            value: nameKey,
                            label: (
                                <span>
                                    {`${nameKey}`}
                                    <span className="text-[#2951F2] ml-2">
                                        {(nameValue * 100).toFixed(1)}%
                                    </span>
                                </span>
                            ),
                        });
                    }
                }
            );

            return primaryOption;
        }),
    ];
    const onChange = (value: any) => {
        if (!value || value.length === 0) {
            setFirstText('');
            setSecondText('');
            setSelectedValue(['all']);
            onFilter('', '');
            return;
        }

        const [primaryName, secondaryName] = value;
        setSelectedValue(value);

        if (primaryName === 'all') {
            setFirstText('');
            setSecondText('');
            onFilter('', '');
            return;
        }

        if (primaryName) {
            setFirstText(primaryName);
        }
        if (secondaryName) {
            setSecondText(secondaryName);
        } else {
            setSecondText('');
        }

        onFilter(primaryName as string, secondaryName as string);
    };

    const handlePrimaryClick = (e: React.MouseEvent) => {
        if (firstText && firstText !== 'all') {
            setSecondText('');
            setSelectedValue([firstText]);
            onFilter(firstText, '');
        }
    };

    return (
        <span className="text-[#121316] text-[1.2rem]">
            &nbsp;
            <Cascader
                options={cascaderOptions}
                onChange={onChange}
                placeholder="请选择筛选条件"
                changeOnSelect
                style={{ width: 240, height: 600 }}
                allowClear
                value={selectedValue}
                defaultValue={['all']}
                expandTrigger="hover"
                popupClassName={styles.customCascader}
                onDropdownVisibleChange={setIsDropdownOpen}
            >
                <a className="cursor-pointer font-semibold">
                    <span
                        className="font-semibold hover:text-[#0D53DE]"
                        onClick={handlePrimaryClick}
                    >
                        {firstText}
                    </span>
                    {secondText && (
                        <IconFont
                            type={'icon-more'}
                            className="mx-1 relative top-[2px]"
                        />
                    )}
                    {secondText && (
                        <span className="font-semibold hover:text-[#0D53DE]">
                            {secondText}
                        </span>
                    )}
                    {!firstText && !secondText && '全部测评数据'}
                    <IconFont
                        type={'icon-arrow-down-filled'}
                        className={cls(
                            'mx-2 text-[1rem] duration-300',
                            isDropdownOpen && 'rotate-180'
                        )}
                    />
                </a>
            </Cascader>
        </span>
    );
};

export default FilterCascader;
