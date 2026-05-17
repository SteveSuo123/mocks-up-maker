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
  --projection-strength 0.24 \
  --occlusion-strength 0.35 \
  --debug-quad-out output/quad_debug.png \
  --out output/my_mug_mockup.png
```

### 参数说明

- `--warp-mode perspective|mesh|cylindrical`: 普通透视、网格变形、圆柱预变形（推荐 cylindrical，条纹最少）
- `--mesh-cols`, `--mesh-rows`: 网格密度
- `--curve-strength`: 圆柱曲率强度（0.4~0.7 常用）
- `--shading-strength`: 印花区域光照调制强度（0.1~0.3 常用）
- `--edge-fade`: 印花边缘淡出（0.16~0.30）
- `--projection-strength`: 画布空间圆柱投影强度，解决右侧“漂浮感”
- `--occlusion-strength`: 基于杯子明暗的遮蔽强度，让右侧更像绕到背面
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


> 若你遇到“右侧没贴上去，而且不是边缘问题”，请提高 `--projection-strength` 与 `--occlusion-strength`，这两个参数作用于整体曲面投影和杯体遮蔽，而不仅仅是边缘。


## 高效调参（批量而不是单次对话）

### 1) 批量出图

```bash
python sweep_params.py
```

会在 `output/sweep/` 下生成多组参数结果图，文件名包含参数值。

### 2) 生成对比拼图

```bash
python make_contact_sheet.py
```

会生成：`output/sweep_contact_sheet.jpg`，用于一眼筛选最优参数。


## Web 端交互调参

运行：

```bash
python web_app.py
```

浏览器打开 `http://localhost:7860`，上传杯子图和印花图后可通过滑杆实时调参并生成效果图。

- 输出图：`output/web/web_mockup.png`
- Quad 调试图：`output/web/web_quad_debug.png`


### 坐标参数更友好的方式（不用手输）

Web 页面新增 **坐标助手**：

1. 上传马克杯底图。
2. 选择当前点位（1左上/2右上/3右下/4左下）。
3. 直接在杯子图上点击对应位置。
4. 坐标会自动写入为 `relative`（0~1）。

这样不用再手动输入 `0.33,0.34` 这类参数，调点效率更高。
