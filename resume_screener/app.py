import streamlit as st
from config.defaults import init_session_state, save_data
from services.pdf_reader import extract_text_from_pdf, extract_text_from_docx
from services.analyzer import analyze_resume, auto_generate_job_config, extract_requirements_from_jd
from ui.sidebar import render_sidebar
from ui.report import render_report
from ui.stats import render_stats

st.set_page_config(page_title="HR智能筛选系统", layout="wide")

init_session_state()

selected_company, selected_job, page = render_sidebar()

if not st.session_state.get("authenticated", False):
    st.info("👈 请先在左侧登录或注册")
    st.stop()

if page == "岗位配置与分析":
    st.header("📌 岗位配置与分析")
    if not selected_company or not selected_job:
        st.warning("请先在左侧选择或创建公司和岗位")
        st.stop()
    st.subheader(f"当前岗位：{selected_job}（{selected_company}）")

    job_key = f"job_data_{selected_company}_{selected_job}"
    jd_key = f"jd_editor_{selected_job}"

    # ★ 从持久化数据读取最新值
    job_data = st.session_state.data["companies"][selected_company]["jobs"][selected_job].copy()

    # ★ 关键：AI生成后用触发器机制，在text_area渲染前读取新值
    trigger_key = f"jd_trigger_{selected_job}"
    if trigger_key in st.session_state and st.session_state[trigger_key] is not None:
        jd_value = st.session_state[trigger_key]
        st.session_state[jd_key] = jd_value
        del st.session_state[trigger_key]
    else:
        jd_value = job_data.get("jd", "")

    st.markdown("**岗位JD**")
    jd = st.text_area("岗位JD内容", value=jd_value, height=200, key=jd_key)
    if jd != jd_value:
        job_data["jd"] = jd
        st.session_state.data["companies"][selected_company]["jobs"][selected_job]["jd"] = jd
        save_data(st.session_state.username, st.session_state.data)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖 AI生成/更新岗位JD"):
            with st.spinner("AI生成中，请稍候..."):
                config = auto_generate_job_config(selected_job)
                if "error" in config:
                    st.error(config["error"])
                else:
                    new_jd = config.get("jd", "")
                    st.session_state.data["companies"][selected_company]["jobs"][selected_job]["jd"] = new_jd
                    save_data(st.session_state.username, st.session_state.data)
                    # ★ 触发器：保存到单独的key，rerun后在text_area渲染前读取
                    st.session_state[trigger_key] = new_jd
                    st.success("岗位JD已更新！")
                    st.rerun()
    with c2:
        if st.button("🔍 从JD中提取必须项/加分项"):
            current_jd = st.session_state.data["companies"][selected_company]["jobs"][selected_job].get("jd", "")
            if current_jd and current_jd.strip():
                with st.spinner("AI分析中..."):
                    extracted = extract_requirements_from_jd(current_jd)
                    if "error" in extracted:
                        st.error(extracted["error"])
                    else:
                        st.session_state.data["companies"][selected_company]["jobs"][selected_job]["must_have"] = extracted.get("must_have", [])
                        st.session_state.data["companies"][selected_company]["jobs"][selected_job]["plus"] = extracted.get("plus", [])
                        save_data(st.session_state.username, st.session_state.data)
                        st.success("已提取必须项和加分项")
            else:
                st.warning("请先生成或填写岗位JD")

    must_str = "\n".join(st.session_state.data["companies"][selected_company]["jobs"][selected_job].get("must_have", []))
    plus_str = "\n".join(st.session_state.data["companies"][selected_company]["jobs"][selected_job].get("plus", []))
    new_must = st.text_area("必须项（每行一个）", value=must_str, height=100)
    new_plus = st.text_area("加分项（每行一个）", value=plus_str, height=100)
    if st.button("💾 保存岗位配置"):
        st.session_state.data["companies"][selected_company]["jobs"][selected_job]["must_have"] = [x.strip() for x in new_must.split("\n") if x.strip()]
        st.session_state.data["companies"][selected_company]["jobs"][selected_job]["plus"] = [x.strip() for x in new_plus.split("\n") if x.strip()]
        save_data(st.session_state.username, st.session_state.data)
        st.success("保存成功")

