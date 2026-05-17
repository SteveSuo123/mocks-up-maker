from __future__ import annotations

from pathlib import Path
import tempfile
import gradio as gr

from minimal_mockup_poc import generate_mockup

DEFAULT_QUAD = ["0.33,0.34", "0.67,0.33", "0.67,0.74", "0.34,0.75"]


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _fmt_point(x: float, y: float) -> str:
    return f"{x:.4f},{y:.4f}"


def _parse_point(text: str):
    x, y = text.split(",")
    return float(x), float(y)


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


def nudge_point(which_point, dx, dy, q1, q2, q3, q4, step):
    pts = [q1, q2, q3, q4]
    idx = int(which_point) - 1
    x, y = _parse_point(pts[idx])
    x = _clamp01(x + dx * float(step))
    y = _clamp01(y + dy * float(step))
    pts[idx] = _fmt_point(x, y)
    return pts[0], pts[1], pts[2], pts[3], x, y, f"点{which_point} 微调后: {pts[idx]}"


def apply_box_to_quad(x1, y1, x2, y2):
    x1, x2 = sorted([_clamp01(float(x1)), _clamp01(float(x2))])
    y1, y2 = sorted([_clamp01(float(y1)), _clamp01(float(y2))])
    q1 = _fmt_point(x1, y1)
    q2 = _fmt_point(x2, y1)
    q3 = _fmt_point(x2, y2)
    q4 = _fmt_point(x1, y2)
    return q1, q2, q3, q4, f"已用框选生成四点: {q1} {q2} {q3} {q4}"


