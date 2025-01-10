import time
import requests
from example_utils import setup, config

from hyperliquid.utils import constants

COIN_SYMBOL = config["coin_symbol"]
COIN_CA = config["coin_ca"]
DCA_AMOUNT = config["dca_amount"]
HL_API_URL = "https://api.hyperliquid.xyz/info"
HL_VAULT_ADDRESS = config.get("hl_vault_address", None)
TG_BOT_API_TOKEN = config.get("tg_bot_api_token", None)
TG_CHAT_ID = config.get("tg_chat_id", None)

def get_spot_balance(coin, user):
    print(coin, user)
    response = requests.post(HL_API_URL, json={"type": "spotClearinghouseState", "user": user})
    print(response)
    balances = response.json()["balances"]
    print(balances)
    for balance in balances:
        if balance["coin"] == coin:
            return balance
    return 0.0

def get_spot_price(coin_ca):
    response = requests.post(HL_API_URL, json={"type": "tokenDetails", "tokenId": coin_ca})
    return float(response.json()["markPx"])

def manboy_notify(message):
    url = f"https://api.telegram.org/bot{TG_BOT_API_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # Optional for bold, italic, etc.
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Error: {response.text}")

def main():
    address, info, exchange, user = setup(constants.MAINNET_API_URL, skip_ws=True)
    # TODO: add vault transfer
    # if HL_VAULT_ADDRESS is not None:
    #     print("Transferring from vault to perp")
    #     transfer_result = exchange.vault_usd_transfer(HL_VAULT_ADDRESS, False, DCA_AMOUNT) # transfer from vault to perp
    #     print("Transferring from perp to spot")
    #     transfer_result = exchange.usd_class_transfer(DCA_AMOUNT, False) # transfer from perp to spot

    is_buy = True
    price = get_spot_price(COIN_CA)

    # since the minium size is 10 thenthe 1.005 multiplier is used as a buffer to account for slippage and price changes
    sz = round((DCA_AMOUNT * 1.005 if DCA_AMOUNT == 10 else DCA_AMOUNT) / price, 2)
    msg = f"Buying {sz} {COIN_SYMBOL} at {price} USDC for {user}"
    print(msg)

    #add a check to make sure user has enough USD in spot
    if get_spot_balance("USDC", user) < 1000:
        print("we're inside the spot balance checker")
        msg = "You aint got no money mf."
        return msg
    #end check 

    return "test"
    order_result = exchange.market_open(COIN_SYMBOL, is_buy, sz, None, 0.01)
    if order_result["status"] == "ok":
        for status in order_result["response"]["data"]["statuses"]:
            try:
                filled = status["filled"]
                balance = get_spot_balance(COIN_SYMBOL.split("/")[0], address)
                pnl = round((float(balance["total"])* price) - float(balance["entryNtl"]), 2)
                pnl_msg = f"Current PNL for {COIN_SYMBOL}: {pnl}"
                print(pnl_msg)
                return f'<b>{user} Order #{filled["oid"]} filled </b> {filled["totalSz"]} @{filled["avgPx"]} <blockquote> {pnl_msg} </blockquote>'
            except KeyError:
                raise Exception(f'Error: {status["error"]}')

if __name__ == "__main__":
    try:
        msg = main()
        print(msg)
        if TG_BOT_API_TOKEN and TG_CHAT_ID:
            manboy_notify(msg)
    except Exception as e:
        if TG_BOT_API_TOKEN and TG_CHAT_ID:
            print(f"Bruh, we're having issues: <pre><code class='language-python'>{e}</code></pre>")
            # manboy_notify(f"Bruh, we're having issues: <pre><code class='language-python'>{e}</code></pre>")
        else:
            raise e
