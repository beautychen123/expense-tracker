import streamlit as st
import pandas as pd
import os
from datetime import datetime
from github import Github
from io import StringIO

# GitHub secrets
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
FILE_PATH = st.secrets["github"]["path"]

# 日期今天
today = datetime.today().strftime('%Y-%m-%d')

# 初始化 repo
repo = None
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.warning("⚠️ 无法连接 GitHub，同步将被跳过。\n\n" + str(e))

# 下载原始 CSV 内容
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

# 保存 CSV 到 GitHub
def save_data(df):
    if not repo:
        st.error("❌ GitHub 无法访问，数据未同步")
        return
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(contents.path, "Update expenses.csv", df.to_csv(index=False), contents.sha)
        st.success("✅ 成功同步到 GitHub!")
    except Exception as e:
        st.error("❌ 上传出错：" + str(e))

st.title("💰 记账小工具")

df = load_data()

st.subheader("➕ 添加新记录")

with st.form(key="entry_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        item = st.text_input("项目")
    with col2:
        amount = st.number_input("金额", min_value=0.0, step=0.01)
    with col3:
        category = st.selectbox("分类", ["饮食", "交通", "娱乐", "购物", "其他"])
    submitted = st.form_submit_button("✅ 提交所有记录")

if submitted and item and amount:
    new_entry = {
        "日期": today,
        "项目": item,
        "金额": amount,
        "分类": category
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)
    st.success(f"成功添加 1 条记录，数据已同步 GitHub!")

# 显示记录
st.subheader("📅 当前记录")
if not df.empty:
    df["年月"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
    st.dataframe(df)

    total = df[df["年月"] == pd.to_datetime(today).strftime("%Y-%m")]["金额"].sum()
    st.subheader(f"💰 {pd.to_datetime(today).strftime('%Y年%m月')}总消费：{total:.2f} 元")
else:
    st.info("暂无记录。")
