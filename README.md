# Project Title

## Conda Environment

```bash
conda create -n df_arena_env python=3.10
conda activate df_arena_env
conda install -c conda-forge librosa
pip install transformers
conda install pytorch torchvision torchaudio cudatoolkit=11.8 -c pytorch  # Adjust cudatoolkit to match your CUDA version
```

your_project/
├── .git/
├── .gitmodules             <-- NEW (Tracks submodules)
├── core.py
├── external/
│   └── aasist/             <-- NEW (This is the entire aasist repo)
├── model/
│   ├── __init__.py
│   ├── base.py
│   ├── model_hf_arena.py
│   └── model_aasist.py     <-- (Your adapter, see below)
└── samples