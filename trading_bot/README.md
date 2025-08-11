# Trading Bot

Install dependencies:

```bash
pip install -r requirements.txt
```

Set env vars:

```bash
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
export BOT_MASTER_KEY="generated_master_key"
```

For encryption:

```python
from core import security
key = security.generate_master_key()
with open("secrets/keys.enc", "wb") as f:
    f.write(security.encrypt_data(b"ALPACA_API_KEY=xxx\nALPACA_SECRET_KEY=yyy", key))
```

Run backtest:

```bash
python main.py  # with mode: backtest in config.yaml
```

Run paper:

```bash
python main.py  # with mode: paper in config.yaml
```