from supabase import create_client, Client

# ✅ 你的 Supabase 项目配置
url = "https://xixtvdzauqlgvyrigfam.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhpa3R2ZHphdXFsZ3Z5cmlnZmFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2NDAzNjcsImV4cCI6MjA2NTIxNjM2N30.poPK_WfD2Kz9SXuYTdYxyOs9Exwq0BAZ1hJnSr9NSvw"

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
