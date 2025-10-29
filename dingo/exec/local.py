import concurrent.futures
import copy
import itertools
import json
import os
import time
import uuid
from typing import Generator, List, Optional

from tqdm import tqdm

from dingo.config import InputArgs
from dingo.data import Dataset, DataSource, dataset_map, datasource_map
from dingo.exec.base import ExecProto, Executor
from dingo.io import Data, ResultInfo, SummaryModel
from dingo.model import Model
from dingo.model.llm.base import BaseLLM
from dingo.model.modelres import ModelRes
from dingo.model.prompt.base import BasePrompt
from dingo.model.rule.base import BaseRule
from dingo.utils import log


@Executor.register("local")
class LocalExecutor(ExecProto):
    def __init__(self, input_args: InputArgs):
        self.input_args: InputArgs = input_args
        self.llm: Optional[BaseLLM] = None
        self.summary: SummaryModel = SummaryModel()

    def load_data(self) -> Generator[Data, None, None]:
        """
        Reads data from given path.

        **Run in executor.**

        Returns:
            Generator[Data]
        """
        datasource_cls = datasource_map[self.input_args.dataset.source]
        dataset_cls = dataset_map[self.input_args.dataset.source]

        datasource: DataSource = datasource_cls(input_args=self.input_args)
        dataset: Dataset = dataset_cls(source=datasource)
        return dataset.get_data()

    def execute(self) -> SummaryModel:
        log.setLevel(self.input_args.log_level)
        create_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        Model.apply_config(self.input_args)
        input_path = self.input_args.input_path
        output_path = os.path.join(
            self.input_args.output_path, create_time + "_" + str(uuid.uuid1())[:8]
        )

        log.debug(str(self.input_args.executor.eval_group))
        for group_name in [self.input_args.executor.eval_group]:
            if self.input_args.executor.result_save.bad:
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
            if self.input_args.evaluator.llm_config:
                for llm_name in self.input_args.evaluator.llm_config:
                    self.llm = Model.get_llm(llm_name)

            self.summary = SummaryModel(
                task_id=str(uuid.uuid1()),
                task_name=self.input_args.task_name,
                eval_group=group_name,
                input_path=input_path,
                output_path=output_path if self.input_args.executor.result_save.bad else "",
                create_time=create_time,
            )
            self.evaluate()
            self.summary = self.summarize(self.summary)
            self.write_summary(self.summary.output_path, self.input_args, self.summary)

        return self.summary

    def merge_result_info(self, existing_list: List[ResultInfo], new_item: ResultInfo) -> List[ResultInfo]:
        existing_item = next((item for item in existing_list if item.data_id == new_item.data_id), None)

        if existing_item:
            existing_item.error_status = existing_item.error_status or new_item.error_status

            existing_item.type_list = list(set(existing_item.type_list + new_item.type_list))
            existing_item.name_list = list(set(existing_item.name_list + new_item.name_list))
            existing_item.reason_list = list(set(existing_item.reason_list + new_item.reason_list))

            existing_item.raw_data = new_item.raw_data
        else:
            existing_list.append(new_item)

        return existing_list

    def evaluate(self):
        """
        get score (main progres).
        Args:
            group (Any): _description_
            group_type (str): _description_
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.input_args.executor.max_workers
        ) as thread_executor, concurrent.futures.ProcessPoolExecutor(
            max_workers=self.input_args.executor.max_workers
        ) as process_executor:
            data_iter = self.load_data()
            data_iter = itertools.islice(
                data_iter,
                self.input_args.executor.start_index,
                self.input_args.executor.end_index if self.input_args.executor.end_index >= 0 else None,
            )
            pbar = tqdm(total=None, unit="items")

            while True:
                batch = list(itertools.islice(data_iter, self.input_args.executor.batch_size))
                if not batch:
                    break

                futures = []
                futures_results = []
                for data in batch:
                    for group_type, group in Model.get_group(
                            self.input_args.executor.eval_group
                    ).items():
                        if group_type == "rule":
                            if os.environ.get("LOCAL_DEPLOYMENT_MODE") == "true":
                                futures += [
                                    thread_executor.submit(
                                        self.evaluate_single_data, group_type, group, data
                                    )
                                ]
                            else:
                                futures += [
                                    process_executor.submit(
                                        self.evaluate_single_data, group_type, group, data
                                    )
                                ]
                        elif group_type == "prompt":
                            futures += [
                                thread_executor.submit(
                                    self.evaluate_single_data, group_type, group, data
                                )
                            ]
                        else:
                            raise RuntimeError(f"Unsupported group type: {group_type}")

                for future in concurrent.futures.as_completed(futures):
                    result_info = future.result()
                    futures_results = self.merge_result_info(futures_results, result_info)

                for result_info in futures_results:
                    for t in result_info.type_list:
                        self.summary.type_ratio[t] += 1
                    for n in result_info.name_list:
                        self.summary.name_ratio[n] += 1
                    if result_info.error_status:
                        self.summary.num_bad += 1
                    else:
                        self.summary.num_good += 1
                    self.summary.total += 1

                    self.write_single_data(
                        self.summary.output_path, self.input_args, result_info
                    )
                    pbar.update()
                self.write_summary(
                    self.summary.output_path,
                    self.input_args,
                    self.summarize(self.summary),
                )

        log.debug("[Summary]: " + str(self.summary))

    def evaluate_single_data(self, group_type, group, data: Data):
        # Ensure dynamic configs are applied in child processes as well
        try:
            Model.apply_config(self.input_args)
        except Exception as e:
            raise RuntimeError(f"Failed to apply config in child process: {e}")
        result_info = ResultInfo(
            data_id=data.data_id, prompt=data.prompt, content=data.content
        )
        if self.input_args.executor.result_save.raw:
            result_info.raw_data = data.raw_data
        bad_type_list = []
        good_type_list = []
        bad_name_list = []
        good_name_list = []
        bad_reason_list = []
        good_reason_list = []
        # for group_type, group in Model.get_group(group_name).items():
        if group_type == "rule":
            r_i = self.evaluate_rule(group, data)
        elif group_type == "prompt":
            r_i = self.evaluate_prompt(group, data)
        else:
            raise RuntimeError(f"Unsupported group type: {group_type}")
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
        return result_info

    def evaluate_rule(self, group: List[BaseRule], d: Data) -> ResultInfo:
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
                if isinstance(tmp.type, str) and isinstance(tmp.name, str):
                    bad_type_list.append(tmp.type)
                    bad_name_list.append(tmp.type + "-" + tmp.name)
                elif isinstance(tmp.type, List) and isinstance(tmp.name, List):
                    if len(tmp.type) != len(tmp.name):
                        raise Exception(f'ModelRes.type is not the same length to ModelRes.name.\n type: {tmp.type} \n name: {tmp.name}')
                    for i in range(len(tmp.type)):
                        bad_type_list.append(tmp.type[i])
                        bad_name_list.append(tmp.type[i] + "-" + tmp.name[i])
                else:
                    raise Exception('ModelRes.type and ModelRes.name are not str or List at the same time.')
                bad_reason_list.extend(tmp.reason)
            else:
                if isinstance(tmp.type, str) and isinstance(tmp.name, str):
                    good_type_list.append(tmp.type)
                    good_name_list.append(tmp.type + "-" + tmp.name)
                elif isinstance(tmp.type, List) and isinstance(tmp.name, List):
                    if len(tmp.type) != len(tmp.name):
                        raise Exception(f'ModelRes.type is not the same length to ModelRes.name.\n type: {tmp.type} \n name: {tmp.name}')
                    for i in range(len(tmp.type)):
                        good_type_list.append(tmp.type[i])
                        good_name_list.append(tmp.type[i] + "-" + tmp.name[i])
                else:
                    raise Exception('ModelRes.type and ModelRes.name are not str or List at the same time.')
                good_reason_list.extend(tmp.reason)

        if self.input_args.executor.result_save.all_labels:
            # Always include both good and bad results when they exist
            # The final error_status is True if ANY evaluation failed
            all_type_list = list(set(bad_type_list + good_type_list))
            all_name_list = bad_name_list + good_name_list
            all_reason_list = bad_reason_list + good_reason_list

            result_info.type_list = all_type_list
            result_info.name_list = all_name_list
            result_info.reason_list = all_reason_list
        else:
            if result_info.error_status:
                result_info.type_list = list(set(bad_type_list))
                result_info.name_list = bad_name_list
                result_info.reason_list = bad_reason_list
            else:
                result_info.type_list = list(set(good_type_list))
                result_info.name_list = good_name_list
                result_info.reason_list = good_reason_list
        return result_info

    def evaluate_prompt(self, group: List[BasePrompt], d: Data) -> ResultInfo:
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
            tmp: ModelRes = self.llm.eval(d)
            # analyze result
            if tmp.error_status:
                result_info.error_status = True
                if isinstance(tmp.type, str) and isinstance(tmp.name, str):
                    bad_type_list.append(tmp.type)
                    bad_name_list.append(tmp.type + "-" + tmp.name)
                elif isinstance(tmp.type, List) and isinstance(tmp.name, List):
                    if len(tmp.type) != len(tmp.name):
                        raise Exception(
                            f'ModelRes.type is not the same length to ModelRes.name.\n type: {tmp.type} \n name: {tmp.name}')
                    for i in range(len(tmp.type)):
                        bad_type_list.append(tmp.type[i])
                        bad_name_list.append(tmp.type[i] + "-" + tmp.name[i])
                else:
                    raise Exception('ModelRes.type and ModelRes.name are not str or List at the same time.')
                bad_reason_list.extend(tmp.reason)
            else:
                if isinstance(tmp.type, str) and isinstance(tmp.name, str):
                    good_type_list.append(tmp.type)
                    good_name_list.append(tmp.type + "-" + tmp.name)
                elif isinstance(tmp.type, List) and isinstance(tmp.name, List):
                    if len(tmp.type) != len(tmp.name):
                        raise Exception(
                            f'ModelRes.type is not the same length to ModelRes.name.\n type: {tmp.type} \n name: {tmp.name}')
                    for i in range(len(tmp.type)):
                        good_type_list.append(tmp.type[i])
                        good_name_list.append(tmp.type[i] + "-" + tmp.name[i])
                else:
                    raise Exception('ModelRes.type and ModelRes.name are not str or List at the same time.')
                good_reason_list.extend(tmp.reason)

        if self.input_args.executor.result_save.all_labels:
            # Always include both good and bad results when they exist
            # The final error_status is True if ANY evaluation failed
            all_type_list = list(set(bad_type_list + good_type_list))
            all_name_list = bad_name_list + good_name_list
            all_reason_list = bad_reason_list + good_reason_list

            result_info.type_list = all_type_list
            result_info.name_list = all_name_list
            result_info.reason_list = all_reason_list
        else:
            if result_info.error_status:
                result_info.type_list = list(set(bad_type_list))
                result_info.name_list = bad_name_list
                result_info.reason_list = bad_reason_list
            else:
                result_info.type_list = list(set(good_type_list))
                result_info.name_list = good_name_list
                result_info.reason_list = good_reason_list
        return result_info

    def summarize(self, summary: SummaryModel) -> SummaryModel:
        new_summary = copy.deepcopy(summary)
        if new_summary.total == 0:
            return new_summary
        new_summary.score = round(new_summary.num_good / new_summary.total * 100, 2)
        for t in new_summary.type_ratio:
            new_summary.type_ratio[t] = round(
                new_summary.type_ratio[t] / new_summary.total, 6
            )
        for n in new_summary.name_ratio:
            new_summary.name_ratio[n] = round(
                new_summary.name_ratio[n] / new_summary.total, 6
            )
        new_summary.type_ratio = dict(sorted(new_summary.type_ratio.items()))
        new_summary.name_ratio = dict(sorted(new_summary.name_ratio.items()))

        new_summary.finish_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        return new_summary

    def write_single_data(
        self, path: str, input_args: InputArgs, result_info: ResultInfo
    ):
        if not input_args.executor.result_save.bad:
            return

        if not input_args.executor.result_save.good and not result_info.error_status:
            return

        for new_name in result_info.name_list:
            t = str(new_name).split("-")[0]
            n = str(new_name).split("-")[1]
            p_t = os.path.join(path, t)
            if not os.path.exists(p_t):
                os.makedirs(p_t)
            f_n = os.path.join(path, t, n) + ".jsonl"
            with open(f_n, "a", encoding="utf-8") as f:
                if input_args.executor.result_save.raw:
                    str_json = json.dumps(result_info.to_raw_dict(), ensure_ascii=False)
                else:
                    str_json = json.dumps(result_info.to_dict(), ensure_ascii=False)
                f.write(str_json + "\n")

    def write_summary(self, path: str, input_args: InputArgs, summary: SummaryModel):
        if not input_args.executor.result_save.bad:
            return
        with open(path + "/summary.json", "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, indent=4, ensure_ascii=False)

    def get_summary(self):
        return self.summary

    def get_info_list(self, high_quality: bool) -> list:
        info_list = []

        save_raw = self.input_args.executor.result_save.raw
        output_path = self.summary.output_path
        if not os.path.isdir(output_path):
            raise ValueError(f"output_path not exists: {output_path}")

        for root, dirs, files in os.walk(output_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_name = file
                if file_name == "summary.json":
                    continue
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())

                        if save_raw:
                            error_status = data['dingo_result']['error_status']
                        else:
                            error_status = data['error_status']
                        if high_quality and not error_status:
                            info_list.append(data)
                        if not high_quality and error_status:
                            info_list.append(data)

        return info_list

    def get_bad_info_list(self):
        return self.get_info_list(high_quality=False)

    def get_good_info_list(self):
        return self.get_info_list(high_quality=True)
