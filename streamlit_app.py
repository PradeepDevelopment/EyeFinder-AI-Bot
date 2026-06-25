import streamlit as st
import pandas as pd
import requests
import re
import time
import json
import urllib.parse
from datetime import datetime
from io import BytesIO
from duckduckgo_search import DDGS
import pydeck as pdk

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="EyeFinder AI - Futuristic Healthcare Intelligence Platform",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GOOGLE API IMPORTS
# ==========================================
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REFRESH_TOKEN = st.secrets["google"]["refresh_token"]
MAPS_API_KEY = st.secrets["google"]["maps_api_key"]

DRIVE_FOLDER_ID = "1EFLBpua66K0wsJ7ZURH03SytJrTeBLQP"
OSM_USER_AGENT = "EyeFinder_Scraper/1.0 (contact@eyefinder.com)"

# High-speed Overpass Endpoints
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

CITY_COORDS_DB = {
    "Patna": (25.5941, 85.1376), "Jaipur": (26.9124, 75.7873), "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946), "Gurgaon": (28.4595, 77.0266), "Delhi": (28.7041, 77.1025),
    "New Delhi": (28.6139, 77.2090), "Bhubaneswar": (20.2961, 85.8245), "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707), "Hyderabad": (17.3850, 78.4867), "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567), "Lucknow": (26.8467, 80.9462), "Chandigarh": (30.7333, 76.7794),
    "Bhopal": (23.2599, 77.4126), "Indore": (22.7196, 75.8577), "Noida": (28.5355, 77.3910)
}

