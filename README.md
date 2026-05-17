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
  --warp-mode mesh \
  --mesh-cols 20 \
  --mesh-rows 16 \
  --curve-strength 0.55 \
  --shading-strength 0.18 \
  --debug-quad-out output/quad_debug.png \
  --out output/my_mug_mockup.png
```

### 参数说明

- `--warp-mode perspective|mesh`: 普通透视或网格变形（推荐 mesh）
- `--mesh-cols`, `--mesh-rows`: 网格密度
- `--curve-strength`: 圆柱曲率强度（0.4~0.7 常用）
- `--shading-strength`: 印花区域光照调制强度（0.1~0.3 常用）
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
