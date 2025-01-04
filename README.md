# Setup

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Run

```
python basic_market_order.py config.json
```

# Schedule cron job

```
$ crontab -e

# Run daily at 10:00 AM
0 10 * * * /path/to/basic_market_order.py /path/to/config.json
```
