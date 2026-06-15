import streamlit as st
from config.defaults import save_data, load_data
from config.auth import authenticate, register

def render_sidebar():
    with st.sidebar:
        # 登录/注册
        st.subheader("🔐 用户登录")
        if not st.session_state.get("authenticated", False):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("登录"):
                    if authenticate(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.data = load_data(username)
                        companies = list(st.session_state.data["companies"].keys())
                        st.session_state.selected_company = companies[0] if companies else ""
                        if st.session_state.selected_company:
                            jobs = list(st.session_state.data["companies"][st.session_state.selected_company]["jobs"].keys())
                            st.session_state.selected_job = jobs[0] if jobs else ""
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
            with c2:
                if st.button("注册"):
                    if username and password:
                        if register(username, password):
                            st.success(f"用户 {username} 注册成功，请登录")
                        else:
                            st.error("用户名已存在")
                    else:
                        st.warning("请输入用户名和密码")
            return None, None, None

        st.success(f"当前用户：{st.session_state.username}")
        if st.button("退出登录"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.data = {}
            st.rerun()

        st.divider()

        # 公司选择
        st.subheader("🏢 选择公司")
        companies = list(st.session_state.data["companies"].keys())
        comp_opts = companies + ["+ 新增公司"]
        sel_comp = st.selectbox("公司", comp_opts, index=0 if companies else 0)

        if sel_comp == "+ 新增公司":
            new_c = st.text_input("新公司名称")
            if new_c and st.button("创建公司"):
                if new_c not in st.session_state.data["companies"]:
                    st.session_state.data["companies"][new_c] = {"company_bg": "", "jobs": {}}
                    save_data(st.session_state.username, st.session_state.data)
                    st.success(f"公司 {new_c} 已创建")
                    st.rerun()
            selected_company = None
        else:
            selected_company = sel_comp

        if selected_company and selected_company in st.session_state.data["companies"]:
            # 公司背景
            bg = st.text_area("公司背景", value=st.session_state.data["companies"][selected_company].get("company_bg", ""), height=100)
            if bg != st.session_state.data["companies"][selected_company].get("company_bg", ""):
                st.session_state.data["companies"][selected_company]["company_bg"] = bg
                save_data(st.session_state.username, st.session_state.data)

            # 修改公司名称
            st.markdown("**修改公司名称**")
            new_nm = st.text_input("新公司名称", value=selected_company)
            if st.button("保存公司名称修改"):
                if new_nm and new_nm != selected_company:
                    if new_nm not in st.session_state.data["companies"]:
                        st.session_state.data["companies"][new_nm] = st.session_state.data["companies"].pop(selected_company)
                        save_data(st.session_state.username, st.session_state.data)
                        st.success(f"公司名称已从「{selected_company}」改为「{new_nm}」")
                        st.rerun()
                    else:
                        st.error("新公司名称已存在")
                elif new_nm == selected_company:
                    st.info("名称未变化")
                else:
                    st.error("请输入新公司名称")

            # 岗位选择
            jobs = list(st.session_state.data["companies"][selected_company]["jobs"].keys())
            job_opts = jobs + ["+ 新增岗位"]
            sel_job = st.selectbox("选择岗位", job_opts, index=0 if jobs else 0)

            if sel_job == "+ 新增岗位":
                new_j = st.text_input("新岗位名称")
                if new_j and st.button("创建空白岗位"):
                    if new_j not in st.session_state.data["companies"][selected_company]["jobs"]:
                        st.session_state.data["companies"][selected_company]["jobs"][new_j] = {
                            "jd": "", "must_have": [], "plus": [], "candidates": []
                        }
                        save_data(st.session_state.username, st.session_state.data)
                        st.success(f"空白岗位 {new_j} 已创建")
                        st.rerun()
                selected_job = None
            else:
                selected_job = sel_job
        else:
            selected_job = None

        st.divider()
        st.title("📋 HR智能筛选系统")
        page = st.radio("导航", ["岗位配置与分析", "批量上传与分析", "人才招聘看板", "招聘数据统计看板"])
        st.caption("数据自动保存在 user_data 文件夹中，不同用户数据隔离")

    return selected_company, selected_job, page