def apply_preset(name):
    presets = {
        "居中小图": ["0.38,0.40", "0.62,0.39", "0.62,0.67", "0.38,0.68"],
        "居中大图": ["0.33,0.34", "0.67,0.33", "0.67,0.74", "0.34,0.75"],
        "偏左": ["0.28,0.35", "0.61,0.34", "0.60,0.73", "0.29,0.74"],
        "偏右": ["0.39,0.35", "0.72,0.34", "0.71,0.73", "0.40,0.74"],
    }
    q = presets.get(name, presets["居中大图"])
    return q[0], q[1], q[2], q[3], f"已应用预设: {name}"


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
    gr.Markdown("## Mug Mockup 交互调参（多面板坐标助手）")
    with gr.Row(equal_height=True):
        with gr.Column(scale=5):
            with gr.Row():
                mug_img = gr.Image(label="马克杯底图（可选）", type="pil", height=220)
                art_img = gr.Image(label="印花图（必填）", type="pil", height=220)

            with gr.Accordion("坐标助手：方式一（点击+微调）", open=True):
                which_point = gr.Radio([1, 2, 3, 4], value=1, label="当前点位（1左上/2右上/3右下/4左下）")
                step = gr.Dropdown([0.001, 0.002, 0.005, 0.01], value=0.005, label="微调步长")
                x_slider = gr.Slider(0, 1, value=0.33, step=0.0005, label="当前点X（相对）")
                y_slider = gr.Slider(0, 1, value=0.34, step=0.0005, label="当前点Y（相对）")
                with gr.Row():
                    apply_xy_btn = gr.Button("应用XY到当前点", size="sm")
                    reset_btn = gr.Button("重置默认", size="sm")
                with gr.Row():
                    left_btn = gr.Button("←", size="sm"); right_btn = gr.Button("→", size="sm")
                    up_btn = gr.Button("↑", size="sm"); down_btn = gr.Button("↓", size="sm")

            with gr.Accordion("坐标助手：方式二（框选生成四点）", open=False):
                gr.Markdown("输入左上和右下坐标（相对值0~1），自动生成四点。")
                with gr.Row():
                    bx1 = gr.Number(value=0.33, label="左上X")
                    by1 = gr.Number(value=0.34, label="左上Y")
                    bx2 = gr.Number(value=0.67, label="右下X")
                    by2 = gr.Number(value=0.74, label="右下Y")
                box_btn = gr.Button("按框选生成四点", size="sm")

            with gr.Accordion("坐标助手：方式三（预设模板）", open=False):
                preset = gr.Dropdown(["居中小图", "居中大图", "偏左", "偏右"], value="居中大图", label="选择预设")
                preset_btn = gr.Button("应用预设", size="sm")

            pick_msg = gr.Textbox(label="坐标状态", lines=2)

            with gr.Accordion("参数面板（中文注释）", open=True):
                gr.Markdown("- **cylindrical**：马克杯推荐。\n- **mesh**：复杂局部形变。\n- **perspective**：快速平面贴图。")
                with gr.Row():
                    quad_mode = gr.Dropdown(choices=["relative", "pixels"], value="relative", label="quad模式（relative推荐）")
                    warp_mode = gr.Dropdown(choices=["cylindrical", "mesh", "perspective"], value="cylindrical", label="warp算法")
                with gr.Row():
                    q1 = gr.Textbox(value=DEFAULT_QUAD[0], label="点1 左上")
                    q2 = gr.Textbox(value=DEFAULT_QUAD[1], label="点2 右上")
                    q3 = gr.Textbox(value=DEFAULT_QUAD[2], label="点3 右下")
                    q4 = gr.Textbox(value=DEFAULT_QUAD[3], label="点4 左下")
                with gr.Row():
                    mesh_cols = gr.Slider(8, 40, value=20, step=1, label="mesh cols（网格列数）")
                    mesh_rows = gr.Slider(8, 40, value=16, step=1, label="mesh rows（网格行数）")
                with gr.Row():
                    curve_strength = gr.Slider(0.1, 0.9, value=0.45, step=0.01, label="curve（曲率强度）")
                    shading_strength = gr.Slider(0.0, 0.4, value=0.14, step=0.01, label="shading（明暗调制）")
                with gr.Row():
                    edge_fade = gr.Slider(0.05, 0.5, value=0.24, step=0.01, label="edge（边缘淡出）")
                    projection_strength = gr.Slider(0.0, 0.6, value=0.28, step=0.01, label="projection（曲面投影）")
                    occlusion_strength = gr.Slider(0.0, 0.8, value=0.40, step=0.01, label="occlusion（遮蔽强度）")
                btn = gr.Button("生成 Mockup", variant="primary", size="sm")

        with gr.Column(scale=5):
            out_img = gr.Image(label="输出效果图", height=560)
            log = gr.Textbox(label="日志", lines=3)

    def _on_select(img, which, q1v, q2v, q3v, q4v, evt: gr.SelectData):
        x, y = evt.index
        return pick_quad_point(img, x, y, which, q1v, q2v, q3v, q4v)

    mug_img.select(_on_select, inputs=[mug_img, which_point, q1, q2, q3, q4], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
    which_point.change(load_selected_point, inputs=[which_point, q1, q2, q3, q4], outputs=[x_slider, y_slider])
    apply_xy_btn.click(apply_xy_to_point, inputs=[which_point, x_slider, y_slider, q1, q2, q3, q4], outputs=[q1, q2, q3, q4, pick_msg])
    reset_btn.click(reset_quad, outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
    left_btn.click(lambda wp, q1, q2, q3, q4, s: nudge_point(wp, -1, 0, q1, q2, q3, q4, s), inputs=[which_point, q1, q2, q3, q4, step], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
    right_btn.click(lambda wp, q1, q2, q3, q4, s: nudge_point(wp, 1, 0, q1, q2, q3, q4, s), inputs=[which_point, q1, q2, q3, q4, step], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
    up_btn.click(lambda wp, q1, q2, q3, q4, s: nudge_point(wp, 0, -1, q1, q2, q3, q4, s), inputs=[which_point, q1, q2, q3, q4, step], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])
    down_btn.click(lambda wp, q1, q2, q3, q4, s: nudge_point(wp, 0, 1, q1, q2, q3, q4, s), inputs=[which_point, q1, q2, q3, q4, step], outputs=[q1, q2, q3, q4, x_slider, y_slider, pick_msg])

    box_btn.click(apply_box_to_quad, inputs=[bx1, by1, bx2, by2], outputs=[q1, q2, q3, q4, pick_msg])
    preset_btn.click(apply_preset, inputs=[preset], outputs=[q1, q2, q3, q4, pick_msg])

    btn.click(run_mockup, inputs=[mug_img, art_img, quad_mode, q1, q2, q3, q4, warp_mode, mesh_cols, mesh_rows, curve_strength, shading_strength, edge_fade, projection_strength, occlusion_strength], outputs=[out_img, log])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
