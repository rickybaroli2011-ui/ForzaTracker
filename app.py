import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="ForzaTrack", page_icon="🏋️", layout="wide")

SUPABASE_URL = "https://wqwarvzdjkivxmbsgftx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indxd2FydnpkamtpdnhtYnNnZnR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU2OTYxNjEsImV4cCI6MjEwMTI3MjE2MX0.3e8N8TZj8_kXcA4lmj-y4Sa9aJg232s5huQt9Cm7lsg"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

st.title("🏋️ ForzaTrack")
st.caption("Genera la tua scheda, traccia i progressi, confronta la tua forza.")

# --- LOGIN / SIGN UP ---
if st.session_state.user is None:
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        st.subheader("Log in")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.access_token = res.session.access_token
                st.rerun()
            except Exception as e:
                st.error(f"Login error: {e}")

    with tab_signup:
        st.subheader("Create a new account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
        if st.button("Sign up", type="primary"):
            try:
                res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                st.success("Account created! Check your email to confirm, then log in.")
            except Exception as e:
                st.error(f"Sign up error: {e}")

# --- MAIN APP ---
else:
    user = st.session_state.user
    col_greeting, col_logout = st.columns([4, 1])
    with col_greeting:
        st.write(f"👋 Hi, **{user.email}**")
    with col_logout:
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.access_token = None
            st.rerun()

    supabase.postgrest.auth(st.session_state.access_token)

    st.divider()

    # --- CHECK IF PROFILE EXISTS ---
    try:
        profile_response = supabase.table("fitness_profiles").select("*").eq("user_id", user.id).execute()
        existing_profile = profile_response.data[0] if profile_response.data else None
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        existing_profile = None

    st.subheader("👤 Your fitness profile")

    if existing_profile:
        st.info("You already have a profile. You can update it below anytime.")

    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input(
            "Age", min_value=10, max_value=100,
            value=existing_profile['age'] if existing_profile and existing_profile.get('age') else 25
        )
    with col2:
        gender = st.selectbox(
            "Gender", ["M", "F"],
            index=["M", "F"].index(existing_profile['gender']) if existing_profile and existing_profile.get('gender') else 0
        )
    with col3:
        body_weight = st.number_input(
            "Body weight (kg)", min_value=30.0, max_value=250.0,
            value=float(existing_profile['body_weight_kg']) if existing_profile and existing_profile.get('body_weight_kg') else 70.0
        )

    col4, col5 = st.columns(2)
    with col4:
        experience_options = ["beginner", "intermediate", "advanced"]
        experience_level = st.selectbox(
            "Experience level", experience_options,
            index=experience_options.index(existing_profile['experience_level']) if existing_profile and existing_profile.get('experience_level') else 0
        )
    with col5:
        available_days = st.slider(
            "Days available per week", 1, 6,
            value=existing_profile['available_days'] if existing_profile and existing_profile.get('available_days') else 3
        )

    col6, col7 = st.columns(2)
    with col6:
        equipment_options = ["full_gym", "home_dumbbells", "bodyweight_only"]
        equipment_labels = {"full_gym": "Full gym", "home_dumbbells": "Home with dumbbells", "bodyweight_only": "Bodyweight only"}
        equipment = st.selectbox(
            "Available equipment", equipment_options,
            format_func=lambda x: equipment_labels[x],
            index=equipment_options.index(existing_profile['equipment']) if existing_profile and existing_profile.get('equipment') else 0
        )
    with col7:
        goal_options = ["strength", "hypertrophy", "fat_loss", "endurance"]
        goal_labels = {"strength": "Strength", "hypertrophy": "Hypertrophy (muscle size)", "fat_loss": "Fat loss", "endurance": "Endurance"}
        goal = st.selectbox(
            "Main goal", goal_options,
            format_func=lambda x: goal_labels[x],
            index=goal_options.index(existing_profile['goal']) if existing_profile and existing_profile.get('goal') else 0
        )

    if st.button("💾 Save profile", type="primary", use_container_width=True):
        try:
            profile_data = {
                "user_id": user.id,
                "age": int(age),
                "gender": gender,
                "body_weight_kg": float(body_weight),
                "experience_level": experience_level,
                "available_days": int(available_days),
                "equipment": equipment,
                "goal": goal
            }
            if existing_profile:
                supabase.table("fitness_profiles").update(profile_data).eq("user_id", user.id).execute()
            else:
                supabase.table("fitness_profiles").insert(profile_data).execute()
            st.success("Profile saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving profile: {e}")

st.divider()
st.caption("ForzaTrack • Phase 2: login and profile")