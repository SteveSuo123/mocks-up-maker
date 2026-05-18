from __future__ import annotations

"""Minimal Printful integration helpers for template/mockup testing.

Usage examples:
  python printful_integration.py products --limit 10
  python printful_integration.py placements --product-id 657
  python printful_integration.py create-task --product-id 657 --variant-id 4011 --image-url https://.../art.png --placement front
  python printful_integration.py task --task-key <TASK_KEY>
"""

import argparse
import os
import time
from dataclasses import dataclass
from typing import Any

import requests

BASE = "https://api.printful.com"


@dataclass
class PrintfulClient:
    api_key: str

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        r = requests.get(f"{BASE}{path}", headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        r = requests.post(f"{BASE}{path}", headers=self._headers(), json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def list_products(self, limit: int = 20) -> dict[str, Any]:
        return self.get("/products", params={"limit": limit})

    def list_mockup_placements(self, product_id: int) -> dict[str, Any]:
        return self.get(f"/mockup-generator/printfiles/{product_id}")

    def create_mockup_task(
        self,
        product_id: int,
        variant_id: int,
        image_url: str,
        placement: str,
        position: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        files_item: dict[str, Any] = {"placement": placement, "image_url": image_url}
        if position:
            files_item["position"] = position
        payload = {"variant_ids": [variant_id], "files": [files_item]}
        return self.post(f"/mockup-generator/create-task/{product_id}", payload)

    def get_task(self, task_key: str) -> dict[str, Any]:
        return self.get("/mockup-generator/task", params={"task_key": task_key})


def require_client() -> PrintfulClient:
    key = os.getenv("PRINTFUL_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing PRINTFUL_API_KEY environment variable")
    return PrintfulClient(api_key=key)


def cmd_products(args: argparse.Namespace) -> None:
    c = require_client()
    res = c.list_products(limit=args.limit)
    print(res)


def cmd_placements(args: argparse.Namespace) -> None:
    c = require_client()
    res = c.list_mockup_placements(product_id=args.product_id)
    print(res)


def cmd_create_task(args: argparse.Namespace) -> None:
    c = require_client()
    position = None
    if args.area_width and args.area_height and args.width and args.height:
        position = {
            "area_width": args.area_width,
            "area_height": args.area_height,
            "width": args.width,
            "height": args.height,
            "top": args.top,
            "left": args.left,
        }
    res = c.create_mockup_task(
        product_id=args.product_id,
        variant_id=args.variant_id,
        image_url=args.image_url,
        placement=args.placement,
        position=position,
    )
    print(res)


def cmd_task(args: argparse.Namespace) -> None:
    c = require_client()
    if args.wait:
        for _ in range(args.max_polls):
            res = c.get_task(args.task_key)
            print(res)
            status = res.get("result", {}).get("status")
            if status in {"completed", "failed"}:
                return
            time.sleep(args.interval)
    else:
        print(c.get_task(args.task_key))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Printful integration CLI")
    sub = p.add_subparsers(required=True)

    sp = sub.add_parser("products")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_products)

    sp = sub.add_parser("placements")
    sp.add_argument("--product-id", type=int, required=True)
    sp.set_defaults(func=cmd_placements)

    sp = sub.add_parser("create-task")
    sp.add_argument("--product-id", type=int, required=True)
    sp.add_argument("--variant-id", type=int, required=True)
    sp.add_argument("--image-url", required=True)
    sp.add_argument("--placement", default="front")
    sp.add_argument("--area-width", type=int)
    sp.add_argument("--area-height", type=int)
    sp.add_argument("--width", type=int)
    sp.add_argument("--height", type=int)
    sp.add_argument("--top", type=int, default=0)
    sp.add_argument("--left", type=int, default=0)
    sp.set_defaults(func=cmd_create_task)

    sp = sub.add_parser("task")
    sp.add_argument("--task-key", required=True)
    sp.add_argument("--wait", action="store_true")
    sp.add_argument("--interval", type=int, default=3)
    sp.add_argument("--max-polls", type=int, default=40)
    sp.set_defaults(func=cmd_task)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
