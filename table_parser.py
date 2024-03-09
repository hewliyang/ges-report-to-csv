import os
import fitz
import argparse
import pandas as pd
from logger import logger
from pathlib import Path
from typing import List, Literal, Optional, Tuple


ACR_2_FULL = {
    "SUSS": "Singapore University of Social Sciences",
    "SUTD": "Singapore University of Technology and Design",
    "SIT": "Singapore Institute of Technology",
    "SMU": "Singapore Management University",
    "NUS": "National University of Singapore",
    "NTU": "Nanyang Technological University",
}


def magic_clean_strings(s: str, special_chars: Optional[str] = "*^#\n ") -> str:
    """
    Get rid of special chars & digits
    """

    s = s.strip()
    s = s.replace("\n", " ")

    # from the right to left trim until reach a valid char
    s = list(s)
    idx = len(s) - 1
    while idx >= 0:
        if not (s[idx] in special_chars or s[idx].isdigit()):
            break
        del s[idx]
        idx -= 1
    return "".join(s)


def parse_val(s: str, ext: Literal["%", "$"]) -> int | float:
    if s == "N.A.":
        return None

    val = s.strip(ext).replace(",", "")
    return float(val) if "." in val else int(val)


def squash_row(r: List[str]) -> List[str]:
    """[1, None, 2, None, None ,3] -> [1,2,3]"""
    return [ele for ele in r if ele != None]


class GESTableParser:
    """
    Parses tables in the annual GES reports by MOE.

    ### Usage:

    ```python
    parser = GESTableParser()

    # dir containing the PDF's
    df: pd.DataFrame = parser.extract_tab_from_one_pdf("data/")
    ```
    """

    def __init__(
        self,
        year: Optional[int] = None,
        university: Optional[str] = None,
        columns: Optional[List[str]] = [
            "year",
            "university",
            "school",
            "degree",
            "employment_rate_overall",
            "employment_rate_ft_perm",
            "basic_monthly_mean",
            "basic_monthly_median",
            "gross_monthly_mean",
            "gross_monthly_median",
            "gross_mthly_25_percentile",
            "gross_mthly_75_percentile",
        ],
    ):
        self.year = year
        self.university = university
        self.columns = columns

    def infer_meta(self, path: Path | str) -> None:
        path = str(path) if isinstance(path, Path) else path
        filename = os.path.basename(path)
        parts = filename.split(".")[0].split()

        self.year = parts[-1]
        self.university = ACR_2_FULL[parts[2]]

    def infer_tab_has_header(self, page: fitz.Page) -> bool:
        tabs = page.find_tables()
        if len(tabs.tables) == 0:
            return False
        tab = tabs[0]
        rows = tab.extract()
        return (rows[0][0] == "Degree") and (
            list(map(lambda x: x[0], rows[1:5])) == [None, None, None, None]
        )

    def _extract_tab_from_one_page(
        self, page: fitz.Page, prev_school: str | None = None
    ) -> Tuple[pd.DataFrame, str]:

        # if the table is continuing on another page
        is_continuing = prev_school is not None

        # get first table. a single page should only have one table
        tabs = page.find_tables()

        # if page has no table exit gracefully
        if len(tabs.tables) == 0:
            logger.warning(f"No table on {page}")
            return [None, prev_school]

        tab = tabs[0]
        rows = tab.extract()

        # store data then create dataframe at the end
        # growing a DF is bad practice!
        data = []

        school = prev_school
        # rows before the 6th are header rows
        rows = rows[5:] if not is_continuing else rows
        for row in rows:
            row = squash_row(row)
            if not any(row):
                continue
            elif row[0] == "" and row[1] != None:
                school = magic_clean_strings(row[1])
            else:
                degree = magic_clean_strings(row[0])

                # handle SMU edge case
                # stats are split into < Cum Laude and > Cum Laude
                if degree == "Cum Laude and above":
                    actual_name = data[-1][3]
                    degree = f"{actual_name} Cum Laude and above"

                employment_rate_overall = parse_val(row[1], "%")
                employment_rate_ft_perm = parse_val(row[2], "%")
                basic_monthly_mean = parse_val(row[3], "$")
                basic_monthly_median = parse_val(row[4], "$")
                gross_monthly_mean = parse_val(row[5], "$")
                gross_monthly_median = parse_val(row[6], "$")
                gross_mthly_25_percentile = parse_val(row[7], "$")
                gross_mthly_75_percentile = parse_val(row[8], "$")

                data.append(
                    [
                        self.year,
                        self.university,
                        school,
                        degree,
                        employment_rate_overall,
                        employment_rate_ft_perm,
                        basic_monthly_mean,
                        basic_monthly_median,
                        gross_monthly_mean,
                        gross_monthly_median,
                        gross_mthly_25_percentile,
                        gross_mthly_75_percentile,
                    ]
                )

        return pd.DataFrame(data, columns=self.columns), school

    def extract_tab_from_one_pdf(self, path: Path | str) -> pd.DataFrame:
        try:
            self.infer_meta(path)
        except Exception as exc:
            logger.error(exc)
            logger.error("Expected filename: Web Publication <UNI_SHORT> GES <YYYY>")

        doc = fitz.open(path)
        dfs = []
        prev_school = None
        for page in doc:
            df, prev_school = (
                self._extract_tab_from_one_page(page)
                if self.infer_tab_has_header(page)
                else self._extract_tab_from_one_page(page, prev_school=prev_school)
            )
            dfs.append(df)

        return pd.concat(dfs, axis=0, ignore_index=True)


if __name__ == "__main__":
    from glob import glob

    parser = argparse.ArgumentParser(
        description="Argument parser converting GES reports into csv"
    )

    parser.add_argument(
        "--filename", type=str, help="File name for resulting .csv file"
    )

    args = parser.parse_args()
    filename = args.filename or "tables"
    filename = (filename + ".csv") if ".csv" not in filename else filename

    parser = GESTableParser()
    dfs = []
    for f in list(glob("in/*.pdf")):
        dfs.append(parser.extract_tab_from_one_pdf(f))
    merged_df = pd.concat(dfs, axis=0, ignore_index=True)
    merged_df["year"] = merged_df["year"].astype(int)
    merged_df = merged_df.fillna("na").sort_values(["year", "university"])
    merged_df.to_csv(f"out/{filename}", index=False)

    logger.info(f"Parsed {len(dfs)} files")
    logger.info(f"Written tables to out/{filename}")
