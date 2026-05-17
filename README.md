# Minimal Mockup POC

提供两种最小化验证方式：

1. `minimal_mockup_poc.py`：OpenCV + Pillow 版本（更接近生产方案）。
2. `minimal_mockup_poc_stdlib.py`：纯 Python 标准库版本（无三方依赖，方便立刻测试）。

## 方式 A：OpenCV + Pillow（推荐）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python minimal_mockup_poc.py --artwork samples/artwork.png --out output/mockup_preview.png
```

## 方式 B：无依赖快速测试

```bash
python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
```

运行后会生成一个马克杯融合效果图：`output/mockup_preview.ppm`。
多数图片查看器可直接打开 `.ppm`。
