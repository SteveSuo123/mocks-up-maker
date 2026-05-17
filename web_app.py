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


def pick_quad_point(mug_img, x, y, which_point, q1, q2, q3, q4):
    if mug_img is None:
        return q1, q2, q3, q4, "请先上传马克杯底图，再点击取点。"

    w, h = mug_img.size
    rx = _clamp01(float(x) / max(1, w - 1))
    ry = _clamp01(float(y) / max(1, h - 1))
    val = _fmt_point(rx, ry)

    pts = [q1, q2, q3, q4]
    idx = int(which_point) - 1
    pts[idx] = val
    return pts[0], pts[1], pts[2], pts[3], f"已设置点{which_point}: {val}"


def reset_quad():
    return DEFAULT_QUAD[0], DEFAULT_QUAD[1], DEFAULT_QUAD[2], DEFAULT_QUAD[3], "已恢复默认相对坐标。"


def run_mockup(
    mug_img,
    art_img,
    quad_mode,
    q1,
    q2,
    q3,
    q4,
    warp_mode,
    mesh_cols,
    mesh_rows,
    curve_strength,
    shading_strength,
    edge_fade,
    projection_strength,
    occlusion_strength,
):
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

        quad = [q1, q2, q3, q4]
        generate_mockup(
            mug=mug_path,
            artwork=art_path,
            out=out_path,
            quad=quad,
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


css = """
.compact .gr-form, .compact .gr-box, .compact .block, .compact .gr-group {padding: 6px !important; margin: 4px 0 !important;}
.compact .gradio-slider {margin-top: 2px !important; margin-bottom: 2px !important;}
.compact .gradio-dropdown, .compact .gradio-textbox {margin-top: 2px !important; margin-bottom: 2px !important;}
"""

with gr.Blocks(title="Mug Mockup Web UI", css=css) as demo:
    gr.Markdown("## Mug Mockup 交互调参（紧凑布局）")

    with gr.Row(equal_height=True):
        with gr.Column(scale=5):
            with gr.Row():
                mug_img = gr.Image(label="马克杯底图（可选）", type="pil", height=220)
                art_img = gr.Image(label="印花图（必填）", type="pil", height=220)

            with gr.Accordion("坐标助手（推荐）", open=True, elem_classes=["compact"]):
                gr.Markdown("选择要设置的点位，然后在杯子图上点击。会自动写入相对坐标（0~1）。")
                with gr.Row():
                    which_point = gr.Radio([1, 2, 3, 4], value=1, label="当前设置点（1左上/2右上/3右下/4左下）")
                    pick_btn = gr.Button("点击杯子图取点", size="sm")
                    reset_btn = gr.Button("重置默认坐标", size="sm")
                pick_msg = gr.Textbox(label="取点状态", lines=1)

            with gr.Accordion("参数面板（紧凑）", open=True, elem_classes=["compact"]):
                with gr.Row():
                    quad_mode = gr.Dropdown(choices=["relative", "pixels"], value="relative", label="quad")
                    warp_mode = gr.Dropdown(choices=["cylindrical", "mesh", "perspective"], value="cylindrical", label="warp")

                with gr.Row():
                    q1 = gr.Textbox(value=DEFAULT_QUAD[0], label="左上")
                    q2 = gr.Textbox(value=DEFAULT_QUAD[1], label="右上")
                    q3 = gr.Textbox(value=DEFAULT_QUAD[2], label="右下")
                    q4 = gr.Textbox(value=DEFAULT_QUAD[3], label="左下")

                with gr.Row():
                    mesh_cols = gr.Slider(8, 40, value=20, step=1, label="mesh cols")
                    mesh_rows = gr.Slider(8, 40, value=16, step=1, label="mesh rows")

                with gr.Row():
                    curve_strength = gr.Slider(0.1, 0.9, value=0.45, step=0.01, label="curve")
                    shading_strength = gr.Slider(0.0, 0.4, value=0.14, step=0.01, label="shading")

                with gr.Row():
                    edge_fade = gr.Slider(0.05, 0.5, value=0.24, step=0.01, label="edge")
                    projection_strength = gr.Slider(0.0, 0.6, value=0.28, step=0.01, label="projection")
                    occlusion_strength = gr.Slider(0.0, 0.8, value=0.40, step=0.01, label="occlusion")

                btn = gr.Button("生成 Mockup", variant="primary", size="sm")

        with gr.Column(scale=5):
            out_img = gr.Image(label="输出效果图", height=560)
            log = gr.Textbox(label="日志", lines=3)

    # image click event API returns SelectData with index(x,y)
    def _on_select(img, which, q1v, q2v, q3v, q4v, evt: gr.SelectData):
        x, y = evt.index
        return pick_quad_point(img, x, y, which, q1v, q2v, q3v, q4v)

    mug_img.select(
        _on_select,
        inputs=[mug_img, which_point, q1, q2, q3, q4],
        outputs=[q1, q2, q3, q4, pick_msg],
    )

    reset_btn.click(reset_quad, outputs=[q1, q2, q3, q4, pick_msg])

    btn.click(
        run_mockup,
        inputs=[mug_img, art_img, quad_mode, q1, q2, q3, q4, warp_mode, mesh_cols, mesh_rows, curve_strength, shading_strength, edge_fade, projection_strength, occlusion_strength],
        outputs=[out_img, log],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
