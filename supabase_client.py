import streamlit as st
from supabase import create_client, Client

# ✅ 从 secrets.toml 中读取 Supabase 配置
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]

# ✅ 初始化 Supabase 客户端
supabase: Client = create_client(url, key)

# ✅ 查询所有消费记录（按日期倒序）
def get_expenses():
    res = supabase.table("expenses").select("*").order("date", desc=True).execute()
    return res.data

# ✅ 插入一条消费记录
def add_expense(date, item, amount, category):
    data = {
        "date": date,
        "item": item,
        "amount": amount,
        "category": category
    }
    supabase.table("expenses").insert(data).execute()