# ALL INDIAN STATES & MAJOR CITIES
LOCATION_MATRIX = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati", "Kurnool", "Rajamahendravaram"],
    "Arunachal Pradesh": ["Itanagar", "Tawang", "Naharlagun", "Pasighat"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Nagaon", "Tezpur"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga", "Purnia", "Chhapra", "Begusarai", "Arrah"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Rajnandgaon", "Raigarh"],
    "Goa": ["Panaji", "Vasco da Gama", "Margao", "Mapusa", "Ponda"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar", "Junagadh"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula"],
    "Himachal Pradesh": ["Shimla", "Dharamshala", "Mandi", "Solan", "Manali", "Kullu"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar", "Hazaribagh"],
    "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Hubli", "Belgaum", "Dharwad", "Gulbarga", "Davangere"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Kannur"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar", "Rewa", "Satna"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad", "Navi Mumbai", "Solapur", "Manmad", "Kolhapur", "Amravati"],
    "Manipur": ["Imphal", "Thoubal", "Kakching", "Ukhrul"],
    "Meghalaya": ["Shillong", "Tura", "Nongstoin", "Jowai"],
    "Mizoram": ["Aizawl", "Lunglei", "Saiha", "Champhai"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung", "Tuensang"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", "Puri", "Balasore"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali", "Pathankot"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer", "Alwar", "Bhilwara", "Sikar"],
    "Sikkim": ["Gangtok", "Namchi", "Geyzing", "Mangan"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tiruppur", "Erode", "Vellore", "Thoothukudi"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Ramagundam"],
    "Tripura": ["Agartala", "Udaipur", "Dharmanagar", "Kailashahar"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Ghaziabad", "Agra", "Varanasi", "Meerut", "Prayagraj", "Gorakhpur", "Mathura", "Bareilly", "Aligarh", "Moradabad"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Rishikesh"],
    "West Bengal": ["Kolkata", "Howrah", "Darjeeling", "Siliguri", "Asansol", "Durgapur", "Kharagpur", "Burdwan", "Malda"]
}
LOCATION_MATRIX = {state: sorted(cities) for state, cities in sorted(LOCATION_MATRIX.items())}

SEARCH_CATEGORIES = [
    "Eye Hospitals",
    "Eye Clinics",
    "Ophthalmologists",
    "Lasik & Refractive Surgery Centers",
    "Retina & Cornea Speciality Centers",
    "Optical Stores",
    "Eye Doctors",
    "Optometrists",
    "Opticians",
    "Cataract Surgeons",
    "Eye Care Centers",
    "Spectacle Shops"
]

OSM_AMENITY_MAPPING = {
    "Eye Hospitals": "hospital",
    "Eye Clinics": "clinic",
    "Ophthalmologists": "doctors",
    "Lasik & Refractive Surgery Centers": "clinic",
    "Retina & Cornea Speciality Centers": "hospital|clinic",
    "Optical Stores": "shop",
    "Eye Doctors": "doctors",
    "Optometrists": "doctors|clinic",
    "Opticians": "shop",
    "Cataract Surgeons": "doctors",
    "Eye Care Centers": "hospital|clinic",
    "Spectacle Shops": "shop"
}

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "scan_count" not in st.session_state:
    st.session_state.scan_count = 0
if "total_leads_found" not in st.session_state:
    st.session_state.total_leads_found = 0
if "scan_engine" not in st.session_state:
    st.session_state.scan_engine = "osm"
if "outreach_history" not in st.session_state:
    st.session_state.outreach_history = []
if "outreach_history_loaded" not in st.session_state:
    st.session_state.outreach_history_loaded = False
if "outreach_log_pending" not in st.session_state:
    st.session_state.outreach_log_pending = None

# ==========================================
# DYNAMIC CLINICAL THEMES CONFIGURATION
# ==========================================
THEMES = {
    "Retina Cyan (Dark HUD)": {
        "bg_gradient": "linear-gradient(135deg, #020617 0%, #070f22 50%, #0b152e 100%)",
        "primary_accent": "#06b6d4",
        "secondary_accent": "#3b82f6",
        "text_primary": "#f8fafc",
        "text_muted": "#94a3b8",
        "panel_bg": "rgba(13, 20, 35, 0.75)",
        "panel_border": "rgba(6, 182, 212, 0.25)",
        "btn_gradient": "linear-gradient(135deg, #0891b2 0%, #2563eb 100%)",
        "btn_hover_shadow": "rgba(6, 182, 212, 0.45)",
        "grid_color": "rgba(6, 182, 212, 0.025)",
        "badge_bg": "rgba(6, 182, 212, 0.08)",
        "badge_border": "rgba(6, 182, 212, 0.35)",
        "badge_color": "#22d3ee",
        "card_bg": "rgba(15, 23, 42, 0.75)",
        "card_hover_border": "rgba(6, 182, 212, 0.55)",
        "card_shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.55)",
        "glow_color_1": "rgba(6, 182, 212, 0.18)",
        "glow_color_2": "rgba(59, 130, 246, 0.12)"
    },
    "Quantum Violet (Dark HUD)": {
        "bg_gradient": "linear-gradient(135deg, #020617 0%, #0d0925 50%, #170b34 100%)",
        "primary_accent": "#a855f7",
        "secondary_accent": "#ec4899",
        "text_primary": "#f8fafc",
        "text_muted": "#c084fc",
        "panel_bg": "rgba(23, 15, 43, 0.75)",
        "panel_border": "rgba(168, 85, 247, 0.25)",
        "btn_gradient": "linear-gradient(135deg, #9333ea 0%, #db2777 100%)",
        "btn_hover_shadow": "rgba(168, 85, 247, 0.45)",
        "grid_color": "rgba(168, 85, 247, 0.025)",
        "badge_bg": "rgba(168, 85, 247, 0.08)",
        "badge_border": "rgba(168, 85, 247, 0.35)",
        "badge_color": "#d8b4fe",
        "card_bg": "rgba(24, 17, 47, 0.75)",
        "card_hover_border": "rgba(168, 85, 247, 0.55)",
        "card_shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.55)",
        "glow_color_1": "rgba(168, 85, 247, 0.18)",
        "glow_color_2": "rgba(236, 72, 153, 0.12)"
    },
    "Bio-Teal Intelligence (Dark HUD)": {
        "bg_gradient": "linear-gradient(135deg, #01070a 0%, #03141a 50%, #06232e 100%)",
        "primary_accent": "#14b8a6",
        "secondary_accent": "#10b981",
        "text_primary": "#ecfdf5",
        "text_muted": "#a7f3d0",
        "panel_bg": "rgba(8, 28, 36, 0.75)",
        "panel_border": "rgba(20, 184, 166, 0.25)",
        "btn_gradient": "linear-gradient(135deg, #0d9488 0%, #059669 100%)",
        "btn_hover_shadow": "rgba(20, 184, 166, 0.45)",
        "grid_color": "rgba(20, 184, 166, 0.025)",
        "badge_bg": "rgba(20, 184, 166, 0.08)",
        "badge_border": "rgba(20, 184, 166, 0.35)",
        "badge_color": "#5eead4",
        "card_bg": "rgba(9, 31, 40, 0.75)",
        "card_hover_border": "rgba(20, 184, 166, 0.55)",
        "card_shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.55)",
        "glow_color_1": "rgba(20, 184, 166, 0.18)",
        "glow_color_2": "rgba(16, 185, 129, 0.12)"
    }
}

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Retina Cyan (Dark HUD)"

theme_val = THEMES[st.session_state.app_theme]

# Injected CSS stylesheet based on active theme
st.markdown(f"""
<div class="stApp-grid-overlay"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;600&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
    
    :root {{
        --bg-gradient: {theme_val['bg_gradient']};
        --primary-accent: {theme_val['primary_accent']};
        --secondary-accent: {theme_val['secondary_accent']};
        --text-primary: {theme_val['text_primary']};
        --text-muted: {theme_val['text_muted']};
        --panel-bg: {theme_val['panel_bg']};
        --panel-border: {theme_val['panel_border']};
        --btn-gradient: {theme_val['btn_gradient']};
        --btn-hover-shadow: {theme_val['btn_hover_shadow']};
        --grid-color: {theme_val['grid_color']};
        --badge-bg: {theme_val['badge_bg']};
        --badge-border: {theme_val['badge_border']};
        --badge-color: {theme_val['badge_color']};
        --card-bg: {theme_val['card_bg']};
        --card-hover-border: {theme_val['card_hover_border']};
        --card-shadow: {theme_val['card_shadow']};
        --glow-color-1: {theme_val['glow_color_1']};
        --glow-color-2: {theme_val['glow_color_2']};
    }}

    /* Root and Page Background Styling */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background: var(--bg-gradient) !important;
        background-size: 400% 400% !important;
        animation: moveGradient 24s ease infinite !important;
        background-attachment: fixed !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* Hide default Streamlit elements (header, footer, menu, decorations) */
    [data-testid="stHeader"], header, footer, [data-testid="stFooter"], #MainMenu, [data-testid="stDecoration"] {{
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    
    [data-testid="stMainBlockContainer"], 
    [data-testid="stVerticalBlock"], 
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: transparent !important;
    }}
    
    /* Ensure all text labels and elements are visible */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stWidgetLabel"] {{
        color: var(--text-primary) !important;
        font-family: 'Outfit', sans-serif !important;
    }}
    
    @keyframes moveGradient {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    
    /* Digital Grid Overlay */
    .stApp-grid-overlay {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            linear-gradient(var(--grid-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: -2;
    }}
    
    /* Floating Glowing Nebulas on Body */
    body::before {{
        content: "";
        position: fixed;
        top: -15%; left: -15%;
        width: 60%; height: 60%;
        background: radial-gradient(circle, var(--glow-color-1) 0%, transparent 70%);
        pointer-events: none;
        z-index: -1;
        animation: floatGlow1 28s ease-in-out infinite alternate;
    }}
    
    body::after {{
        content: "";
        position: fixed;
        bottom: -20%; right: -15%;
        width: 70%; height: 70%;
        background: radial-gradient(circle, var(--glow-color-2) 0%, transparent 70%);
        pointer-events: none;
        z-index: -1;
        animation: floatGlow2 32s ease-in-out infinite alternate;
    }}
    
    @keyframes floatGlow1 {{
        0% {{ transform: translate(0, 0) scale(1); }}
        100% {{ transform: translate(15%, 10%) scale(1.15); }}
    }}
    
    @keyframes floatGlow2 {{
        0% {{ transform: translate(0, 0) scale(1); }}
        100% {{ transform: translate(-10%, -15%) scale(1.1); }}
    }}

    /* Custom SVG Eye Hero V2 Styling */
    .hero-container-v2 {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        margin: 15px 0 30px 0;
        padding: 30px;
        background: var(--panel-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--panel-border);
        border-radius: 20px;
        box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.03), var(--card-shadow);
        position: relative;
        overflow: hidden;
        min-height: 280px;
        animation: fadeIn 1.2s ease-out;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .hero-left-eye {{
        flex: 1.2;
        display: flex;
        align-items: center;
        justify-content: center;
        max-width: 380px;
        position: relative;
        z-index: 2;
    }}

    .detailed-eye-svg {{
        width: 100%;
        height: auto;
        filter: drop-shadow(0 0 12px var(--primary-accent));
    }}

    /* SVG rotational & detailed animations */
    .ring-outer {{
        transform-origin: 120px 125px;
        animation: rotateCW 20s linear infinite;
    }}

    .ring-middle {{
        transform-origin: 120px 125px;
        animation: rotateCCW 12s linear infinite;
    }}

    .iris-detailed {{
        transform-origin: 120px 125px;
        animation: pulseIris 4s ease-in-out infinite alternate;
    }}

    .scanner-sweep {{
        transform-origin: 120px 125px;
        animation: rotateCW 6s linear infinite;
    }}

    @keyframes rotateCW {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}

    @keyframes rotateCCW {{
        from {{ transform: rotate(360deg); }}
        to {{ transform: rotate(0deg); }}
    }}

    @keyframes pulseIris {{
        0% {{ transform: scale(0.95); opacity: 0.85; }}
        100% {{ transform: scale(1.02); opacity: 1; filter: drop-shadow(0 0 10px var(--primary-accent)); }}
    }}

    .hero-right-text {{
        flex: 1.5;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        z-index: 2;
        padding-left: 20px;
    }}

    .hero-title-v2 {{
        font-family: 'Orbitron', sans-serif !important;
        font-size: 3.4rem !important;
        font-weight: 900 !important;
        letter-spacing: 4px !important;
        margin: 0 !important;
        padding: 0 !important;
        background: linear-gradient(90deg, #ffffff 0%, var(--primary-accent) 50%, var(--secondary-accent) 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        position: relative;
        display: inline-block;
        animation: shine 8s linear infinite;
    }}

    /* Scanning line sliding down text */
    .hero-title-v2::after {{
        content: '';
        position: absolute;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--primary-accent), var(--secondary-accent), transparent);
        animation: scanLine 4s ease-in-out infinite;
        box-shadow: 0 0 10px var(--primary-accent);
    }}

    @keyframes scanLine {{
        0% {{ top: 0%; opacity: 0; }}
        10% {{ opacity: 1; }}
        90% {{ opacity: 1; }}
        100% {{ top: 100%; opacity: 0; }}
    }}

    @keyframes shine {{
        to {{ background-position: 200% center; }}
    }}

    .hero-tagline {{
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.4rem !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-top: 5px !important;
        margin-bottom: 8px !important;
        letter-spacing: 1px !important;
    }}

    .hero-links {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.95rem;
        color: var(--text-muted);
        letter-spacing: 2px;
        margin-bottom: 25px;
    }}

    .hero-links span {{
        color: var(--primary-accent);
        text-shadow: 0 0 5px rgba(6, 182, 212, 0.3);
    }}

    .vision-scan-btn {{
        display: inline-flex;
        align-items: center;
        gap: 15px;
        background: var(--btn-gradient);
        border: 1px solid rgba(255,255,255,0.15);
        color: #ffffff !important;
        font-family: 'Outfit', sans-serif;
        font-size: 0.95rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 12px 28px;
        border-radius: 30px;
        text-decoration: none !important;
        box-shadow: 0 6px 20px var(--btn-hover-shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .vision-scan-btn:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 30px var(--primary-accent);
        border-color: rgba(255,255,255,0.3);
    }}

    .scan-btn-icon {{
        display: inline-block;
        animation: pulseDot 1.5s infinite alternate;
    }}

    /* Vascular Pattern Background on the right */
    .vascular-pattern-container {{
        position: absolute;
        right: -10px;
        top: 0;
        bottom: 0;
        width: 320px;
        opacity: 0.25;
        pointer-events: none;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }}

    .vascular-svg {{
        height: 100%;
        width: auto;
        filter: drop-shadow(0 0 5px var(--primary-accent));
    }}

    /* Scan Progress pipeline HUD style */
    .scan-progress-hud {{
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: var(--card-shadow);
        animation: fadeIn 1s ease-out;
    }}

    .scan-progress-title {{
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 20px;
        font-size: 1.1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    .progress-pipeline {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        position: relative;
    }}

    .pipeline-step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        flex: 1;
        text-align: center;
        transition: all 0.3s ease;
        opacity: 0.35;
    }}

    .pipeline-step.active {{
        opacity: 1;
    }}

    .pipeline-step.active .step-icon {{
        background: rgba(6, 182, 212, 0.15);
        border-color: var(--primary-accent);
        color: var(--primary-accent);
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
        animation: pulseCircle 1.5s infinite alternate;
    }}

    .pipeline-step.completed {{
        opacity: 0.85;
    }}

    .pipeline-step.completed .step-icon {{
        background: rgba(16, 185, 129, 0.1);
        border-color: #10b981;
        color: #10b981;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.2);
    }}

    .step-icon {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid var(--panel-border);
        background: var(--card-bg);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        transition: all 0.3s ease;
    }}

    .step-label {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .pipeline-step.active .step-label {{
        color: var(--text-primary);
        font-weight: 600;
    }}

    .pipeline-connector {{
        height: 2px;
        background: var(--panel-border);
        flex-grow: 1;
        margin-bottom: 25px;
        position: relative;
        max-width: 80px;
        opacity: 0.3;
        transition: all 0.3s ease;
    }}

    .pipeline-connector.active {{
        background: linear-gradient(90deg, var(--primary-accent), var(--secondary-accent));
        opacity: 1;
        box-shadow: 0 0 5px var(--primary-accent);
    }}

    .pipeline-connector::after {{
        content: '>';
        position: absolute;
        right: -3px;
        top: -6px;
        color: var(--panel-border);
        font-size: 0.7rem;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }}

    .pipeline-connector.active::after {{
        color: var(--secondary-accent);
    }}

    @keyframes pulseCircle {{
        0% {{ transform: scale(0.96); box-shadow: 0 0 8px var(--primary-accent); }}
        100% {{ transform: scale(1.04); box-shadow: 0 0 20px var(--primary-accent); }}
    }}
    
    /* Glassmorphic Panel Styling & Streamlit Container Override */
    .glass-panel, 
    div[data-key="left_col_container"] div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-key="right_col_container"] div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-key="scanning_container"] div[data-testid="stVerticalBlockBorderWrapper"] {{ 
        background: var(--panel-bg) !important; 
        backdrop-filter: blur(16px) !important; 
        -webkit-backdrop-filter: blur(16px) !important; 
        border: 1px solid var(--panel-border) !important; 
        border-radius: 20px !important; 
        box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.03), var(--card-shadow) !important; 
        padding: 25px !important; 
        margin-bottom: 25px !important; 
        position: relative;
        z-index: 1;
    }}
    
    /* Medical Button Override */
    .stButton button, .stDownloadButton button,
    div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {{ 
        background: var(--btn-gradient) !important; 
        color: #ffffff !important; 
        font-family: 'Outfit', sans-serif !important; 
        font-weight: 700 !important; 
        letter-spacing: 1.5px; 
        border-radius: 10px !important; 
        border: 1px solid rgba(255,255,255,0.12) !important; 
        padding: 12px 28px !important; 
        box-shadow: 0 4px 20px var(--btn-hover-shadow) !important; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; 
        width: 100%; 
        text-transform: uppercase;
    }}
    
    .stButton button:hover, .stDownloadButton button:hover,
    div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {{ 
        box-shadow: 0 6px 30px var(--primary-accent) !important; 
        transform: translateY(-2px) !important; 
        border: 1px solid rgba(255,255,255,0.3) !important; 
    }}
    
    .stButton button:active, .stDownloadButton button:active,
    div[data-testid="stButton"] button:active, div[data-testid="stDownloadButton"] button:active {{
        transform: translateY(1px) !important;
    }}
    
    /* Divider */
    hr {{ 
        border: 0; 
        height: 1px; 
        background: linear-gradient(90deg, rgba(255,255,255,0) 0%, var(--panel-border) 50%, rgba(255,255,255,0) 100%); 
        margin: 30px 0; 
    }}
    
    /* Badges and labels */
    .status-badge {{ 
        display: inline-block; 
        padding: 6px 14px; 
        border-radius: 20px; 
        background: var(--badge-bg); 
        border: 1px solid var(--badge-border); 
        color: var(--badge-color); 
        font-weight: 700; 
        font-size: 0.8rem; 
        font-family: 'Outfit', sans-serif;
        letter-spacing: 1.2px;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.05);
    }}
    
    /* Sidebar Adaptations */
    [data-testid="stSidebar"] {{
        background-color: rgba(6, 9, 17, 0.95) !important;
        border-right: 1px solid var(--panel-border) !important;
    }}
    
    /* Style all native Streamlit inputs, selectboxes, multiselects, textareas, link buttons, tooltips, and dropdowns to have a white background and black text */
    div[data-testid="stLinkButton"] a,
    div[data-testid="stLinkButton"] a:hover,
    div[data-testid="stLinkButton"] a:active,
    div[data-testid="stTooltipContent"],
    div[role="tooltip"],
    div[data-baseweb="popover"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    ul[role="listbox"],
    li[role="option"] {{
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #000000 !important;
    }}

    /* Target all nested descendants within these elements to ensure text and SVGs are black */
    div[data-testid="stLinkButton"] a *,
    div[data-testid="stTooltipContent"] *,
    div[role="tooltip"] *,
    div[data-baseweb="popover"] *,
    div[data-baseweb="select"] *,
    div[data-baseweb="input"] *,
    div[data-baseweb="textarea"] *,
    ul[role="listbox"] *,
    li[role="option"] * {{
        color: #000000 !important;
        fill: #000000 !important;
    }}

    /* Fix placeholder text contrast (visible dark gray on white input background) */
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder,
    input::placeholder,
    textarea::placeholder {{
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
        opacity: 0.75 !important;
    }}
    
    div[data-baseweb="select"] > div:hover {{
        border-color: var(--primary-accent) !important;
    }}
    
    /* Tab customizations */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: var(--panel-bg);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid var(--panel-border);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        background-color: transparent !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--primary-accent) !important;
        background-color: rgba(6, 182, 212, 0.1) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: var(--text-primary) !important;
        background: var(--btn-gradient) !important;
        border: 1px solid var(--panel-border) !important;
        box-shadow: 0 0 15px var(--panel-border) !important;
    }}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(10, 15, 30, 0.1);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--panel-border);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-accent);
    }}

    /* Clinic Cards Grid UI */
    .clinic-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }}
    
    .clinic-card {{
        background: var(--card-bg) !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 14px !important;
        padding: 22px !important;
        box-shadow: var(--card-shadow) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 230px;
        position: relative;
        overflow: hidden;
    }}
    
    .clinic-card:hover {{
        transform: translateY(-5px) scale(1.02);
        border-color: var(--primary-accent) !important;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4), 0 0 20px rgba(6, 182, 212, 0.2) !important;
    }}
    
    .clinic-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: var(--btn-gradient);
    }}
    
    .clinic-card-header {{
        margin-bottom: 12px;
    }}
    
    .clinic-card-title {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.4;
        margin-bottom: 6px;
    }}
    
    .clinic-card-category {{
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 30px;
        background: var(--badge-bg);
        border: 1px solid var(--badge-border);
        color: var(--badge-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .clinic-card-body {{
        font-size: 0.85rem;
        color: var(--text-muted);
        line-height: 1.5;
        margin-bottom: 16px;
        flex-grow: 1;
    }}
    
    .clinic-card-detail {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 8px;
        gap: 6px;
    }}
    
    .clinic-card-detail-icon {{
        color: var(--primary-accent);
        font-size: 1rem;
        margin-top: 2px;
    }}
    
    .clinic-card-actions {{
        display: flex;
        gap: 8px;
        margin-top: auto;
    }}
    
    .clinic-btn {{
        flex: 1;
        text-align: center;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-decoration: none !important;
        font-family: 'Outfit', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }}
    
    .clinic-btn-wa {{
        background: rgba(37, 211, 102, 0.1);
        border: 1px solid rgba(37, 211, 102, 0.4);
        color: #25D366;
    }}
    .clinic-btn-wa:hover {{
        background: #25D366;
        color: #ffffff;
        box-shadow: 0 0 10px rgba(37, 211, 102, 0.4);
    }}
    
    .clinic-btn-map {{
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.4);
        color: var(--primary-accent);
    }}
    .clinic-btn-map:hover {{
        background: var(--primary-accent);
        color: #ffffff;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.4);
    }}
    
    .clinic-btn-call {{
        background: rgba(244, 63, 94, 0.1);
        border: 1px solid rgba(244, 63, 94, 0.4);
        color: #f43f5e;
    }}
    .clinic-btn-call:hover {{
        background: #f43f5e;
        color: #ffffff;
        box-shadow: 0 0 10px rgba(244, 63, 94, 0.4);
    }}

    /* ----------------------------------------------------
       FUTURISTIC SCI-FI HUD DASHBOARD STYLES
       ---------------------------------------------------- */
    .kpi-dashboard-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
        animation: fadeIn 1.2s ease-out;
    }}

    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--card-shadow);
    }}

    .kpi-card:hover {{
        transform: translateY(-5px);
        border-color: var(--primary-accent);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4), 0 0 15px rgba(6, 182, 212, 0.15);
    }}

    .kpi-card-inner {{
        display: flex;
        align-items: center;
        gap: 16px;
        position: relative;
        z-index: 2;
    }}

    .kpi-icon {{
        font-size: 2.2rem;
        filter: drop-shadow(0 0 8px var(--primary-accent));
        display: flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
        background: rgba(6, 182, 212, 0.08);
        border-radius: 12px;
        border: 1px solid rgba(6, 182, 212, 0.15);
    }}

    .kpi-content {{
        display: flex;
        flex-direction: column;
        text-align: left;
    }}

    .kpi-label {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}

    .kpi-value {{
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: var(--primary-accent);
        margin-top: 4px;
        text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
        animation: pulseValue 2s infinite alternate;
    }}

    @keyframes pulseValue {{
        0% {{ opacity: 0.95; }}
        100% {{ opacity: 1; text-shadow: 0 0 15px var(--primary-accent); }}
    }}

    .kpi-card-glow {{
        position: absolute;
        bottom: -50%;
        right: -50%;
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, var(--primary-accent) 0%, transparent 70%);
        opacity: 0.12;
        z-index: 1;
        pointer-events: none;
        transition: all 0.4s ease;
    }}

    .kpi-card:hover .kpi-card-glow {{
        opacity: 0.25;
        width: 160px;
        height: 160px;
    }}

    /* ----------------------------------------------------
       SCANNING LOADER SPIN MODAL/CARD
       ---------------------------------------------------- */
    .scanner-hud {{
        background: rgba(8, 14, 27, 0.9);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 0 30px rgba(6, 182, 212, 0.15);
        animation: pulseBorder 1.5s infinite alternate;
    }}

    @keyframes pulseBorder {{
        0% {{ border-color: rgba(6, 182, 212, 0.2); }}
        100% {{ border-color: var(--primary-accent); }}
    }}

    .scanner-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 1px solid var(--panel-border);
        padding-bottom: 10px;
        font-family: 'Share Tech Mono', monospace;
    }}

    .scanner-title {{
        color: var(--primary-accent);
        font-weight: 700;
        letter-spacing: 1px;
    }}

    .scanner-blink {{
        color: var(--secondary-accent);
        animation: blinkText 0.8s infinite alternate;
    }}

    @keyframes blinkText {{
        0% {{ opacity: 0.3; }}
        100% {{ opacity: 1; }}
    }}

    .scanner-visual {{
        position: relative;
        width: 100%;
        height: 100px;
        background: rgba(0, 0, 0, 0.4);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(6, 182, 212, 0.1);
    }}

    .scanner-circle {{
        width: 60px;
        height: 60px;
        border: 2px dashed var(--primary-accent);
        border-radius: 50%;
        animation: spinCircle 5s linear infinite;
        filter: drop-shadow(0 0 8px var(--primary-accent));
    }}

    @keyframes spinCircle {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}

    .scanner-line {{
        position: absolute;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, transparent, var(--primary-accent), transparent);
        box-shadow: 0 0 12px var(--primary-accent);
        top: 0;
        animation: scanVertical 2.2s ease-in-out infinite;
    }}

    @keyframes scanVertical {{
        0% {{ top: 0%; }}
        50% {{ top: 96%; }}
        100% {{ top: 0%; }}
    }}

    .scanner-log {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.85rem;
        color: var(--text-muted);
    }}

    .log-line {{
        margin-bottom: 6px;
        display: flex;
        align-items: center;
    }}

    .log-line::before {{
        content: '>';
        color: var(--primary-accent);
        margin-right: 8px;
        animation: blinkText 0.5s infinite;
    }}

    /* Streamlit overrides for interactive input widgets */
    div[data-testid="stProgress"] > div > div > div > div {{
        background: linear-gradient(90deg, var(--primary-accent) 0%, var(--secondary-accent) 100%) !important;
        border-radius: 4px !important;
        box-shadow: 0 0 10px var(--primary-accent) !important;
    }}

    .stSpinner > div {{
        border-top-color: var(--primary-accent) !important;
        border-left-color: var(--primary-accent) !important;
    }}

    /* ====== OUTREACH HISTORY STYLES ====== */
    .outreach-history-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 18px 24px;
        background: linear-gradient(135deg, rgba(6,182,212,0.08) 0%, rgba(59,130,246,0.05) 50%, rgba(168,85,247,0.08) 100%);
        border: 1px solid var(--panel-border);
        border-radius: 14px;
        margin: 20px 0 16px 0;
    }}
    .outreach-history-header .oh-icon {{
        font-size: 1.6rem;
    }}
    .outreach-history-header .oh-title {{
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--primary-accent);
        letter-spacing: 2px;
        text-transform: uppercase;
    }}
    .outreach-history-header .oh-subtitle {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 2px;
    }}

    .outreach-stats-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 12px 0 18px 0;
    }}
    .outreach-stat-card {{
        background: var(--card-bg);
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}
    .outreach-stat-card:hover {{
        border-color: var(--primary-accent);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }}
    .outreach-stat-card .stat-value {{
        font-family: 'Orbitron', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary-accent);
        display: block;
    }}
    .outreach-stat-card .stat-label {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.68rem;
        color: var(--text-muted);
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 4px;
        display: block;
    }}

    .outreach-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.5px;
        animation: fadeIn 0.4s ease;
    }}
    .outreach-badge-wa {{
        background: rgba(37, 211, 102, 0.1);
        border: 1px solid rgba(37, 211, 102, 0.35);
        color: #25d366;
    }}
    .outreach-badge-email {{
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.35);
        color: #60a5fa;
    }}
    .outreach-badge-both {{
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid rgba(168, 85, 247, 0.35);
        color: #c084fc;
    }}

    .history-row {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 18px;
        background: var(--card-bg);
        border: 1px solid var(--panel-border);
        border-radius: 10px;
        margin-bottom: 8px;
        transition: all 0.25s ease;
        backdrop-filter: blur(8px);
    }}
    .history-row:hover {{
        border-color: var(--primary-accent);
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }}
    .history-row .hr-channel {{
        font-size: 1.4rem;
        min-width: 36px;
        text-align: center;
    }}
    .history-row .hr-info {{
        flex: 1;
    }}
    .history-row .hr-name {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        color: var(--text-primary);
    }}
    .history-row .hr-meta {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.68rem;
        color: var(--text-muted);
        margin-top: 2px;
    }}
    .history-row .hr-time {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-muted);
        white-space: nowrap;
    }}
    .history-row .hr-status {{
        padding: 4px 10px;
        border-radius: 6px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.5px;
    }}
    .hr-status-sent {{
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #10b981;
    }}
    .hr-status-resend {{
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #f59e0b;
    }}

    /* ====== SMART FOLLOW-UP STYLES ====== */
    .outreach-badge-due {{
        background: rgba(249, 115, 22, 0.12);
        border: 1px solid rgba(249, 115, 22, 0.35);
        color: #f97316;
    }}
    .outreach-badge-ok {{
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #10b981;
    }}
    .timeline-container {{
        border-left: 2px dashed var(--primary-accent);
        padding-left: 20px;
        margin-left: 10px;
        margin-top: 15px;
        margin-bottom: 20px;
    }}
    .timeline-node {{
        position: relative;
        margin-bottom: 18px;
    }}
    .timeline-node::before {{
        content: '●';
        position: absolute;
        left: -27px;
        top: -2px;
        font-size: 1.1rem;
    }}
    .timeline-node.completed::before {{
        color: var(--primary-accent);
        text-shadow: 0 0 8px var(--primary-accent);
    }}
    .timeline-node.pending::before {{
        color: #f97316;
        text-shadow: 0 0 8px #f97316;
    }}
    .timeline-label {{
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.72rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }}
    .timeline-title {{
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--text-primary);
    }}
    .due-card {{
        background: rgba(249, 115, 22, 0.04);
        border: 1px solid rgba(249, 115, 22, 0.15);
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.25s ease;
    }}
    .due-card:hover {{
        border-color: #f97316;
        box-shadow: 0 4px 16px rgba(249, 115, 22, 0.15);
    }}
    .due-title {{
        color: #f97316;
        font-weight: 700;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.85rem;
    }}
    .due-subtitle {{
        color: var(--text-muted);
        font-size: 0.75rem;
    }}

    /* Fix for multiselect tag alignment and clipping */
    div[data-baseweb="select"] span[data-baseweb="tag"],
    div[data-baseweb="select"] div[data-baseweb="tag"] {{
        margin-left: 6px !important;
    }}
    
    div[data-baseweb="select"] > div > div {{
        background-color: transparent !important;
        background: transparent !important;
    }}

    @media (max-width: 768px) {{
        .outreach-stats-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
</style>
""", unsafe_allow_html=True)


def update_scan_progress(placeholder, stage):
    step_active = ["", "", "", "", ""]
    step_comp = ["", "", "", "", ""]
    conn_active = ["", "", "", ""]
    
    for i in range(1, 6):
        if i == stage:
            step_active[i-1] = "active"
        elif i < stage:
            step_comp[i-1] = "completed"
            if i < 5:
                conn_active[i-1] = "active"
                
    placeholder.html(f"""
    <div class="scan-progress-hud">
        <h4 class="scan-progress-title">Scan Progress</h4>
        <div class="progress-pipeline">
            <div class="pipeline-step step-1 {step_active[0]} {step_comp[0]}">
                <div class="step-icon">⚙️</div>
                <span class="step-label">Initializing System</span>
            </div>
            <div class="pipeline-connector {conn_active[0]}"></div>
            <div class="pipeline-step step-2 {step_active[1]} {step_comp[1]}">
                <div class="step-icon">🌐</div>
                <span class="step-label">Connecting Network</span>
            </div>
            <div class="pipeline-connector {conn_active[1]}"></div>
            <div class="pipeline-step step-3 {step_active[2]} {step_comp[2]}">
                <div class="step-icon">🏥</div>
                <span class="step-label">Scanning Hospitals</span>
            </div>
            <div class="pipeline-connector {conn_active[2]}"></div>
            <div class="pipeline-step step-4 {step_active[3]} {step_comp[3]}">
                <div class="step-icon">📥</div>
                <span class="step-label">Fetching Data</span>
            </div>
            <div class="pipeline-connector {conn_active[3]}"></div>
            <div class="pipeline-step step-5 {step_active[4]} {step_comp[4]}">
                <div class="step-icon">🧠</div>
                <span class="step-label">Building Intelligence</span>
            </div>
        </div>
    </div>
    """)

def connect_google_drive():
    try:
        creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return build("drive", "v3", credentials=creds)
    except Exception: return None

@st.cache_data(ttl=120)
def fetch_vault_history(_service, folder_id):
    try:
        query = f"'{folder_id}' in parents and trashed=false and mimeType='text/csv'"
        results = _service.files().list(q=query, spaces='drive', fields='files(id, name, modifiedTime, webViewLink)', orderBy='modifiedTime desc').execute()
        return results.get('files', [])
    except Exception: return []

def log_debug(message):
    try:
        with open("drive_sync_debug.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
    except Exception as e:
        pass

def get_or_create_drive_folder(service, folder_name, parent_folder_id):
    log_debug(f"get_or_create_drive_folder called for: {folder_name} (parent: {parent_folder_id})")
    try:
        query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        if items:
            log_debug(f"Folder '{folder_name}' found: {items[0]['id']}")
            return items[0]['id']
        else:
            log_debug(f"Folder '{folder_name}' not found. Creating...")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            log_debug(f"Folder '{folder_name}' created successfully: {folder.get('id')}")
            return folder.get('id')
    except Exception as e:
        log_debug(f"Error resolving folder '{folder_name}': {str(e)}")
        st.error(f"Error resolving folder '{folder_name}': {str(e)}")
        return None

def update_or_create_drive_file(service, new_df, location_name, folder_id, engine_type):
    log_debug(f"update_or_create_drive_file called. Location: {location_name}, Parent folder: {folder_id}")
    # Determine state name from session state or lookup
    state_name = st.session_state.get("sync_state_name", "Unknown")
    log_debug(f"sync_state_name in session state: {state_name}")
    if state_name == "Unknown" or not state_name:
        for s, cities in LOCATION_MATRIX.items():
            if location_name in cities or location_name.replace("_multi", "") == s:
                state_name = s
                break
        log_debug(f"State resolved by lookup: {state_name}")
        if state_name == "Unknown":
            state_name = location_name  # Fallback to location name if state not found
            
    state_folder_name = state_name.strip()
    file_name = f"eye_leads_{state_folder_name.lower().replace(' ', '_')}.csv"
    log_debug(f"State folder name: {state_folder_name}, Target file name: {file_name}")
    
    try:
        # Get or create the subfolder for the state
        state_folder_id = get_or_create_drive_folder(service, state_folder_name, folder_id)
        if not state_folder_id:
            log_debug("Failed to resolve state subfolder.")
            return "Failed to resolve state subfolder."
            
        # Search for file inside the state subfolder
        query = f"name='{file_name}' and '{state_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            file_id = items[0]['id']
            log_debug(f"Target file found in subfolder: {file_id}. Merging...")
            request = service.files().get_media(fileId=file_id)
            downloaded = BytesIO()
            downloader = MediaIoBaseDownload(downloaded, request)
            done = False
            while not done: 
                status, done = downloader.next_chunk()
            downloaded.seek(0)
            existing_df = pd.read_csv(downloaded)
            
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)
            # Remove duplicates case-insensitively based on Business Name
            merged_df['temp_name'] = merged_df['Business Name'].astype(str).str.strip().str.lower()
            merged_df.drop_duplicates(subset=["temp_name"], keep='last', inplace=True)
            merged_df.drop(columns=['temp_name'], inplace=True)
            
            csv_data = merged_df.to_csv(index=False).encode('utf-8')
            media = MediaIoBaseUpload(BytesIO(csv_data), mimetype='text/csv', resumable=True)
            service.files().update(fileId=file_id, media_body=media).execute()
            log_debug(f"Merge successful! Total targets: {len(merged_df)}")
            return f"Synced to {state_folder_name}/{file_name}! Total targets: {len(merged_df)}"
        else:
            log_debug(f"Target file not found. Creating new file...")
            # Make a copy of new_df so we don't modify the session state in-place
            upload_df = new_df.copy()
            upload_df['temp_name'] = upload_df['Business Name'].astype(str).str.strip().str.lower()
            upload_df.drop_duplicates(subset=["temp_name"], keep='last', inplace=True)
            upload_df.drop(columns=['temp_name'], inplace=True)
            
            csv_data = upload_df.to_csv(index=False).encode('utf-8')
            media = MediaIoBaseUpload(BytesIO(csv_data), mimetype='text/csv', resumable=True)
            file_metadata = {'name': file_name, 'parents': [state_folder_id]}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            log_debug(f"New file created successfully! Total leads: {len(upload_df)}")
            return f"Created new file: {state_folder_name}/{file_name} (Total: {len(upload_df)})!"
    except Exception as e:
        log_debug(f"Drive Sync Exception: {str(e)}")
        st.error(f"Drive Sync Error: {str(e)}")
        return None

def format_whatsapp_link(phone_str):
    if phone_str == "N/A": return "N/A"
    clean_num = re.sub(r'\D', '', phone_str)
    if len(clean_num) == 10: clean_num = "91" + clean_num
    elif len(clean_num) > 10 and clean_num.startswith("0"): clean_num = "91" + clean_num[1:]
    return f"https://wa.me/{clean_num}"

# ==========================================
# OUTREACH HISTORY: RECORD, LOAD, SAVE
# ==========================================
OUTREACH_HISTORY_FILENAME = "outreach_history.json"

def record_outreach(business_name, category, address, phone, channel, campaign_type, city, state):
    """Record an outreach action into session state history."""
    # Calculate the sequence stage number for this lead
    prior = get_lead_outreach_info(business_name)
    stage = len(prior) + 1
    
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "business_name": business_name,
        "category": category,
        "address": address,
        "phone": phone,
        "channel": channel,  # 'WhatsApp' or 'Email'
        "campaign_type": campaign_type,
        "city": city,
        "state": state,
        "status": "Sent",
        "stage": stage
    }
    # Check for duplicate (same lead + channel) — mark as re-send
    for existing in st.session_state.outreach_history:
        if existing["business_name"].strip().lower() == business_name.strip().lower() and existing["channel"] == channel:
            existing["status"] = "Re-sent"
    st.session_state.outreach_history.insert(0, entry)
    # Trigger async save to Drive
    save_outreach_history_to_drive()

