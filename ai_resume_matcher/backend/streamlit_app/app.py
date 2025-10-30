# streamlit_app/app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.title("AI Resume Matcher — Demo")
title = st.text_input("Job title (optional)")
desc = st.text_area("Job description", height=200)
if st.button("Match Resumes"):
    payload = {"title": title, "description": desc}
    res = requests.post(f"{API_URL}/match_job/", json=payload).json()
    for r in res["results"]:
        st.subheader(f"{r['filename']} — {int(r['score']*100)}%")
        st.write("Resume skills:", r["resume_skills"])
        st.write("Missing skills:", r["missing_skills"])
