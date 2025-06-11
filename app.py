import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase_client import get_expenses, add_expense

st.set_page_config(page_title="消费记录系统", layout="wide")
st.title("💰 消费记录系统")

# 获取数据
data = get_expenses()

# ✅ 添加记录表单
st.subheader("➕ 添加新记录")

with st.form("entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        category = st.selectbox("分类", options=["饮食", "交通", "娱乐", "购物"])

    date = st.date_input("日期", value=datetime.today())
    submitted = st.form_submit_button("✅ 提交所有记录")

if submitted and item and amount:
    add_expense(str(date), item, amount, category)
    st.success("✅ 已添加成功，请刷新查看")

# ✅ 显示数据
st.subheader("📅 消费记录列表")

df = pd.DataFrame(data)
if not df.empty:
    df["日期"] = pd.to_datetime(df["date"]).dt.date
    df["金额"] = df["amount"]
    df["项目"] = df["item"]
    df["分类"] = df["category"]
    st.dataframe(df[["日期", "项目", "金额", "分类"]], use_container_width=True)

    st.subheader("📊 分类消费占比")
    fig = px.pie(df, names="分类", values="金额")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("暂无记录")
