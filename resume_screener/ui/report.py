# ui/report.py (仅调整列顺序：面试时间移到是否接受面试和面试结果之间)
import streamlit as st
import pandas as pd
from datetime import datetime
from config.defaults import save_data
import os
import io

ATTACH_DIR = "attachments"
os.makedirs(ATTACH_DIR, exist_ok=True)

def render_report(company, job):
    st.header("👥 人才招聘看板")
    if not company or not job:
        st.info("请先在左侧选择公司和岗位")
        return

    if "upload_counter" not in st.session_state:
        st.session_state.upload_counter = 0
    if "table_refresh_counter" not in st.session_state:
        st.session_state.table_refresh_counter = 0

    candidates = st.session_state.data["companies"][company]["jobs"][job].get("candidates", [])
    if not candidates:
        st.info("暂无候选人，请先上传简历分析")
        return

    candidates = sorted(candidates, key=lambda x: x.get("匹配度评分", 0), reverse=True)

    for c in candidates:
        if "上传时间" not in c:
            c["上传时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if "邀请面试" not in c:
            c["邀请面试"] = False
        if "是否接受面试" not in c:
            c["是否接受面试"] = ""
        if "面试结果" not in c:
            c["面试结果"] = ""
        if "offer结果" not in c:
            c["offer结果"] = ""
        if "面试时间" not in c:
            c["面试时间"] = None
        if "来源渠道" not in c:
            c["来源渠道"] = "boss直聘"
        if "电话" not in c:
            c["电话"] = ""
        if "邮箱" not in c:
            c["邮箱"] = ""
        if "标签" not in c:
            c["标签"] = ""
        if "备注" not in c:
            c["备注"] = ""
        if "附件路径" not in c:
            c["附件路径"] = ""
        if "附件" not in c:
            c["附件"] = ""
        if "追问问题" in c and isinstance(c["追问问题"], list):
            c["追问问题"] = "\n".join([f"{i+1}. {q}" for i, q in enumerate(c["追问问题"])])
        elif "追问问题" not in c:
            c["追问问题"] = ""
        if "完整报告" not in c:
            c["完整报告"] = ""

        if isinstance(c["面试时间"], str):
            try:
                c["面试时间"] = pd.to_datetime(c["面试时间"])
            except:
                c["面试时间"] = None

    df = pd.DataFrame(candidates)

    status_filter = st.multiselect("按状态筛选", options=df["简历状态"].unique(), default=df["简历状态"].unique())
    filtered_df = df[df["简历状态"].isin(status_filter)]

    sort_options = ["匹配度评分", "上传时间"]
    sort_by = st.selectbox("排序依据", sort_options)
    ascending = st.checkbox("升序", False)
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # 附件上传
    st.markdown("**📎 为候选人上传简历附件**")
    col_upload1, col_upload2 = st.columns([1, 2])
    with col_upload1:
        candidate_names = filtered_df["姓名"].tolist()
        selected_upload_name = st.selectbox("选择候选人", candidate_names, key="upload_select")
    with col_upload2:
        upload_key = f"file_uploader_{st.session_state.upload_counter}"
        uploaded_file = st.file_uploader("选择文件 (PDF/DOCX)", type=["pdf", "docx"], key=upload_key, label_visibility="collapsed")
        if uploaded_file is not None and selected_upload_name:
            idx = next((i for i, c in enumerate(candidates) if c["姓名"] == selected_upload_name), None)
            if idx is not None:
                safe_name = f"{company}_{job}_{selected_upload_name}_{uploaded_file.name}"
                file_path = os.path.join(ATTACH_DIR, safe_name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                candidates[idx]["附件路径"] = file_path
                candidates[idx]["附件"] = uploaded_file.name
                st.session_state.data["companies"][company]["jobs"][job]["candidates"] = candidates
                save_data(st.session_state.username, st.session_state.data)
                st.session_state.upload_counter += 1
                st.session_state.table_refresh_counter += 1
                st.success(f"✅ 已上传附件：{uploaded_file.name} 已关联到 {selected_upload_name}")
                st.rerun()

    # 打开附件
    st.markdown("**📂 打开附件**")
    col_open1, col_open2 = st.columns([1, 2])
    with col_open1:
        selected_open_name = st.selectbox("选择候选人", candidate_names, key="open_select")
    with col_open2:
        if st.button("打开附件"):
            for c in candidates:
                if c["姓名"] == selected_open_name:
                    file_path = c.get("附件路径", "")
                    if file_path and os.path.exists(file_path):
                        os.startfile(file_path)
                        st.success(f"正在打开 {os.path.basename(file_path)}")
                    else:
                        st.warning(f"候选人 {selected_open_name} 没有附件，请先上传。")
                    break

    # 可编辑表格（列顺序调整：面试时间移到是否接受面试和面试结果之间）
    display_df = filtered_df.copy()
    display_df.insert(0, "选择", False)
    # 定义列顺序（关键修改）
    display_columns = [
        "选择", "姓名", "附件", "简历状态", "匹配度评分", "上传时间",
        "HR专业总结", "完整报告", "追问问题",
        "邀请面试", "是否接受面试", "面试时间", "面试结果", "offer结果",
        "来源渠道", "电话", "邮箱", "标签", "备注"
    ]
    for col in display_columns:
        if col not in display_df.columns:
            if col in ["选择", "邀请面试"]:
                display_df[col] = False
            else:
                display_df[col] = ""

    table_key = f"data_editor_{st.session_state.table_refresh_counter}"
    edited_df = st.data_editor(
        display_df[display_columns],
        use_container_width=True,
        column_config={
            "选择": st.column_config.CheckboxColumn("选择", default=False, width="small"),
            "HR专业总结": st.column_config.TextColumn(width="medium"),
            "完整报告": st.column_config.TextColumn("完整报告", width="large"),
            "追问问题": st.column_config.TextColumn(width="medium"),
            "邀请面试": st.column_config.CheckboxColumn("邀请面试", default=False),
            "是否接受面试": st.column_config.SelectboxColumn("是否接受面试", options=["", "接受", "放弃"]),
            "面试时间": st.column_config.DatetimeColumn("面试时间", format="YYYY-MM-DD HH:mm", step=30),
            "面试结果": st.column_config.SelectboxColumn("面试结果", options=["", "通过", "淘汰"]),
            "offer结果": st.column_config.SelectboxColumn("offer结果", options=["", "接受", "拒绝"]),
            "来源渠道": st.column_config.SelectboxColumn("来源渠道", options=["boss直聘", "内推", "猎头", "自投", "其他"]),
            "标签": st.column_config.TextColumn("标签"),
            "备注": st.column_config.TextColumn("备注"),
            "上传时间": st.column_config.TextColumn("上传时间")
        },
        hide_index=True,
        num_rows="dynamic",
        key=table_key
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 保存所有修改"):
            save_df = edited_df.drop(columns=["选择"], errors='ignore')
            updated_candidates = save_df.to_dict("records")
            for new_c in updated_candidates:
                old_c = next((c for c in candidates if c["姓名"] == new_c["姓名"]), None)
                if old_c:
                    new_c["附件路径"] = old_c.get("附件路径", "")
                    new_c["附件"] = old_c.get("附件", "")
                else:
                    new_c["附件路径"] = ""
                    new_c["附件"] = ""
                if "面试时间" in new_c and isinstance(new_c["面试时间"], (pd.Timestamp, datetime)):
                    new_c["面试时间"] = new_c["面试时间"].strftime("%Y-%m-%d %H:%M")
                else:
                    new_c["面试时间"] = None
            st.session_state.data["companies"][company]["jobs"][job]["candidates"] = updated_candidates
            save_data(st.session_state.username, st.session_state.data)
            st.success("已保存所有修改")
            st.rerun()
    with col_btn2:
        if st.button("🗑️ 删除选中"):
            selected_rows = edited_df[edited_df["选择"] == True]
            if not selected_rows.empty:
                selected_names = selected_rows["姓名"].tolist()
                new_candidates = [c for c in candidates if c["姓名"] not in selected_names]
                st.session_state.data["companies"][company]["jobs"][job]["candidates"] = new_candidates
                save_data(st.session_state.username, st.session_state.data)
                st.session_state.table_refresh_counter += 1
                st.success(f"已删除 {len(selected_names)} 名候选人")
                st.rerun()
            else:
                st.warning("请先在表格最左侧复选框勾选要删除的候选人")

    if st.button("📎 导出当前数据为Excel"):
        export_df = edited_df.drop(columns=["选择"], errors='ignore')
        if "面试时间" in export_df.columns:
            export_df["面试时间"] = export_df["面试时间"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if pd.notnull(x) else "")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name="候选人列表", index=False)
        st.download_button("下载Excel", data=output.getvalue(), file_name=f"候选人_{st.session_state.data.get('last_update', '')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")