# SEB-task

Extracts ECB daily and historical FX rates from ECB links, keeps only `USD`, `SEK`, `GBP`, and `JPY`, and calculates historical mean rates.

## Run

```bash
python ecb_rates_etl.py
```

## Note

I provided the text for task point 3 (`Load`), and I had ChatGPT create the part that generates an HTML or Markdown table with the columns `Currency Code`, `Rate`, and `Mean Historical Rate` because writing it manually felt too time-consuming. The rest of the task was completed by me.
