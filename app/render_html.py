import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def render_html_to_pdf(html: str, out_pdf_path: str, options: dict):
    # options: pageFormat/margins/timeout etc.
    timeout_ms = int(options.get("timeoutSeconds", 300)) * 1000

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle", timeout=timeout_ms)

        pdf_kwargs = {}
        if options.get("pageFormat"):
            pdf_kwargs["format"] = options["pageFormat"]
        # margins (Playwright expects strings like "10mm")
        margin = {}
        for k_src, k_dst in [
            ("marginTop", "top"),
            ("marginRight", "right"),
            ("marginBottom", "bottom"),
            ("marginLeft", "left"),
        ]:
            if options.get(k_src):
                margin[k_dst] = options[k_src]
        if margin:
            pdf_kwargs["margin"] = margin

        pdf_bytes = await page.pdf(print_background=True, **pdf_kwargs)
        Path(out_pdf_path).write_bytes(pdf_bytes)

        await browser.close()


def render_html(html: str, out_pdf_path: str, options: dict):
    asyncio.run(render_html_to_pdf(html, out_pdf_path, options))