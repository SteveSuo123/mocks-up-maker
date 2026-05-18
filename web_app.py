from __future__ import annotations

from pathlib import Path
import os
import tempfile
import time
import gradio as gr

from minimal_mockup_poc import generate_mockup
from printful_integration import PrintfulClient

DEFAULT_QUAD = ["0.33,0.34", "0.67,0.33", "0.67,0.74", "0.34,0.75"]


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _fmt_point(x: float, y: float) -> str:
    return f"{x:.4f},{y:.4f}"


def _parse_point(text: str):
    x, y = text.split(",")
    return float(x), float(y)


def _client(api_key_input: str) -> PrintfulClient:
    key = (api_key_input or "").strip() or os.getenv("PRINTFUL_API_KEY", "").strip()
    if not key:
        raise ValueError("缺少 Printful API Key：请在页面输入，或设置环境变量 PRINTFUL_API_KEY")
    return PrintfulClient(api_key=key)


def load_products(api_key_input: str):
    c = _client(api_key_input)
    data = c.list_products(limit=50)
    result = data.get("result", [])
    choices = []
    for p in result:
        pid = p.get("id")
        title = p.get("title") or p.get("model") or f"product_{pid}"
        choices.append(f"{pid} | {title}")
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None), f"已加载产品 {len(choices)} 个"


def load_placements(api_key_input: str, product_choice: str):
    if not product_choice:
        return gr.Dropdown(choices=[]), gr.Dropdown(choices=[]), "请先选择产品"
    product_id = int(product_choice.split("|")[0].strip())
    c = _client(api_key_input)
    data = c.list_mockup_placements(product_id=product_id).get("result", {})

    placements = []
    variants = []

    pf = data.get("printfiles", [])
    if isinstance(pf, list):
        for item in pf:
            pl = item.get("placement")
            if pl and pl not in placements:
                placements.append(pl)

    var = data.get("variant_printfiles", [])
    if isinstance(var, list):
        for v in var:
            vid = v.get("variant_id")
            if vid is not None:
                variants.append(str(vid))

    msg = f"已加载 placement={len(placements)}，variant={len(variants)}"
    return gr.Dropdown(choices=placements, value=placements[0] if placements else None), gr.Dropdown(choices=variants, value=variants[0] if variants else None), msg


def create_printful_task(api_key_input: str, product_choice: str, variant_id: str, placement: str, image_url: str,
                         area_width, area_height, width, height, top, left):
    if not product_choice:
        return "", "请先选择产品"
    if not variant_id:
        return "", "请先选择变体"
    if not placement:
        return "", "请先选择 placement"
    if not image_url:
        return "", "请填写公网可访问的设计图 URL"

    c = _client(api_key_input)
    product_id = int(product_choice.split("|")[0].strip())

    pos = None
    if area_width and area_height and width and height:
        pos = {
            "area_width": int(area_width),
            "area_height": int(area_height),
            "width": int(width),
            "height": int(height),
            "top": int(top or 0),
            "left": int(left or 0),
        }

    res = c.create_mockup_task(
        product_id=product_id,
        variant_id=int(variant_id),
        image_url=image_url,
        placement=placement,
        position=pos,
    )
    task_key = res.get("result", {}).get("task_key", "")
    return task_key, f"任务已创建: {task_key or '[no task_key]'}"


def poll_printful_task(api_key_input: str, task_key: str, interval_sec: int, max_polls: int):
    if not task_key:
        return "", "请先创建 task 并获得 task_key"
    c = _client(api_key_input)
    last = {}
    for _ in range(int(max_polls)):
        last = c.get_task(task_key)
        status = last.get("result", {}).get("status")
        if status in {"completed", "failed"}:
            break
        time.sleep(int(interval_sec))

    result = last.get("result", {})
    mockups = result.get("mockups", [])
    preview_url = ""
    if isinstance(mockups, list) and mockups:
        preview_url = mockups[0].get("mockup_url") or mockups[0].get("url") or ""

    return preview_url, f"状态: {result.get('status')}\nTask: {task_key}\nMockups: {len(mockups) if isinstance(mockups, list) else 0}"


