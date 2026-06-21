import os
import csv
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf
# ====================================
# 美股情緒
# ====================================
nvda_change = 0
nasdaq_change = 0
sox_change = 0
def get_us_market_score():

    try:

        nvda = yf.Ticker("NVDA").history(period="5d")
        nasdaq = yf.Ticker("^IXIC").history(period="5d")
        sox = yf.Ticker("^SOX").history(period="5d")

        nvda_change = (
            (nvda["Close"].iloc[-1] /
             nvda["Close"].iloc[-2]) - 1
        ) * 100

        nasdaq_change = (
            (nasdaq["Close"].iloc[-1] /
             nasdaq["Close"].iloc[-2]) - 1
        ) * 100

        sox_change = (
            (sox["Close"].iloc[-1] /
             sox["Close"].iloc[-2]) - 1
        ) * 100

        us_score = 0

        if nvda_change > 0:
            us_score += 1

        if nasdaq_change > 0:
            us_score += 1

        if sox_change > 0:
            us_score += 1

        return (
            us_score,
            nvda_change,
            nasdaq_change,
            sox_change
        )

    except Exception as e:

        print("美股資料錯誤:", e)

        return (
            0,
            0,
            0,
            0
        )

       
# ====================================
# 基本設定
# ====================================

CAPITAL = 30000
RISK_PERCENT = 1
TAKE_PROFIT_RATIO = 2

 

import os

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

if not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("找不到 LINE_TOKEN Secret")

if not LINE_USER_ID:
    raise Exception("找不到 LINE_USER_ID Secret")

# ====================================
# 股票名稱
# ====================================

STOCK_NAMES = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2454.TW": "聯發科",
    "2382.TW": "廣達",
    "3231.TW": "緯創",
    "6669.TWO": "緯穎",
    "3017.TW": "奇鋐",
    "2376.TW": "技嘉",
    "2383.TW": "台光電",
    "8996.TWO": "高力",

    "2603.TW": "長榮",
    "2609.TW": "陽明",
    "2615.TW": "萬海",

    "2881.TW": "富邦金",
    "2882.TW": "國泰金",

    "2303.TW": "聯電",
    "2408.TW": "南亞科",
    "2002.TW": "中鋼"
}


if symbol == "8996.TWO":
            print("========== 高力 ==========")

            print(df.tail(5)[["Open","High","Low","Close","Volume"]])

            print("close =", close)
            print("ma5 =", ma5)
            print("ma20 =", ma20)
            print("volume =", volume)
            print("vol5 =", vol5)
            print("high20 =", high20)
            print("rsi =", rsi)
            print("macd =", macd)
            print("signal =", signal)
            print("score =", score)
            print("最後日期 =", df.index[-1])
        stop_loss = round(
            close * 0.99,
            2
        )

        risk_per_share = (
            close -
            stop_loss
        )

        take_profit = round(
            close +
            risk_per_share *
            TAKE_PROFIT_RATIO,
            2
        )

        shares = 0

        if risk_per_share > 0:

            shares = int(
                risk_money /
                risk_per_share
            )

            shares = (
                shares // 1000
            ) * 1000

        results.append({

            "股票":
            STOCK_NAMES.get(
                symbol,
                symbol
            ),

            "代號":
            symbol,

            "現價":
            round(close, 2),

            "RSI":
            round(rsi, 2),

            "MACD":
            round(macd, 2),

            "停損價":
            stop_loss,

            "停利價":
            take_profit,

            "建議股數":
            shares,

            "評分":
            score
        })

    except Exception as e:

        print(
            symbol,
            e
        )
# ====================================
# 排序
# ====================================

results.sort(
    key=lambda x:
    x["評分"],
    reverse=True
)

# ====================================
# 存CSV
# ====================================

from zoneinfo import ZoneInfo

today = datetime.now(
    ZoneInfo("Asia/Taipei")
).strftime("%Y-%m-%d")

with open(
    "trade_log.csv",
    "a",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    for item in results[:5]:

        writer.writerow([
            today,
            item["股票"],
            item["評分"],
            item["現價"]
        ])

# ====================================
# 存SQLite
# ====================================

for item in results:

    conn.execute(
        """
        INSERT INTO rankings
        VALUES (?,?,?,?)
        """,
        (
            today,
            item["股票"],
            item["評分"],
            item["現價"]
        )
    )

conn.commit()

conn.close()

# ====================================
# Excel
# ====================================

os.makedirs(
    "reports",
    exist_ok=True
)

filename = os.path.join(
    "reports",
    today + ".xlsx"
)

pd.DataFrame(
    results
).to_excel(
    filename,
    index=False
)

# ====================================
# TOP5
# ====================================

line_msg = (
    f"【台股當沖助手 v6.7】\n"
    f"{today}\n\n"
    
)

for i, item in enumerate(results[:5], start=1):

    

    line_msg += (
        f"{i}. {item['股票']}\n"
        f"評分:{item['評分']}/20\n"
        f"現價:{item['現價']}\n"
        
        f"RSI:{item['RSI']}\n"
        f"停損:{item['停損價']}\n"
        f"停利:{item['停利價']}\n\n"
    )

print("\n")
print(line_msg)

status = send_line_message(
    line_msg
)

print(
    "\nLINE狀態:",
    status
)

print(
    "\n報表:",
    filename
)

show_statistics()
print(os.path.exists("trade_log.csv"))
print("\n完成")
