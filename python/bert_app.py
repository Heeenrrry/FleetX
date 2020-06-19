# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import numpy as np
import fleet_lightning as lighting
import paddle.fluid as fluid
from paddle.fluid.incubate.fleet.collective import fleet, DistributedStrategy
import paddle.fluid.incubate.fleet.base.role_maker as role_maker
from fleet_lightning.dataset.bert_reader import load_bert_dataset
import time
# lightning help users to focus more on learning to train a large scale model
# if you want to learn how to write a model, lightning is not for you
# focus more on engineering staff in fleet-lightning

configs = lighting.parse_train_configs()
role = role_maker.PaddleCloudRoleMaker(is_collective=True)
fleet.init(role)

model = lighting.applications.Bert()

data_loader = model.load_digital_dataset_from_file(
    data_dir='./train_data', vocab_path='./vocab.txt')
place = fluid.CUDAPlace(int(os.environ.get('FLAGS_selected_gpus', 0)))
optimizer = fluid.optimizer.Adam(learning_rate=configs.lr)
optimizer = fleet.distributed_optimizer(optimizer)
optimizer.minimize(model.loss)

exe = fluid.Executor(place)
exe.run(fluid.default_startup_program())

total_time = 0
for i, data in enumerate(data_loader()):
    start_time = time.time()
    cost_val = exe.run(fleet.main_program,
                       feed=data,
                       fetch_list=[model.loss.name])
    end_time = time.time()
    total_time += (end_time - start_time)
    print("worker_index: %d, step%d cost = %f, total time cost = %f" %
          (fleet.worker_index(), i, cost_val[0], total_time))