import os
import time
import uuid
from typing import Any, Callable, Dict, Generator, List, Optional, Union

from pyspark import SparkConf, SparkContext
from pyspark.rdd import RDD
from pyspark.sql import DataFrame, Row, SparkSession

from dingo.config import GlobalConfig
from dingo.data import Dataset, DataSource, dataset_map, datasource_map
from dingo.exec.base import Executor
from dingo.io import InputArgs, MetaData, ResultInfo, SummaryModel
from dingo.model import Model
from dingo.model.modelres import ModelRes
from dingo.model.prompt.base import BasePrompt
from dingo.model.rule.base import BaseRule
from dingo.model.llm.base import BaseLLM
from dingo.utils import log


@Executor.register('spark')
class SparkExecutor(Executor):
    """
    Spark executor
    """

    def __init__(self, input_args: InputArgs,
                 spark_rdd: RDD = None,
                 spark_session: SparkSession = None,
                 spark_conf: SparkConf = None):
        # eval param
        self.llm: Optional[BaseLLM] = None
        self.group: Optional[Dict] = None
        self.summary: Optional[SummaryModel] = None
        self.bad_info_list: Optional[RDD] = None
        self.good_info_list: Optional[RDD] = None

        # init param
        self.input_args = input_args
        self.spark_rdd = spark_rdd
        self.spark_session = spark_session
        self.spark_conf = spark_conf

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['spark_session']
        del state['spark_rdd']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    # def load_data(self) -> Generator[Any, None, None]:
    #     """
    #     Reads data from given path. Returns generator of raw data.
    #
    #     **Run in executor.**
    #
    #     Returns:
    #         Generator[Any, None, None]: Generator of raw data.
    #     """
    #     datasource_cls = datasource_map[self.input_args.datasource]
    #     dataset_cls = dataset_map["spark"]
    #
    #     datasource: DataSource = datasource_cls(input_args=self.input_args)
    #     dataset: Dataset = dataset_cls(source=datasource)
    #     return dataset.get_data()

    def load_data(self) -> RDD:
        return self.spark_rdd

    def execute(self) -> List[SummaryModel]:
        create_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        Model.apply_config(self.input_args.custom_config, self.input_args.eval_group)
        self.group = Model.get_group(self.input_args.eval_group)
        if GlobalConfig.config and GlobalConfig.config.llm_config:
            for llm_name in GlobalConfig.config.llm_config:
                self.llm = Model.get_llm(llm_name)
        print("============= Init pyspark =============")
        if self.spark_session is not None:
            spark = self.spark_session
            sc = spark.sparkContext
        elif self.spark_conf is not None:
            spark = SparkSession.builder.config(conf=self.spark_conf).getOrCreate()
            sc = spark.sparkContext
        else:
            raise ValueError('[spark_session] and [spark_conf] is none. Please input.')
        print("============== Init Done ===============")

        try:
            # Exec Eval
            # if self.spark_rdd is not None:
            #     data_rdd = self.spark_rdd
            # else:
            #     data_rdd = sc.parallelize(self.load_data(), 3)
            data_rdd = self.load_data()
            total = data_rdd.count()

            data_info_list = data_rdd.map(self.evaluate)
            bad_info_list = data_info_list.filter(lambda x: True if x['error_status'] else False)
            bad_info_list.cache()
            self.bad_info_list = bad_info_list
            if self.input_args.save_correct:
                good_info_list = data_info_list.filter(lambda x: True if not x['error_status'] else False)
                good_info_list.cache()
                self.good_info_list = good_info_list

            num_bad = bad_info_list.count()
            # calculate count
            self.summary = SummaryModel(
                task_id=str(uuid.uuid1()),
                task_name=self.input_args.task_name,
                eval_group=self.input_args.eval_group,
                input_path=self.input_args.input_path,
                output_path='',
                create_time=create_time,
                score=0,
                num_good=0,
                num_bad=0,
                total=0,
                type_ratio={},
                name_ratio={}
            )
            self.summary.total = total
            self.summary.num_bad = num_bad
            self.summary.num_good = total - num_bad
            self.summary.score = round(self.summary.num_good / self.summary.total * 100, 2)

            self.summarize()
            self.summary.finish_time = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        except Exception as e:
            raise e
        finally:
            if not self.input_args.save_data:
                self.clean_context_and_session()
            else:
                self.spark_session = spark
        return [self.summary]

    def evaluate(self, data_rdd_item) -> Dict[str, Any]:
        # eval with models ( Big Data Caution ）
        data: MetaData = data_rdd_item
        result_info = ResultInfo(data_id=data.data_id, prompt=data.prompt, content=data.content)
        if self.input_args.save_raw:
            result_info.raw_data = data.raw_data
        bad_type_list = []
        good_type_list = []
        bad_name_list = []
        good_name_list = []
        bad_reason_list = []
        good_reason_list = []
        for group_type, group in self.group.items():
            if group_type == 'rule':
                r_i = self.evaluate_rule(group, data)
            elif group_type == 'prompt':
                r_i = self.evaluate_prompt(group, data)
            else:
                raise RuntimeError(f'Unsupported group type: {group_type}')
            if r_i.error_status:
                result_info.error_status = True
                bad_type_list = bad_type_list + r_i.type_list
                bad_name_list = bad_name_list + r_i.name_list
                bad_reason_list = bad_reason_list + r_i.reason_list
            else:
                good_type_list = good_type_list + r_i.type_list
                good_name_list = good_name_list + r_i.name_list
                good_reason_list = good_reason_list + r_i.reason_list
        if result_info.error_status:
            result_info.type_list = list(set(bad_type_list))
            for name in bad_name_list:
                if name not in result_info.name_list:
                    result_info.name_list.append(name)
            for reason in bad_reason_list:
                if reason and reason not in result_info.reason_list:
                    result_info.reason_list.append(reason)
        else:
            result_info.type_list = list(set(good_type_list))
            for name in good_name_list:
                if name not in result_info.name_list:
                    result_info.name_list.append(name)
            for reason in good_reason_list:
                if reason and reason not in result_info.reason_list:
                    result_info.reason_list.append(reason)

        return result_info.to_dict()

    def evaluate_rule(self, group: List[BaseRule], d: MetaData) -> ResultInfo:
        result_info = ResultInfo(data_id=d.data_id, prompt=d.prompt, content=d.content)
        log.debug("[RuleGroup]: " + str(group))
        bad_type_list = []
        good_type_list = []
        bad_name_list = []
        good_name_list = []
        bad_reason_list = []
        good_reason_list = []
        for r in group:
            # execute rule
            tmp: ModelRes = r.eval(d)
            # analyze result
            if tmp.error_status:
                result_info.error_status = True
                bad_type_list.append(tmp.type)
                bad_name_list.append(tmp.type + '-' + tmp.name)
                bad_reason_list.extend(tmp.reason)
            else:
                good_type_list.append(tmp.type)
                good_name_list.append(tmp.type + '-' + tmp.name)
                good_reason_list.extend(tmp.reason)
        if result_info.error_status:
            result_info.type_list = list(set(bad_type_list))
            result_info.name_list = bad_name_list
            result_info.reason_list = bad_reason_list
        else:
            result_info.type_list = list(set(good_type_list))
            result_info.name_list = good_name_list
            result_info.reason_list = good_reason_list
        return result_info

    def evaluate_prompt(self, group: List[BasePrompt], d: MetaData) -> ResultInfo:
        result_info = ResultInfo(data_id=d.data_id, prompt=d.prompt, content=d.content)
        log.debug("[PromptGroup]: " + str(group))
        bad_type_list = []
        good_type_list = []
        bad_name_list = []
        good_name_list = []
        bad_reason_list = []
        good_reason_list = []
        for p in group:
            self.llm.set_prompt(p)
            # execute prompt
            tmp: ModelRes = self.llm.call_api(d)
            # analyze result
            if tmp.error_status:
                result_info.error_status = True
                bad_type_list.append(tmp.type)
                bad_name_list.append(tmp.type + '-' + tmp.name)
                bad_reason_list.extend(tmp.reason)
            else:
                good_type_list.append(tmp.type)
                good_name_list.append(tmp.type + '-' + tmp.name)
                good_reason_list.extend(tmp.reason)
        if result_info.error_status:
            result_info.type_list = list(set(bad_type_list))
            result_info.name_list = bad_name_list
            result_info.reason_list = bad_reason_list
        else:
            result_info.type_list = list(set(good_type_list))
            result_info.name_list = good_name_list
            result_info.reason_list = good_reason_list
        return result_info

    def summarize(self):
        list_rdd = self.bad_info_list.flatMap(lambda row: row['type_list'])
        unique_list = list_rdd.distinct().collect()
        for metric_type in unique_list:
            num = self.bad_info_list.filter(lambda x: metric_type in x['type_list']).count()
            self.summary.type_ratio[metric_type] = round(num / self.summary.total, 6)

        list_rdd = self.bad_info_list.flatMap(lambda row: row['name_list'])
        unique_list = list_rdd.distinct().collect()
        for name in unique_list:
            num = self.bad_info_list.filter(lambda x: name in x['name_list']).count()
            self.summary.name_ratio[name] = round(num / self.summary.total, 6)

        self.summary.type_ratio = dict(sorted(self.summary.type_ratio.items()))
        self.summary.name_ratio = dict(sorted(self.summary.name_ratio.items()))

    def get_summary(self):
        return self.summary

    def get_bad_info_list(self):
        return self.bad_info_list

    def get_good_info_list(self):
        return self.good_info_list

    def save_data(self, start_time):
        output_path = os.path.join(self.input_args.output_path, start_time)
        model_path = os.path.join(output_path, self.input_args.eval_group)
        if not os.path.exists(model_path):
            os.makedirs(model_path)

    def clean_context_and_session(self):
        self.spark_session.stop()
        self.spark_session.sparkContext.stop()