def get_lead_outreach_info(business_name):
    """Check if a lead has been contacted before. Returns list of matching records."""
    matches = []
    for record in st.session_state.outreach_history:
        if record["business_name"].strip().lower() == business_name.strip().lower():
            matches.append(record)
    return matches

def save_outreach_history_to_drive():
    """Save outreach history JSON to Google Drive."""
    try:
        drive_service = connect_google_drive()
        if not drive_service:
            return
        history_json = json.dumps(st.session_state.outreach_history, indent=2)
        json_bytes = history_json.encode('utf-8')
        media = MediaIoBaseUpload(BytesIO(json_bytes), mimetype='application/json', resumable=True)
        # Search for existing file
        query = f"name='{OUTREACH_HISTORY_FILENAME}' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        if items:
            drive_service.files().update(fileId=items[0]['id'], media_body=media).execute()
        else:
            file_metadata = {'name': OUTREACH_HISTORY_FILENAME, 'parents': [DRIVE_FOLDER_ID]}
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    except Exception as e:
        log_debug(f"Outreach history save error: {str(e)}")

def load_outreach_history_from_drive():
    """Load outreach history JSON from Google Drive on startup."""
    if st.session_state.outreach_history_loaded:
        return
    try:
        drive_service = connect_google_drive()
        if not drive_service:
            st.session_state.outreach_history_loaded = True
            return
        query = f"name='{OUTREACH_HISTORY_FILENAME}' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = drive_service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        if items:
            request = drive_service.files().get_media(fileId=items[0]['id'])
            downloaded = BytesIO()
            downloader = MediaIoBaseDownload(downloaded, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            downloaded.seek(0)
            history_data = json.loads(downloaded.read().decode('utf-8'))
            if isinstance(history_data, list):
                st.session_state.outreach_history = history_data
    except Exception as e:
        log_debug(f"Outreach history load error: {str(e)}")
    st.session_state.outreach_history_loaded = True

def backup_web_scraper(business_name, location):
    phone = "N/A"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f'{business_name} {location} clinic contact number', max_results=2))
        page_text = " ".join([res.get('body', '') + " " + res.get('href', '') for res in results])
        patterns = [r'\+91[\-\s]?[6-9]\d{2}[\-\s]?\d{3}[\-\s]?\d{4}', r'\+91\s?\d{10}', r'\b[6-9]\d{2}[\-\s]?\d{3}[\-\s]?\d{4}\b', r'\b0?[6-9]\d{9}\b']
        for p in patterns:
            match = re.search(p, page_text)
            if match:
                phone = match.group(0).strip()
                break
    except Exception: pass
    return phone

