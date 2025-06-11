import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
from io import StringIO
import plotly.express as px

# -------------------- GitHub 配置 --------------------
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
FILE_PATH = st.secrets["github"]["path"]

# -------------------- 初始化 --------------------
today = datetime.today().strftime('%Y-%m-%d')
current_month = datetime.today().strftime('%Y-%m')

repo = None
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.warning("🚨 GitHub 无法连接：" + str(e))

# -------------------- 加载数据 --------------------
def load_data():
    if repo:
        try:
            contents = repo.get_contents(FILE_PATH)
            df = pd.read_csv(StringIO(contents.decoded_content.decode()))
        except Exception:
            df = pd.DataFrame(columns=["日期", "项目", "金额", "分类"])
    else:
        df = pd.DataFrame(columns=["日期", "项目", "金额", "分类"])
    return df

# -------------------- 保存数据到 GitHub --------------------
def save_data(df):
    if not repo:
        st.error("❌ GitHub 无法连接，数据未同步")
        return
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(contents.path, "Update expenses.csv", df.to_csv(index=False), contents.sha)
        st.success("✅ 成功同步到 GitHub!")
    except Exception as e:
        st.error("❌ 上传失败：" + str(e))

# -------------------- UI 标题 --------------------
st.title("💰 消费记录")

df = load_data()

# -------------------- 补充 年月 列 --------------------
if not df.empty:
    df["年月"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)

# -------------------- 表单输入 --------------------
st.subheader("➕ 添加新记录")
with st.form(key="entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        # 动态分类
        categories = list(df["分类"].unique()) if not df.empty else ["饮食", "交通", "娱乐", "购物"]
        category = st.selectbox("分类", options=categories + ["+ 添加新分类"])

    if category == "+ 添加新分类":
        category = st.text_input("请输入新分类名称")

    submitted = st.form_submit_button("✅ 提交所有记录")

if submitted and item and amount is not None:
    new_entry = {
        "日期": today,
        "项目": item,
        "金额": amount,
        "分类": category
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)
    st.success("成功添加 1 条记录，数据已同步 GitHub!")

# -------------------- 显示当月记录 --------------------
st.subheader(f"📅 {current_month} 的记录")
df_month = df[df["年月"] == current_month]
st.data_editor(df_month, num_rows="dynamic", use_container_width=True, disabled=["年月"])

# -------------------- 当月合计 --------------------
month_total = df_month["金额"].sum()
st.subheader(f"💰 {current_month} 总消费：{month_total:.2f} 元")

# -------------------- 统计图表 --------------------
if not df.empty:
    st.subheader("📊 消费统计分析")

    # 类型分布 - 条形图
    by_category = df_month.groupby("分类")["金额"].sum().reset_index()
    fig_bar = px.bar(by_category, x="分类", y="金额", title="不同类型消费分布", text_auto=True)
    st.plotly_chart(fig_bar, use_container_width=True)

    # 月份趋势 - 折线图
    df["月份"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
    by_month = df.groupby("月份")["金额"].sum().reset_index()
    fig_line = px.line(by_month, x="月份", y="金额", title="每月消费趋势")
    st.plotly_chart(fig_line, use_container_width=True)

    # 消费占比 - 饼图
    fig_pie = px.pie(by_category, names="分类", values="金额", title="分类消费占比")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("暂无记录，快来添加吧！")
