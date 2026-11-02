# Team 3 — SCE Transmission Planning Analytics Dashboard

A Streamlit dashboard for exploring normalized transmission planning findings. It includes illustrative sample data, and it can also load findings from a CSV file.

## Required downloads

- **Python 3.10 or newer** — install Python from [python.org](https://www.python.org/downloads/). On Windows, enable **Add Python to PATH** during installation.
- **Project dependencies** — installed with the `pip install -r requirements.txt` command below. This installs Streamlit, pandas, NumPy, and Plotly; no separate downloads are needed for these packages.

You do not need to download a dataset to launch the dashboard. It starts with illustrative sample data. To use your own data, prepare a CSV with these columns: `report`, `report_date`, `facility`, `contingency`, `scenario`, `loading_pct`, `severity`, `mitigation`, and `source_page`.

## Install and run (Windows)

Open command prompt in this folder and run:

```
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser. If the `py` command is unavailable, reinstall Python and enable **Add Python to PATH**.

## Use your own findings

In the dashboard sidebar, upload a CSV containing the required columns above. The built-in sample is illustrative only and is not extracted from an SCE PDF.