# ==========================================
# CORE ENGINES: GOOGLE PLACES & OSM FREE
# ==========================================
def fetch_from_google_places(city, state, selected_categories, max_leads):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": MAPS_API_KEY, "X-Goog-FieldMask": "places.displayName.text,places.formattedAddress,places.nationalPhoneNumber,places.googleMapsUri,places.location,nextPageToken"}
    all_records = []
    progress_text = "Establishing uplink to Google API..."
    my_bar = st.progress(0, text=progress_text)
    total_cats = len(selected_categories)

    # Resolve coordinates for Location Bias
    lookup_name = city.replace(" City", "").strip()
    lat, lon = CITY_COORDS_DB.get(lookup_name, (None, None))
    if not lat:
        try:
            res = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&state={state}&country=India&format=json&limit=1", headers={"User-Agent": OSM_USER_AGENT}, timeout=10)
            if res.status_code == 200 and res.json():
                lat, lon = float(res.json()[0]['lat']), float(res.json()[0]['lon'])
        except Exception:
            pass

    for i, category in enumerate(selected_categories):
        if len(all_records) >= max_leads: break
        my_bar.progress((i) / total_cats, text=f"Scanning Sector: {category}...")
        payload = {"textQuery": f"{category} in {city}, {state}, India", "languageCode": "en"}
        if lat and lon:
            payload["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 25000.0
                }
            }
        
        page_token = ""
        while True:
            if page_token: payload["pageToken"] = page_token
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200: 
                st.error(f"🔴 Google API Error Code: {response.status_code}\nDetails: {response.text}")
                break 
            data = response.json()
            for place in data.get("places", []):
                phone = place.get("nationalPhoneNumber", "N/A")
                name = place.get("displayName", {}).get("text", "Unknown")
                
                # Attempt to find the phone number using web scraper if Google doesn't have it
                if phone == "N/A":
                    phone = backup_web_scraper(name, city)
                
                loc_data = place.get("location", {})
                lat_val = loc_data.get("latitude", None)
                lon_val = loc_data.get("longitude", None)
                all_records.append({
                    "Business Name": name,
                    "Category": category, "Address": place.get("formattedAddress", "N/A"),
                    "Phone": phone, "WhatsApp": format_whatsapp_link(phone),
                    "Google Maps Link": place.get("googleMapsUri", "N/A"),
                    "latitude": float(lat_val) if lat_val is not None else None,
                    "longitude": float(lon_val) if lon_val is not None else None
                })
                if len(all_records) >= max_leads: break
            if len(all_records) >= max_leads: break
            page_token = data.get("nextPageToken")
            if not page_token: break
            time.sleep(1)
    my_bar.empty()
    return all_records

def fetch_from_osm_bulk(city, state, selected_categories, max_leads):
    osm_city_translation = {"Gurugram": "Gurgaon", "New Delhi": "New Delhi", "Delhi": "Delhi", "Mumbai City": "Mumbai", "Patna": "Patna"}
    search_city_name = osm_city_translation.get(city, city)
    
    lookup_name = search_city_name.replace(" City", "").strip()
    lat, lon = CITY_COORDS_DB.get(lookup_name, (None, None))
    
    # Auto-fetch coordinates if not in DB
    if not lat:
        try:
            res = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&state={state}&country=India&format=json&limit=1", headers={"User-Agent": OSM_USER_AGENT}, timeout=10)
            if res.status_code == 200 and res.json():
                lat, lon = float(res.json()[0]['lat']), float(res.json()[0]['lon'])
        except Exception:
            pass

    # Resolve OSM Amenity Filter based on UI categories
    amenity_types = []
    include_optical_shops = False
    for cat in selected_categories:
        if cat == "Optical Stores":
            include_optical_shops = True
        elif cat in OSM_AMENITY_MAPPING:
            amenity_types.append(OSM_AMENITY_MAPPING[cat])
    amenity_regex = "|".join(set(amenity_types)) if amenity_types else "hospital|clinic|doctors"

    # Regex targeting eye, ophthalmology, lens, vision, sight, Netra/Nethra, Drishti, optical stores, etc.
    eye_keywords_regex = "eye|opt|nethra|netra|drishti|vision|sight|cornea|retina|lasik|cataract|glaucoma|ophthalm|lens|nayana|spectacle|frame|glass"
    radius = 25000 # 25km radius
    
    # Build the Overpass query with optional optical shop support
    if lat and lon:
        optical_query = f"""
          nwr["shop"="optician"](around:{radius},{lat},{lon});
          nwr["shop"~"optical"](around:{radius},{lat},{lon});""" if include_optical_shops else ""
        query = f"""[out:json][timeout:180];
        (
          nwr["amenity"~"{amenity_regex}"]["name"~"{eye_keywords_regex}",i](around:{radius},{lat},{lon});
          nwr["amenity"~"{amenity_regex}"]["healthcare:speciality"="ophthalmology"](around:{radius},{lat},{lon});
          nwr["healthcare"~"doctor|clinic|hospital"]["healthcare:speciality"="ophthalmology"](around:{radius},{lat},{lon});{optical_query}
        );
        out center;"""
    else:
        optical_query = f"""
          nwr["shop"="optician"](area.searchArea);
          nwr["shop"~"optical"](area.searchArea);""" if include_optical_shops else ""
        query = f"""[out:json][timeout:180];
        area["name"="{search_city_name}"]->\.searchArea;
        (
          nwr["amenity"~"{amenity_regex}"]["name"~"{eye_keywords_regex}",i](area.searchArea);
          nwr["amenity"~"{amenity_regex}"]["healthcare:speciality"="ophthalmology"](area.searchArea);
          nwr["healthcare"~"doctor|clinic|hospital"]["healthcare:speciality"="ophthalmology"](area.searchArea);{optical_query}
        );
        out center;"""

    osm_fetched_elements = []
    last_error_msg = "Unknown Error"
    
    for url in OVERPASS_ENDPOINTS:
        try:
            res = requests.post(url, data={"data": query}, headers={"User-Agent": OSM_USER_AGENT}, timeout=90)
            if res.status_code == 200:
                data = res.json()
                if data.get("elements"):
                    osm_fetched_elements = data.get("elements", [])
                    break
                else: last_error_msg = f"No eye care data found in {city}."
            elif res.status_code == 429: 
                last_error_msg = "OSM Server Rate Limited. Too many requests."
                time.sleep(2)
            else: last_error_msg = f"OSM Error {res.status_code}"
        except Exception as e:
            last_error_msg = f"Timeout/Connection Error: {str(e)}"
            continue

    if not osm_fetched_elements:
        st.error(f"🔴 **OSM ENGINE FAILED:** {last_error_msg}\n\n*Try selecting different categories or use Google API Pro.*")
        return []

    osm_fetched_elements = osm_fetched_elements[:max_leads]
    all_records = []
    my_bar = st.progress(0, text="Establishing uplink to OSM Servers...")
    total_elements = len(osm_fetched_elements)

    for i, el in enumerate(osm_fetched_elements):
        my_bar.progress((i + 1) / total_elements, text=f"Processing target {i+1} of {total_elements}...")
        tags = el.get("tags", {})
        cat_type = tags.get("amenity", tags.get("tourism", "Eye Care")).title()
        b_name = tags.get("name", f"Premium Eye Care {cat_type}")
        
        phone = tags.get("phone", "N/A")
        if phone == "N/A" and total_elements <= 30: 
            phone = backup_web_scraper(b_name, city)
            
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
            
        search_query = urllib.parse.quote_plus(f"{b_name} {city}")
        all_records.append({
            "Business Name": b_name, "Category": cat_type,
            "Address": tags.get("addr:street", f"Local Area, {city}"),
            "Phone": phone, "WhatsApp": format_whatsapp_link(phone),
            "Google Maps Link": f"https://www.google.com/search?q={search_query}",
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lon) if lon is not None else None
        })
    my_bar.empty()
    return all_records

def render_clinic_cards(df):
    html = '<div class="clinic-grid">'
    for idx, row in df.iterrows():
        b_name = row.get("Business Name", "Unknown")
        cat = row.get("Category", "Eye Care")
        addr = row.get("Address", "N/A")
        phone = row.get("Phone", "N/A")
        wa = row.get("WhatsApp", "N/A")
        maps = row.get("Google Maps Link", "#")
        
        if phone != "N/A":
            clean_phone = re.sub(r'\D', '', phone)
            call_href = f"tel:+{clean_phone}"
            call_btn = f'<a href="{call_href}" class="clinic-btn clinic-btn-call">📞 Call</a>'
            phone_display = phone
        else:
            call_btn = '<a href="#" class="clinic-btn clinic-btn-call" style="opacity: 0.4; pointer-events: none;">📞 N/A</a>'
            phone_display = "No phone number available"
            
        wa_btn = f'<a href="{wa}" target="_blank" class="clinic-btn clinic-btn-wa">💬 WhatsApp</a>' if wa != "N/A" else '<a href="#" class="clinic-btn clinic-btn-wa" style="opacity: 0.4; pointer-events: none;">💬 WhatsApp</a>'
        maps_btn = f'<a href="{maps}" target="_blank" class="clinic-btn clinic-btn-map">📍 Navigate</a>' if maps != "N/A" else '<a href="#" class="clinic-btn clinic-btn-map" style="opacity: 0.4; pointer-events: none;">📍 Navigate</a>'
        
        html += f"""
        <div class="clinic-card">
            <div class="clinic-card-header">
                <div class="clinic-card-title">{b_name}</div>
                <div class="clinic-card-category">{cat}</div>
            </div>
            <div class="clinic-card-body">
                <div class="clinic-card-detail">
                    <span class="clinic-card-detail-icon">📍</span>
                    <span>{addr}</span>
                </div>
                <div class="clinic-card-detail">
                    <span class="clinic-card-detail-icon">📞</span>
                    <span>{phone_display}</span>
                </div>
            </div>
            <div class="clinic-card-actions">
                {call_btn}
                {wa_btn}
                {maps_btn}
            </div>
        </div>
        """
    html += '</div>'
    return html

