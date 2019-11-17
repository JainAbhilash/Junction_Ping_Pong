#!/bin/bash
conda init bash
conda activate intel
cd ./PrinceOfAI/a3c-newstuff
python main.py --load_checkpoint=checkpoint_combined
