import React, { useState, useEffect } from 'react';
import { Button, message, Tabs, Popover } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import styles from '@/styles/custom-antd.module.scss';
import SummaryDataTable from '@/pages/main-home/components/summary-data-table';
import FileStructureTable, { TableDataItem } from './file-structure-table';
import { useIntl } from 'react-intl';
import DetailTable from './detail-table';
import Empty from '@/components/empty';
const { TabPane } = Tabs;
import { useDALStore } from '@/store/dal';
import { isElectron } from '@/utils/env';
import { WEB_DATA_SOURCE } from '@/constant';
import cls from 'classnames';
import IconFont from './icon-font';
import copy from 'copy-to-clipboard';

interface Config {
    summaryPathName: string;
}

export interface FileStructure {
    name: string;
    files: string[];
}

interface ReadFileDirProps {
    className?: string;
}

const CONFIG: Config = {
    summaryPathName: 'summary.json',
};

const ReadFileDir: React.FC<ReadFileDirProps> = ({ className }) => {
    const [currentPath, setCurrentPath] = useState<string>('');
    const [fileStructure, setFileStructure] = useState<FileStructure[]>([]);
    const [summary, setSummary] = useState<any>(null);
    const dal = useDALStore(state => state.dal);

    const { formatMessage } = useIntl();
    const [allDataPath, setAllDataPath] = useState<any[]>([]);

    useEffect(() => {
        if (currentPath) {
            dal
                ?.getSummary?.({
                    path: currentPath + '/' + CONFIG.summaryPathName,
                })
                .then(res => {
                    setSummary(res);
                    readFileStructure(currentPath);
                })
                .catch(() => {
                    message.error(
                        formatMessage({ id: 'summary.compile.error' })
                    );
                });
        }
    }, [currentPath]);

    const readFileStructure = async (dirPath: string): Promise<void> => {
        try {
            const structure = await dal?.getEvaluationList?.({
                dirPath,
            });

            setFileStructure(structure as FileStructure[]);
        } catch (error) {
            console.error('Error reading directory structure:', error);
        }
    };

    const selectDirectory = async (): Promise<void> => {
        try {
            const result: string | undefined =
                await window.electronAPI.selectDirectory();
            if (result) {
                setCurrentPath(result);
            }
        } catch (error) {
            console.error('Error selecting directory:', error);
        }
    };

    console.log(
        'records-detailPath-init',
        dal?.getInputPath?.(),
        window?.[WEB_DATA_SOURCE]
    );

    useEffect(() => {
        dal?.getInputPath?.().then(res => {
            if (res) {
                setCurrentPath(res);
            }
        });
    }, [dal]);

    const configInfo = [
        {
            key: 'task_id',
            label: '任务ID',
            value: summary?.task_id,
        },
        {
            key: 'eval_group',
            label: '评测方法',
            value: summary?.eval_group,
        },

        {
            key: 'input_path',
            label: '输入路径',
            value: summary?.input_path,
        },
        {
            key: 'output_path',
            label: '输出路径',
            value: summary?.output_path,
        },
    ];

    useEffect(() => {
        setAllDataPath(
            fileStructure.map(i => ({
                primaryName: i.name,
                secondaryNameList: i.files,
            }))
        );
    }, [fileStructure]);

    return (
        <div
            className={`${className} py-[30px] px-9 h-full overflow-auto scrollbar-thin`}
        >
            <header className="h-[2.25rem] text-black-1 flex items-center font-semibold text-[1.5rem] mb-6 ">
                {summary && (
                    <span className="text-[1.5rem] font-semibold">
                        {summary?.task_name}
                    </span>
                )}
                <Popover
                    align={{
                        offset: [172, -10],
                    }}
                    content={
                        <div className="min-w-[25rem]">
                            {configInfo.map(i => (
                                <div
                                    key={i.key}
                                    className={cls(
                                        'my-[0.3rem] p-2 text-[#121316]/[0.8] pr-8 group relative',
                                        i.key !== 'eval_group' &&
                                            'hover:bg-[#F9F9F9]'
                                    )}
                                >
                                    <span className="inline-block w-[5rem] ml-3  ">
                                        <span> {i.label}</span>
                                    </span>
                                    <span
                                        className={cls(
                                            'bg-red-100',
                                            i.key === 'eval_group' &&
                                                'bg-[#F4F5F9] p-2 rounded'
                                        )}
                                    >
                                        {i.value}
                                    </span>
                                    {i.key !== 'eval_group' && (
                                        <IconFont
                                            type={'icon-copy'}
                                            onClick={e => {
                                                e?.stopPropagation();
                                                copy(i?.value);
                                                message.success('复制成功');
                                            }}
                                            className="opacity-0 cursor-pointer group-hover:opacity-100 absolute top-1/2 right-[6px] -translate-y-1/2 right-0"
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    }
                    overlayClassName={styles.customConfigPopover}
                >
                    <div className="ml-6 flex items-center text-[0.875rem] text-[#0D53DE] cursor-pointer">
                        {formatMessage({
                            id: 'summary.config.popover.title',
                        })}
                        <IconFont
                            type="icon-info"
                            className="ml-1 text-[1rem]"
                        />
                    </div>
                </Popover>
                {isElectron() && (
                    <Button
                        className={'rounded-full ml-4'}
                        onClick={selectDirectory}
                    >
                        {formatMessage({ id: 'button.selectDirectory' })}
                    </Button>
                )}
            </header>
            {summary ? (
                <>
                    <SummaryDataTable data={summary} className="mb-9" />
                    <DetailTable
                        summary={summary}
                        currentPath={currentPath}
                        detailPathList={[]}
                        allDataPath={allDataPath}
                        defaultErrorTypes={[]}
                        defaultErrorNames={[]}
                    />
                </>
            ) : (
                <Empty
                    className="h-[60vh]"
                    title={formatMessage({ id: 'empty.title' })}
                ></Empty>
            )}
        </div>
    );
};

export default ReadFileDir;
