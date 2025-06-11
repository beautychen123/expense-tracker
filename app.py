
import streamlit as st
import pandas as pd
from datetime import date, datetime
import plotly.graph_objects as go
import os
import base64
import json
import requests

# 从 secrets 中读取配置
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO = st.secrets["github"]["repo"]
GITHUB_PATH = st.secrets["github"]["path"]
LOCAL_CSV = "expenses.csv"
DATA_CSV = "data/expenses.csv"

def upload_to_github():
    try:
        api_url = f"https://api.github.com/repos/{REPO}/contents/{GITHUB_PATH}"
        with open(DATA_CSV, "rb") as f:
            content = f.read()
        encoded = base64.b64encode(content).decode("utf-8")
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        get_resp = requests.get(api_url, headers=headers)
        sha = get_resp.json()["sha"] if get_resp.status_code == 200 else None
        payload = {
            "message": f"auto update {datetime.now().isoformat()}",
            "content": encoded,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        resp = requests.put(api_url, headers=headers, data=json.dumps(payload))
        if resp.status_code in [200, 201]:
            st.toast("✅ GitHub 同步成功", icon="🌐")
        else:
            st.warning(f"GitHub 同步失败: {resp.status_code}")
    except Exception as e:
        st.error(f"上传出错: {e}")

st.set_page_config(page_title="消费记录", page_icon="💰")
st.title("💸 我的消费记录系统")

if not os.path.exists(LOCAL_CSV) and os.path.exists(DATA_CSV):
    df = pd.read_csv(DATA_CSV)
    df.to_csv(LOCAL_CSV, index=False)
elif os.path.exists(LOCAL_CSV):
    df = pd.read_csv(LOCAL_CSV)
elif os.path.exists(DATA_CSV):
    df = pd.read_csv(DATA_CSV)
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

if st.button("✅ 提交所有记录"):
    if rows:
        new_data = pd.DataFrame(rows, columns=["日期", "项目", "金额", "分类"])
        new_data["日期"] = pd.to_datetime(new_data["日期"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(LOCAL_CSV, index=False)
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_CSV, index=False)
        st.success(f"成功添加 {len(rows)} 条记录，数据已同步 GitHub!")
        upload_to_github()
    else:
        st.warning("请填写至少一项记录。")

if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"])
    df["年月"] = df["日期"].dt.to_period("M").astype(str)
    display_df = df[["日期", "项目", "金额", "分类"]].copy()
    this_year, this_month = date.today().year, date.today().month
    current_month_df = df[(df["日期"].dt.year == this_year) & (df["日期"].dt.month == this_month)]

    st.subheader(f"📅 {this_year}年{this_month}月的记录")
    monthly_total = current_month_df["金额"].sum()
    st.markdown(f"### 💰 {this_year}年{this_month}月总消费：{monthly_total:.2f} 元")

    with st.expander("📋 查看/编辑详细记录", expanded=True):
        st.markdown("（表格可编辑，修改后自动保存并同步）")
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
        df.to_csv(DATA_CSV, index=False)
        st.success("✅ 修改内容已保存并同步到 GitHub")
        upload_to_github()

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
        xaxis_title="分类"
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
        hovermode="x unified"
    )
    st.plotly_chart(fig_line, use_container_width=True)
