import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import os
import qrcode

try:
    from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
except:
    webrtc_streamer = None

# ---------------- MBTI Mapping ---------------- #
def map_to_mbti(traits):
    E = 'E' if traits['Extraversion'] > 50 else 'I'
    N = 'N' if traits['Openness'] > 50 else 'S'
    F = 'F' if traits['Agreeableness'] > 50 else 'T'
    J = 'J' if traits['Conscientiousness'] > 50 else 'P'
    return E + N + F + J

mbti_stats = {
    "INFJ": 1.5, "ENFJ": 2.5, "INTJ": 2, "ENTJ": 2,
    "INFP": 4.5, "ENFP": 8, "ISTJ": 12, "ESTJ": 9,
    "ISFJ": 13, "ESFJ": 12, "ISTP": 5, "ESTP": 4.5,
    "ISFP": 9, "ESFP": 8.5, "INTP": 3, "ENTP": 4
}

famous_mbti = {
    "INFJ": "Oprah Winfrey", "ENFJ": "Barack Obama",
    "INTJ": "Elon Musk", "ENTJ": "Steve Jobs",
    "INFP": "Shakespeare", "ENFP": "Robin Williams",
    "ISTJ": "Natalie Portman", "ESTJ": "Judge Judy",
    "ISFJ": "Mother Teresa", "ESFJ": "Taylor Swift",
    "ISTP": "Clint Eastwood", "ESTP": "Madonna",
    "ISFP": "Britney Spears", "ESFP": "Elton John",
    "INTP": "Albert Einstein", "ENTP": "Tom Hanks"
}

