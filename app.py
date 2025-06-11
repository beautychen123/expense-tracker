import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
from io import StringIO
import plotly.express as px

# -------------------- GitHub 配置 --------------------
GITHUB_TOKEN = st.secrets["github"]["token"]
REPO_NAME = st.secrets["github"]["repo"]
RECORD_FILE = "data/expenses.csv"
CATEGORY_FILE = "data/categories.csv"

# -------------------- 工具函数 --------------------
def get_repo():
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(REPO_NAME)
    except Exception as e:
        st.warning("🚨 GitHub 无法连接：" + str(e))
        return None

def load_data():
    try:
        contents = get_repo().get_contents(RECORD_FILE)
        return pd.read_csv(StringIO(contents.decoded_content.decode()))
    except:
        return pd.DataFrame(columns=["日期", "项目", "金额", "分类"])

def save_data(df):
    try:
        repo = get_repo()
        contents = repo.get_contents(RECORD_FILE)
        repo.update_file(RECORD_FILE, "批量更新消费记录", df.to_csv(index=False), contents.sha)
        st.success("✅ 所有记录已同步到 GitHub")
    except Exception as e:
        st.error("❌ 数据同步失败：" + str(e))

def load_categories():
    try:
        contents = get_repo().get_contents(CATEGORY_FILE)
        df = pd.read_csv(StringIO(contents.decoded_content.decode()))
        return df["分类"].dropna().unique().tolist()
    except:
        return ["饮食", "交通", "娱乐", "购物"]

def save_categories(categories):
    try:
        df_cat = pd.DataFrame({"分类": sorted(set(categories))})
        repo = get_repo()
        try:
            contents = repo.get_contents(CATEGORY_FILE)
            repo.update_file(CATEGORY_FILE, "更新分类", df_cat.to_csv(index=False), contents.sha)
        except:
            repo.create_file(CATEGORY_FILE, "创建分类", df_cat.to_csv(index=False))
        st.success("✅ 分类列表已更新")
    except Exception as e:
        st.error(f"❌ 分类保存失败：{e}")

# -------------------- 主 UI --------------------
st.title("💰 消费记录系统（批量录入模式）")

df = load_data()
categories = load_categories()

# 添加新分类支持
if "entries" not in st.session_state:
    st.session_state.entries = [{"项目": "", "金额": 0.0, "分类": categories[0], "日期": datetime.today()}]

st.subheader("➕ 添加新记录")

for idx, entry in enumerate(st.session_state.entries):
    with st.container():
        cols = st.columns([3, 2, 2, 3])
        entry["项目"] = cols[0].text_input(f"项目 {idx+1}", value=entry["项目"], key=f"item_{idx}")
        entry["金额"] = cols[1].number_input(f"金额 {idx+1}", value=entry["金额"], min_value=0.0, step=0.01, key=f"amount_{idx}")
        
        cat_selection = cols[2].selectbox(f"分类 {idx+1}", options=categories + ["+ 添加新分类"], index=categories.index(entry["分类"]) if entry["分类"] in categories else 0, key=f"cat_{idx}")
        if cat_selection == "+ 添加新分类":
            new_cat = cols[2].text_input(f"请输入新分类名称", key=f"new_cat_{idx}")
            if new_cat and new_cat not in categories:
                categories.append(new_cat)
                save_categories(categories)
                cat_selection = new_cat
        entry["分类"] = cat_selection

        entry["日期"] = cols[3].date_input(f"日期 {idx+1}", value=entry["日期"], key=f"date_{idx}")

st.button("➕ 添加更多记录", on_click=lambda: st.session_state.entries.append({"项目": "", "金额": 0.0, "分类": categories[0], "日期": datetime.today()}))

if st.button("✅ 提交所有记录"):
    valid_entries = [e for e in st.session_state.entries if e["项目"] and e["金额"] > 0]
    if not valid_entries:
        st.warning("⚠️ 没有有效记录要提交")
    else:
        new_df = pd.DataFrame([{
            "日期": e["日期"].strftime('%Y-%m-%d'),
            "项目": e["项目"],
            "金额": e["金额"],
            "分类": e["分类"]
        } for e in valid_entries])
        df = pd.concat([df, new_df], ignore_index=True)
        save_data(df)
        st.session_state.entries = [{"项目": "", "金额": 0.0, "分类": categories[0], "日期": datetime.today()}]

# -------------------- 显示记录 + 图表 --------------------
current_month = datetime.today().strftime('%Y-%m')
if not df.empty:
    df["年月"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
    df_month = df[df["年月"] == current_month]
    
    st.subheader(f"📅 {current_month} 的记录")
    st.data_editor(df_month.drop(columns=["年月"]), num_rows="dynamic", use_container_width=True)
    
    total = df_month["金额"].sum()
    st.subheader(f"💰 本月总消费：{total:.2f} 元")
    
    st.subheader("📊 消费统计分析")

    by_cat = df_month.groupby("分类")["金额"].sum().reset_index()
    fig_bar = px.bar(by_cat, x="分类", y="金额", title="分类分布", text="金额")
    fig_bar.update_traces(textposition="outside", textfont_size=16)
    st.plotly_chart(fig_bar, use_container_width=True)

    df["月份"] = pd.to_datetime(df["日期"]).dt.to_period("M").astype(str)
    by_month = df.groupby("月份")["金额"].sum().reset_index()
    fig_line = px.line(by_month, x="月份", y="金额", title="每月趋势")
    st.plotly_chart(fig_line, use_container_width=True)

    by_cat["label"] = by_cat.apply(lambda r: f"{r['金额']/by_cat['金额'].sum():.1%} {r['分类']}", axis=1)
    fig_pie = px.pie(by_cat, names="label", values="金额", title="占比", color_discrete_sequence=["red", "gold", "blue", "green"])
    fig_pie.update_traces(textposition="outside", textinfo="label", textfont_size=16)
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("📭 暂无记录，请添加消费记录。")
