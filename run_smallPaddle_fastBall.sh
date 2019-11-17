#!/bin/bash
conda init bash
conda activate intel
cd ./PrinceOfAI/a3c-ball
python main.py --load_checkpoint=checkpoint_balls_final
