#!/bin/bash
conda init bash
conda activate intel
cd ./PrinceOfAI/a3c
python main.py --load_checkpoint=final-model
