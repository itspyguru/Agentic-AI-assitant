import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel
from services.pdf_parser import extract_pdf_text
from services.resume_extractor import clean_resume_text
from chains.ats_chain import analyze_resume_chain
from chains.skill_chain import extract_skills_from_resume_chain
from chains.interview_chain import generate_question_chain

import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview")

SECTIONS = ["ATS Analysis", "Skills", "Interview"]

for key in ("resume_text", "ats", "skills", "source_file","current_question"):
    st.session_state.setdefault(key, None)
for key in ("questions", "answers", "evaluations"):
    st.session_state.setdefault(key, [])
if "total_score" not in st.session_state:
    st.session_state.total_score = 0


def run_analysis(cleaned_text: str):
    ats_chain = analyze_resume_chain(cleaned_text, llm)
    skill_chain = extract_skills_from_resume_chain(cleaned_text, llm)
    parallel_chain = RunnableParallel(ats=ats_chain, skills=skill_chain)
    result = parallel_chain.invoke({})
    st.session_state.ats = result["ats"]
    st.session_state.skills = result["skills"]


def render_ats(ats):
    st.header("ATS Analysis")
    st.metric("ATS Score", ats.ats_score)

    st.subheader("Strengths")
    for item in ats.strengths:
        st.write(f"✅ {item}")

    st.subheader("Weaknesses")
    for item in ats.weaknesses:
        st.write(f"❌ {item}")

    st.subheader("Missing Keywords")
    for item in ats.missing_keywords:
        st.write(f"⚠️ {item}")

    st.subheader("Improvements")
    for item in ats.improvements:
        st.write(f"💡 {item}")

    st.subheader("Summary")
    st.write(ats.summary)


def render_skills(skills_result):
    st.header("Skills Overview")

    if skills_result.candidate_name:
        st.markdown(f"**Candidate:** {skills_result.candidate_name}")
    if skills_result.target_role:
        st.markdown(f"**Target Role:** {skills_result.target_role}")

    st.subheader("Profile Summary")
    st.write(skills_result.extraction_summary)

    st.subheader("Skills by Category")
    skill_groups = {
        "Programming Languages": skills_result.skills.programming_languages,
        "Frameworks & Libraries": skills_result.skills.frameworks_and_libraries,
        "Databases": skills_result.skills.databases,
        "Cloud & DevOps": skills_result.skills.cloud_and_devops,
        "Tools & Platforms": skills_result.skills.tools_and_platforms,
        "AI & ML": skills_result.skills.ai_and_ml,
        "Domains & Concepts": skills_result.skills.domains_and_concepts,
        "APIs & Protocols": skills_result.skills.apis_and_protocols,
    }
    for group_name, items in skill_groups.items():
        if not items:
            continue
        with st.expander(f"{group_name} ({len(items)})"):
            for skill in items:
                st.markdown(
                    f"- **{skill.name}** — "
                    f"`{skill.confidence.value}` · `{skill.proficiency_signal.value}`  \n"
                    f"  _{skill.evidence}_"
                )

    if skills_result.interview_focus_areas:
        st.subheader("Interview Focus Areas")
        for focus in skills_result.interview_focus_areas:
            st.markdown(
                f"🎯 **{focus.skill}** (`{focus.suggested_depth.value}`)  \n"
                f"{focus.reason}"
            )

    if skills_result.skills_flat_list:
        st.subheader("All Skills")
        st.markdown(" ".join(f"`{s}`" for s in skills_result.skills_flat_list))

def render_questions():
    if st.button("Start Mock Interview"):
        st.session_state.questions = []
        question = generate_question_chain(name=st.session_state.skills.candidate_name,
                role=st.session_state.skills.target_role,
                skills=st.session_state.skills.skills_flat_list,
                previous_questions=[],
                llm=llm).invoke({})
        st.session_state.current_question = question
        st.session_state.questions.append(question)

    if st.session_state.current_question:
        st.subheader("Interview Question", st.session_state.current_question.difficulty)
        st.info(st.session_state.current_question)

        answer = st.text_area("Your Answer")
        if st.button("Submit Answer"):
            st.session_state.answers.append(answer)
            next_question = generate_question_chain(
                name=st.session_state.skills.candidate_name,
                role=st.ession_state.skills.target_role,
                skills=st.session_state.skills.skills_flat_list,
                previous_questions=st.session_state.questions,
                llm=llm
            ).invoke({})
            st.session_state.current_question = next_question
            st.session_state.questions.append(next_question)

            st.rerun()


def main():
    st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

    with st.sidebar:
        st.title("AI Resume Analyzer")
        uploaded_file = st.file_uploader("Upload a pdf file", type=["pdf"])

        if uploaded_file and uploaded_file.name != st.session_state.source_file:
            with st.spinner("Extracting Resume..."):
                raw_text = extract_pdf_text(uploaded_file)
                cleaned_text = clean_resume_text(raw_text)
            if not cleaned_text:
                st.error("Could not extract text from PDF")
                return
            st.session_state.resume_text = cleaned_text
            st.session_state.source_file = uploaded_file.name
            with st.spinner("Analyzing Resume..."):
                run_analysis(cleaned_text)
            st.success("Analysis complete")

        section = st.radio("Section", SECTIONS, disabled=st.session_state.ats is None)

    if st.session_state.ats is None:
        st.title("AI Resume ATS Analyzer")
        st.info("Upload a PDF resume from the sidebar to get started.")
        return

    if section == "ATS Analysis":
        render_ats(st.session_state.ats)
    elif section == "Skills":
        render_skills(st.session_state.skills)
    elif section == "Interview":
        render_questions()


main()
