import React from 'react';
import cls from 'classnames';
import PieChart from './pieChart';
import IconFont from '@/components/icon-font';

interface ErrorRatio {
    [key: string]: number;
}

export interface SummaryData {
    dataset_id: string;
    input_model: string;
    input_path: string;
    output_path: string;
    score: number;
    num_good: number;
    num_bad: number;
    total: number;
    type_ratio: ErrorRatio;
    name_ratio: ErrorRatio;
    task_id: string;
    eval_model: string;
    task_name: string;
}

interface SummaryDataTableProps {
    data: SummaryData;
    className?: string;
}

const SummaryDataTable: React.FC<SummaryDataTableProps> = ({
    data,
    className,
}) => {
    return (
        <div className={cls(className, 'flex max-h-[500px] relative')}>
            <div
                className={cls(
                    'relative p-8 text-black-1 bg-[#F4F5F9] rounded overflow-hidden w-[380px] 2xl:min-w-[480px] 3xl:min-w-[520px] py-[88px] rounded-lg items-center flex justify-center'
                )}
            >
                <div className="grid grid-cols-3 gap-x-9">
                    <div className="col-span-3 mb-12">
                        <p className="font-semibold text-[3.75rem] leading-[100%] mb-3">
                            {data.score.toFixed(2)}
                        </p>
                        <p className="text-sm text-black-1/[0.8]">评分</p>
                    </div>
                    <div>
                        <p className="text-lg font-semibold mb-4">
                            {data.total}
                        </p>
                        <p className="text-sm text-black-1/[0.8]">总计</p>
                    </div>
                    <div>
                        <p className="text-lg font-semibold mb-4 text-[#00B365]">
                            {data.num_good}
                        </p>
                        <p className="text-sm text-black-1/[0.8]">正确数据</p>
                    </div>
                    <div>
                        <p className="text-lg font-semibold mb-4 text-[#F5483B]">
                            {data.num_bad}
                        </p>
                        <p className="text-sm text-black-1/[0.8]">错误数据</p>
                    </div>
                </div>
            </div>
            <div
                className="absolute top-4 right-5 flex items-center justify-center text-[14px] text-[#0D53DE] cursor-pointer"
                onClick={() =>
                    window.open(
                        'https://github.com/shijinpjlab/Dingo/blob/main/docs/metrics.md'
                    )
                }
            >
                <IconFont
                    type={'icon-GithubFilled'}
                    className="text-[1.25rem] mr-1 z-9"
                />
                维度释义
            </div>
            <div
                className={cls(
                    'px-4 py-12 text-black-1 bg-[#F4F5F9] rounded overflow-hidden flex-1 ml-4 rounded-lg overflow-x-auto  scrollbar-thin relative'
                )}
            >
                <PieChart data={data} />
            </div>
        </div>
    );
};

export default SummaryDataTable;
