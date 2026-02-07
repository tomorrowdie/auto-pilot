import streamlit as st
from PIL import Image
import os
from pathlib import Path

# --- PATH SETTINGS ---
current_dir = Path(__file__).parent.resolve()
assets_dir = current_dir / "assets"
styles_dir = current_dir / "styles"

# Ensure directories exist
assets_dir.mkdir(exist_ok=True)
styles_dir.mkdir(exist_ok=True)

# Define file paths
css_file = styles_dir / "main.css"
profile_pic_file = next(assets_dir.glob('john_chin_photo.*'), None)
resume_file = assets_dir / "Resume_John_Chin_with_reference_20250107.pdf"
profile_file = assets_dir / "John_Chin_Self_Intro_and_Profile_20241119-1.pdf"

# --- GENERAL SETTINGS ---
PAGE_TITLE = "Digital CV | John Chin"
PAGE_ICON = ":wave:"
NAME = "John Chin"
DESCRIPTION = (
    "Visionary eCommerce strategist with 20+ years of global experience specializing "
    "in AI integration, digital marketing, and eCommerce platform optimization."
)
EMAIL = "chinhotak@gmail.com"
PHONE = "+852-60171279"
SOCIAL_MEDIA = {
    "LinkedIn": "https://www.linkedin.com/in/john-chin-81078682/",
    "Amazon Author Page": "https://www.amazon.com/author/angry-factory",
}
PROJECTS = {
    "Amazon Certified Trainer & Community Ambassador": (
        "Delivered licensed training modules across Greater China. "
        "Guest speaker for Helium10 and Amazon China/USA projects. "
        "Recognized as a top holiday seller for electronics and luxury items."
    ),
    "Shopify Fashion Brand Consultant": (
        "Optimized ad spend and listings to increase profitability by 67%. "
        "Improved engagement using analytics tools."
    ),
    "AI-Powered Learning Model for Amazon Sellers": (
        "Developed a Python model achieving 80% accuracy for actionable insights. "
        "Boosted organic sales via UGC strategies."
    ),
    "Panda Ocean Inc.": (
        "Managed eCommerce operations across USA, EU5, Canada, and Japan. "
        "Transitioned brands into successful Amazon Accelerator programs."
    ),
    "Amazon Ads Optimization": (
        "Lowered CPC from $1.5 to $0.5 using data-driven strategies."
    ),
}
CERTIFICATIONS = [
    "Amazon Certified Trainer & Ambassador",
    "AI, Business & the Future of Work Certification (Lund University)",
]
EDUCATION = [
    "BBA in Hotel Management (Columbus University, 2005)",
    "Social Media Marketing Program (British Columbia Institute of Technology, 2017)",
    "Ongoing Study: CS50's Artificial Intelligence with Python (Harvard University)",
]
VOLUNTEER_WORK = [
    "Business Advisor (HSBC x Junior Achievement HK): Mentored high school students on entrepreneurship and financial literacy."
]

def load_profile_picture():
    try:
        if profile_pic_file:
            return Image.open(profile_pic_file)
        else:
            st.warning(f"Profile picture not found in: {assets_dir}")
            return None
    except Exception as e:
        st.error(f"Error loading profile picture: {e}")
        print(f"Debug - profile_pic_file: {profile_pic_file}")  # Debug line
        return None

def load_css():
    try:
        if css_file.exists():
            with open(css_file) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        else:
            st.warning(f"CSS file not found at: {css_file}")
    except Exception as e:
        st.error(f"Error loading CSS: {e}")

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)

# Load CSS and profile picture
load_css()
profile_pic = load_profile_picture()

# --- HERO SECTION ---
col1, col2 = st.columns(2, gap="small")
with col1:
    if profile_pic:
        st.image(profile_pic, width=230)

with col2:
    st.title(NAME)
    st.write(DESCRIPTION)
    st.write(f":email: {EMAIL}")
    st.write(f":phone: {PHONE}")

# --- LOAD AND SHOW RESUME DOWNLOAD ---
if resume_file.exists():
    with open(resume_file, 'rb') as pdf_file:
        PDFbyte = pdf_file.read()
        st.download_button(
            label="Download Resume",
            data=PDFbyte,
            file_name=resume_file.name,
            mime="application/pdf"
        )

# --- SOCIAL MEDIA LINKS ---
st.header("Connect with Me")
SOCIAL_MEDIA = {
    "LinkedIn": "https://www.linkedin.com/in/john-chin-81078682/",
    "Amazon Author Page": "https://www.amazon.com/author/angry-factory"
}

cols = st.columns(len(SOCIAL_MEDIA))
for index, (platform, link) in enumerate(SOCIAL_MEDIA.items()):
    cols[index].write(f"[{platform}]({link})")



# --- PROJECTS ---
st.header("Key Projects/Experience Highlights")
for project, details in PROJECTS.items():
    st.subheader(f"🏆 {project}")
    st.write(details)

# --- CERTIFICATIONS ---
st.header("Certifications")
for cert in CERTIFICATIONS:
    st.write(f"- {cert}")

# --- EDUCATION ---
st.header("Education")
for edu in EDUCATION:
    st.write(f"- {edu}")

# --- VOLUNTEER WORK ---
st.header("Volunteer Work")
for work in VOLUNTEER_WORK:
    st.write(f"- {work}")