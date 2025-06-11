import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
from io import StringIO
import plotly.express as px

# -------------------- GitHub 配置 --------------------
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
RECORD_FILE = "data/expenses.csv"       # 消费记录文件
CATEGORY_FILE = "data/categories.csv"   # 分类列表文件

# -------------------- 初始化 --------------------
today = datetime.today().strftime('%Y-%m-%d')
current_month = datetime.today().strftime('%Y-%m')

repo = None
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.warning("🚨 GitHub 无法连接：" + str(e))

# -------------------- 数据加载与保存 --------------------
@st.cache_data(ttl=60)
def load_data():
    try:
        contents = repo.get_contents(RECORD_FILE)
        return pd.read_csv(StringIO(contents.decoded_content.decode()))
    except:
        return pd.DataFrame(columns=["日期", "项目", "金额", "分类"])

def save_data(df):
    try:
        contents = repo.get_contents(RECORD_FILE)
        repo.update_file(contents.path, "Update expenses.csv", df.to_csv(index=False), contents.sha)
        st.success("✅ 数据已同步到 GitHub")
    except Exception as e:
        st.error("❌ 数据同步失败：" + str(e))

def load_categories():
    try:
        contents = repo.get_contents(CATEGORY_FILE)
        df_cat = pd.read_csv(StringIO(contents.decoded_content.decode()))
        return df_cat["分类"].dropna().unique().tolist()
    except:
        return ["饮食", "交通", "娱乐", "购物"]

def save_categories(categories):
    try:
        df_cat = pd.DataFrame({"分类": sorted(set(categories))})
        try:
            contents = repo.get_contents(CATEGORY_FILE)
            repo.update_file(CATEGORY_FILE, "更新分类", df_cat.to_csv(index=False), contents.sha)
        except:
            repo.create_file(CATEGORY_FILE, "创建分类", df_cat.to_csv(index=False))
        st.success("✅ 分类列表已更新")
    except Exception as e:
        st.error(f"❌ 分类保存失败：{e}")

# -------------------- UI：标题与初始化 --------------------
st.title("💰 消费记录系统")

df = load_data()
categories = load_categories()

# 补充年月列
if not df.empty:
    df["年月"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)

# -------------------- 表单输入区域 --------------------
st.subheader("➕ 添加新记录")
with st.form(key="entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        category = st.selectbox("分类", options=categories + ["+ 添加新分类"])

    if category == "+ 添加新分类":
        new_cat = st.text_input("请输入新分类名称")
        if new_cat and new_cat not in categories:
            categories.append(new_cat)
            save_categories(categories)
            category = new_cat
        elif new_cat in categories:
            st.info("该分类已存在")

    date = st.date_input("日期", value=datetime.today())
    submitted = st.form_submit_button("✅ 提交所有记录")

if submitted and item and amount is not None:
    new_entry = {
        "日期": date.strftime('%Y-%m-%d'),
        "项目": item,
        "金额": amount,
        "分类": category
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)

# -------------------- 显示本月记录 --------------------
st.subheader(f"📅 {current_month} 的记录")
df["年月"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
df_month = df[df["年月"] == current_month]
st.data_editor(df_month.drop(columns=["年月"]), num_rows="dynamic", use_container_width=True)

# -------------------- 显示当月总消费 --------------------
month_total = df_month["金额"].sum()
st.subheader(f"💰 {current_month} 总消费：{month_total:.2f} 元")

# -------------------- 图表分析 --------------------
if not df_month.empty:
    st.subheader("📊 消费统计分析")

    # 条形图
    by_category = df_month.groupby("分类")["金额"].sum().reset_index()
    fig_bar = px.bar(by_category, x="分类", y="金额", title="不同类型消费分布", text="金额")
    fig_bar.update_traces(textposition="outside", textfont_size=16, marker_color="lightblue")
    fig_bar.update_layout(uniformtext_minsize=12, uniformtext_mode="hide")
    st.plotly_chart(fig_bar, use_container_width=True)

    # 折线图
    df["月份"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
    by_month = df.groupby("月份")["金额"].sum().reset_index()
    fig_line = px.line(by_month, x="月份", y="金额", title="每月消费趋势")
    st.plotly_chart(fig_line, use_container_width=True)

    # 饼图
    color_sequence = ["red", "gold", "blue", "green"]
    by_category["label"] = by_category.apply(
        lambda row: f"{row['金额'] / by_category['金额'].sum():.1%} {row['分类']}", axis=1
    )
    fig_pie = px.pie(by_category, names="label", values="金额", title="分类消费占比", color_discrete_sequence=color_sequence)
    fig_pie.update_traces(textposition="outside", textinfo="label", textfont_size=16)
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("📭 当前月份暂无消费记录。")
