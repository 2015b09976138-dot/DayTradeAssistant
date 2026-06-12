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

# ====================================
# LINE 推播
# ====================================

def send_line_message(message):

    try:

        if "請填入" in LINE_CHANNEL_ACCESS_TOKEN:
            return "未設定 LINE"

        url = "https://api.line.me/v2/bot/message/push"

        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "to": LINE_USER_ID,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        r = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )

        return r.status_code

    except Exception as e:

        return str(e)

# ====================================
# RSI
# ====================================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# ====================================
# SQLite
# ====================================

def init_database():

    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(
        "data/stocks.db"
    )

    conn.execute("""
    CREATE TABLE IF NOT EXISTS rankings(
        trade_date TEXT,
        stock TEXT,
        score INTEGER,
        close REAL
    )
    """)

    conn.commit()

    return conn

# ====================================
# 勝率紀錄
# ====================================

def init_trade_log():

    if not os.path.exists("trade_log.csv"):

        with open(
            "trade_log.csv",
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "日期",
                "股票",
                "評分",
                "收盤價"
            ])

# ====================================
# 統計
# ====================================

def show_statistics():

    try:

        df = pd.read_csv(
            "trade_log.csv"
        )

        print("\n")
        print("=" * 50)
        print("歷史統計")
        print("=" * 50)

        print(
            "總紀錄數：",
            len(df)
        )

        print(
            "平均評分：",
            round(
                df["評分"].mean(),
                2
            )
        )

    except:

        pass

# ====================================
# 讀取觀察名單
# ====================================

stocks = []

try:

    with open(
        "watchlist.txt",
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            code = line.strip()

            if code:

                stocks.append(
                    code + ".TW"
                )

except:

    stocks = list(
        STOCK_NAMES.keys()
    )

# ====================================
# 開始
# ====================================

conn = init_database()

init_trade_log()

risk_money = (
    CAPITAL *
    (RISK_PERCENT / 100)
)

results = []
us_score, nvda_pct, nasdaq_pct, sox_pct = (
    get_us_market_score()
)
print("=" * 60)
print("台股當沖助手 v5.1")
print("=" * 60)

for symbol in stocks:

    try:

        df = yf.Ticker(
            symbol
        ).history(
            period="3mo"
        )

        if len(df) < 30:
            continue

        df["MA5"] = (
            df["Close"]
            .rolling(5)
            .mean()
        )

        df["MA20"] = (
            df["Close"]
            .rolling(20)
            .mean()
        )

        df["VOL5"] = (
            df["Volume"]
            .rolling(5)
            .mean()
        )

        df["HIGH20"] = (
            df["High"]
            .rolling(20)
            .max()
            .shift(1)
        )

        df["EMA12"] = (
            df["Close"]
            .ewm(span=12)
            .mean()
        )

        df["EMA26"] = (
            df["Close"]
            .ewm(span=26)
            .mean()
        )

        df["MACD"] = (
            df["EMA12"]
            - df["EMA26"]
        )

        df["SIGNAL"] = (
            df["MACD"]
            .ewm(span=9)
            .mean()
        )

        df["RSI"] = calculate_rsi(
            df["Close"]
        )

        df = df.dropna()

        latest = df.iloc[-1]

        close = float(
            latest["Close"]
        )

  

        ma5 = float(
            latest["MA5"]
        )

        ma20 = float(
            latest["MA20"]
        )

        volume = float(
            latest["Volume"]
        )

        vol5 = float(
            latest["VOL5"]
        )

        high20 = float(
            latest["HIGH20"]
        )

        rsi = float(
            latest["RSI"]
        )

        macd = float(
            latest["MACD"]
        )

        signal = float(
            latest["SIGNAL"]
        )

        trend_ok = ma5 > ma20

        volume_ok = (
            volume >
            vol5 * 1.5
        )

        breakout_ok = (
            close >
            high20
        )

        score = 0

        if trend_ok:
            score += 3

        if volume_ok:
            score += 3

        if breakout_ok:
            score += 3

        if 60 <= rsi <= 75:
            score += 3

        elif 75 < rsi <= 85:
            score += 2

        elif rsi > 85:
            score += 1

        if macd > signal:
            score += 3
        if symbol == "8996.TW":
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
AI_STOCKS = [
    "2330.TW",
    "2454.TW",
    "2382.TW",
    "3231.TW",
    "6669.TW",
    "3017.TW",
    "2376.TW",
    "2383.TW",
    "8996.TW"
]

if symbol in AI_STOCKS:
    score += us_score
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
    f"【台股當沖助手 v6.6】\n"
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
