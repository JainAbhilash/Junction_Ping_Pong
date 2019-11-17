#!/bin/bash
conda init bash
conda activate intel
cd ./PrinceOfAI/a3c-obstacle
python main.py --load_checkpoint=checkpoint-ob
