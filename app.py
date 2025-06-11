import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from supabase_client import get_expenses, add_expense

# 页面配置
st.set_page_config(page_title="消费记录系统", layout="wide")
st.title("💰 消费记录系统")

# 当前年月
today = datetime.today()
current_month = today.strftime("%Y-%m")

# 表单输入区域
st.subheader("➕ 添加新记录")
with st.form("entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        category = st.selectbox("分类", ["饮食", "交通", "娱乐", "购物", "其他"])

    date = st.date_input("日期", value=today)
    submitted = st.form_submit_button("✅ 提交所有记录")

    if submitted and item and amount:
        add_expense(str(date), item, amount, category)
        st.success("✅ 添加成功！请刷新页面查看最新数据")

# 获取数据库记录
data = get_expenses()
if not data:
    st.info("暂无记录，请添加消费数据。")
    st.stop()

# 转换为 DataFrame
df = pd.DataFrame(data)
df["日期"] = pd.to_datetime(df["date"])
df["年月"] = df["日期"].dt.to_period("M").astype(str)

# 当前月份筛选
df_month = df[df["年月"] == current_month]

# 表格展示
st.subheader(f"📅 {current_month} 的记录")
st.data_editor(
    df_month[["日期", "item", "amount", "category"]],
    use_container_width=True,
    disabled=True,
    hide_index=True
)

# 本月总消费
month_total = df_month["amount"].sum()
st.subheader(f"💰 本月总消费：{month_total:.2f} 元")

# 图表展示
st.subheader("📊 消费统计分析")

# 1. 分类条形图
by_category = df_month.groupby("category")["amount"].sum().reset_index()
fig_bar = px.bar(by_category, x="category", y="amount", title="分类消费分布", text_auto=".2f")
st.plotly_chart(fig_bar, use_container_width=True)

# 2. 分类饼图
fig_pie = px.pie(by_category, names="category", values="amount", title="分类消费占比", hole=0.3)
st.plotly_chart(fig_pie, use_container_width=True)

# 3. 月度趋势折线图
df["月份"] = df["日期"].dt.to_period("M").astype(str)
by_month = df.groupby("月份")["amount"].sum().reset_index()
fig_line = px.line(by_month, x="月份", y="amount", title="每月消费趋势")
st.plotly_chart(fig_line, use_container_width=True)
