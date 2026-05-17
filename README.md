# Minimal Mockup POC

提供两种最小化验证方式：

1. `minimal_mockup_poc.py`：OpenCV + Pillow 版本（支持你自己提供马克杯图和融合图）。
2. `minimal_mockup_poc_stdlib.py`：纯 Python 标准库版本（无三方依赖，方便立刻测试）。

## 方式 A：OpenCV + Pillow（推荐）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 使用内置马克杯模板

```bash
python minimal_mockup_poc.py \
  --artwork samples/artwork.png \
  --out output/mockup_preview.png
```

### 使用你自己的马克杯图 + 融合图

```bash
python minimal_mockup_poc.py \
  --mug samples/my_mug.jpg \
  --artwork samples/my_design.png \
  --quad 460,300 820,285 840,640 470,655 \
  --out output/my_mug_mockup.png
```

- `--mug`: 你的马克杯底图（JPG/PNG）
- `--artwork`: 要融合的图案
- `--quad`: 印刷区域四点（左上、右上、右下、左下）
- `--out`: 输出文件

> 如果不传 `--quad`，程序会使用一个基于图片尺寸的默认区域。

## 方式 B：无依赖快速测试

```bash
python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
```
