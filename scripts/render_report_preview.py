"""Render the generated technical report for visual review in CI."""

from pathlib import Path

import pymupdf


def main():
    source = Path("output/pdf/technical-report.pdf")
    destination = Path("output/report-review")
    destination.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(source) as document:
        for index, page in enumerate(document, 1):
            image = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            image.save(str(destination / f"page-{index:02}.png"))
        print(f"Rendered {len(document)} report pages to {destination}")


if __name__ == "__main__":
    main()
