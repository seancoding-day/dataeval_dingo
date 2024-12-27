import React from 'react';
import { Table, Button, Tooltip } from 'antd';
import { FormattedMessage, useIntl } from 'react-intl';
import IconFont from '@/components/icon-font';
import cls from 'classnames';
import styles from '@/styles/custom-antd.module.scss';

export const getColorByRatio = (parentIndex: number, isSecondary: boolean) => {
    const colors = [
        '#0D53DE',
        '#0080B0',
        '#008858',
        '#B38500',
        '#BE5A00',
        '#D54941',
        '#C43695',
    ];

    const secondaryColors = [
        '#5E9BF7',
        '#41B8F2',
        '#56C08D',
        '#F5BA18',
        '#FA9550',
        '#FF988E',
        '#FF79CD',
    ];

    return isSecondary && parentIndex !== undefined
        ? secondaryColors[parentIndex]
        : colors[parentIndex];
};

// 定义文件结构的接口
interface FileStructure {
    name: string;
    files: string[];
}

// 定义摘要数据的接口
interface Summary {
    type_ratio: { [key: string]: number };
    name_ratio: { [key: string]: number };
}

// 定义组件的 props 接口
interface FileStructureTableProps {
    fileStructure: FileStructure[];
    summary: Summary | null;
    handleView: (record: TableDataItem) => void;
}

// 定义表格数据项的接口
export interface TableDataItem {
    key: string;
    name: string;
    isFile: boolean;
    category?: string;
    value: number;
    ratio?: number;
    children?: TableDataItem[];
    parentIndex?: number;
}

const FileStructureTable: React.FC<FileStructureTableProps> = ({
    fileStructure,
    summary,
    handleView: handleRecordView,
}) => {
    const { formatMessage } = useIntl();
    const handleView = (record: TableDataItem) => {
        handleRecordView(record);
    };

    // 更新颜色映射函数
    const getColorByRatio = (parentIndex: number, isSecondary: boolean) => {
        const colors = [
            '#0D53DE',
            '#0080B0',
            '#008858',
            '#B38500',
            '#BE5A00',
            '#D54941',
            '#C43695',
        ];

        const secondaryColors = [
            '#5E9BF7',
            '#41B8F2',
            '#56C08D',
            '#F5BA18',
            '#FA9550',
            '#FF988E',
            '#FF79CD',
        ];

        return isSecondary && parentIndex !== undefined
            ? secondaryColors[parentIndex]
            : colors[parentIndex];
    };

    const columns = [
        {
            title: (
                <div className="flex justify-between">
                    {formatMessage({ id: 'error.type' })}
                    <Tooltip
                        overlayStyle={{ maxWidth: 'max-content' }}
                        title={
                            <div className="whitespace-nowrap">
                                <FormattedMessage
                                    id="error.type.tooltip"
                                    values={{
                                        link: (
                                            <a
                                                href="https://github.com/shijinpjlab/Dingo"
                                                className="whitespace-nowrap mr-2 text-base text-[#3477EB]"
                                            >
                                                <IconFont
                                                    type="icon-GithubFilled"
                                                    className="mr-1"
                                                />
                                                Github
                                            </a>
                                        ),
                                    }}
                                />
                            </div>
                        }
                    >
                        <IconFont
                            type="icon-QuestionCircleOutlined"
                            className="hover:text-blue cursor-pointer text-base"
                        />
                    </Tooltip>
                </div>
            ),
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: TableDataItem) => (
                <span>{text}</span>
            ),
        },
        {
            title: formatMessage({ id: 'error.rate' }),
            dataIndex: 'value',
            key: 'value',
            width: 500,
            render: (_: any, record: TableDataItem) => (
                <div className="block flex items-center">
                    <div className="mr-2 min-w-[100px]">{record?.value}</div>
                    <div className="flex-1 ">
                        <div
                            style={{
                                width: `${(record?.ratio || 0) * 100}%`,
                                height: '12px',
                                backgroundColor: getColorByRatio(
                                    record?.parentIndex ||
                                        record?.children?.[0]?.parentIndex ||
                                        0,

                                    record?.isFile
                                ),
                            }}
                        />
                    </div>
                </div>
            ),
        },
        // {
        //     title: '',
        //     dataIndex: 'ratio',
        //     key: 'ratio',
        //     render: (_: any, record: TableDataItem) => (
        //         <div className="w-full"></div>
        //     ),
        // },
        {
            title: '',
            key: 'action',
            render: (_: any, record: TableDataItem) => (
                <Button
                    type="link"
                    onClick={e => {
                        e.stopPropagation();
                        handleView(record);
                    }}
                >
                    查看
                </Button>
            ),
        },
    ];

    const getTableData = (): TableDataItem[] => {
        if (!summary || !fileStructure) return [];

        const allValues = fileStructure?.flatMap(category => [
            summary?.type_ratio?.[category.name] || 0,
            ...(category?.files || []).map(
                file =>
                    summary.name_ratio?.[
                        `${category?.name}-${file?.replace('.jsonl', '')}`
                    ] || 0
            ),
        ]);
        const maxValue = Math.max(...allValues);

        return fileStructure.map((category, index) => {
            const categoryValue = summary?.type_ratio?.[category.name] || 0;
            const children: TableDataItem[] = (category?.files || []).map(
                file => ({
                    key: `${category?.name}-${file}`,
                    name: file,
                    isFile: true,
                    category: category?.name,
                    value:
                        summary?.name_ratio?.[
                            `${category?.name}-${file.replace('.jsonl', '')}`
                        ] || 0,
                    ratio:
                        (summary?.name_ratio?.[
                            `${category?.name}-${file.replace('.jsonl', '')}`
                        ] || 0) / maxValue,
                    parentIndex: index,
                })
            );

            return {
                key: category.name,
                name: category.name,
                isFile: false,
                value: categoryValue,
                ratio: categoryValue / maxValue,
                children,
            };
        });
    };

    return (
        <Table<TableDataItem>
            columns={columns}
            dataSource={getTableData()}
            expandable={{
                expandIcon: ({ expanded, onExpand, record }) => {
                    if (!record?.isFile) {
                        return (
                            <IconFont
                                type="icon-CaretDownOutlined"
                                onClick={e => {
                                    e.stopPropagation();
                                    onExpand(record, e);
                                }}
                                className={cls(
                                    'cursor-pointer transition-all -rotate-90 text-gray-2 mr-2',
                                    expanded ? 'rotate-0' : ''
                                )}
                            />
                        );
                    }
                    return <span className="mr-6"></span>;
                },
                expandRowByClick: true,
            }}
            pagination={false}
            className={cls('w-full', styles.customFileStructureTable)}
        />
    );
};

export default FileStructureTable;
