# config/defaults.py
import streamlit as st
import json
import os
from datetime import datetime

DATA_ROOT = "user_data"   # 所有用户数据存放的文件夹
os.makedirs(DATA_ROOT, exist_ok=True)

DEEPSEEK_API_KEY = "sk-4e128671f97b4173a4e8b0df70e75344"   # 请填入你的真实 API Key

def get_user_data_path(username):
    """根据用户名返回数据文件路径"""
    safe_name = username.replace(" ", "_").replace("/", "_")
    return os.path.join(DATA_ROOT, f"{safe_name}.json")

def load_data(username):
    """加载指定用户的数据，如果不存在则创建默认结构"""
    file_path = get_user_data_path(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 默认数据结构
        default_data = {
            "companies": {
                "我的公司": {
                    "company_bg": "我们是国内头部教育MCN机构，英语赛道TOP1，全网粉丝2500万+，专注低幼启蒙、少儿教育领域。",
                    "jobs": {
                        "直播运营经理": {
                            "jd": """- 盯盘、调策略、优化投产比，实时决策
- 和素材编导打磨千川素材，形成闭环
- 管理主播团队，打磨话术和节奏，提升转化率
- 每日复盘数据，自我驱动""",
                            "must_have": ["抖音直播经验", "独立操盘能力", "数据复盘能力"],
                            "plus": ["教育/图书赛道经验", "千川投流ROI>3", "管理过主播团队"],
                            "candidates": []
                        }
                    }
                }
            },
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_data(username, default_data)
        return default_data

def save_data(username, data):
    """保存指定用户的数据"""
    data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_path = get_user_data_path(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_session_state():
    """初始化session状态，包含当前用户"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "data" not in st.session_state:
        # 未登录时没有数据
        st.session_state.data = {}
    if "edit_jd_mode" not in st.session_state:
        st.session_state.edit_jd_mode = False
    if "selected_company" not in st.session_state:
        st.session_state.selected_company = ""
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = ""