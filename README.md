# ges-report-to-csv

Utilities to download & convert PDF reports from the Ministry of Educations Graduate Employment Survey (GES) into `.csv` for whatever downstream use case you may have. The data is subject to [Singapore Open Data License](https://beta.data.gov.sg/open-data-license).

I wrote this because [data.gov.sg](https://beta.data.gov.sg/collections/415/view) has not been updating this dataset since 2021.

### Quick Start

Install dependencies with `poetry`.

```bash
poetry i
```

Download the PDF reports:

```bash
# displayed are the default values if args are not supplied
poetry run python download_reports.py --year 2022 2023 --institution nus ntu smu sutd suss smu
```

This will download the relevant PDFs into `in/`

Run the conversion:

```bash
# displayed are the default values if args not supplied
poetry run python table_parser.py --filename tables.csv
```

This will output the merged tables to `out/tables.csv`

Examples on how to use programatically included in `derive_full_dataset.ipynb`.

### Without Poetry

Install these dependencies:

```
pymupdf
pandas
requests
```

And run the above lines excluding `poetry run`.
