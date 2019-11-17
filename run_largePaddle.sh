#!/bin/bash
conda init bash
conda activate intel
cd ./PrinceOfAI/a3c-largepad
python main.py --load_checkpoint=checkpoint_pad_final
