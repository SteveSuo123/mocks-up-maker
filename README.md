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

### 使用你自己的马克杯图 + 融合图（像素坐标）

```bash
python minimal_mockup_poc.py \
  --mug samples/m.png \
  --artwork samples/2.jpg \
  --quad 460,300 820,285 840,640 470,655 \
  --debug-quad-out output/quad_debug.png \
  --out output/my_mug_mockup.png
```

### 使用相对坐标（推荐跨不同分辨率）

```bash
python minimal_mockup_poc.py \
  --mug samples/m.png \
  --artwork samples/2.jpg \
  --quad-mode relative \
  --quad 0.33,0.34 0.67,0.33 0.67,0.74 0.34,0.75 \
  --out output/my_mug_mockup.png
```

- `--quad-mode pixels`: `--quad` 按像素解释（默认）
- `--quad-mode relative`: `--quad` 按 0~1 比例解释
- `--debug-quad-out`: 输出红色四边形调试图，先确认印刷区域位置再做融合

> 你反馈“看不到融合效果”通常是 `--quad` 与杯子图分辨率不匹配。优先先看 `--debug-quad-out` 是否覆盖在杯身上。

## 方式 B：无依赖快速测试

```bash
python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
```


### PowerShell 一行版（Windows）

```powershell
python minimal_mockup_poc.py --mug samples/m.png --artwork samples/2.jpg --quad-mode relative --quad 0.33,0.34 0.67,0.33 0.67,0.74 0.34,0.75 --out output/my_mug_mockup1.png
```

如果提示 `unrecognized arguments: --quad-mode relative`，请先确认是最新脚本，或使用兼容别名：

```powershell
python minimal_mockup_poc.py --mug samples/m.png --artwork samples/2.jpg --quad_mode relative --quad 0.33,0.34 0.67,0.33 0.67,0.74 0.34,0.75 --out output/my_mug_mockup1.png
```