elif page == "批量上传与分析":
    st.header("📄 批量简历智能筛选")
    if not selected_company or not selected_job:
        st.warning("请先在左侧创建岗位")
    else:
        st.markdown("### 📄 上传简历")
        resume_files = st.file_uploader("支持同时上传多份PDF或DOCX（最多5份）", type=["pdf", "docx"], accept_multiple_files=True, key="resume_upload")
        if resume_files and len(resume_files) > 5:
            st.error("最多上传5份简历")
            resume_files = resume_files[:5]

        st.markdown("### 🎨 上传作品集（可选）")
        portfolio_files = st.file_uploader("支持同时上传多份PDF或DOCX（最多5份）", type=["pdf", "docx"], accept_multiple_files=True, key="portfolio_upload")
        if portfolio_files and len(portfolio_files) > 5:
            st.error("最多上传5份作品集")
            portfolio_files = portfolio_files[:5]

        if st.button("🚀 开始批量分析") and resume_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            candidates = st.session_state.data["companies"][selected_company]["jobs"][selected_job].get("candidates", [])
            new_reports = []

            resume_map = {f.name.replace(".pdf", "").replace(".docx", ""): f for f in resume_files}
            portfolio_map = {f.name.replace(".pdf", "").replace(".docx", ""): f for f in portfolio_files} if portfolio_files else {}

            total = len(resume_files)
            for i, (name, resume_file) in enumerate(resume_map.items()):
                status_text.text(f"正在分析：{resume_file.name}")
                if resume_file.name.endswith(".pdf"):
                    resume_text = extract_text_from_pdf(resume_file)
                else:
                    resume_text = extract_text_from_docx(resume_file)

                portfolio_text = ""
                if name in portfolio_map:
                    pf = portfolio_map[name]
                    if pf.name.endswith(".pdf"):
                        portfolio_text = extract_text_from_pdf(pf)
                    else:
                        portfolio_text = extract_text_from_docx(pf)
                    status_text.text(f"正在分析：{resume_file.name} + 作品集 {pf.name}")

                result = analyze_resume(
                    name,
                    resume_text,
                    st.session_state.data["companies"][selected_company]["jobs"][selected_job]["jd"],
                    st.session_state.data["companies"][selected_company]["company_bg"],
                    portfolio_text
                )

                candidate = {
                    "姓名": name,
                    "附件": resume_file.name,
                    "简历状态": result["status"],
                    "匹配度评分": result["total_score"],
                    "HR专业总结": result["summary"],
                    "维度评估": result["dimensions"],
                    "追问问题": result["questions"],
                    "完整报告": result["full_report"],
                    "上传时间": result["timestamp"],
                    "来源渠道": "上传",
                    "备注": "",
                    "标签": "",
                    "面试时间": "",
                    "电话": "",
                    "邮箱": "",
                    "是否接受面试": False,
                    "附件路径": "",
                    "作品集附件": portfolio_map[name].name if name in portfolio_map else ""
                }
                candidates.append(candidate)
                new_reports.append(candidate)
                progress_bar.progress((i+1)/total)

            st.session_state.data["companies"][selected_company]["jobs"][selected_job]["candidates"] = candidates
            save_data(st.session_state.username, st.session_state.data)
            st.session_state.batch_reports = new_reports
            status_text.text("分析完成！")
            st.success(f"已完成 {total} 份简历分析")
            st.rerun()

        if hasattr(st.session_state, "batch_reports") and st.session_state.batch_reports:
            st.subheader("本次上传简历分析报告")
            for c in st.session_state.batch_reports:
                with st.expander(f"{c.get('姓名', '未知')} - 匹配度 {c.get('匹配度评分', '?')}分 - {c.get('简历状态', '未知')}"):
                    full = c.get("完整报告", "")
                    if full:
                        st.markdown(full)
                    else:
                        st.write(f"**总结：** {c.get('HR专业总结', '无')}")
                    if c.get("作品集附件"):
                        st.info(f"附带作品集：{c['作品集附件']}")
        else:
            st.info("上传简历并点击「开始批量分析」后，这里会显示本次分析结果。")

elif page == "人才招聘看板":
    render_report(selected_company, selected_job)

elif page == "招聘数据统计看板":
    render_stats(selected_company, selected_job)