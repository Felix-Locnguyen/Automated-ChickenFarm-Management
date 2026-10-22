from pathlib import Path

DATASET = Path("04_machine_learning/datasets/chicken_v2")

for split in ("train", "valid", "test"):
    for label_path in sorted((DATASET / split / "labels").glob("*.txt")):
        lines = label_path.read_text().strip().splitlines()
        new_lines = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            cls, coords = parts[0], [float(v) for v in parts[1:]]
            xs, ys = coords[0::2], coords[1::2]
            # ... bạn tính cx, cy, w, h rồi append dòng format 5 cột
        # ... ghi lại file