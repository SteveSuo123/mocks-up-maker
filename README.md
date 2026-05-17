# Minimal Mockup POC (Python + OpenCV + Pillow)

这是一个最小化效果验证方案（PoC）：
- 读取用户上传图（`--artwork`）
- 通过 OpenCV 透视变换贴到“马克杯模板”的印刷区域
- 用 Pillow 做遮罩、阴影、高光融合
- 输出效果图（`--out`）

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python minimal_mockup_poc.py --artwork samples/artwork.png --out output/mockup_preview.png
```

如果 `samples/artwork.png` 不存在，脚本会自动生成一张默认图用于验证。

## 目录说明

- `minimal_mockup_poc.py`: 最小可运行渲染脚本
- `requirements.txt`: 依赖
- `samples/`: 用户图样例（自动生成）
- `output/`: 输出 mockup 图

## 后续扩展方向

1. 将模板配置从代码中抽离为 JSON（print area / mask / shadow / highlight）。
2. 接入任务队列（Celery/RQ）实现异步 Mockup API。
3. 为 T 恤/帽子引入 mesh warp 和 displacement map 提升真实感。
