import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="我的消费记录", page_icon="💸")
st.title("💸 我的消费记录系统")

DATA_FILE = "expenses.csv"

# 初始化 CSV 文件
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["日期", "项目", "金额", "分类"])
    df.to_csv(DATA_FILE, index=False)

# 初始化 session_state 中的行数
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 3  # 默认显示3项

st.header("📥 多项消费录入")
record_date = st.date_input("消费日期", value=date.today())

# 增加/删除行的按钮
col_add, col_del = st.columns([1, 1])
with col_add:
    if st.button("➕ 添加一行"):
        st.session_state.num_rows += 1
with col_del:
    if st.button("➖ 删除一行") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1

# 显示表单输入行
rows = []
for i in range(st.session_state.num_rows):
    st.markdown(f"**第 {i+1} 项**")
    cols = st.columns([2, 1, 1])
    item = cols[0].text_input("项目", key=f"item_{i}")
    amount = cols[1].number_input("金额", min_value=0.01, step=0.01, key=f"amount_{i}")
    category = cols[2].selectbox("分类", ["饮食", "交通", "购物", "娱乐", "其他"], key=f"category_{i}")

    if item and amount:
        rows.append([record_date, item, amount, category])

# 提交按钮
if st.button("✅ 提交所有记录"):
    if rows:
        new_data = pd.DataFrame(rows, columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"成功添加 {len(rows)} 条记录！")
    else:
        st.warning("请至少填写一项完整消费")

# --- 展示与统计区域 ---
st.header("📊 消费记录一览")

if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"])
    df["年"] = df["日期"].dt.year
    df["月"] = df["日期"].dt.month
    df["日"] = df["日期"].dt.day

    selected_year = st.selectbox("选择年份", sorted(df["年"].unique(), reverse=True))
    available_months = sorted(df[df["年"] == selected_year]["月"].unique(), reverse=True)
    selected_month = st.selectbox("选择月份", available_months)

    filtered = df[(df["年"] == selected_year) & (df["月"] == selected_month)]

    st.subheader(f"📅 {selected_year}年{selected_month}月的记录")
    st.dataframe(filtered)

    total = filtered["金额"].sum()
    st.metric("该月累计消费", f"{total:.2f} 元")

    daily_sum = (
        filtered.groupby("日")["金额"]
        .sum()
        .reset_index()
        .sort_values("日")
        .set_index("日")
    )
    st.subheader("📈 每日消费趋势")
    st.line_chart(daily_sum)

    st.subheader("📊 分类消费柱状图")
    st.bar_chart(filtered.groupby("分类")["金额"].sum())
else:
    st.info("暂无记录，请添加一些消费数据。")

