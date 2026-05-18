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


### warp 算法怎么选（应用场景）

- `cylindrical`：**默认推荐**，最适合马克杯等圆柱曲面，整体贴附更自然。  
- `mesh`：适合局部复杂形变（比如布料褶皱类场景），但参数更多、调节成本更高。  
- `perspective`：最快，适合近似平面或你只想快速验证位置。  

### 还有哪些参数可调？

当前核心参数：
- `curve_strength`：曲率强度（弧度）
- `shading_strength`：印花明暗调制
- `edge_fade`：边缘淡出
- `projection_strength`：曲面投影强度
- `occlusion_strength`：杯体遮蔽强度
- `mesh_cols / mesh_rows`：mesh 分辨率（仅 mesh 模式关键）

### 坐标调节优化（防止点歪）

现在支持“粗定位 + 微调”流程：
1. 鼠标点击粗定位。  
2. 用方向键按钮（↑↓←→）按步长微调。  
3. 或直接拖动 X/Y 滑条精调并应用到当前点。  


### 多面板坐标调节（可自由选择）

Web 端已支持三种坐标调节 panel：
1. **方式一：点击 + 微调**（适合精细调点）
2. **方式二：框选生成四点**（适合快速出初版）
3. **方式三：预设模板**（适合先套用常用版式）

你可以在页面中自由选择任意方式，也可以组合使用（例如“先预设，再微调”）。


## Printful API 接入（用于测试官方模板/Mockup）

### 1) 配置 API Key

```bash
export PRINTFUL_API_KEY=pfk_xxx
```

### 2) 查看产品列表

```bash
python printful_integration.py products --limit 10
```

### 3) 查看某个商品可用印刷区域/printfiles

```bash
python printful_integration.py placements --product-id 657
```

### 4) 创建 mockup 任务

```bash
python printful_integration.py create-task   --product-id 657   --variant-id 4011   --image-url https://your-cdn/design.png   --placement front
```

### 5) 轮询任务结果

```bash
python printful_integration.py task --task-key <TASK_KEY> --wait
```


## Web 界面内置 Printful 测试

现在 `web_app.py` 已包含 **Printful 集成测试 Tab**，可在页面完成：

1. 页面输入 API Key（或使用环境变量 `PRINTFUL_API_KEY`）
2. 下拉选择 `product / variant / placement`
3. 一键创建 mockup task
4. 轮询并展示 Printful 返回的 mockup 结果

启动后访问 `http://localhost:7860`，切换到 **Printful 集成测试** 标签页即可。
