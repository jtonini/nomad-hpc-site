#!/usr/bin/env python3
"""Make the site's screenshots again from `nomad demo --console` (made-up people).

What it needs:
  - nomad (pip install nomad-hpc), Pillow, ansi2html and Playwright with a
    Chromium (pip install pillow ansi2html playwright && playwright install chromium)
  - the demo, made with a fixed seed so the job numbers below exist:
        nomad demo --console ~/nomad-site-demo --seed 2
  - (or set NOMAD_SITE_CHROME to a Chrome or Chromium already installed)
  - the Console running on that demo, on port 8000, from its backend folder:
        HOME=~/nomad-site-demo NOMAD_CONSOLE_DEMO=1 python3 -m uvicorn app.main:app --port 8000

Then, from this repository:
        python3 scripts/make_screenshots.py ~/nomad-site-demo

It writes static/images/console-*.webp, cli-explain.webp and email-weekly.webp.
Nothing it shows is real: the demo's people (bob, grace, adam...) and its
cluster are made up.
"""
from __future__ import annotations

import html
import os
import pty
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

CONSOLE = "http://localhost:8000"
OUT = Path(__file__).resolve().parent.parent / "static" / "images"
SCALE = 1.5                     # 1440 x 900 pages, saved at 2160 x 1350

# Who signs in, which page, the file name, and a node to click first if any.
PAGES = {
    "bob": [("/home", "home", None), ("/edu/explain", "my-jobs", None),
            ("/edu/explain?job=1278", "job", None), ("/me", "doing", None)],
    "grace": [("/lab?tab=members", "lab", None), ("/lab?tab=clusters", "lab-share", None),
              ("/lab/report", "term-report", None)],
    "adam": [("/dashboard", "overview", None), ("/infrastructure", "busy", None),
             ("/nodes", "nodes", "node07"), ("/interactive", "interactive", None),
             ("/alerts", "alerts", None), ("/insights", "trends", None),
             ("/network", "network", None), ("/predict", "waits", None)],
}
CLI_JOB = "1653"                # a finished job of bob's in the seed-2 demo


def webp(png: Path, name: str, quality: int = 82, width: int | None = None) -> None:
    im = Image.open(png)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA") else "RGB")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(OUT / name, "WEBP", quality=quality, method=6)
    print("wrote", OUT / name)


def sign_in(browser, who: str, **kw):
    ctx = browser.new_context(**kw)
    page = ctx.new_page()
    page.goto(CONSOLE + "/", wait_until="networkidle")
    page.get_by_text(who, exact=True).first.click()     # the demo's sign-in, no password
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    return ctx, page


def console_pages(browser, tmp: Path) -> None:
    for who, pages in PAGES.items():
        ctx, page = sign_in(browser, who, viewport={"width": 1440, "height": 900},
                            device_scale_factor=SCALE)
        for path, name, click in pages:
            page.goto(CONSOLE + path, wait_until="networkidle")
            page.wait_for_timeout(2500)
            if click:
                page.get_by_text(click, exact=True).first.click()
                page.wait_for_timeout(2500)
            page.mouse.move(5, 895)                     # no hover marks
            png = tmp / f"console-{name}.png"
            page.screenshot(path=str(png))
            webp(png, f"console-{name}.webp")
        ctx.close()
    ctx, page = sign_in(browser, "bob", viewport={"width": 390, "height": 844},
                        device_scale_factor=3, is_mobile=True, has_touch=True)
    page.goto(CONSOLE + "/home", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(tmp / "console-phone.png"))
    webp(tmp / "console-phone.png", "console-phone.webp", width=780)
    ctx.close()


def in_terminal(cmd: list[str], env: dict) -> str:
    """Run a command in a pseudo-terminal, so nomad prints its colours."""
    out = bytearray()
    pid, fd = pty.fork()
    if pid == 0:
        os.environ.update(env)
        os.environ["COLUMNS"] = "78"
        os.execvp(cmd[0], cmd)
    while True:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    os.waitpid(pid, 0)
    return out.decode("utf-8", "replace").replace("\r", "")


def shoot_element(browser, page_html: Path, selector: str, png: Path) -> None:
    page = browser.new_page(viewport={"width": 1100, "height": 800}, device_scale_factor=2)
    page.goto(page_html.as_uri(), wait_until="networkidle")
    page.wait_for_timeout(500)
    page.locator(selector).screenshot(path=str(png), omit_background=True)
    page.close()


