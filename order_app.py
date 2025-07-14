import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# 設定台灣時區
tz = pytz.timezone("Asia/Taipei")
now = datetime.now(tz)
today_str = now.strftime("%Y-%m-%d %H:%M:%S")

# 訂單資料檔案
ORDER_FILE = "orders.csv"
ADMIN_PASSWORD = "usl123"

# 每週菜單
menu = {
    "葷": {
        "週一": "蔥油餅+豆漿",
        "週二": "燒餅+蛋+豆漿",
        "週三": "飯糰+豆漿",
        "週四": "漢堡+奶茶",
        "週五": "肉鬆吐司+奶茶",
    },
    "素": {
        "週一": "雜糧饅頭+豆漿",
        "週二": "蘿蔔糕+豆漿",
        "週三": "素飯糰+豆漿",
        "週四": "蛋餅+奶茶",
        "週五": "花生吐司+奶茶",
    }
}

# 建立訂單檔案（如果還沒存在）
if not os.path.exists(ORDER_FILE):
    df = pd.DataFrame(columns=["時間", "姓名", "葷/素", "訂購日", "份數"])
    df.to_csv(ORDER_FILE, index=False)

st.title("USL 早餐訂購系統")

# 用戶登入區塊
with st.sidebar:
    mode = st.radio("請選擇身份", ["一般顧客", "管理者"])
    if mode == "管理者":
        password = st.text_input("請輸入管理者密碼", type="password")
        if password != ADMIN_PASSWORD:
            st.stop()

# 載入訂單
def load_orders():
    return pd.read_csv(ORDER_FILE)

# 儲存訂單
def save_order(data):
    df = load_orders()
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(ORDER_FILE, index=False)

# 刪除訂單
def delete_order(index):
    df = load_orders()
    df.drop(index=index, inplace=True)
    df.to_csv(ORDER_FILE, index=False)

# 顧客介面
if mode == "一般顧客":
    st.header("我要訂早餐 🍱")
    with st.form("order_form"):
        name = st.text_input("姓名")
        food_type = st.radio("選擇葷/素", ["葷", "素"])
        days = st.multiselect("請選擇訂購日", ["週一", "週二", "週三", "週四", "週五"])

        # 照週一到週五順序排序
        weekday_order = ["週一", "週二", "週三", "週四", "週五"]
        days_sorted = [day for day in weekday_order if day in days]

        quantities = {}
        for day in days_sorted:
            item = menu[food_type][day]
            quantities[day] = st.number_input(f"{day}（{item}）的份數", min_value=0, max_value=10, step=1, value=0)

        submitted = st.form_submit_button("送出訂單")

        if submitted:
            for day, qty in quantities.items():
                if qty > 0:
                    save_order({
                        "時間": today_str,
                        "姓名": name,
                        "葷/素": food_type,
                        "訂購日": day,
                        "份數": qty
                    })
            st.success("✅ 訂單已送出，感謝您的訂購！")

# 管理者介面
elif mode == "管理者":
    st.header("📋 訂單管理後台")
    orders = load_orders()

    if orders.empty:
        st.info("目前尚無訂單。")
    else:
        # 顯示訂單摘要
        summary = orders.groupby(["訂購日", "葷/素"])["份數"].sum().unstack(fill_value=0)
        st.subheader("📊 每日訂購統計")
        st.dataframe(summary)

        # 顯示詳細訂單
        st.subheader("📄 所有訂單列表")
        for idx, row in orders.iterrows():
            col1, col2 = st.columns([6, 1])
            with col1:
                st.write(
                    f"{row['時間']} | {row['姓名']} | {row['葷/素']} | {row['訂購日']} | {row['份數']}份"
                )
            with col2:
                if st.button("刪除", key=f"del_{idx}"):
                    delete_order(idx)
                    st.success(f"已刪除 {row['姓名']} 的訂單")
                    st.experimental_rerun()