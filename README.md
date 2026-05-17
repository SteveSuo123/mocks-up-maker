# Minimal Mockup POC

提供两种最小化验证方式：

1. `minimal_mockup_poc.py`：OpenCV + Pillow 版本（支持你自己提供马克杯图和融合图，含 mesh 网格变形）。
2. `minimal_mockup_poc_stdlib.py`：纯 Python 标准库版本（无三方依赖，方便立刻测试）。

## 方式 A：OpenCV + Pillow（推荐）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 中阶真实感（Mesh Warp + 物理感融合）

```bash
python minimal_mockup_poc.py \
  --mug samples/m.png \
  --artwork samples/2.jpg \
  --quad-mode relative \
  --quad 0.33,0.34 0.67,0.33 0.67,0.74 0.34,0.75 \
  --warp-mode cylindrical \
  --curve-strength 0.45 \
  --shading-strength 0.18 \
  --edge-fade 0.24 \
  --debug-quad-out output/quad_debug.png \
  --out output/my_mug_mockup.png
```

### 参数说明

- `--warp-mode perspective|mesh|cylindrical`: 普通透视、网格变形、圆柱预变形（推荐 cylindrical，条纹最少）
- `--mesh-cols`, `--mesh-rows`: 网格密度
- `--curve-strength`: 圆柱曲率强度（0.4~0.7 常用）
- `--shading-strength`: 印花区域光照调制强度（0.1~0.3 常用）
- `--edge-fade`: 印花边缘淡出（0.16~0.30），可解决“右边像没贴在杯子上”
- `--quad-mode`: `pixels` 或 `relative`
- `--debug-quad-out`: 导出红色印刷区调试图

## 方式 B：无依赖快速测试

```bash
python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
```


## 常见问题：融合后有条纹感

已在 mesh 渲染中加入软化叠加，减少网格边界条纹。
如果仍有轻微条纹，可尝试：

- 提高网格密度：`--mesh-cols 28 --mesh-rows 22`
- 降低曲率强度：`--curve-strength 0.45`
- 适当降低光照调制：`--shading-strength 0.12`


## 常见问题：有明显竖条

优先使用 `--warp-mode cylindrical`（默认），它使用连续 remap，不依赖网格块拼接，竖条最少。
若仍有条纹：
- `--curve-strength 0.40~0.50`
- 降低 `--shading-strength` 到 `0.10~0.16`
- 避免过小或高压缩的源图


## 常见问题：右侧没有贴在杯子上

已加入更强的右侧曲面贴附策略（右侧 alpha 收边 + 垂直羽化 + 基于杯子亮度的印花调制）。
建议参数：
- `--warp-mode cylindrical`
- `--curve-strength 0.42~0.50`
- `--edge-fade 0.24~0.30`
- `--shading-strength 0.12~0.18`
