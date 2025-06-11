from supabase import create_client, Client

# 你的 Supabase 项目 URL 和 anon key（从 API 设置中复制）
url = "https://xyz.supabase.co"  # 替换为你的 Project URL
key = "your_anon_key"  # 替换为你的 anon key

# 创建 Supabase 客户端
supabase: Client = create_client(url, key)

def get_expenses():
    # 从 Supabase 获取数据
    data = supabase.table("expenses").select("*").execute()
    return data["data"]

def add_expense(date, item, amount, category):
    # 向 Supabase 添加一条新的记录
    new_expense = {
        "日期": date,
        "项目": item,
        "金额": amount,
        "分类": category,
    }
    supabase.table("expenses").insert(new_expense).execute()
