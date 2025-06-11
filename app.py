import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# Supabase 配置
url = "https://xyz.supabase.co"  # 替换为你的 Project URL
key = "your_anon_key"  # 替换为你的 anon key
supabase: Client = create_client(url, key)

# 获取费用数据
def get_expenses():
    data = supabase.table("expenses").select("*").execute()
    return data["data"]

# 添加费用数据
def add_expense(date, item, amount, category):
    new_expense = {
        "日期": date,
        "项目": item,
        "金额": amount,
        "分类": category,
    }
    supabase.table("expenses").insert(new_expense).execute()

# 获取数据
df = pd.DataFrame(get_expenses())

# 初始化数据
if df.empty:
    st.info("没有记录，请添加数据")
else:
    df["日期"] = pd.to_datetime(df["日期"])
    df["年月"] = df["日期"].dt.to_period("M").astype(str)

# 表单输入
st.subheader("➕ 添加记录")
with st.form(key="entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        category = st.selectbox("分类", ["饮食", "交通", "娱乐", "购物"])

    submitted = st.form_submit_button("✅ 提交记录")
    if submitted and item and amount is not None:
        add_expense(datetime.today().strftime('%Y-%m-%d'), item, amount, category)
        st.success("成功添加记录！")
        df = pd.DataFrame(get_expenses())  # 刷新数据

# 显示记录
st.subheader("📅 本月的消费记录")
current_month = datetime.today().strftime('%Y-%m')
df_month = df[df["年月"] == current_month]
st.data_editor(df_month, num_rows="dynamic", use_container_width=True)

# 总消费
month_total = df_month["金额"].sum()
st.subheader(f"💰 本月总消费：{month_total:.2f} 元")

# 饼图、条形图等图表
st.subheader("📊 消费统计分析")
by_category = df_month.groupby("分类")["金额"].sum().reset_index()
fig_bar = px.bar(by_category, x="分类", y="金额", title="分类消费分布")
st.plotly_chart(fig_bar, use_container_width=True)
