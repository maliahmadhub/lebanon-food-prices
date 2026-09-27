# Lebanon's food prices, 2000-2023 (Streamlit)

Interactive page showing how Lebanon's 2019 crisis changed food and consumer prices.

**Live app:** https://YOUR-APP-NAME.streamlit.app  <!-- replace after deploying -->

## Data
`data/lebanon_cpi.csv`: monthly General CPI, Food CPI (2015 = 100) and food price inflation for Lebanon, Jan 2000 to Sep 2023.
Source: AUB PKGCubes portal (Economical Data > consumer-price-indices), originally published by FAO.

## Features
- Period slider (2000-2023) that rescales both charts and the headline numbers
- Linked year drill-down: options follow the period, defaults to the worst year in it, highlights that year and shows it month by month

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

MSBA 325, American University of Beirut.
