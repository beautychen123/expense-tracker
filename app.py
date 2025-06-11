
import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

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
    st.session_state.num_rows = 3

st.header("📥 多项消费录入")

# 第三点：默认今天日期，但允许编辑
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
        st.warning("没有有效记录被填写。")

# 加载并展示表格数据（第二点：表格可编辑）
if not df.empty:
    df["年"] = pd.to_datetime(df["日期"]).dt.year
    df["月"] = pd.to_datetime(df["日期"]).dt.month
    df["日"] = pd.to_datetime(df["日期"]).dt.day
    st.subheader(f"📅 {date.today().year}年{date.today().month}月的记录")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 保存编辑"):
        edited_df.to_csv(DATA_FILE, index=False)
        st.success("修改已保存")

    # 第一项：柱状图显示数值
    fig = px.bar(edited_df.groupby("分类", as_index=False)["金额"].sum(),
                 x="分类", y="金额",
                 text_auto=".2s",
                 title="📊 分类消费柱状图")
    fig.update_traces(marker_color="lightskyblue", textfont_size=14)
    fig.update_layout(yaxis=dict(range=[0, max(edited_df['金额'].sum(), 100)]))
    st.plotly_chart(fig, use_container_width=True)