# ---------------- UI Setup ---------------- #
st.set_page_config(page_title="Personality Mix Analyzer", layout="wide")
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #e0c3fc, #8ec5fc);
    }
    .reportview-container {
        background: linear-gradient(135deg, #e0c3fc, #8ec5fc);
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #4B0082;'>🧬 Personality Mix Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Predict your personality traits using text or voice input</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- Sidebar ---------------- #
with st.sidebar:
    st.markdown("## About This App")
    st.info("This app predicts personality traits based on your input using Machine Learning.")
    st.markdown("Built by **Pragati Tripathi**")
    language = st.radio("Choose Language", ['English', 'Hindi'])
    st.markdown("---")
    show_history = st.checkbox("Show Prediction History")

# ---------------- Input ---------------- #
user_name = st.text_input("Enter your name:")
user_input = st.text_area("Enter a paragraph about yourself:")

# ---------------- Voice Input (Optional) ---------------- #
if webrtc_streamer:
    st.markdown("🎤 Or record your voice input below:")
    webrtc_streamer(key="example")

# ---------------- Dummy ML Model ---------------- #
def predict_personality(text):
    return {
        "Openness": 70,
        "Conscientiousness": 65,
        "Extraversion": 55,
        "Agreeableness": 80,
        "Neuroticism": 35
    }

# ---------------- Explanation Generator ---------------- #
def generate_explanations(traits, lang="English"):
    messages = []
    for trait, value in traits.items():
        if lang == "English":
            if trait == "Openness":
                msg = f"You are {value}% open to new experiences."
            elif trait == "Conscientiousness":
                msg = f"You show {value}% responsibility and discipline."
            elif trait == "Extraversion":
                msg = f"You exhibit {value}% sociability."
            elif trait == "Agreeableness":
                msg = f"You reflect {value}% kindness and cooperation."
            elif trait == "Neuroticism":
                msg = f"You have {value}% emotional instability."
        else:
            if trait == "Openness":
                msg = f"आप नई चीज़ों के लिए {value}% खुले विचारों वाले हैं।"
            elif trait == "Conscientiousness":
                msg = f"आप {value}% जिम्मेदार और अनुशासित हैं।"
            elif trait == "Extraversion":
                msg = f"आप {value}% मिलनसार हैं।"
            elif trait == "Agreeableness":
                msg = f"आप {value}% दयालु और सहयोगी हैं।"
            elif trait == "Neuroticism":
                msg = f"आपमें {value}% भावनात्मक चञ्चालता है।"
        messages.append(msg)
    return messages

# ---------------- Job Role Suggestions ---------------- #
def suggest_roles(traits):
    dominant_trait = max(traits, key=traits.get)
    if dominant_trait == "Openness":
        return ["Graphic Designer", "Writer", "Product Designer", "Innovation Strategist"]
    elif dominant_trait == "Conscientiousness":
        return ["Project Manager", "Data Analyst", "Quality Assurance", "Accountant"]
    elif dominant_trait == "Extraversion":
        return ["Sales Executive", "HR Manager", "Public Relations Officer", "Event Coordinator"]
    elif dominant_trait == "Agreeableness":
        return ["Teacher", "Psychologist", "Nurse", "Social Worker"]
    elif dominant_trait == "Neuroticism" and traits["Neuroticism"] < 40:
        return ["Researcher", "Doctor", "Engineer", "Software Developer"]
    else:
        return ["Consultant", "Generalist", "Content Creator"]

# ---------------- Quote Generator ---------------- #
def generate_tip(trait):
    tips = {
        "Openness": "Stay curious and keep exploring new ideas.",
        "Conscientiousness": "Your discipline can be your superpower.",
        "Extraversion": "Your energy is contagious! Use it wisely.",
        "Agreeableness": "Your kindness makes you a great team player.",
        "Neuroticism": "Practice mindfulness to handle stress effectively."
    }
    return tips.get(trait, "Be your best self!")

# ---------------- Chart ---------------- #
def show_chart(traits):
    labels = list(traits.keys())
    values = list(traits.values())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='skyblue', alpha=0.4)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    st.pyplot(fig)

# ---------------- PDF Generator ---------------- #
def generate_pdf_report(name, traits, explanations, roles, quotes, mbti, percent, famous):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Personality Mix Analyzer Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d %B %Y')}", ln=True)

    pdf.ln(5)
    for trait, score in traits.items():
        pdf.cell(200, 10, txt=f"{trait}: {score}%", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"MBTI Personality: {mbti}", ln=True)
    pdf.cell(200, 10, txt=f"Global Population: {percent}%", ln=True)
    pdf.cell(200, 10, txt=f"Famous Personality: {famous}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Trait Explanations:", ln=True)
    for line in explanations:
        safe_line = line.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(180, 10, txt=safe_line)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Suggested Roles:", ln=True)
    for role in roles:
        safe_role = role.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(200, 10, txt=f"- {safe_role}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Tips & Quotes:", ln=True)
    for quote in quotes:
        safe_quote = quote.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(180, 10, txt=f"- {safe_quote}")

    qr = qrcode.make(f"https://your-resume-link-or-summary.com/{name}")
    qr_path = f"{name}_qr.png"
    qr.save(qr_path)
    pdf.image(qr_path, x=80, y=pdf.get_y()+5, w=50)

    path = f"{name}_personality_report.pdf"
    pdf.output(path)
    os.remove(qr_path)
    return path

# ---------------- History ---------------- #
def save_result(name, traits):
    df = pd.DataFrame([{"Name": name, "Date": datetime.now(), **traits}])
    if os.path.exists("history.csv"):
        df.to_csv("history.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("history.csv", index=False)

if show_history and os.path.exists("history.csv"):
    history_df = pd.read_csv("history.csv")
    st.subheader("Past Predictions")
    st.dataframe(history_df)

# ---------------- Predict Button ---------------- #
if st.button("Analyze Personality"):
    if user_input.strip() == "" or user_name.strip() == "":
        st.warning("Please enter both your name and a paragraph.")
    else:
        trait_mix = predict_personality(user_input)
        explanations = generate_explanations(trait_mix, language)
        roles = suggest_roles(trait_mix)
        tips = [generate_tip(trait) for trait in trait_mix]

        mbti_type = map_to_mbti(trait_mix)
        mbti_percent = mbti_stats.get(mbti_type, "N/A")
        famous_person = famous_mbti.get(mbti_type, "Unknown")

        st.success("Personality Analysis Complete!")
        st.balloons()

        st.subheader("Trait Breakdown:")
        for e in explanations:
            st.markdown(f"- {e}")

        st.markdown("### MBTI Personality Match:")
        st.markdown(f"🧠 You align with **{mbti_type}** personality.")
        st.markdown(f"🌍 Around **{mbti_percent}%** of people share this type.")
        st.markdown(f"🌟 Famous Match: **{famous_person}**")

        st.markdown("### Suitable Career Roles:")
        for r in roles:
            st.markdown(f"✅ {r}")

        st.markdown("### Personal Tips:")
        for t in tips:
            st.markdown(f"👉 {t}")

        show_chart(trait_mix)
        save_result(user_name, trait_mix)

        path = generate_pdf_report(user_name, trait_mix, explanations, roles, tips, mbti_type, mbti_percent, famous_person)
        with open(path, "rb") as f:
            st.download_button("Download Report (PDF)", data=f, file_name=path, mime="application/pdf")

# ---------------- Footer ---------------- #
st.markdown("---")
st.markdown("<p style='text-align: center;'>Made by <b>Pragati Tripathi</b> | 2025</p>", unsafe_allow_html=True)
