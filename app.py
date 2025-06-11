import streamlit as st
import pandas as pd
import os
from datetime import date
from io import StringIO
from github import Github
import base64

# 加载 GitHub token 和路径配置
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
FILE_PATH = st.secrets["github"]["path"]

# GitHub 初始化
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# 加载 CSV 数据（从本地或 GitHub）
@st.cache_data
def load_data():
    try:
        file_content = repo.get_contents(FILE_PATH)
        df = pd.read_csv(StringIO(file_content.decoded_content.decode("utf-8")))
        return df
    except Exception:
        return pd.DataFrame(columns=["日期", "项目", "金额", "分类"])

df = load_data()

# 设置页面标题
st.title("🧾 我的消费记录系统")
st.markdown("📅 多项消费录入")

# 初始化 session state
if "num_rows" not in st.session_state:
    st.session_state.num_rows = 1

# 日期选择
record_date = st.date_input("消费日期", date.today())

# 添加/删除行按钮
col_add, col_del = st.columns([1, 1])
with col_add:
    if st.button("➕ 添加一行"):
        st.session_state.num_rows += 1
with col_del:
    if st.button("➖ 删除一行") and st.session_state.num_rows > 1:
        st.session_state.num_rows -= 1

# 输入多项
rows = []
for i in range(st.session_state.num_rows):
    st.markdown(f"### 第 {i+1} 项")
    cols = st.columns([2, 1, 1])
    item = cols[0].text_input("项目", key=f"item_{i}")
    amount = cols[1].number_input("金额", min_value=0.01, step=1.0, key=f"amount_{i}")
    category = cols[2].selectbox("分类", ["饮食", "交通", "其他"], key=f"cat_{i}")
    if item and amount:
        rows.append([record_date, item, amount, category])

# 提交记录按钮
if st.button("✅ 提交所有记录"):
    if rows:
        new_df = pd.DataFrame(rows, columns=["日期", "项目", "金额", "分类"])
        df = pd.concat([df, new_df], ignore_index=True)
        df["日期"] = pd.to_datetime(df["日期"])
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        repo_file = repo.get_contents(FILE_PATH)
        try:
            repo.update_file(FILE_PATH, "Update expenses", csv_buffer.getvalue(), repo_file.sha)
            st.success("成功添加记录，数据已同步 GitHub!")
        except Exception as e:
            st.error(f"上传出错: {str(e)}")

# 本月消费数据
df["日期"] = pd.to_datetime(df["日期"])
df["年月"] = df["日期"].dt.to_period("M").astype(str)
current_month = date.today().strftime("%Y-%m")
monthly_df = df[df["年月"] == current_month]

# 总消费
total = monthly_df["金额"].sum()
st.markdown(f"## 🗓️ {current_month} 的记录")
st.markdown(f"### 💰 {current_month} 总消费：{total:.2f} 元")

# 折叠编辑表格
with st.expander("🗂️ 查看/编辑详细记录"):
    edited_df = st.data_editor(monthly_df.drop(columns=["年月"]), num_rows="dynamic")
    if edited_df is not None:
        df.update(edited_df)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        repo_file = repo.get_contents(FILE_PATH)
        try:
            repo.update_file(FILE_PATH, "Auto sync after edit", csv_buffer.getvalue(), repo_file.sha)
            st.success("修改内容已保存并同步到 GitHub")
        except Exception as e:
            st.error(f"同步失败: {str(e)}")
