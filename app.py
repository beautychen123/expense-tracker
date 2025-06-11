import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
from datetime import datetime
from io import StringIO

st.set_page_config(page_title="消费记录系统", layout="wide")  # ✅ 必须是第一个 st. 调用

# DEBUG 调试信息（放在 set_page_config 后）
st.write("当前 secrets 内容：", st.secrets)

# 读取 secrets.toml 中的 GitHub 配置
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
FILE_PATH = st.secrets["github"]["path"]




# GitHub 对象初始化
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# 尝试读取远程 CSV 文件
@st.cache_data(ttl=60)
def load_data():
    try:
        contents = repo.get_contents(FILE_PATH)
        df = pd.read_csv(StringIO(contents.decoded_content.decode("utf-8")))
        return df
    except Exception:
        return pd.DataFrame(columns=["日期", "项目", "金额", "分类"])

# 保存 DataFrame 到 GitHub
def save_data(df):
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(
            contents.path,
            "Update expenses.csv",
            df.to_csv(index=False, encoding="utf-8"),
            contents.sha
        )
    except Exception:
        repo.create_file(
            FILE_PATH,
            "Create expenses.csv",
            df.to_csv(index=False, encoding="utf-8")
        )

st.set_page_config(page_title="消费记录系统", layout="wide")

st.title("💸 我的消费记录系统")
st.subheader("📬 多项消费录入")

today = datetime.today().strftime("%Y-%m-%d")
input_date = st.date_input("消费日期", value=pd.to_datetime(today), format="YYYY/MM/DD")

if "rows" not in st.session_state:
    st.session_state.rows = 1

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("➕ 添加一行"):
        st.session_state.rows += 1
with col2:
    if st.button("➖ 删除一行") and st.session_state.rows > 1:
        st.session_state.rows -= 1

items = []
for i in range(st.session_state.rows):
    st.markdown(f"#### 第{i+1}项")
    cols = st.columns([3, 1, 2])
    item = cols[0].text_input("项目", key=f"item_{i}")
    amount = cols[1].number_input("金额", min_value=0.0, step=0.01, key=f"amount_{i}")
    category = cols[2].selectbox("分类", ["饮食", "交通", "购物", "娱乐", "其他"], key=f"category_{i}")
    items.append({"项目": item, "金额": amount, "分类": category})

if st.button("✅ 提交所有记录"):
    df = load_data()
    for item in items:
        if item["项目"]:
            df = pd.concat([df, pd.DataFrame([{
                "日期": pd.to_datetime(input_date).strftime("%Y-%m-%d"),
                "项目": item["项目"],
                "金额": item["金额"],
                "分类": item["分类"]
            }])], ignore_index=True)
    save_data(df)
    st.success("成功添加 {} 条记录，数据已同步 GitHub!".format(len(items)))

df = load_data()
if not df.empty:
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df["年月"] = df["日期"].dt.to_period("M").astype(str)

    current_month = datetime.today().strftime("%Y-%m")
    month_df = df[df["年月"] == current_month]

    st.header(f"📅 {current_month} 的记录")
    total = month_df["金额"].sum()
    st.subheader(f"💰 {current_month} 总消费： {total:.2f} 元")

    with st.expander("📋 查看/编辑详细记录"):
        edited_df = st.data_editor(month_df, use_container_width=True, num_rows="dynamic")
        if edited_df.equals(month_df) is False:
            df.update(edited_df)
            save_data(df)
            st.success("修改内容已保存并同步到 GitHub")

    fig = px.bar(month_df, x="分类", y="金额", color="分类", title="📊 分类消费柱状图")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("暂无记录，请添加一些消费项")