def cli_image(browser, demo: Path, tmp: Path) -> None:
    from ansi2html import Ansi2HTMLConverter
    env = {"HOME": str(demo)}
    text = in_terminal(["nomad", "edu", "explain", CLI_JOB, "--db", str(demo / "nomad_demo.db")], env)
    text = "\n".join(l for l in text.split("\n") if "[ERROR]" not in l).strip("\n")
    body = Ansi2HTMLConverter(inline=True, scheme="xterm", dark_bg=True).convert(text, full=False)
    page = tmp / "cli.html"
    page.write_text(f"""<!doctype html><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
body{{margin:0;padding:28px;background:transparent}}
.win{{width:max-content;min-width:640px;background:#0c1118;border:1px solid #23303d;border-radius:12px;overflow:hidden}}
.bar{{height:34px;background:#141c25;display:flex;align-items:center;gap:8px;padding:0 14px;border-bottom:1px solid #1e2a36}}
.dot{{width:11px;height:11px;border-radius:50%;background:#2c3a48}}
.ttl{{margin-left:12px;color:#7d8fa1;font:12px 'JetBrains Mono',monospace}}
pre{{margin:0;padding:18px 22px 22px;color:#d7e1ea;font:13.5px/1.5 'JetBrains Mono',monospace}}
.p{{color:#5fd3e6}}</style>
<div class="win"><div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span>
<span class="ttl">bob@login-node-01</span></div><pre><span class="p">$</span> nomad edu explain {CLI_JOB}\n\n{body}</pre></div>""")
    shoot_element(browser, page, ".win", tmp / "cli.png")
    webp(tmp / "cli.png", "cli-explain.webp", quality=86)


def email_image(browser, demo: Path, tmp: Path) -> None:
    # nomad notices reads the hub's database: point it at the demo's.
    share = demo / ".local" / "share" / "nomad"
    share.mkdir(parents=True, exist_ok=True)
    combined = share / "combined.db"
    made_link = not combined.exists()
    if made_link:
        combined.symlink_to(demo / "nomad_demo.db")
    mails = tmp / "mails"
    mails.mkdir()
    try:
        # Exits 1 in the demo (its people have no email address); the copies are written all the same.
        run = subprocess.run(["nomad", "notices", "mail", "--html", str(mails)],
                             env={**os.environ, "HOME": str(demo)}, capture_output=True, text=True)
    finally:
        if made_link:
            combined.unlink()
    if not list(mails.glob("*.html")):
        sys.exit("nomad notices mail wrote no email:\n" + run.stdout + run.stderr)
    pick = next((f for f in sorted(mails.glob("*.html")) if "more cores" in f.read_text()), None)
    pick = pick or sorted(mails.glob("*.html"))[0]
    src = pick.read_text()
    inner = re.search(r"<body[^>]*>(.*)</body>", src, re.S)
    styles = "".join(re.findall(r"<style[^>]*>.*?</style>", src, re.S))
    page = tmp / "email.html"
    page.write_text(f"""<!doctype html><meta charset="utf-8">{styles}<style>
body{{margin:0;padding:28px;background:transparent;font-family:Inter,system-ui,sans-serif}}
.mail{{width:720px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #d8dee6}}
.hdr{{background:#f4f6f9;border-bottom:1px solid #e3e8ee;padding:16px 26px;font-size:13.5px;color:#4a5563;line-height:1.7}}
.hdr b{{color:#1b2430;font-weight:600;display:inline-block;width:62px}}
.subj{{font-size:17px;color:#111;font-weight:600;margin-top:6px}}
.content{{padding:4px 26px 18px}}</style>
<div class="mail"><div class="hdr"><div><b>From</b>Research Computing</div><div><b>To</b>{html.escape(pick.stem)}</div>
<div class="subj">Research computing: a note on your recent work</div></div>
<div class="content">{inner.group(1) if inner else src}</div></div>""")
    shoot_element(browser, page, ".mail", tmp / "email.png")
    webp(tmp / "email.png", "email-weekly.webp", quality=86)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    demo = Path(sys.argv[1]).expanduser().resolve()
    if not (demo / "nomad_demo.db").exists():
        sys.exit(f"No demo in {demo}: nomad demo --console {demo} --seed 2")
    with tempfile.TemporaryDirectory() as t, sync_playwright() as p:
        tmp = Path(t)
        chrome = os.environ.get("NOMAD_SITE_CHROME")   # a Chrome of your own instead of Playwright's
        browser = p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        console_pages(browser, tmp)
        cli_image(browser, demo, tmp)
        email_image(browser, demo, tmp)
        browser.close()


if __name__ == "__main__":
    main()