# ==========================================
# MULTI-CITY BATCH SCANNING ENGINE
# ==========================================
def fetch_multi_city_batch(state, cities, selected_categories, engine_key, max_leads_per_city):
    """Scan multiple cities in a state sequentially and aggregate results."""
    all_aggregated = []
    total_cities = len(cities)
    city_progress = st.progress(0, text="Initializing multi-city sweep...")
    
    for idx, city in enumerate(cities):
        city_progress.progress((idx) / total_cities, text=f"🌐 Scanning {city}... ({idx+1}/{total_cities} cities)")
        try:
            if engine_key == "google":
                records = fetch_from_google_places(city, state, selected_categories, max_leads_per_city)
            else:
                records = fetch_from_osm_bulk(city, state, selected_categories, max_leads_per_city)
            
            # Add city column to each record
            for r in records:
                r["City"] = city
            all_aggregated.extend(records)
        except Exception as e:
            st.warning(f"⚠️ Skipped {city}: {str(e)}")
            continue
    
    city_progress.progress(1.0, text=f"✅ Multi-city sweep complete! Scanned {total_cities} cities.")
    time.sleep(0.5)
    city_progress.empty()
    return all_aggregated

# ==========================================
# UI & APPLICATION LAYOUT
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='font-family: \"Outfit\", sans-serif; font-weight: 700; color: var(--primary-accent); margin-bottom: 2px;'>👁️ DIAGNOSTIC ENGINE HUD</h2>", unsafe_allow_html=True)
    st.selectbox(
        "DIAGNOSTIC VISION THEME",
        options=list(THEMES.keys()),
        key="app_theme",
        label_visibility="collapsed"
    )
    st.markdown("<hr style='border: 0; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0) 0%, var(--panel-border) 50%, rgba(255,255,255,0) 100%); margin: 15px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='font-family: \"Outfit\", sans-serif; font-weight: 700; color: var(--secondary-accent); font-size: 1.25rem; margin-bottom: 10px;'>☁️ CLINICAL VAULT</h3>", unsafe_allow_html=True)
    drive_service = connect_google_drive()
    if drive_service: 
        st.markdown("<div class='status-badge'>🟢 SECURE CLOUD ONLINE</div><br><br>", unsafe_allow_html=True)
        st.link_button("📂 ACCESS CLOUD VAULT", f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}", use_container_width=True)
        st.markdown("<hr style='border: 0; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0) 0%, var(--panel-border) 50%, rgba(255,255,255,0) 100%); margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: var(--text-muted); font-family: \"Outfit\", sans-serif; font-weight: 600;'>📜 DATA ARCHIVES</h4>", unsafe_allow_html=True)
        recent_files = fetch_vault_history(drive_service, DRIVE_FOLDER_ID)
        if recent_files:
            file_dict = {f['name']: f.get('webViewLink', f"https://drive.google.com/file/d/{f['id']}/view") for f in recent_files}
            selected_file = st.selectbox("Select Archive File:", ["-- Initialize File --"] + list(file_dict.keys()))
            if selected_file != "-- Initialize File --":
                st.link_button(label=f"👁️ DECRYPT {selected_file}", url=file_dict[selected_file], use_container_width=True)
        else: st.info("Archive empty. No logs found.")
    else: st.markdown("<div class='status-badge' style='color:#ef4444; border-color:#ef4444; background:rgba(239, 68, 68, 0.1)'>🔴 CLOUD OFFLINE</div>", unsafe_allow_html=True)
    
    # Session Scan History Counter
    st.markdown("<hr style='border: 0; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0) 0%, var(--panel-border) 50%, rgba(255,255,255,0) 100%); margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-family: \"Outfit\", sans-serif; font-weight: 700; color: var(--primary-accent); font-size: 1.1rem; margin-bottom: 10px;'>📊 SESSION TELEMETRY</h3>", unsafe_allow_html=True)
    sess_scan_count = st.session_state.get("scan_count", 0)
    sess_total_leads = st.session_state.get("total_leads_found", 0)
    st.html(f"""
    <div style='display: flex; gap: 10px; margin-bottom: 10px;'>
        <div style='flex: 1; background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 10px; padding: 12px; text-align: center;'>
            <div style='font-family: "Orbitron", sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--primary-accent);'>{sess_scan_count}</div>
            <div style='font-family: "Share Tech Mono", monospace; font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;'>Scans Run</div>
        </div>
        <div style='flex: 1; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 10px; padding: 12px; text-align: center;'>
            <div style='font-family: "Orbitron", sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--secondary-accent);'>{sess_total_leads}</div>
            <div style='font-family: "Share Tech Mono", monospace; font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;'>Total Leads</div>
        </div>
    </div>
    """)

# Main layout header with custom animated cybernetic eye SVG logo V2
st.markdown("""<div class="hero-container-v2">
<div class="hero-left-eye">
<svg class="detailed-eye-svg" viewBox="0 0 350 250" xmlns="http://www.w3.org/2000/svg">
<circle class="ring ring-outer" cx="120" cy="125" r="90" stroke="var(--primary-accent)" stroke-width="1.5" stroke-dasharray="10 5" fill="none" opacity="0.6"/>
<circle class="ring ring-middle" cx="120" cy="125" r="75" stroke="var(--secondary-accent)" stroke-width="1" stroke-dasharray="5 15" fill="none" opacity="0.8"/>
<path d="M 40 125 Q 120 70 200 125 Q 120 180 40 125 Z" fill="rgba(6, 182, 212, 0.05)" stroke="var(--panel-border)" stroke-width="1"/>
<circle class="iris-detailed" cx="120" cy="125" r="45" fill="url(#irisGradient)" stroke="var(--primary-accent)" stroke-width="1.5"/>
<circle class="pupil-detailed" cx="120" cy="125" r="22" fill="#020617" stroke="var(--secondary-accent)" stroke-width="1"/>
<circle cx="108" cy="113" r="4" fill="#ffffff" opacity="0.8"/>
<circle cx="128" cy="133" r="2" fill="#ffffff" opacity="0.6"/>
<line class="scanner-sweep" x1="120" y1="125" x2="120" y2="35" stroke="var(--primary-accent)" stroke-width="1.5" opacity="0.8"/>
<path d="M 115 82 L 180 60 L 230 60" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.8"/>
<text x="235" y="64" fill="var(--text-muted)" font-family="Share Tech Mono" font-size="10" letter-spacing="1">CORNEA</text>
<path d="M 145 105 L 195 105 L 230 105" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.8"/>
<text x="235" y="109" fill="var(--text-muted)" font-family="Share Tech Mono" font-size="10" letter-spacing="1">IRIS</text>
<path d="M 132 125 L 180 145 L 230 145" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.8"/>
<text x="235" y="149" fill="var(--text-muted)" font-family="Share Tech Mono" font-size="10" letter-spacing="1">PUPIL</text>
<path d="M 90 155 L 140 190 L 230 190" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.8"/>
<text x="235" y="194" fill="var(--text-muted)" font-family="Share Tech Mono" font-size="10" letter-spacing="1">RETINA</text>
<path d="M 40 125 L 90 230 L 230 230" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.8"/>
<text x="235" y="234" fill="var(--text-muted)" font-family="Share Tech Mono" font-size="10" letter-spacing="1">OPTIC NERVE</text>
<defs>
<radialGradient id="irisGradient" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#020617"/>
<stop offset="40%" stop-color="var(--secondary-accent)"/>
<stop offset="100%" stop-color="var(--primary-accent)"/>
</radialGradient>
</defs>
</svg>
</div>
<div class="hero-right-text">
<h1 class="hero-title-v2">EyeFinder AI</h1>
<p class="hero-tagline">Advanced Eye Care Intelligence</p>
<div class="hero-links">
<span>Discover</span> • <span>Connect</span> • <span>Transform</span>
</div>
<a href="#engine-protocol-section" class="vision-scan-btn">
<span>START VISION SCAN</span>
<span class="scan-btn-icon">👁️</span>
</a>
</div>
<div class="vascular-pattern-container">
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" class="vascular-svg">
<circle cx="150" cy="100" r="10" fill="var(--primary-accent)" opacity="0.3" filter="blur(4px)"/>
<circle cx="150" cy="100" r="4" fill="var(--primary-accent)" opacity="0.8"/>
<path d="M 150 100 Q 120 70 80 80 T 30 60" stroke="var(--primary-accent)" stroke-width="1" fill="none" opacity="0.4"/>
<path d="M 150 100 Q 130 130 90 120 T 40 150" stroke="var(--primary-accent)" stroke-width="0.8" fill="none" opacity="0.4"/>
<path d="M 150 100 Q 170 60 190 40" stroke="var(--primary-accent)" stroke-width="0.8" fill="none" opacity="0.4"/>
<path d="M 150 100 Q 160 140 180 170" stroke="var(--primary-accent)" stroke-width="0.6" fill="none" opacity="0.3"/>
<path d="M 120 70 Q 100 50 60 40" stroke="var(--primary-accent)" stroke-width="0.6" fill="none" opacity="0.3"/>
<path d="M 90 120 Q 70 110 50 90" stroke="var(--primary-accent)" stroke-width="0.5" fill="none" opacity="0.3"/>
</svg>
</div>
</div>""", unsafe_allow_html=True)

# Render Statistics Dashboard
if st.session_state.raw_df is not None and not st.session_state.raw_df.empty:
    display_df = st.session_state.raw_df
    total_leads = len(display_df)
    hospitals_count = (display_df['Category'].str.contains('Hospital|hospital', case=False, na=False)).sum()
    clinics_count = total_leads - hospitals_count
    contacts_found = (display_df['Phone'] != 'N/A').sum()
    
    st.html(f"""
    <div class="kpi-dashboard-grid">
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(6, 182, 212, 0.1); border-color: var(--primary-accent); color: var(--primary-accent);">🏥</div>
                <div class="kpi-content">
                    <span class="kpi-label">Eye Hospitals</span>
                    <span class="kpi-value" style="color: var(--text-primary);">{hospitals_count}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(168, 85, 247, 0.1); border-color: var(--secondary-accent); color: var(--secondary-accent);">🩺</div>
                <div class="kpi-content">
                    <span class="kpi-label">Eye Clinics</span>
                    <span class="kpi-value" style="color: var(--text-primary);">{clinics_count}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.1); border-color: #10b981; color: #10b981;">📍</div>
                <div class="kpi-content">
                    <span class="kpi-label">Cities Covered</span>
                    <span class="kpi-value" style="color: var(--text-primary);">1</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(236, 72, 153, 0.1); border-color: #ec4899; color: #ec4899;">📞</div>
                <div class="kpi-content">
                    <span class="kpi-label">Contacts Found</span>
                    <span class="kpi-value" style="color: var(--text-primary);">{contacts_found}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
    </div>
    """)
else:
    # Default global system telemetry view matching the reference layout
    st.html("""
    <div class="kpi-dashboard-grid">
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(6, 182, 212, 0.1); border-color: var(--primary-accent); color: var(--primary-accent);">🏥</div>
                <div class="kpi-content">
                    <span class="kpi-label">Eye Hospitals</span>
                    <span class="kpi-value" style="color: var(--text-primary);">12,547</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(168, 85, 247, 0.1); border-color: var(--secondary-accent); color: var(--secondary-accent);">🩺</div>
                <div class="kpi-content">
                    <span class="kpi-label">Eye Clinics</span>
                    <span class="kpi-value" style="color: var(--text-primary);">8,932</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.1); border-color: #10b981; color: #10b981;">📍</div>
                <div class="kpi-content">
                    <span class="kpi-label">Cities Covered</span>
                    <span class="kpi-value" style="color: var(--text-primary);">425</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon" style="background: rgba(236, 72, 153, 0.1); border-color: #ec4899; color: #ec4899;">📞</div>
                <div class="kpi-content">
                    <span class="kpi-label">Contacts Found</span>
                    <span class="kpi-value" style="color: var(--text-primary);">10,224</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
    </div>
    """)

# ----------------------------------------------------
# SCANNING EXECUTION FLOW (FULL-WIDTH SCIFI HUD)
# ----------------------------------------------------
if st.session_state.get("is_scanning", False):
    st.markdown("<div id='engine-protocol-section'></div>", unsafe_allow_html=True)
    
    with st.container(border=True, key="scanning_container"):
        progress_hud = st.empty()
        loader_placeholder = st.empty()
        
        selected_city = st.session_state.scan_city
        selected_state = st.session_state.scan_state
        selected_categories = st.session_state.scan_categories
        engine_key = st.session_state.scan_engine
        max_leads = st.session_state.scan_max_leads
        
        # Stage 1: Init System
        update_scan_progress(progress_hud, 1)
        time.sleep(0.8)
        
        # Stage 2: Connecting Network
        update_scan_progress(progress_hud, 2)
        loader_placeholder.html(f"""
        <div class="scanner-hud">
            <div class="scanner-header">
                <span class="scanner-title">👁️ RETINA DATA ACQUISITION ACTIVE</span>
                <span class="scanner-blink">SYSTEM CONNECTED</span>
            </div>
            <div class="scanner-body">
                <div class="scanner-visual">
                    <div class="scanner-circle"></div>
                    <div class="scanner-line"></div>
                </div>
                <div class="scanner-log">
                    <div class="log-line">INITIATING UPLINK PROTOCOL FOR {selected_city.upper()} ({selected_state.upper()})...</div>
                    <div class="log-line">ESTABLISHING CONNECTION TO {"GOOGLE PLACES DATABASE" if engine_key == "google" else "OSM OVERPASS NODES"}...</div>
                    <div class="log-line">DECRYPTING SECTORS: {", ".join(selected_categories).upper()}...</div>
                </div>
            </div>
        </div>
        """)
        time.sleep(0.8)
        
        # Stage 3: Scanning Hospitals
        update_scan_progress(progress_hud, 3)
        with st.spinner("Processing request..."):
            if engine_key == "google":
                all_records = fetch_from_google_places(selected_city, selected_state, selected_categories, max_leads)
            else:
                all_records = fetch_from_osm_bulk(selected_city, selected_state, selected_categories, max_leads)
            
            # Stage 4: Fetching Data
            update_scan_progress(progress_hud, 4)
            if all_records:
                df = pd.DataFrame(all_records)
                st.session_state.raw_df = df.drop_duplicates(subset=["Business Name"]).reset_index(drop=True)
                st.session_state.current_city = selected_city
                st.session_state.scan_count += 1
                st.session_state.total_leads_found += len(st.session_state.raw_df)
                st.success(f"✅ Extraction Successful: Retrieved {len(st.session_state.raw_df)} high-value targets.")
                time.sleep(0.8)
                
                # Stage 5: Building Intelligence
                update_scan_progress(progress_hud, 5)
                st.session_state.needs_drive_sync = True
                st.session_state.sync_city_name = selected_city
                st.session_state.sync_engine_key = engine_key
                st.success("☁️ Target matrix loaded. Finalizing intelligence vault uplink...")
                time.sleep(1)
            else:
                st.info("No records found matching the criteria.")
                time.sleep(2)
        
        st.session_state.is_scanning = False
        st.rerun()

