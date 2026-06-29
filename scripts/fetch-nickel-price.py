#!/usr/bin/env python3
"""Fetch SMM 1#电解镍 spot price. Primary: SMM AJAX API; Fallback: AKShare.
   Saves to data/price.json for GitHub Pages.
"""
import json, urllib.request, os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

DEFAULT_PRICE = 127250

result = {
    "symbol": "SMM 1#电解镍",
    "price": DEFAULT_PRICE,
    "unit": "元/吨",
    "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    "source": "default",
}

# ========== Primary: SMM AJAX API ==========
SMM_PRODUCT_ID = "201102250423"  # 1#电解镍 (confirmed from hq.smm.cn/nickel)
end_date = now.strftime("%Y-%m-%d")
start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
smm_api = f"https://hq.smm.cn/ajax/spot/history/{SMM_PRODUCT_ID}/{start_date}/{end_date}"
try:
    req = urllib.request.Request(
        smm_api,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://hq.smm.cn/nickel/category/{SMM_PRODUCT_ID}",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        smm = json.loads(resp.read().decode())
        if smm.get("code") == 0 and smm.get("data"):
            latest = smm["data"][-1]
            avg = latest.get("average", 0)
            if avg and int(float(avg)) > 0:
                result["price"] = int(float(avg))
                result["source"] = "smm_ajax"
                result["date"] = latest.get("renew_date", "")
                result["smm_high"] = latest.get("high_show", "")
                result["smm_low"] = latest.get("low_show", "")
                print(f"SMM: {int(float(avg))} 元/吨 (updated: {latest.get('renew_date')})")
except Exception as e:
    print(f"SMM failed: {e}")

# ========== Fallback: AKShare ==========
if result["source"] == "default":
    try:
        import akshare as ak
        start_day = (now - timedelta(days=10)).strftime("%Y%m%d")
        end_day = now.strftime("%Y%m%d")
        df = ak.futures_spot_price_daily(start_day=start_day, end_day=end_day, vars_list=["NI"])
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            price = float(latest["spot_price"])
            if price > 0:
                result["price"] = int(price)
                result["source"] = "akshare_smm"
                result["date"] = str(latest["date"])
                print(f"AKShare: {int(price)} 元/吨 (date: {latest['date']})")
    except Exception as e:
        print(f"AKShare failed: {e}")

if result["source"] == "default":
    print(f"Using default price: {DEFAULT_PRICE} 元/吨")

out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "price.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"OK -> {out_path}")