# Copyright (C) 2019-2020 Zilliz. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations under the License.


import random
import numpy as np
import time
import argparse
from pymilvus import (
    connections, list_collections,
    FieldSchema, CollectionSchema, DataType,
    Collection
)
TIMEOUT = 120


def hello_milvus(host="127.0.0.1"):
    import time
    # create connection
    connections.connect(host=host, port="19530")

    print(f"\nList collections...")
    print(list_collections())

    # create collection
    dim = 128
    default_fields = [
        FieldSchema(name="int64", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="float", dtype=DataType.FLOAT),
        FieldSchema(name="varchar", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="float_vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    default_schema = CollectionSchema(fields=default_fields, description="test collection")

    print(f"\nCreate collection...")
    collection = Collection(name="hello_milvus", schema=default_schema)

    print(f"\nList collections...")
    print(list_collections())

    #  insert data
    nb = 3000
    vectors = [[random.random() for _ in range(dim)] for _ in range(nb)]
    t0 = time.time()
    collection.insert(
        [
            [i for i in range(nb)],
            [np.float32(i) for i in range(nb)],
            [str(i) for i in range(nb)],
            vectors
        ]
    )
    t1 = time.time()
    print(f"\nInsert {nb} vectors cost {t1 - t0:.4f} seconds")

    t0 = time.time()
    print(f"\nGet collection entities...")
    collection.flush()
    print(collection.num_entities)
    t1 = time.time()
    print(f"\nGet collection entities cost {t1 - t0:.4f} seconds")

    print("\nGet replicas number")
    try:
        replicas_info = collection.get_replicas()
        replica_number = len(replicas_info.groups)
        print(f"\nReplicas number is {replica_number}")
    except Exception as e:
        print(str(e))
        replica_number = 1

    # create index and load table
    default_index = {"index_type": "IVF_SQ8", "metric_type": "L2", "params": {"nlist": 64}}
    print(f"\nCreate index...")
    t0 = time.time()

    collection.release()

    collection.create_index(field_name="float_vector", index_params=default_index)
    t1 = time.time()
    print(f"\nCreate index cost {t1 - t0:.4f} seconds")
    print(f"\nload collection...")
    t0 = time.time()
    collection.load(replica_number=replica_number)
    t1 = time.time()
    print(f"\nload collection cost {t1 - t0:.4f} seconds")

    # load and search
    topK = 5
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    t0 = time.time()
    print(f"\nSearch...")
    # define output_fields of search result
    res = collection.search(
        vectors[-2:], "float_vector", search_params, topK,
        "int64 > 100", output_fields=["int64", "float"], timeout=TIMEOUT
    )
    t1 = time.time()
    print(f"search cost  {t1 - t0:.4f} seconds")
    # show result
    for hits in res:
        for hit in hits:
            # Get value of the random value field for search result
            print(hit, hit.entity.get("float"))

    # query
    expr = "int64 in [2,4,6,8]"
    output_fields = ["int64", "float"]
    res = collection.query(expr, output_fields, timeout=TIMEOUT)
    sorted_res = sorted(res, key=lambda k: k['int64'])
    for r in sorted_res:
        print(r)


parser = argparse.ArgumentParser(description='host ip')
parser.add_argument('--host', type=str, default='127.0.0.1', help='host ip')
args = parser.parse_args()
# add time stamp
print(f"\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}")
hello_milvus(args.host)