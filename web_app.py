from __future__ import annotations

from pathlib import Path
import tempfile
import gradio as gr

from minimal_mockup_poc import generate_mockup


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


with gr.Blocks(title="Mug Mockup Web UI") as demo:
    gr.Markdown("## Mug Mockup 交互调参\n上传马克杯图和印花图，实时调参数生成效果图。")

    with gr.Row():
        mug_img = gr.Image(label="马克杯底图（可选，不上传则用内置模板）", type="pil")
        art_img = gr.Image(label="印花图（必填）", type="pil")

    with gr.Row():
        quad_mode = gr.Dropdown(choices=["relative", "pixels"], value="relative", label="quad 模式")
        warp_mode = gr.Dropdown(choices=["cylindrical", "mesh", "perspective"], value="cylindrical", label="warp 模式")

    with gr.Row():
        q1 = gr.Textbox(value="0.33,0.34", label="左上")
        q2 = gr.Textbox(value="0.67,0.33", label="右上")
        q3 = gr.Textbox(value="0.67,0.74", label="右下")
        q4 = gr.Textbox(value="0.34,0.75", label="左下")

    with gr.Row():
        mesh_cols = gr.Slider(8, 40, value=20, step=1, label="mesh cols")
        mesh_rows = gr.Slider(8, 40, value=16, step=1, label="mesh rows")

    with gr.Row():
        curve_strength = gr.Slider(0.1, 0.9, value=0.45, step=0.01, label="curve strength")
        shading_strength = gr.Slider(0.0, 0.4, value=0.14, step=0.01, label="shading strength")

    with gr.Row():
        edge_fade = gr.Slider(0.05, 0.5, value=0.24, step=0.01, label="edge fade")
        projection_strength = gr.Slider(0.0, 0.6, value=0.28, step=0.01, label="projection strength")
        occlusion_strength = gr.Slider(0.0, 0.8, value=0.40, step=0.01, label="occlusion strength")

    btn = gr.Button("生成 Mockup", variant="primary")
    out_img = gr.Image(label="输出效果图")
    log = gr.Textbox(label="日志")

    btn.click(
        run_mockup,
        inputs=[mug_img, art_img, quad_mode, q1, q2, q3, q4, warp_mode, mesh_cols, mesh_rows, curve_strength, shading_strength, edge_fade, projection_strength, occlusion_strength],
        outputs=[out_img, log],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
