import streamlit as st
from datetime import datetime
import pandas as pd
import sys
import os

st.set_page_config(page_title="優碩力餐廳早餐訂購", layout="centered")

MENU = {
    "葷": {
        "週一": "蔥油餅+豆漿",
        "週二": "蘿蔔糕+豆漿",
        "週三": "煎餃+豆漿",
        "週四": "鹹粥+豆漿",
        "週五": "花生肉粽+豆漿",
    },
    "素": {
        "週一": "雜糧饅頭+豆漿",
        "週二": "手工饅頭+豆漿",
        "週三": "雜糧饅頭+豆漿",
        "週四": "素鹹粥+豆漿",
        "週五": "雜糧饅頭+豆漿",
    },
}

ADMIN_PASSWORD = "0000"
ORDERS_CSV = "orders.csv"

def load_orders():
    if os.path.exists(ORDERS_CSV):
        df = pd.read_csv(ORDERS_CSV, dtype=str)
        return df
    else:
        return pd.DataFrame(columns=["時間","房號","姓名","電話","葷/素","訂餐日與份數","加購蛋"])

def save_orders(df):
    df.to_csv(ORDERS_CSV, index=False)

def rerun():
    sys.exit()

if "current_order" not in st.session_state:
    st.session_state.current_order = {}

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

mode = st.sidebar.selectbox("請選擇模式", ["顧客模式", "管理員模式"])

if mode == "管理員模式":
    st.title("早餐訂購管理者介面")

    if not st.session_state.is_admin:
        pwd = st.text_input("請輸入管理員密碼", type="password")
        if st.button("登入"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                rerun()
            else:
                st.error("密碼錯誤，請重新輸入")
    else:
        st.success("管理員登入成功！")

        # 每次讀最新訂單資料
        st.session_state.orders_df = load_orders()

        if not st.session_state.orders_df.empty:
            st.subheader("📋 訂單紀錄")
            df = st.session_state.orders_df.sort_values("房號").reset_index(drop=True)

            header_cols = st.columns([3,1,1,3,1,2,1,1])
            header_cols[0].write("時間")
            header_cols[1].write("房號")
            header_cols[2].write("姓名")
            header_cols[3].write("電話")
            header_cols[4].write("葷/素")
            header_cols[5].write("訂餐日與份數")
            header_cols[6].write("加購蛋")
            header_cols[7].write("操作")

            for idx, row in df.iterrows():
                cols = st.columns([3,1,1,3,1,2,1,1])
                cols[0].write(row["時間"])
                cols[1].write(row["房號"])
                cols[2].write(row["姓名"])
                cols[3].write(row["電話"])
                cols[4].write(row["葷/素"])
                cols[5].write(row["訂餐日與份數"])
                cols[6].write(row["加購蛋"])
                if cols[7].button("刪除", key=f"del_{idx}"):
                    updated_df = st.session_state.orders_df.drop(df.index[idx]).reset_index(drop=True)
                    save_orders(updated_df)
                    st.session_state.orders_df = updated_df
                    rerun()
        else:
            st.info("目前尚無訂單")

        if not st.session_state.orders_df.empty:
            st.subheader("📅 每日訂購彙整")
            all_rows = []
            for _, row in st.session_state.orders_df.iterrows():
                items = [x.strip() for x in row["訂餐日與份數"].split(",")]
                for item in items:
                    if ":" in item:
                        day, qty = item.split(":")
                        all_rows.append({
                            "訂餐日": day,
                            "姓名": row["姓名"],
                            "房號": row["房號"],
                            "份數": qty,
                            "葷/素": row["葷/素"]
                        })

            df_summary = pd.DataFrame(all_rows)
            day_order = ["週一", "週二", "週三", "週四", "週五"]
            df_summary["訂餐日"] = pd.Categorical(df_summary["訂餐日"], categories=day_order, ordered=True)
            df_summary = df_summary.sort_values(
                ["訂餐日", "葷/素", "房號"],
                key=lambda col: col.map({"葷": 0, "素": 1}) if col.name == "葷/素" else col
            )

            for day, group_day in df_summary.groupby("訂餐日"):
                st.markdown(f"**{day} 訂購名單**")
                for food_type in ["葷", "素"]:
                    group_food = group_day[group_day["葷/素"] == food_type]
                    if not group_food.empty:
                        st.markdown(f"_{food_type}_")
                        df_display = group_food[["房號","姓名","份數"]].reset_index(drop=True)
                        df_display.index += 1
                        st.table(df_display)

else:
    st.title("優碩力餐廳早餐訂購")

    food_type = st.radio("請選擇餐別", ["葷", "素"], index=0)

    with st.form("meal_order_form"):
        selected_menu = MENU[food_type]

        full_labels = [f"{day}（{selected_menu[day]}）" for day in selected_menu]
        selected_day_labels = st.multiselect("選擇欲訂購的日子", full_labels)

        day_order = ["週一", "週二", "週三", "週四", "週五"]

        def sort_by_day(label):
            day = label.split("（")[0]
            return day_order.index(day) if day in day_order else 99

        selected_day_labels = sorted(selected_day_labels, key=sort_by_day)

        quantities = {}
        for label in selected_day_labels:
            day = label.split("（")[0]
            qty = st.number_input(f"{label} 份數", min_value=1, value=1, key=f"qty_{day}")
            quantities[day] = qty

        submit1 = st.form_submit_button("確認訂餐")

        if submit1:
            if not selected_day_labels:
                st.warning("請至少選擇一天並填寫份數")
            else:
                st.session_state.current_order = {
                    "葷/素": food_type,
                    "訂餐日與份數": ", ".join([f"{day}:{quantities[day]}" for day in quantities]),
                }
                st.success("訂餐資料已暫存，請繼續填寫個人資料")

    if st.session_state.current_order:
        with st.form("personal_form"):
            name = st.text_input("姓名")
            room = st.text_input("房號（5碼）")
            phone = st.text_input("電話（10碼）")
            egg = st.radio("是否加購蛋", ["荷包蛋", "水煮蛋", "否"])

            submit2 = st.form_submit_button("送出訂單")

            if submit2:
                if (not name or len(room) != 5 or not room.isdigit() or
                    len(phone) != 10 or not phone.isdigit()):
                    st.error("請確認基本資料填寫正確")
                else:
                    new_order = {
                        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "房號": room,
                        "姓名": name,
                        "電話": phone,
                        "葷/素": st.session_state.current_order["葷/素"],
                        "訂餐日與份數": st.session_state.current_order["訂餐日與份數"],
                        "加購蛋": egg,
                    }
                    orders_df = load_orders()
                    orders_df = pd.concat([orders_df, pd.DataFrame([new_order])], ignore_index=True)
                    save_orders(orders_df)
                    st.session_state.current_order = {}
                    st.success("感謝您的訂購！")
                    rerun()
