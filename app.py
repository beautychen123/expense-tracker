
import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(page_title="我的消费记录", page_icon="💸")
st.title("💸 我的消费记录系统")

LOCAL_CSV = "expenses.csv"
GITHUB_CSV = "data/expenses.csv"

# 初始化数据
try:
    df = pd.read_csv(LOCAL_CSV)
except FileNotFoundError:
    df = pd.DataFrame(columns=["日期", "项目", "金额", "分类"])
    df.to_csv(LOCAL_CSV, index=False)

# 行数初始设置
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 3

st.header("📥 多项消费录入")
record_date = st.date_input("消费日期", value=date.today())

# 添加/删除输入行
col_add, col_del = st.columns([1, 1])
with col_add:
    if st.button("➕ 添加一行"):
        st.session_state.num_rows += 1
with col_del:
    if st.button("➖ 删除一行") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1

# 录入表单
rows = []
for i in range(st.session_state.num_rows):
    st.markdown(f"**第 {i+1} 项**")
    cols = st.columns([2, 1, 1])
    item = cols[0].text_input("项目", key=f"item_{i}")
    amount = cols[1].number_input("金额", min_value=0.01, step=0.01, key=f"amount_{i}")
    category = cols[2].selectbox("分类", ["饮食", "交通", "购物", "娱乐", "其他"], key=f"category_{i}")
    if item and amount:
        rows.append([record_date, item, amount, category])

# 提交记录并备份
if st.button("✅ 提交所有记录"):
    if rows:
        new_data = pd.DataFrame(rows, columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(LOCAL_CSV, index=False)
        os.makedirs("data", exist_ok=True)
        df.to_csv(GITHUB_CSV, index=False)
        st.success(f"成功添加 {len(rows)} 条记录，数据已备份到 GitHub！")
    else:
        st.warning("没有填写任何有效记录。")

# 展示数据和图表
if not df.empty:
    df["年"] = pd.to_datetime(df["日期"]).dt.year
    df["月"] = pd.to_datetime(df["日期"]).dt.month
    df["日"] = pd.to_datetime(df["日期"]).dt.day
    st.subheader(f"📅 {date.today().year}年{date.today().month}月的记录")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 修改已保存"):
        edited_df.to_csv(LOCAL_CSV, index=False)
        edited_df.to_csv(GITHUB_CSV, index=False)
        st.success("修改内容已保存并同步到 GitHub")

    # 分类消费柱状图
    st.subheader("📊 分类消费柱状图")
    category_sum = edited_df.groupby("分类", as_index=False)["金额"].sum()
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=category_sum["分类"],
        y=category_sum["金额"],
        text=category_sum["金额"],
        textposition="outside",
        marker_color="lightskyblue"
    ))
    fig_bar.update_layout(
        yaxis_title="金额",
        xaxis_title="分类",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # 每月消费趋势折线图（美化版）
    st.subheader("📈 每月消费趋势")
    edited_df["年月"] = pd.to_datetime(edited_df["日期"]).dt.to_period("M").astype(str)
    monthly_sum = edited_df.groupby("年月", as_index=False)["金额"].sum()
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=monthly_sum["年月"],
        y=monthly_sum["金额"],
        mode="lines+markers+text",
        text=monthly_sum["金额"],
        textposition="top center",
        line=dict(shape='spline', color='orange', width=3),
        marker=dict(size=8)
    ))
    fig_line.update_layout(
        xaxis_title="月份",
        yaxis_title="金额",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="lightgray")
    )
    st.plotly_chart(fig_line, use_container_width=True)
