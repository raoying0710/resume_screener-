import streamlit as st

def render_stats(company, job):
    st.header("📈 招聘数据统计看板")
    if not company or not job:
        st.info("请先在左侧选择公司和岗位")
        return

    candidates = st.session_state.data["companies"][company]["jobs"][job].get("candidates", [])
    total = len(candidates)

    # 自动统计（完全基于表格字段）
    passed_screening = sum(1 for c in candidates if c.get("简历状态") == "通过")
    doubtful = sum(1 for c in candidates if c.get("简历状态") == "存疑")
    invited_sent = sum(1 for c in candidates if c.get("邀请面试") is True)
    interview_accepted = sum(1 for c in candidates if c.get("是否接受面试") == "接受")
    interview_passed = sum(1 for c in candidates if c.get("面试结果") == "通过")
    interview_failed = sum(1 for c in candidates if c.get("面试结果") == "淘汰")
    offer_accepted = sum(1 for c in candidates if c.get("offer结果") == "接受")
    offer_rejected = sum(1 for c in candidates if c.get("offer结果") == "拒绝")

    # 第一行指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 投递简历", total)
    with col2:
        st.metric("✅ 简历通过", passed_screening)
    with col3:
        st.metric("❓ 存疑", doubtful)
    with col4:
        st.metric("📞 发出邀请", invited_sent)

    # 第二行指标
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("🎉 面试通过", interview_passed)   # 名称按你的要求：面试通过・人 但这里简单显示
    with col6:
        st.metric("📉 面试淘汰", interview_failed)
    with col7:
        st.metric("💼 接受 Offer", offer_accepted)
    with col8:
        st.metric("🚫 拒绝 Offer", offer_rejected)

    st.caption("数据自动联动：投递→简历通过→发出邀请→接受邀请→面试结果→offer结果")