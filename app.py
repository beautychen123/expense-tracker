
import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(page_title="我的消费记录", page_icon="💸")
st.title("💸 我的消费记录系统")

LOCAL_CSV = "expenses.csv"
GITHUB_CSV = "data/expenses.csv"

# 自动恢复机制：优先从 GitHub 拉取
if not os.path.exists(LOCAL_CSV) and os.path.exists(GITHUB_CSV):
    st.warning("🔁 本地账本不存在，已从 GitHub 备份恢复。")
    df = pd.read_csv(GITHUB_CSV)
    df.to_csv(LOCAL_CSV, index=False)
elif os.path.exists(LOCAL_CSV):
    df = pd.read_csv(LOCAL_CSV)
elif os.path.exists(GITHUB_CSV):
    df = pd.read_csv(GITHUB_CSV)
else:
    df = pd.DataFrame(columns=["日期", "项目", "金额", "分类"])
    df.to_csv(LOCAL_CSV, index=False)

if "num_rows" not in st.session_state:
    st.session_state.num_rows = 3

st.header("📥 多项消费录入")
record_date = st.date_input("消费日期", value=date.today())

col_add, col_del = st.columns([1, 1])
with col_add:
    if st.button("➕ 添加一行"):
        st.session_state.num_rows += 1
with col_del:
    if st.button("➖ 删除一行") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1

rows = []
for i in range(st.session_state.num_rows):
    st.markdown(f"**第 {i+1} 项**")
    cols = st.columns([2, 1, 1])
    item = cols[0].text_input("项目", key=f"item_{i}")
    amount = cols[1].number_input("金额", min_value=0.01, step=0.01, key=f"amount_{i}")
    category = cols[2].selectbox("分类", ["饮食", "交通", "购物", "娱乐", "其他"], key=f"category_{i}")
    if item and amount:
        rows.append([record_date, item, amount, category])

# ✅ 避免写入重复演示数据
if st.button("✅ 提交所有记录"):
    if rows:
        new_data = pd.DataFrame(rows, columns=["日期", "项目", "金额", "分类"])
        new_data["日期"] = pd.to_datetime(new_data["日期"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(LOCAL_CSV, index=False)
        os.makedirs("data", exist_ok=True)
        df.to_csv(GITHUB_CSV, index=False)
        st.success(f"成功添加 {len(rows)} 条记录，数据已同步 GitHub！")
    else:
        st.warning("没有填写任何有效记录。")

# ========================== 展示与自动保存 ==========================

if not df.empty:
   df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df["年月"] = df["日期"].dt.to_period("M").astype(str)
    display_df = df[["日期", "项目", "金额", "分类"]].copy()
    this_year, this_month = date.today().year, date.today().month
    current_month_df = df[(df["日期"].dt.year == this_year) & (df["日期"].dt.month == this_month)]

    st.subheader(f"📅 {this_year}年{this_month}月的记录")
    monthly_total = current_month_df["金额"].sum()
    st.markdown(f"### 💰 {this_year}年{this_month}月总消费：{monthly_total:.2f} 元")

    # 自动保存逻辑：编辑后对比保存
    with st.expander("📋 查看/编辑详细记录", expanded=True):
        st.markdown("（表格可编辑，编辑后将自动保存）")
        edited_df = st.data_editor(
            display_df,
            num_rows="dynamic",
            use_container_width=True,
            height=400,
            key="editable_data"
        )

    if not edited_df.equals(display_df):
        df.update(edited_df)
        df.to_csv(LOCAL_CSV, index=False)
        df.to_csv(GITHUB_CSV, index=False)
        st.success("✅ 修改已自动保存并同步 GitHub")

    # 分类图表
    st.subheader("📊 分类消费柱状图")
    category_sum = df.groupby("分类", as_index=False)["金额"].sum()
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

    st.subheader("📈 每月消费趋势")
    monthly_sum = df.groupby("年月", as_index=False)["金额"].sum()
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
