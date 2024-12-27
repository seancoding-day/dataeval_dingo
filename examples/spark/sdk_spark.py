import json

from pyspark.sql import SparkSession, DataFrame

from dingo.io import InputArgs, MetaData
from dingo.exec import Executor

##################
# please prepare #
spark: SparkSession = None # please input
input_df: DataFrame = None # please input
input_rdd = input_df.rdd.map(lambda x: MetaData(
    data_id= str(json.loads(x)['id']),
    prompt=str(json.loads(x)['prompt']),
    content=str(json.loads(x)['content']),
    raw_data=json.loads(x)
))
#################

input_data = {
    "eval_group": "default",
    'save_data': True
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["spark"](input_args, spark_session=spark, spark_rdd=input_rdd)
result = executor.execute()
print(result)