else:
    # ----------------------------------------------------
    # SEARCH DASHBOARD PANELS (NON-SCANNING VIEW)
    # ----------------------------------------------------
    col_left, col_right = st.columns([6, 4])
    
    with col_left:
        st.markdown("<div id='engine-protocol-section'></div>", unsafe_allow_html=True)
        with st.container(border=True, key="left_col_container"):
            st.markdown("<h4 style='color: var(--primary-accent); margin-bottom: 20px; font-family: \"Outfit\", sans-serif; font-weight: 700;'>⚙️ ENGINE PROTOCOL</h4>", unsafe_allow_html=True)
            scraper_engine = st.radio("Select Scraper Engine Mode", ["Google API Pro (Highly Accurate + Auto-Phone)", "OSM Free Bulk Engine (Huge Number of Leads + Verification Link)"], horizontal=True, label_visibility="collapsed")
            st.markdown("<hr>", unsafe_allow_html=True)
            
            st.markdown("<h4 style='color: var(--primary-accent); margin-bottom: 20px; font-family: \"Outfit\", sans-serif; font-weight: 700;'>📍 TARGET COORDINATES</h4>", unsafe_allow_html=True)
            ctrl_c1, ctrl_c2 = st.columns([1, 1])
            with ctrl_c1: selected_state = st.selectbox("Select State", ["Select State..."] + list(LOCATION_MATRIX.keys()))
            with ctrl_c2:
                city_options = ["Select City..."] + LOCATION_MATRIX[selected_state] if selected_state != "Select State..." else ["Select City..."]
                selected_city = st.selectbox("Target City", city_options)
            
            st.markdown("<br>", unsafe_allow_html=True)
            selected_categories = st.multiselect("🏷️ TARGET SECTORS", SEARCH_CATEGORIES, default=["Eye Hospitals", "Eye Clinics"])
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#a5b4fc;'>⚡ EXTRACTION VOLUME</h4>", unsafe_allow_html=True)
            max_leads = st.slider("Target Lead Count", min_value=10, max_value=500, value=100, step=10, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 INITIATE EXTRACTION PROTOCOL"):
                if selected_state == "Select State..." or selected_city == "Select City...":
                    st.error("⚠️ Error: Target coordinates not set. Please select a valid State and City.")
                elif not selected_categories:
                    st.warning("⚠️ Error: No target sectors selected.")
                else:
                    st.session_state.is_scanning = True
                    st.session_state.scan_city = selected_city
                    st.session_state.scan_state = selected_state
                    st.session_state.scan_categories = selected_categories
                    st.session_state.scan_engine = "google" if "Google" in scraper_engine else "osm"
                    st.session_state.scan_max_leads = max_leads
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Multi-City Batch Sweep
            if st.button("🌐 MULTI-CITY STATE SWEEP", help="Scan ALL cities in the selected state sequentially"):
                if selected_state == "Select State...":
                    st.error("⚠️ Error: Select a state first for multi-city sweep.")
                elif not selected_categories:
                    st.warning("⚠️ Error: No target sectors selected.")
                else:
                    sweep_engine = "google" if "Google" in scraper_engine else "osm"
                    cities_to_sweep = LOCATION_MATRIX[selected_state]
                    st.session_state.scan_engine = sweep_engine
                    
                    with st.spinner(f"🌐 Sweeping {len(cities_to_sweep)} cities in {selected_state}..."):
                        all_records = fetch_multi_city_batch(
                            selected_state, cities_to_sweep, selected_categories,
                            sweep_engine, max_leads_per_city=max_leads
                        )
                    
                    if all_records:
                        df = pd.DataFrame(all_records)
                        st.session_state.raw_df = df.drop_duplicates(subset=["Business Name"]).reset_index(drop=True)
                        st.session_state.current_city = f"{selected_state} (Multi-City)"
                        st.session_state.scan_count += 1
                        st.session_state.total_leads_found += len(st.session_state.raw_df)
                        
                        # Set auto-save flag for Drive sync
                        st.session_state.needs_drive_sync = True
                        st.session_state.sync_city_name = f"{selected_state}_multi"
                        st.session_state.sync_engine_key = sweep_engine
                        
                        st.success(f"✅ Multi-City Sweep Complete: {len(st.session_state.raw_df)} leads from {len(cities_to_sweep)} cities!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("No records found across any city in this state.")
                    
    with col_right:
        with st.container(border=True, key="right_col_container"):
            st.markdown("<h4 style='color: var(--primary-accent); margin-bottom: 15px; font-family: \"Outfit\", sans-serif; font-weight: 700; text-transform: uppercase;'>📜 DATALINK ACQUISITION LOGS</h4>", unsafe_allow_html=True)
            
            drive_service = connect_google_drive()
            log_tabs = st.tabs(["☁️ CLOUD VAULT", "💾 LOCAL CACHE"])
            
            with log_tabs[0]:
                st.markdown("<br>", unsafe_allow_html=True)
                if drive_service:
                    recent_files = fetch_vault_history(drive_service, DRIVE_FOLDER_ID)
                    if recent_files:
                        # Display list of recent scans
                        for f in recent_files[:4]:
                            name = f['name']
                            mod_time = f.get('modifiedTime', '')
                            city_name = "Unknown"
                            match_name = re.match(r"eye_leads_([a-zA-Z0-9]+)_([a-zA-Z0-9\s_]+)\.csv", name)
                            if match_name:
                                city_name = match_name.group(2).replace("_", " ").title()
                            state_name = "India"
                            for s, cities in LOCATION_MATRIX.items():
                                if city_name in cities:
                                    state_name = s
                                    break
                            try:
                                dt = datetime.strptime(mod_time.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                                time_str = dt.strftime("%d %b %Y %I:%M %p")
                            except Exception:
                                time_str = mod_time
                            
                            st.html(f"""
                            <div style='background: rgba(255, 255, 255, 0.03); border: 1px solid var(--panel-border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;'>
                                <div style='display: flex; align-items: center; gap: 10px;'>
                                    <div style='width: 30px; height: 30px; border-radius: 50%; background: rgba(6, 182, 212, 0.1); border: 1px solid var(--panel-border); display: flex; align-items: center; justify-content: center; color: var(--primary-accent); font-size: 0.85rem;'>👁️</div>
                                    <div>
                                        <div style='font-family: "Outfit", sans-serif; font-weight: 600; font-size: 0.85rem; color: var(--text-primary);'>{state_name} - {city_name}</div>
                                        <div style='font-family: "Share Tech Mono", monospace; font-size: 0.7rem; color: var(--text-muted);'>{time_str}</div>
                                    </div>
                                </div>
                                <div style='font-family: "Orbitron", sans-serif; font-size: 0.75rem; font-weight: 700; color: var(--primary-accent);'>Indexed</div>
                            </div>
                            """)
                        
                        # Select archive to decrypt and load
                        st.markdown("<br>", unsafe_allow_html=True)
                        file_options = {f['name']: f['id'] for f in recent_files}
                        selected_archive = st.selectbox("Select past scan to load:", ["-- Select Log --"] + list(file_options.keys()))
                        if selected_archive != "-- Select Log --":
                            if st.button("🔓 DECRYPT & LOAD SCAN"):
                                with st.spinner("Downloading scan archive..."):
                                    file_id = file_options[selected_archive]
                                    request = drive_service.files().get_media(fileId=file_id)
                                    downloaded = BytesIO()
                                    downloader = MediaIoBaseDownload(downloaded, request)
                                    done = False
                                    while not done:
                                        status, done = downloader.next_chunk()
                                    downloaded.seek(0)
                                    df_archive = pd.read_csv(downloaded)
                                    
                                    city_extract = "Patna"
                                    match_extract = re.match(r"eye_leads_([a-zA-Z0-9]+)_([a-zA-Z0-9\s_]+)\.csv", selected_archive)
                                    if match_extract:
                                        city_extract = match_extract.group(2).replace("_", " ").title()
                                    
                                    st.session_state.raw_df = df_archive.drop_duplicates(subset=["Business Name"]).reset_index(drop=True)
                                    st.session_state.current_city = city_extract
                                    st.success(f"🔓 Scan Decrypted: Loaded {len(st.session_state.raw_df)} targets for {city_extract}!")
                                    time.sleep(1)
                                    st.rerun()
                    else:
                        st.info("No logs in cloud vault.")
                else:
                    st.warning("Cloud connection offline. Recent scans feed unavailable.")
                    
            with log_tabs[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='status-badge' style='color: var(--secondary-accent); border-color: var(--secondary-accent); background: rgba(168, 85, 247, 0.1); margin-bottom: 20px;'>💾 LOCAL REPLICATION CACHE ACTIVE</div>", unsafe_allow_html=True)
                
                st.html("""
                <div style='background: rgba(255, 255, 255, 0.02); border: 1px solid var(--panel-border); border-radius: 10px; padding: 12px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
                        <span style='color: var(--text-primary); font-weight: 600;'>📍 Rajasthan - Jaipur Hub</span>
                        <span style='color: var(--primary-accent); font-family: "Share Tech Mono"; font-weight: 700;'>112 Leads</span>
                    </div>
                    <div style='font-size: 0.7rem; color: var(--text-muted); margin-top: 4px;'>Sync Date: 16 Jun 2026 // Crypt: AES-256</div>
                </div>
                <div style='background: rgba(255, 255, 255, 0.02); border: 1px solid var(--panel-border); border-radius: 10px; padding: 12px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
                        <span style='color: var(--text-primary); font-weight: 600;'>📍 Bihar - Patna Hub</span>
                        <span style='color: var(--primary-accent); font-family: "Share Tech Mono"; font-weight: 700;'>145 Leads</span>
                    </div>
                    <div style='font-size: 0.7rem; color: var(--text-muted); margin-top: 4px;'>Sync Date: 15 Jun 2026 // Crypt: AES-256</div>
                </div>
                <div style='background: rgba(255, 255, 255, 0.02); border: 1px solid var(--panel-border); border-radius: 10px; padding: 12px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
                        <span style='color: var(--text-primary); font-weight: 600;'>📍 Maharashtra - Mumbai Hub</span>
                        <span style='color: var(--primary-accent); font-family: "Share Tech Mono"; font-weight: 700;'>284 Leads</span>
                    </div>
                    <div style='font-size: 0.7rem; color: var(--text-muted); margin-top: 4px;'>Sync Date: 14 Jun 2026 // Crypt: AES-256</div>
                </div>
                """)
                
                local_cache_choices = {
                    "Jaipur (112 leads)": "Jaipur",
                    "Patna (145 leads)": "Patna",
                    "Mumbai (284 leads)": "Mumbai"
                }
                selected_cache = st.selectbox("Select Cached Dataset:", ["-- Initialize Cache --"] + list(local_cache_choices.keys()), key="local_cache_select")
                if selected_cache != "-- Initialize Cache --":
                    if st.button("🔓 DECRYPT & LOAD LOCAL CACHE", key="load_local_cache_btn"):
                        city_name = local_cache_choices[selected_cache]
                        mock_leads = []
                        for i in range(1, 21):
                            mock_leads.append({
                                "Business Name": f"Nayana Eye Center & Hospital - {city_name} Hub {i}",
                                "Category": "Eye Clinic" if i % 3 == 0 else "Eye Hospital",
                                "Address": f"Block {i * 3}, Main Road, {city_name}, India",
                                "Phone": f"+91 98765 430{i:02d}",
                                "Google Maps Link": "https://maps.google.com",
                                "WhatsApp": f"https://wa.me/9198765430{i:02d}" if i % 2 == 0 else "N/A",
                                "latitude": CITY_COORDS_DB.get(city_name, (20.0, 78.0))[0] + (i * 0.003 - 0.03),
                                "longitude": CITY_COORDS_DB.get(city_name, (20.0, 78.0))[1] + (i * 0.003 - 0.03),
                            })
                        st.session_state.raw_df = pd.DataFrame(mock_leads)
                        st.session_state.current_city = city_name
                        st.success(f"🔓 Cache Decrypted: Loaded {len(st.session_state.raw_df)} cached targets for {city_name}!")
                        time.sleep(1)
                        st.rerun()

if st.session_state.raw_df is not None and not st.session_state.raw_df.empty:
    display_df = st.session_state.raw_df
    engine_key = st.session_state.get("scan_engine", "osm")
    
    # Auto-save to Google Drive after showing data
    if st.session_state.get("needs_drive_sync", False):
        log_debug("needs_drive_sync flag detected as True in dashboard view.")
        sync_placeholder = st.empty()
        with sync_placeholder.container():
            st.info("🔄 Google Drive Vault Sync Active: Archiving target matrix in background...")
            drive_service = connect_google_drive()
            if drive_service:
                city = st.session_state.get("sync_city_name", st.session_state.get("current_city", "Unknown"))
                engine = st.session_state.get("sync_engine_key", engine_key)
                log_debug(f"Triggering drive update for location: {city}, engine: {engine}")
                res = update_or_create_drive_file(drive_service, display_df, city, DRIVE_FOLDER_ID, engine)
                if res:
                    st.success(f"☁️ Vault Sync Complete: {res}")
                    log_debug(f"Vault sync complete. Result: {res}")
                else:
                    st.error("⚠️ Google Drive Sync failed. Please check credentials.")
                    log_debug("Vault sync failed (returned None).")
            else:
                st.error("🔴 Google Drive Connection Offline.")
                log_debug("Vault sync failed: drive_service is None.")
        st.session_state.needs_drive_sync = False
        time.sleep(2)
        sync_placeholder.empty()
    
    st.markdown("<br><h3 style='color: var(--primary-accent); font-family: \"Outfit\", sans-serif; font-weight: 700; letter-spacing: 1px;'>📊 TARGET DISCOVERY HUD</h3>", unsafe_allow_html=True)
    
    # Clinical scan header banner
    st.html(f"""
    <div style='background: linear-gradient(90deg, rgba(6,182,212,0.08) 0%, rgba(59,130,246,0.04) 50%, rgba(168,85,247,0.08) 100%); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px 22px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;'>
        <div style='display: flex; align-items: center; gap: 14px;'>
            <div style='width: 44px; height: 44px; border-radius: 50%; background: rgba(6,182,212,0.12); border: 2px solid var(--primary-accent); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; animation: pulseCircle 2s infinite alternate;'>👁️</div>
            <div>
                <div style='font-family: "Orbitron", sans-serif; font-size: 0.85rem; font-weight: 700; color: var(--primary-accent); letter-spacing: 2px; text-transform: uppercase;'>Retina Scan Report</div>
                <div style='font-family: "Share Tech Mono", monospace; font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;'>TARGET: {st.session_state.current_city.upper()} // {len(display_df)} ENTITIES DETECTED</div>
            </div>
        </div>
        <div style='display: flex; align-items: center; gap: 8px;'>
            <div style='width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: blinkText 1.2s infinite;'></div>
            <span style='font-family: "Share Tech Mono", monospace; font-size: 0.7rem; color: #10b981; letter-spacing: 1px;'>SCAN ACTIVE</span>
        </div>
    </div>
    """)

    # Search + Filter row
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Leads", placeholder="Type to search by business name...", label_visibility="collapsed", key="top_search_query")
    with col_filter:
        filter_choice = st.selectbox("Quick Filter", ["All Targets", "With Phone Number Only", "Hospitals Only", "Clinics Only", "Optical Stores Only"], label_visibility="collapsed", key="top_filter_choice")

    # Apply Search + Quick Filter
    filtered_df = display_df.copy()
    if search_query and search_query.strip():
        filtered_df = filtered_df[filtered_df["Business Name"].astype(str).str.contains(search_query.strip(), case=False, na=False)]
    
    if filter_choice == "With Phone Number Only":
        filtered_df = filtered_df[filtered_df["Phone"] != "N/A"]
    elif filter_choice == "Hospitals Only":
        filtered_df = filtered_df[filtered_df["Category"].str.contains("Hospital", case=False, na=False)]
    elif filter_choice == "Clinics Only":
        filtered_df = filtered_df[filtered_df["Category"].str.contains("Clinic", case=False, na=False)]
    elif filter_choice == "Optical Stores Only":
        filtered_df = filtered_df[filtered_df["Category"].str.contains("Shop|Optical|Optic", case=False, na=False)]

    # Calculate statistics dynamically based on filtered data
    total_leads = len(filtered_df)
    hospitals_count = (filtered_df['Category'].str.contains('Hospital|hospital', case=False, na=False)).sum()
    clinics_count = total_leads - hospitals_count
    contact_rate = (filtered_df['Phone'] != 'N/A').sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
    
    # ----------------------------------------------------
    # KPI STATS CARDS (Redesigned & Reactive)
    # ----------------------------------------------------
    st.html(f"""
    <div class="kpi-dashboard-grid">
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">🏥</div>
                <div class="kpi-content">
                    <span class="kpi-label">Hospitals Detected</span>
                    <span class="kpi-value">{hospitals_count}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">🩺</div>
                <div class="kpi-content">
                    <span class="kpi-label">Clinics Detected</span>
                    <span class="kpi-value">{clinics_count}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">📍</div>
                <div class="kpi-content">
                    <span class="kpi-label">Target City</span>
                    <span class="kpi-value">{st.session_state.current_city.upper()}</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">📞</div>
                <div class="kpi-content">
                    <span class="kpi-label">Contact Coverage</span>
                    <span class="kpi-value">{contact_rate:.1f}%</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
    </div>
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # DASHBOARD TABS
    # ----------------------------------------------------
    tab1, tab2 = st.tabs(["📊 DATA MATRIX", "💬 SMART OUTREACH"])

    # Tab 1: Leads Data Grid with Export
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 1: Download buttons
        col_csv, col_xlsx = st.columns([1, 1])
        with col_csv: 
            st.download_button("💾 DOWNLOAD CSV", filtered_df.to_csv(index=False).encode('utf-8'), f"backup_{engine_key}_{st.session_state.current_city}.csv", "text/csv", use_container_width=True)
        with col_xlsx:
            try:
                xlsx_buffer = BytesIO()
                with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
                    export_df = filtered_df.drop(columns=['latitude', 'longitude'], errors='ignore')
                    export_df.to_excel(writer, index=False, sheet_name='Eye Leads')
                xlsx_buffer.seek(0)
                st.download_button("📊 DOWNLOAD XLSX", xlsx_buffer.getvalue(), f"report_{engine_key}_{st.session_state.current_city}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except ImportError:
                st.button("📊 XLSX (Install openpyxl)", disabled=True, use_container_width=True)
            
        # Results count badge
        st.html(f"""
        <div style='display: flex; align-items: center; gap: 12px; font-family: "Share Tech Mono", monospace; font-size: 0.78rem; color: var(--text-muted); margin: 10px 0; padding: 8px 14px; background: rgba(6,182,212,0.04); border-left: 3px solid var(--primary-accent); border-radius: 0 8px 8px 0;'>
            <span>👁️ SCAN RESULTS:</span>
            <span style='color: var(--primary-accent); font-weight: 700; font-size: 1rem;'>{len(filtered_df)}</span>
            <span>of {len(display_df)} targets identified</span>
            <span style='margin-left: auto; color: var(--secondary-accent);'>▸ {filter_choice}</span>
        </div>
        """)
            
        if filtered_df.empty:
            st.info("No targets match the active filter criteria.")
        else:
            st.markdown("<div style='border: 1px solid var(--panel-border); border-radius: 12px; overflow: hidden; box-shadow: var(--card-shadow); padding: 5px; background: var(--card-bg); backdrop-filter: blur(10px); margin-top:15px;'>", unsafe_allow_html=True)
            st.dataframe(filtered_df, use_container_width=True, height=500, hide_index=True, column_config={
                "WhatsApp": st.column_config.LinkColumn("💬 COMMS", display_text="Open WhatsApp"), 
                "Google Maps Link": st.column_config.LinkColumn("📍 INTEL", display_text="View Map"),
                "latitude": None,
                "longitude": None
            })
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 2: Personalized Outreach Template Builder
    with tab2:
        # Load outreach history from Drive on first load
        load_outreach_history_from_drive()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: var(--primary-accent); font-family: \"Outfit\", sans-serif; font-weight: 700;'>💬 SMART OUTREACH GENERATOR</h4>", unsafe_allow_html=True)
        st.write("Generate and copy personalized messages or instantly initiate WhatsApp chats and emails with targeted clients.")
        
        # ==========================================
        # [START] SMART FOLLOW-UP RADAR HUD
        # ==========================================
        history = st.session_state.outreach_history
        threshold_days = 3  # default follow-up threshold in days
        due_leads = []
        
        # Group history by business name to get the newest contact for each
        newest_contacts = {}
        for h in history:
            bname = h["business_name"].strip().lower()
            if bname not in newest_contacts:
                newest_contacts[bname] = h
            else:
                try:
                    t_existing = datetime.strptime(newest_contacts[bname]["timestamp"], "%Y-%m-%d %H:%M:%S")
                    t_new = datetime.strptime(h["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if t_new > t_existing:
                        newest_contacts[bname] = h
                except Exception:
                    pass
        
        # Check which of these are older than threshold_days
        now = datetime.now()
        for bname, record in newest_contacts.items():
            try:
                contact_date = datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S")
                days_since = (now - contact_date).days
                if days_since >= threshold_days:
                    due_leads.append({
                        "business_name": record["business_name"],
                        "category": record["category"],
                        "last_channel": record["channel"],
                        "last_stage": record.get("stage", 1),
                        "days_since": days_since,
                        "timestamp": record["timestamp"]
                    })
            except Exception:
                pass
                
        # Render Follow-Up Radar UI
        st.markdown("<h5 style='color: var(--primary-accent); font-family: \"Orbitron\", sans-serif; font-weight: 700; margin-top: 25px; letter-spacing: 1.5px;'>🚨 SMART FOLLOW-UP RADAR</h5>", unsafe_allow_html=True)
        if due_leads:
            st.markdown(f"<div style='font-family: \"Share Tech Mono\", monospace; font-size: 0.78rem; color: var(--warning-accent); margin-bottom: 12px;'>⏰ DETECTED COLD LEADS ({len(due_leads)} REQUIRE IMMEDIATE ATTENTION):</div>", unsafe_allow_html=True)
            
            # Display due leads in a clean 2-column grid
            due_col1, due_col2 = st.columns([1, 1])
            for idx, item in enumerate(due_leads[:4]):
                col_target = due_col1 if idx % 2 == 0 else due_col2
                with col_target:
                    st.markdown(f"""
                    <div class="due-card">
                        <div>
                            <div class="due-title">⚠️ {item['business_name']}</div>
                            <div class="due-subtitle">{item['category']} • Contacted {item['days_since']}d ago ({item['last_channel']})</div>
                        </div>
                        <span style="font-family: 'Share Tech Mono', monospace; font-size: 0.72rem; background: #ea580c; color: white; padding: 2px 8px; border-radius: 4px; font-weight: 700; text-shadow: none;">STAGE {item['last_stage']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            if len(due_leads) > 4:
                st.markdown(f"<div style='font-family: \"Share Tech Mono\", monospace; font-size: 0.7rem; color: var(--text-muted); text-align: right; margin-top: 5px;'>and {len(due_leads) - 4} more leads are due for follow-up...</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: rgba(16, 185, 129, 0.04); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 8px; margin-bottom: 20px;'>
                <span style='color: #10b981; font-size: 1.1rem;'>🎉</span>
                <span style='font-family: "Share Tech Mono", monospace; font-size: 0.72rem; color: var(--text-muted);'>ALL RECENT LEADS ARE UP-TO-DATE. NO URGENT FOLLOW-UPS PENDING.</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        # ==========================================
        # [END] SMART FOLLOW-UP RADAR HUD
        # ==========================================

        outreach_panel1, outreach_panel2 = st.columns([1, 1])
        with outreach_panel1:
            lead_df = filtered_df if not filtered_df.empty else display_df
            lead_names = lead_df["Business Name"].tolist()
            selected_lead = st.selectbox("Select Target Lead:", lead_names)
            
            # ---- Previously Contacted Badge ----
            prior_outreach = get_lead_outreach_info(selected_lead)
            if prior_outreach:
                channels_used = list(set(r["channel"] for r in prior_outreach))
                last_contact = prior_outreach[0]  # most recent (list is newest-first)
                if len(channels_used) > 1:
                    badge_class = "outreach-badge-both"
                    badge_icon = "🔄"
                    badge_text = f"Contacted {len(prior_outreach)}x via {', '.join(channels_used)}"
                elif channels_used[0] == "WhatsApp":
                    badge_class = "outreach-badge-wa"
                    badge_icon = "💬"
                    badge_text = f"WhatsApp sent on {last_contact['timestamp'][:10]}"
                else:
                    badge_class = "outreach-badge-email"
                    badge_icon = "📧"
                    badge_text = f"Email sent on {last_contact['timestamp'][:10]}"
                st.markdown(f"""
                <div class="outreach-badge {badge_class}">
                    <span>{badge_icon}</span>
                    <span>✅ {badge_text}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Calculate next stage based on history count
            next_stage = len(prior_outreach) + 1
            
            # Select Campaign Template options based on stage
            templates = [
                "B2B Partnership Proposal",
                "Advanced Equipment Supply",
                "Software/EMR Demo Pitch",
                "📧 Email Introduction"
            ]
            
            if next_stage >= 2:
                # Add follow-up options if they have been contacted
                templates.extend([
                    "Follow-up 1: Quick Check-in",
                    "Follow-up 2: Demo Proposal",
                    "Follow-up 3: Custom Offer"
                ])
            
            campaign_type = st.selectbox("Select Campaign Template:", templates)
            
            sender_name = st.text_input("Your Name/Signature", value="Eye Finder Sales Team")
            sender_email = st.text_input("Your Email (for email template)", value="sales@eyefinder.com") if campaign_type == "📧 Email Introduction" else ""
        
        # Find lead details
        lead_row = display_df[display_df["Business Name"] == selected_lead].iloc[0]
        lead_phone = lead_row["Phone"]
        lead_category = lead_row["Category"]
        lead_address = lead_row["Address"]
        current_city = st.session_state.get("current_city", "Unknown")
        current_state = st.session_state.get("scan_state", "")
        # Resolve state from LOCATION_MATRIX if not set
        if not current_state or current_state == "Select State...":
            for s, cities in LOCATION_MATRIX.items():
                if current_city in cities or current_city.replace(" (Multi-City)", "") == s:
                    current_state = s
                    break
            if not current_state or current_state == "Select State...":
                current_state = "Unknown"
        
        # Build templates based on selected category & details
        if campaign_type == "B2B Partnership Proposal":
            subject = f"Collaboration Proposal: Eye Finder & {selected_lead}"
            message = (
                f"Hello Team {selected_lead},\n\n"
                f"I hope this message finds you well. We are reaching out from our healthcare network to discuss a strategic partnership. "
                f"We have identified your facility at {lead_address} as a premier {lead_category} in the region.\n\n"
                f"We would love to share how we can collaborate to drive more patients needing specialized eye care. "
                f"Please let us know a suitable time to connect next week.\n\n"
                f"Best regards,\n"
                f"{sender_name}"
            )
        elif campaign_type == "Advanced Equipment Supply":
            subject = f"Ophthalmic Diagnostic Equipments Proposal for {selected_lead}"
            message = (
                f"Dear Director,\n\n"
                f"We are offering a suite of modern diagnostic and surgical ophthalmic devices designed specifically for {lead_category}s. "
                f"Our new laser and imaging solutions help doctors at {selected_lead} perform screenings with higher precision.\n\n"
                f"Would you be interested in a brief virtual demo or receiving our product catalog for review?\n\n"
                f"Sincerely,\n"
                f"{sender_name}"
            )
        elif campaign_type == "📧 Email Introduction":
            subject = f"Introduction: Eye Care Solutions for {selected_lead}"
            message = (
                f"Dear {selected_lead} Team,\n\n"
                f"I'm writing to introduce our comprehensive eye care solutions platform. "
                f"We specialize in connecting {lead_category}s with cutting-edge diagnostic tools, patient management systems, and industry partnerships.\n\n"
                f"Having identified your facility at {lead_address} as a leading eye care provider, "
                f"we believe there's a strong opportunity for collaboration that could benefit both your patients and practice.\n\n"
                f"Key areas we can support:\n"
                f"• Advanced diagnostic equipment procurement\n"
                f"• Cloud-based patient management systems\n"
                f"• Strategic B2B partnerships & referral networks\n"
                f"• Staff training and certification programs\n\n"
                f"I would welcome the opportunity to discuss how we can add value to your practice. "
                f"Please feel free to reply to this email or reach me at the contact below.\n\n"
                f"Warm regards,\n"
                f"{sender_name}\n"
                f"{sender_email}"
            )
        elif campaign_type == "Follow-up 1: Quick Check-in":
            subject = f"Re: Collaboration Proposal: Eye Finder & {selected_lead}"
            message = (
                f"Hello Team {selected_lead},\n\n"
                f"I wanted to follow up briefly on the partnership proposal I sent over a few days ago. "
                f"I understand your schedule is busy, but I'd love to know if you've had a chance to review it.\n\n"
                f"Do you have 5 minutes for a quick introductory call next week?\n\n"
                f"Best regards,\n"
                f"{sender_name}"
            )
        elif campaign_type == "Follow-up 2: Demo Proposal":
            subject = f"Complimentary clinical equipment demonstration for {selected_lead}"
            message = (
                f"Dear Director,\n\n"
                f"Just dropping a note to see if there is any interest in exploring new eye care diagnostic equipment or clinical software for {selected_lead}.\n\n"
                f"We would be glad to set up a short 10-minute online presentation for your team at any convenient time.\n\n"
                f"Sincerely,\n"
                f"{sender_name}"
            )
        elif campaign_type == "Follow-up 3: Custom Offer":
            subject = f"Special Partnership Terms for {selected_lead}"
            message = (
                f"Hello,\n\n"
                f"As a final touchpoint, we are offering special trial terms on our patient management system and diagnostic platforms for premium practices like {selected_lead}.\n\n"
                f"Please let me know if you would like to receive the custom collaboration plan.\n\n"
                f"Regards,\n"
                f"{sender_name}"
            )
        else:  # Software/EMR Demo Pitch
            subject = f"Transform Patient Workflows at {selected_lead}"
            message = (
                f"Hello,\n\n"
                f"Managing clinical workflows, patient appointments, and digital EMRs can be challenging for busy {lead_category}s like {selected_lead}. "
                f"We build secure, cloud-based practice management software tailored to ophthalmologists.\n\n"
                f"I'd love to schedule a 10-minute demo to show you how we can automate your check-ins and billing.\n\n"
                f"Regards,\n"
                f"{sender_name}"
            )
            
        with outreach_panel2:
            st.markdown(f"**Subject:** `{subject}`")
            st.text_area("Generated Outreach Message:", value=message, height=250)
            
            # Action Buttons — Log outreach then open link
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                # WhatsApp — Log + Send
                if lead_phone != "N/A":
                    encoded_msg = urllib.parse.quote(message)
                    clean_phone = re.sub(r'\D', '', lead_phone)
                    if len(clean_phone) == 10:
                        clean_phone = "91" + clean_phone
                    elif len(clean_phone) > 10 and clean_phone.startswith("0"):
                        clean_phone = "91" + clean_phone[1:]
                    wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
                    
                    if st.button("📲 LOG & SEND WHATSAPP", key="btn_wa_log", use_container_width=True):
                        record_outreach(selected_lead, lead_category, lead_address, lead_phone, "WhatsApp", campaign_type, current_city, current_state)
                        st.session_state.outreach_log_pending = "whatsapp"
                        st.rerun()
                    
                    # Show the actual link after logging
                    if st.session_state.get("outreach_log_pending") == "whatsapp":
                        st.success("✅ Outreach logged! Click below to open WhatsApp:")
                        st.link_button("💬 OPEN WHATSAPP NOW", wa_url, use_container_width=True)
                        st.session_state.outreach_log_pending = None
                else:
                    st.button("💬 WhatsApp N/A", disabled=True, use_container_width=True)
            
            with action_col2:
                # Email — Log + Send
                encoded_subject = urllib.parse.quote(subject)
                encoded_body = urllib.parse.quote(message)
                mailto_url = f"mailto:?subject={encoded_subject}&body={encoded_body}"
                
                if st.button("📨 LOG & COMPOSE EMAIL", key="btn_email_log", use_container_width=True):
                    record_outreach(selected_lead, lead_category, lead_address, lead_phone, "Email", campaign_type, current_city, current_state)
                    st.session_state.outreach_log_pending = "email"
                    st.rerun()
                
                # Show the actual link after logging
                if st.session_state.get("outreach_log_pending") == "email":
                    st.success("✅ Outreach logged! Click below to compose email:")
                    st.link_button("📧 OPEN EMAIL NOW", mailto_url, use_container_width=True)
                    st.session_state.outreach_log_pending = None
 
        # ==========================================
        # [START] LEAD OUTREACH TIMELINE WIDGET
        # ==========================================
        st.markdown("<br><hr style='border-color: var(--panel-border); margin: 20px 0 15px 0;'>", unsafe_allow_html=True)
        st.markdown(f"<h5 style='color: var(--primary-accent); font-family: \"Orbitron\", sans-serif; font-weight: 700; margin-bottom: 12px; letter-spacing: 1px;'>⏳ LEAD OUTREACH TIMELINE: {selected_lead.upper()}</h5>", unsafe_allow_html=True)
        
        if not prior_outreach:
            st.info("No communications have occurred with this target yet. Ready for Initial Contact.")
        else:
            st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
            # Sort prior outreach from oldest to newest chronologically for timeline display
            chrono_history = sorted(prior_outreach, key=lambda x: x["timestamp"])
            for record in chrono_history:
                channel_icon = "💬" if record["channel"] == "WhatsApp" else "📧"
                stage_num = record.get("stage", 1)
                st.markdown(f"""
                <div class="timeline-node completed">
                    <div class="timeline-label">✓ STAGE {stage_num} • {record['channel']} ({record['timestamp']})</div>
                    <div class="timeline-title">{record['campaign_type']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Preview the next pending step
            st.markdown(f"""
            <div class="timeline-node pending">
                <div class="timeline-label" style="color: #f97316;">⚡ STAGE {next_stage} (PENDING)</div>
                <div class="timeline-title" style="color: var(--text-muted);">Ready to initiate: {campaign_type}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        # ==========================================
        # [END] LEAD OUTREACH TIMELINE WIDGET
        # ==========================================

        # ============================================
        # 📋 OUTREACH HISTORY LOG PANEL
        # ============================================
        st.markdown("<hr style='border-color: var(--panel-border); margin: 30px 0 10px 0;'>", unsafe_allow_html=True)
        
        history = st.session_state.outreach_history
        total_outreach = len(history)
        wa_count = sum(1 for h in history if h["channel"] == "WhatsApp")
        email_count = sum(1 for h in history if h["channel"] == "Email")
        unique_leads = len(set(h["business_name"].strip().lower() for h in history)) if history else 0
        
        # History Header
        st.markdown(f"""
        <div class="outreach-history-header">
            <div class="oh-icon">📋</div>
            <div>
                <div class="oh-title">OUTREACH HISTORY LOG</div>
                <div class="oh-subtitle">TOTAL ACTIONS: {total_outreach} // UNIQUE LEADS: {unique_leads} // SESSION ACTIVE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats Grid
        st.markdown(f"""
        <div class="outreach-stats-grid">
            <div class="outreach-stat-card">
                <span class="stat-value">{total_outreach}</span>
                <span class="stat-label">Total Outreach</span>
            </div>
            <div class="outreach-stat-card">
                <span class="stat-value">{wa_count}</span>
                <span class="stat-label">💬 WhatsApp</span>
            </div>
            <div class="outreach-stat-card">
                <span class="stat-value">{email_count}</span>
                <span class="stat-label">📧 Email</span>
            </div>
            <div class="outreach-stat-card">
                <span class="stat-value">{unique_leads}</span>
                <span class="stat-label">Unique Leads</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if history:
            # Controls: Filter, Export, Clear
            ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
            with ctrl_col1:
                history_filter = st.selectbox("Filter History:", ["All", "WhatsApp Only", "Email Only"], key="history_filter_select")
            with ctrl_col2:
                # Export CSV
                history_df = pd.DataFrame(history)
                csv_data = history_df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 EXPORT LOG", csv_data, "outreach_history.csv", "text/csv", use_container_width=True, key="export_outreach_csv")
            with ctrl_col3:
                if st.button("🗑️ CLEAR HISTORY", use_container_width=True, key="clear_outreach_history"):
                    st.session_state.outreach_history = []
                    save_outreach_history_to_drive()
                    st.rerun()
            
            # Filter the history
            filtered_history = history
            if history_filter == "WhatsApp Only":
                filtered_history = [h for h in history if h["channel"] == "WhatsApp"]
            elif history_filter == "Email Only":
                filtered_history = [h for h in history if h["channel"] == "Email"]
            
            # Render history rows
            if filtered_history:
                for record in filtered_history:
                    channel_icon = "💬" if record["channel"] == "WhatsApp" else "📧"
                    status_class = "hr-status-resend" if record["status"] == "Re-sent" else "hr-status-sent"
                    status_label = record["status"].upper()
                    st.markdown(f"""
                    <div class="history-row">
                        <div class="hr-channel">{channel_icon}</div>
                        <div class="hr-info">
                            <div class="hr-name">{record['business_name']}</div>
                            <div class="hr-meta">{record['category']} • {record.get('city', 'N/A')}, {record.get('state', '')} • {record['campaign_type']}</div>
                        </div>
                        <div class="hr-time">{record['timestamp']}</div>
                        <div class="hr-status {status_class}">{status_label}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"No {history_filter.replace(' Only', '').lower()} outreach records found.")
        else:
            st.markdown("""
            <div style='text-align: center; padding: 40px 20px; color: var(--text-muted); font-family: "Share Tech Mono", monospace;'>
                <div style='font-size: 2.5rem; margin-bottom: 12px; opacity: 0.5;'>📭</div>
                <div style='font-size: 0.85rem; letter-spacing: 1px;'>NO OUTREACH HISTORY YET</div>
                <div style='font-size: 0.72rem; margin-top: 6px; opacity: 0.7;'>Send a WhatsApp message or email to start tracking your outreach.</div>
            </div>
            """, unsafe_allow_html=True)



else:
    # Default global system telemetry view
    st.markdown("<br><h3 style='color: var(--primary-accent); font-family: \"Outfit\", sans-serif; font-weight: 700; letter-spacing: 1px;'>📊 GLOBAL TELEMETRY HUD</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="kpi-dashboard-grid">
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">🌐</div>
                <div class="kpi-content">
                    <span class="kpi-label">Cities Covered</span>
                    <span class="kpi-value">250+</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">🏛️</div>
                <div class="kpi-content">
                    <span class="kpi-label">States Covered</span>
                    <span class="kpi-value">28 (All India)</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">⚡</div>
                <div class="kpi-content">
                    <span class="kpi-label">Scraper Nodes</span>
                    <span class="kpi-value">2 Active</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-icon">🛡️</div>
                <div class="kpi-content">
                    <span class="kpi-label">System Uplink</span>
                    <span class="kpi-value">Optimal</span>
                </div>
            </div>
            <div class="kpi-card-glow"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