def pick_quad_point(mug_img, x, y, which_point, q1, q2, q3, q4):
    if mug_img is None:
        return q1, q2, q3, q4, 0.33, 0.34, "请先上传马克杯底图，再点击取点。"
    w, h = mug_img.size
    rx = _clamp01(float(x) / max(1, w - 1))
    ry = _clamp01(float(y) / max(1, h - 1))
    val = _fmt_point(rx, ry)
    pts = [q1, q2, q3, q4]
    idx = int(which_point) - 1
    pts[idx] = val
    return pts[0], pts[1], pts[2], pts[3], rx, ry, f"已设置点{which_point}: {val}（可微调）"


def reset_quad():
    return DEFAULT_QUAD[0], DEFAULT_QUAD[1], DEFAULT_QUAD[2], DEFAULT_QUAD[3], 0.33, 0.34, "已恢复默认相对坐标。"


def load_selected_point(which_point, q1, q2, q3, q4):
    pts = [q1, q2, q3, q4]
    x, y = _parse_point(pts[int(which_point) - 1])
    return x, y


def apply_xy_to_point(which_point, x, y, q1, q2, q3, q4):
    pts = [q1, q2, q3, q4]
    pts[int(which_point) - 1] = _fmt_point(_clamp01(float(x)), _clamp01(float(y)))
    return pts[0], pts[1], pts[2], pts[3], f"已应用到点{which_point}: {pts[int(which_point)-1]}"


def run_mockup(mug_img, art_img, quad_mode, q1, q2, q3, q4, warp_mode, mesh_cols, mesh_rows, curve_strength, shading_strength, edge_fade, projection_strength, occlusion_strength):
    if art_img is None:
        return None, "请上传要融合的图案（artwork）"
    out_dir = Path("output/web")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        art_path = tdp / "art.png"
        art_img.save(art_path)
        mug_path = None
        if mug_img is not None:
            mug_path = tdp / "mug.png"
            mug_img.save(mug_path)
        out_path = out_dir / "web_mockup.png"
        debug_path = out_dir / "web_quad_debug.png"
        generate_mockup(
            mug=mug_path,
            artwork=art_path,
            out=out_path,
            quad=[q1, q2, q3, q4],
            quad_mode=quad_mode,
            warp_mode=warp_mode,
            mesh_cols=int(mesh_cols),
            mesh_rows=int(mesh_rows),
            curve_strength=float(curve_strength),
            shading_strength=float(shading_strength),
            edge_fade=float(edge_fade),
            projection_strength=float(projection_strength),
            occlusion_strength=float(occlusion_strength),
            debug_quad_out=debug_path,
        )
    return str(out_path), f"生成完成\n结果: {out_path}\nQuad调试图: {debug_path}"


