import streamlit as st
import numpy as np
import joblib
import os
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import speech_recognition as sr
import unicodedata
from streamlit_option_menu import option_menu

# ---------------------------- Load Models ----------------------------
model = joblib.load("personality_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# ---------------------------- Helper Data ----------------------------
personality_data = {
    "Extrovert": {
        "desc": "You are social, outgoing, and energized by being around people.",
        "tip": "Engage in team-based projects to amplify your strengths.",
        "quote": "The more you praise and celebrate your life, the more there is in life to celebrate.",
        "jobs": ["Public Speaker", "Sales Manager", "Team Lead"]
    },
    "Introvert": {
        "desc": "You enjoy solitude, deep thoughts, and recharge by spending time alone.",
        "tip": "Leverage your focus and depth in fields requiring attention to detail.",
        "quote": "Silence is only frightening to people who are compulsively verbalizing.",
        "jobs": ["Writer", "Researcher", "Software Developer"]
    },
    "Leader": {
        "desc": "You take initiative, guide others, and enjoy managing responsibilities.",
        "tip": "Continue improving your communication and delegation skills.",
        "quote": "Leadership is not about being in charge. It's about taking care of those in your charge.",
        "jobs": ["Project Manager", "Entrepreneur", "HR Head"]
    },
    "Thinker": {
        "desc": "You are analytical, curious, and enjoy deep understanding.",
        "tip": "Apply your problem-solving in research or tech-heavy roles.",
        "quote": "The important thing is not to stop questioning. Curiosity has its own reason for existing.",
        "jobs": ["Scientist", "Data Analyst", "Philosopher"]
    }
}

# ---------------------------- PDF Utilities ----------------------------
def clean(text):
    return ''.join(c for c in text if unicodedata.category(c)[0] != 'C' and ord(c) < 128)

def generate_pdf(user_name, text_input, top_trait, scores, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(180, 10, txt="Personality Mix Analyzer Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(180, 10, txt=f"Name: {clean(user_name)}", ln=True)
    pdf.cell(180, 10, txt=f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(180, 10, clean(f"Input Summary:\n{text_input}"))
    pdf.ln(5)
    pdf.cell(180, 10, txt=f"Top Trait: {clean(top_trait)}", ln=True)
    pdf.multi_cell(180, 10, clean(f"Explanation: {data['desc']}"))
    pdf.multi_cell(180, 10, clean(f"Tip: {data['tip']}"))
    pdf.multi_cell(180, 10, clean(f"Quote: {data['quote']}"))
    pdf.multi_cell(180, 10, clean(f"Recommended Roles: {', '.join(data['jobs'])}"))
    pdf.ln(5)
    pdf.cell(180, 10, txt="Confidence Scores:", ln=True)
    for trait, score in scores.items():
        pdf.cell(180, 10, txt=f"{trait}: {score * 100:.2f}%", ln=True)
    pdf.ln(10)
    pdf.cell(180, 10, txt="Designed with love by Pragati Tripathi", ln=True, align="C")
    filename = f"report_{user_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(os.getcwd(), filename)
    pdf.output(path)
    return path

# ---------------------------- Chart ----------------------------
def show_radar_chart(scores):
    labels = list(scores.keys()) + [list(scores.keys())[0]]
    values = list(scores.values()) + [list(scores.values())[0]]
    fig = go.Figure(go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(fig)

# ---------------------------- Speech Input ----------------------------
def get_speech_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙 Speak now...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return ""

# ---------------------------- Main UI ----------------------------
st.set_page_config(page_title="Personality Analyzer", layout="centered")
selected = option_menu(None, ["Analyze", "History", "About"],
    icons=['person-bounding-box', 'clock-history', 'info-circle'],
    default_index=0, orientation="horizontal")

if selected == "Analyze":
    st.title("🧠 Personality Mix Analyzer")
    user_name = st.text_input("👤 Enter your name:")
    input_method = st.radio("🎯 Choose input method:", ["📝 Type", "🎙 Speak"])
    user_input = ""
    if input_method == "📝 Type":
        user_input = st.text_area("✍️ Write something about yourself (4–5 lines):")
    elif input_method == "🎙 Speak":
        if st.button("🎤 Start Recording"):
            user_input = get_speech_input()
            st.success(f"You said: {user_input}")

    if st.button("🔍 Analyze Personality"):
        if not user_name or not user_input.strip():
            st.warning("Please enter your name and description.")
        else:
            X = vectorizer.transform([user_input])
            probs = model.predict_proba(X)[0]
            classes = model.classes_
            scores = dict(zip(classes, probs * 100))
            top_trait = max(scores, key=scores.get)
            data = personality_data[top_trait]

            st.subheader(f"📚 Top Trait: {top_trait}")
            st.write(data["desc"])
            st.write(f"💬 Quote: *{data['quote']}*")
            st.write(f"💡 Tip: {data['tip']}")
            st.write(f"👔 Suggested Roles: {', '.join(data['jobs'])}")

            st.subheader("📊 Confidence Scores:")
            for trait, score in scores.items():
                st.write(f"{trait}: {score:.2f}%")
                st.progress(score / 100)

            st.subheader("📈 Radar Chart Overview:")
            show_radar_chart(scores)

            path = generate_pdf(user_name, user_input, top_trait, scores, data)
            with open(path, "rb") as file:
                st.download_button("📄 Download Report as PDF", data=file, file_name=os.path.basename(path), mime="application/pdf")

            # Save history
            df_new = pd.DataFrame([{
                "Name": user_name,
                "Text": user_input,
                "Top Trait": top_trait,
                "Date": datetime.now().strftime('%d-%m-%Y %H:%M')
            }])
            history_path = "prediction_history.csv"
            if os.path.exists(history_path):
                df_old = pd.read_csv(history_path)
                df_all = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df_all = df_new
            df_all.to_csv(history_path, index=False)
            st.success("✅ Analysis saved successfully!")

elif selected == "History":
    st.title("🕓 Past Predictions")
    history_path = "prediction_history.csv"
    if os.path.exists(history_path):
        df = pd.read_csv(history_path)
        st.dataframe(df[::-1])
    else:
        st.info("No history found.")

elif selected == "About":
    st.title("ℹ️ About This App")
    st.markdown("""
    This app analyzes user-written or spoken descriptions to predict personality traits
    based on machine learning. It includes PDF reports, role suggestions, and radar charts.

    **Developed by:** Pragati Tripathi  
    **Built with:** Streamlit, scikit-learn, Python, FPDF, Plotly  
    **Version:** Final Showcase
    """)

st.markdown("---")
st.markdown("<center><small>🚀 Designed by Pragati • All Rights Reserved</small></center>", unsafe_allow_html=True)
