# Data Notice

This repository does not include raw Xperience-10M files.

Place a local sample episode on your machine and pass it with `--data-root`:

```bash
export DATA_ROOT=/path/to/xperience-10m-sample
python scripts/scene_graph_demo.py --data-root "$DATA_ROOT"
```

The scene graph exporter expects:

- `annotation.hdf5`

Generated graph artifacts are written under `outputs/`.
