import json
import logging
from typing import Any
from pathlib import Path

import requests
from PIL import Image

log = logging.getLogger(__name__)


def get_info_json(input_url: str) -> dict[str, Any]:
    # Örnek URL: https://www.yumpu.com/tr/document/read/63048200/mucize-ugur-bocegi-ile-kara-kedi-cizgi-roman-tekrarlama
    # Alınacak JSON URL: https://www.yumpu.com/tr/document/json/63048200
    pdf_id = None
    for e in input_URL.split("/"):
        if e.isdigit():
            pdf_id = int(e)
            log.debug(f"file id found: {pdf_id}")
            break
    else:
        raise ValueError("File id cannot found")
    json_URL = f"https://www.yumpu.com/tr/document/json/{pdf_id}"
    response = requests.get(json_URL)
    return response.json()


def download_title_image(base_url: str, images: dict) -> Path:
    title_img_name = images.get("title")
    sprites = images.get("sprites", [])
    r = requests.get(base_url + sprites[0])
    title_img = Path(title_img_name)
    title_img.write_bytes(r.content)
    log.info("Title img downloaded.")
    return title_img


def download_all_pages(base_url: str, resources: list) -> list[Path]:
    if len(resources) < 2:
        raise ValueError("Length of resources must be at least 2")
    pages: list[Path] = []
    for i, _r in enumerate(resources):
        if not i:
            continue
        img_path = Path(f"bg{i:0>3}_00.jpg")
        r = requests.get(base_url + _r)
        img_path.write_bytes(r.content)
        log.debug(f"Downloaded page {i}")
        pages.append(img_path)
    log.info("Downloaded all pages.")
    return pages



def convert_images_to_pdf(images: list[Path], filename: str = "output.pdf") -> Path:
    imgs = [Image.open(path).convert('RGB') for path in images]
    imgs[0].save(filename, save_all=True, append_images=imgs[1:])
    for path in images:
        path.unlink(missing_ok=True)
    return Path(filename)


if __name__ == "__main__":
    input_URL = input("Enter Yumpu document URL: ")
    info_json = get_info_json(input_URL)

    id = info_json.get("document", {}).get("id")
    title = info_json.get("document", {}).get("title")
    pdf_filename = f"{title} [{id}]"
    #with open(f"{pdf_filename}.info.json", "w") as file:
    #    json.dump(info_json, file, ensure_ascii=False, indent="\t")

    base_url = info_json.get("document", {}).get("base_path")
    if base_url is None:
        print("There is no base path exiting...")
        exit(1)

    #download_title_image(base_url, info_json.get("document", {}).get("images", {}))
    images = download_all_pages(base_url, info_json.get("document", {}).get("html", {}).get("resources", []))
    _name = convert_images_to_pdf(images, filename=f"{pdf_filename}.pdf")
    print(f"File saved to '{_name!s}'")