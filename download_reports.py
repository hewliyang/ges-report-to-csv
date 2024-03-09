import os
import requests
import argparse
import itertools
from typing import Literal
from logger import logger


def download_pdf(
    year: int, institution: Literal["nus", "ntu", "sutd", "suss", "sit", "smu"]
) -> None:
    url = f"https://www.moe.gov.sg/-/media/files/post-secondary/ges-{year}/web-publication-{institution}-ges-{year}.ashx"
    resp = requests.get(url)

    if (
        resp.status_code == 200
        and resp.headers.get("Content-Type") == "application/pdf"
    ):
        folder = "in"
        filename = f"Web Publication {institution.upper()} GES {year}.pdf"
        file_path = os.path.join(folder, filename)

        with open(file_path, "wb") as f:
            f.write(resp.content)

        logger.info(f"PDF downloaded: {file_path}")
    else:
        logger.error(
            f"GES Report for {institution.upper()} in {year} has not been released yet!"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Argument parser for downloading PDFs."
    )
    parser.add_argument("--year", nargs="+", type=int, help="Year(s) for PDF download")
    parser.add_argument(
        "--institution", nargs="+", help="Institution(s) for PDF download"
    )
    args = parser.parse_args()

    year = args.year or [2022, 2023]
    institution = args.institution or ["nus", "ntu", "sutd", "suss", "sit", "smu"]

    for yr, inst in itertools.product(year, institution):
        download_pdf(yr, inst)