with gr.Blocks(title="Mug Mockup Web UI") as demo:
    gr.Markdown("## Mug Mockup 交互调参（含 Printful 集成）")

    with gr.Tab("本地融合测试"):
        with gr.Row(equal_height=True):
            with gr.Column(scale=5):
                with gr.Row():
                    mug_img = gr.Image(label="马克杯底图（可选）", type="pil", height=220)
                    art_img = gr.Image(label="印花图（必填）", type="pil", height=220)
                which_point = gr.Radio([1, 2, 3, 4], value=1, label="当前点位")
                x_slider = gr.Slider(0, 1, value=0.33, step=0.0005, label="X")
                y_slider = gr.Slider(0, 1, value=0.34, step=0.0005, label="Y")
                with gr.Row():
                    q1 = gr.Textbox(value=DEFAULT_QUAD[0], label="点1 左上")
                    q2 = gr.Textbox(value=DEFAULT_QUAD[1], label="点2 右上")
                    q3 = gr.Textbox(value=DEFAULT_QUAD[2], label="点3 右下")
                    q4 = gr.Textbox(value=DEFAULT_QUAD[3], label="点4 左下")
                pick_msg = gr.Textbox(label="坐标状态", lines=2)
                with gr.Row():
                    reset_btn = gr.Button("重置默认", size="sm")
                    apply_xy_btn = gr.Button("应用XY", size="sm")

                quad_mode = gr.Dropdown(choices=["relative", "pixels"], value="relative", label="quad模式")
                warp_mode = gr.Dropdown(choices=["cylindrical", "mesh", "perspective"], value="cylindrical", label="warp算法")
                mesh_cols = gr.Slider(8, 40, value=20, step=1, label="mesh cols")
                mesh_rows = gr.Slider(8, 40, value=16, step=1, label="mesh rows")
                curve_strength = gr.Slider(0.1, 0.9, value=0.45, step=0.01, label="curve")
                shading_strength = gr.Slider(0.0, 0.4, value=0.14, step=0.01, label="shading")
                edge_fade = gr.Slider(0.05, 0.5, value=0.24, step=0.01, label="edge")
                projection_strength = gr.Slider(0.0, 0.6, value=0.28, step=0.01, label="projection")
                occlusion_strength = gr.Slider(0.0, 0.8, value=0.40, step=0.01, label="occlusion")
                btn = gr.Button("生成本地 Mockup", variant="primary")

            with gr.Column(scale=5):
                out_img = gr.Image(label="本地输出效果图", height=560)
                log = gr.Textbox(label="日志", lines=3)

        def _on_select(img, which, q1v, q2v, q3v, q4v, evt: gr.SelectData):
            x, y = evt.index
            return pick_quad_point(img, x, y, which, q1v, q2v, q3v, q4v)

        mug_img.select(_on_select, inputs=[mug_img, which_point, q1, q2, q3, q4], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
        which_point.change(load_selected_point, inputs=[which_point, q1, q2, q3, q4], outputs=[x_slider, y_slider])
        apply_xy_btn.click(apply_xy_to_point, inputs=[which_point, x_slider, y_slider, q1, q2, q3, q4], outputs=[q1, q2, q3, q4, pick_msg])
        reset_btn.click(reset_quad, outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
        btn.click(run_mockup, inputs=[mug_img, art_img, quad_mode, q1, q2, q3, q4, warp_mode, mesh_cols, mesh_rows, curve_strength, shading_strength, edge_fade, projection_strength, occlusion_strength], outputs=[out_img, log])

    with gr.Tab("Printful 集成测试"):
        gr.Markdown("输入 API Key（可选，留空则读环境变量 PRINTFUL_API_KEY）")
        api_key_input = gr.Textbox(label="Printful API Key", type="password")
        with gr.Row():
            load_products_btn = gr.Button("1) 加载产品")
            product_dropdown = gr.Dropdown(label="产品 product_id | title", choices=[])
        with gr.Row():
            load_placements_btn = gr.Button("2) 加载 placement/variant")
            placement_dropdown = gr.Dropdown(label="placement", choices=[])
            variant_dropdown = gr.Dropdown(label="variant_id", choices=[])
        status_box = gr.Textbox(label="状态", lines=2)

        gr.Markdown("3) 创建 mockup task")
        image_url_input = gr.Textbox(label="设计图公网 URL（Printful 必须可访问）")
        with gr.Accordion("可选 position（不填则由 Printful 默认）", open=False):
            with gr.Row():
                area_w = gr.Number(label="area_width", value=None)
                area_h = gr.Number(label="area_height", value=None)
                width = gr.Number(label="width", value=None)
                height = gr.Number(label="height", value=None)
            with gr.Row():
                top = gr.Number(label="top", value=0)
                left = gr.Number(label="left", value=0)
        create_task_btn = gr.Button("创建任务", variant="primary")
        task_key_box = gr.Textbox(label="task_key")

        gr.Markdown("4) 轮询并展示结果")
        with gr.Row():
            poll_interval = gr.Number(label="轮询间隔(秒)", value=3)
            max_polls = gr.Number(label="最大轮询次数", value=40)
            poll_btn = gr.Button("轮询任务")
        printful_preview = gr.Image(label="Printful mockup 结果预览")
        printful_log = gr.Textbox(label="Printful 日志", lines=4)

        load_products_btn.click(load_products, inputs=[api_key_input], outputs=[product_dropdown, status_box])
        load_placements_btn.click(load_placements, inputs=[api_key_input, product_dropdown], outputs=[placement_dropdown, variant_dropdown, status_box])
        create_task_btn.click(
            create_printful_task,
            inputs=[api_key_input, product_dropdown, variant_dropdown, placement_dropdown, image_url_input, area_w, area_h, width, height, top, left],
            outputs=[task_key_box, status_box],
        )
        poll_btn.click(
            poll_printful_task,
            inputs=[api_key_input, task_key_box, poll_interval, max_polls],
            outputs=[printful_preview, printful_log],
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
