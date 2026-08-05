import streamlit as st
from supabase import create_client
import pandas as pd
from numpy import polyfit

st.set_page_config(page_title="ForzaTrack", page_icon="🏋️", layout="wide")

SUPABASE_URL = "https://wqwarvzdjkivxmbsgftx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indxd2FydnpkamtpdnhtYnNnZnR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU2OTYxNjEsImV4cCI6MjEwMTI3MjE2MX0.3e8N8TZj8_kXcA4lmj-y4Sa9aJg232s5huQt9Cm7lsg"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CUSTOM STYLING ---
st.markdown("""
<style>
    /* General spacing and font */
    .main .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* Card style container */
    div[data-testid="stExpander"] {
        border: 1px solid #2D3139;
        border-radius: 12px;
        background-color: #1C1F26;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #1C1F26;
        border: 1px solid #2D3139;
        border-radius: 12px;
        padding: 16px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #14161B;
        border-right: 1px solid #2D3139;
    }

    /* Headers */
    h1, h2, h3 {
        font-weight: 700;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Divider spacing */
    hr {
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# --- EXERCISE DATABASE ---
EXERCISE_DB = {
    "full_gym": {
        "push": ["Bench Press", "Overhead Press", "Incline Dumbbell Press", "Dips", "Cable Fly"],
        "pull": ["Deadlift", "Pull-ups", "Barbell Row", "Lat Pulldown", "Face Pull"],
        "legs": ["Back Squat", "Leg Press", "Romanian Deadlift", "Leg Curl", "Calf Raise"],
        "core": ["Hanging Leg Raise", "Cable Crunch", "Plank"]
    },
    "home_dumbbells": {
        "push": ["Dumbbell Bench Press", "Dumbbell Shoulder Press", "Dumbbell Fly", "Push-ups"],
        "pull": ["Dumbbell Row", "Dumbbell Deadlift", "Renegade Row"],
        "legs": ["Goblet Squat", "Dumbbell Lunges", "Romanian Deadlift (Dumbbell)", "Calf Raise"],
        "core": ["Plank", "Russian Twist", "Leg Raise"]
    },
    "bodyweight_only": {
        "push": ["Push-ups", "Pike Push-ups", "Dips (chair)", "Diamond Push-ups"],
        "pull": ["Pull-ups", "Inverted Row", "Superman"],
        "legs": ["Bodyweight Squat", "Lunges", "Bulgarian Split Squat", "Glute Bridge"],
        "core": ["Plank", "Mountain Climbers", "Leg Raise"]
    }
}

REP_SCHEMES = {
    "strength": {"sets": 5, "reps": "3-5"},
    "hypertrophy": {"sets": 4, "reps": "8-12"},
    "fat_loss": {"sets": 3, "reps": "12-15"},
    "endurance": {"sets": 3, "reps": "15-20"}
}

equipment_options = ["full_gym", "home_dumbbells", "bodyweight_only"]
equipment_labels = {"full_gym": "Full gym", "home_dumbbells": "Home with dumbbells", "bodyweight_only": "Bodyweight only"}
goal_options = ["strength", "hypertrophy", "fat_loss", "endurance"]
goal_labels = {"strength": "Strength", "hypertrophy": "Hypertrophy (muscle size)", "fat_loss": "Fat loss", "endurance": "Endurance"}
experience_options = ["beginner", "intermediate", "advanced"]


def generate_plan(equipment, goal, days_per_week, experience_level):
    exercises = EXERCISE_DB[equipment]
    scheme = REP_SCHEMES[goal]

    sets_adjustment = {"beginner": -1, "intermediate": 0, "advanced": 1}
    adjusted_sets = max(2, scheme["sets"] + sets_adjustment[experience_level])

    if days_per_week <= 2:
        split = ["full_body", "full_body"]
    elif days_per_week == 3:
        split = ["push", "pull", "legs"]
    elif days_per_week == 4:
        split = ["push", "pull", "legs", "full_body"]
    else:
        split = ["push", "pull", "legs", "push", "pull", "legs"][:days_per_week]

    plan_days = []
    for day_num, day_type in enumerate(split[:days_per_week], start=1):
        day_exercises = []
        if day_type == "full_body":
            for group in ["push", "pull", "legs"]:
                day_exercises.append(exercises[group][0])
            day_exercises.append(exercises["core"][0])
        else:
            group_exercises = exercises[day_type][:3]
            day_exercises.extend(group_exercises)
            day_exercises.append(exercises["core"][day_num % len(exercises["core"])])

        plan_days.append({
            "day_number": day_num,
            "day_type": day_type,
            "exercises": [
                {"name": ex, "sets": adjusted_sets, "reps": scheme["reps"]}
                for ex in day_exercises
            ]
        })

    return plan_days


# --- LOGIN / SIGN UP ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align: center;'>🏋️ ForzaTrack</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Generate your plan, track your progress, compare your strength.</p>", unsafe_allow_html=True)
    st.write("")

    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    with col_center:
        tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

        with tab_login:
            st.write("")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            st.write("")
            if st.button("Log in", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.session_state.access_token = res.session.access_token
                    st.rerun()
                except Exception as e:
                    st.error(f"Login error: {e}")

        with tab_signup:
            st.write("")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            st.write("")
            if st.button("Sign up", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("Account created! Check your email to confirm, then log in.")
                except Exception as e:
                    st.error(f"Sign up error: {e}")

# --- MAIN APP ---
else:
    user = st.session_state.user

    supabase.postgrest.auth(st.session_state.access_token)

    try:
        profile_response = supabase.table("fitness_profiles").select("*").eq("user_id", user.id).execute()
        existing_profile = profile_response.data[0] if profile_response.data else None
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        existing_profile = None

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown("## 🏋️ ForzaTrack")
        st.markdown(f"👋 **{user.email}**")
        st.divider()

        page = st.radio(
            "Navigate",
            ["👤 Profile", "🎯 Generate Plan", "📋 My Plans", "📝 Log Workout", "📈 Progress", "💪 Strength Level"],
            label_visibility="collapsed"
        )

        st.divider()
        if st.button("Log out", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.access_token = None
            st.rerun()

    # --- PAGE: PROFILE ---
    if page == "👤 Profile":
        st.markdown("# 👤 Your Profile")
        st.caption("This information powers your plan and strength comparisons.")
        st.write("")

        if existing_profile:
            st.info("You already have a profile. Update it below anytime.")

        with st.container(border=True):
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
                equipment = st.selectbox(
                    "Available equipment", equipment_options,
                    format_func=lambda x: equipment_labels[x],
                    index=equipment_options.index(existing_profile['equipment']) if existing_profile and existing_profile.get('equipment') else 0
                )
            with col7:
                goal = st.selectbox(
                    "Main goal", goal_options,
                    format_func=lambda x: goal_labels[x],
                    index=goal_options.index(existing_profile['goal']) if existing_profile and existing_profile.get('goal') else 0
                )

            st.write("")
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

    # --- PAGE: GENERATE PLAN ---
    elif page == "🎯 Generate Plan":
        st.markdown("# 🎯 Generate a Plan")
        st.write("")

        if not existing_profile:
            st.warning("Please complete your profile first before generating a plan.")
        else:
            with st.container(border=True):
                st.markdown(f"**Goal:** {goal_labels[existing_profile['goal']]} &nbsp;|&nbsp; "
                            f"**Days/week:** {existing_profile['available_days']} &nbsp;|&nbsp; "
                            f"**Equipment:** {equipment_labels.get(existing_profile['equipment'], existing_profile['equipment'])} &nbsp;|&nbsp; "
                            f"**Level:** {existing_profile['experience_level'].capitalize()}")

            st.write("")
            plan_name = st.text_input("Plan name", value=f"My {existing_profile['goal'].capitalize()} Plan")

            if st.button("🎲 Generate plan", type="primary", use_container_width=True):
                generated_days = generate_plan(
                    existing_profile['equipment'],
                    existing_profile['goal'],
                    existing_profile['available_days'],
                    existing_profile['experience_level']
                )
                st.session_state.generated_plan_preview = generated_days
                st.session_state.generated_plan_name = plan_name

            if "generated_plan_preview" in st.session_state:
                st.write("")
                st.markdown("### Preview")
                for day in st.session_state.generated_plan_preview:
                    with st.container(border=True):
                        st.markdown(f"**Day {day['day_number']} — {day['day_type'].replace('_', ' ').title()}**")
                        for ex in day['exercises']:
                            st.write(f"🔹 {ex['name']} — {ex['sets']} sets × {ex['reps']} reps")

                st.write("")
                if st.button("✅ Save this plan", type="primary", use_container_width=True):
                    try:
                        plan_response = supabase.table("workout_plans").insert({
                            "user_id": user.id,
                            "plan_name": st.session_state.generated_plan_name,
                            "goal": existing_profile['goal'],
                            "days_per_week": existing_profile['available_days']
                        }).execute()

                        new_plan_id = plan_response.data[0]['id']

                        for day in st.session_state.generated_plan_preview:
                            for ex in day['exercises']:
                                supabase.table("plan_exercises").insert({
                                    "plan_id": new_plan_id,
                                    "day_number": day['day_number'],
                                    "exercise_name": ex['name'],
                                    "sets": ex['sets'],
                                    "reps": ex['reps']
                                }).execute()

                        st.success(f"Plan '{st.session_state.generated_plan_name}' saved!")
                        del st.session_state.generated_plan_preview
                        del st.session_state.generated_plan_name
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving plan: {e}")

    # --- PAGE: MY PLANS ---
    elif page == "📋 My Plans":
        st.markdown("# 📋 Your Plans")
        st.write("")
        try:
            plans_response = supabase.table("workout_plans").select("*").order("created_at", desc=True).execute()
            plans_data = plans_response.data

            if not plans_data:
                st.info("No plans saved yet. Generate one in the 'Generate Plan' page.")
            else:
                for plan in plans_data:
                    with st.expander(f"📄 {plan['plan_name']}  —  {plan['days_per_week']} days/week · {goal_labels.get(plan['goal'], plan['goal'])}"):
                        exercises_response = supabase.table("plan_exercises").select("*").eq("plan_id", plan['id']).order("day_number").execute()
                        exercises_data = exercises_response.data

                        if exercises_data:
                            days_grouped = {}
                            for ex in exercises_data:
                                days_grouped.setdefault(ex['day_number'], []).append(ex)

                            for day_num in sorted(days_grouped.keys()):
                                st.markdown(f"**Day {day_num}**")
                                for ex in days_grouped[day_num]:
                                    st.write(f"🔹 {ex['exercise_name']} — {ex['sets']} sets × {ex['reps']} reps")
                                st.write("")
        except Exception as e:
            st.error(f"Error loading plans: {e}")

    # --- PAGE: LOG WORKOUT ---
    elif page == "📝 Log Workout":
        st.markdown("# 📝 Log a Workout")
        st.write("")

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                log_date = st.date_input("Date", value=pd.Timestamp.today())
                exercise_name = st.text_input("Exercise", placeholder="e.g. Bench Press")
            with col2:
                sets = st.number_input("Sets", min_value=1, max_value=20, value=3)
                reps = st.number_input("Reps", min_value=1, max_value=100, value=10)
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=20.0, step=2.5)

            st.write("")
            if st.button("💾 Save log", type="primary", use_container_width=True):
                if not exercise_name.strip():
                    st.warning("Please enter an exercise name.")
                else:
                    try:
                        supabase.table("workout_logs").insert({
                            "user_id": user.id,
                            "log_date": log_date.isoformat(),
                            "exercise_name": exercise_name.strip(),
                            "sets": int(sets),
                            "reps": int(reps),
                            "weight_kg": float(weight_kg)
                        }).execute()
                        st.success("Workout logged!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving log: {e}")

    # --- PAGE: PROGRESS ---
    elif page == "📈 Progress":
        st.markdown("# 📈 Your Progress")
        st.write("")
        try:
            logs_response = supabase.table("workout_logs").select("*").order("log_date").execute()
            logs_data = logs_response.data

            if not logs_data:
                st.info("No workouts logged yet. Log one in the 'Log Workout' page.")
            else:
                df_logs = pd.DataFrame(logs_data)
                df_logs['log_date'] = pd.to_datetime(df_logs['log_date'])

                exercises_available = sorted(df_logs['exercise_name'].unique())
                selected_exercise = st.selectbox("Select exercise", exercises_available)

                df_exercise = df_logs[df_logs['exercise_name'] == selected_exercise].sort_values('log_date')

                if len(df_exercise) < 2:
                    st.info("Log this exercise at least twice to see a progress chart.")
                    st.dataframe(
                        df_exercise[['log_date', 'sets', 'reps', 'weight_kg']].rename(columns={
                            'log_date': 'Date', 'sets': 'Sets', 'reps': 'Reps', 'weight_kg': 'Weight (kg)'
                        }),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.line_chart(df_exercise.set_index('log_date')['weight_kg'])

                    df_exercise = df_exercise.reset_index(drop=True)
                    df_exercise['days_since_start'] = (df_exercise['log_date'] - df_exercise['log_date'].min()).dt.days

                    if df_exercise['days_since_start'].nunique() > 1:
                        x = df_exercise['days_since_start'].values
                        y = df_exercise['weight_kg'].values
                        slope, intercept = polyfit(x, y, 1)

                        st.write("")
                        st.markdown("### 🔮 Simple projection")

                        if slope > 0:
                            current_weight = y[-1]
                            target_weight = st.number_input(
                                f"Target weight for {selected_exercise} (kg)",
                                min_value=current_weight, max_value=current_weight + 200.0,
                                value=current_weight + 10.0, step=2.5
                            )
                            days_needed = (target_weight - intercept) / slope - x[-1]
                            if days_needed > 0:
                                weeks_needed = days_needed / 7
                                st.metric(
                                    f"Estimated time to reach {target_weight}kg",
                                    f"~{weeks_needed:.1f} weeks"
                                )
                                st.caption("Rough estimate based on your recent trend. Real progress depends on many factors (recovery, nutrition, consistency).")
                            else:
                                st.info("You may have already reached this target based on your trend!")
                        else:
                            st.info("Your recent trend is flat or decreasing — keep logging to refine this.")

                        st.dataframe(
                            df_exercise[['log_date', 'sets', 'reps', 'weight_kg']].rename(columns={
                                'log_date': 'Date', 'sets': 'Sets', 'reps': 'Reps', 'weight_kg': 'Weight (kg)'
                            }),
                            use_container_width=True, hide_index=True
                        )
        except Exception as e:
            st.error(f"Error loading progress: {e}")

    # --- PAGE: STRENGTH LEVEL ---
    elif page == "💪 Strength Level":
        st.markdown("# 💪 Strength Level")
        st.caption("Based on your one-rep max compared to public strength standards.")
        st.write("")

        if not existing_profile or not existing_profile.get('body_weight_kg') or not existing_profile.get('gender'):
            st.warning("Please complete your profile (body weight and gender) first.")
        else:
            with st.container(border=True):
                comparison_exercises = ["Bench Press", "Squat", "Deadlift"]
                selected_lift = st.selectbox("Select lift", comparison_exercises)
                your_max = st.number_input(f"Your {selected_lift} 1-rep max (kg)", min_value=0.0, max_value=500.0, value=60.0, step=2.5)

                st.write("")
                check_pressed = st.button("🏆 Check my level", type="primary", use_container_width=True)

            if check_pressed:
                try:
                    standards_response = supabase.table("strength_standards").select("*").eq(
                        "exercise_name", selected_lift
                    ).eq("gender", existing_profile['gender']).execute()
                    standards_data = standards_response.data

                    if not standards_data:
                        st.error("No standards found for this exercise/gender combination.")
                    else:
                        body_weight = existing_profile['body_weight_kg']
                        your_ratio = your_max / body_weight

                        standards_sorted = sorted(standards_data, key=lambda s: s['bodyweight_ratio'])

                        level_reached = "below beginner"
                        for standard in standards_sorted:
                            if your_ratio >= standard['bodyweight_ratio']:
                                level_reached = standard['level']

                        st.write("")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Your ratio (lift/bodyweight)", f"{your_ratio:.2f}x")
                        with col2:
                            st.metric("Your level", level_reached.capitalize())

                        st.write("")
                        st.markdown("**Standards for your gender:**")
                        df_standards = pd.DataFrame(standards_sorted)
                        df_standards['Weight needed (kg)'] = (df_standards['bodyweight_ratio'] * body_weight).round(1)
                        st.dataframe(
                            df_standards[['level', 'bodyweight_ratio', 'Weight needed (kg)']].rename(columns={
                                'level': 'Level', 'bodyweight_ratio': 'Ratio'
                            }),
                            use_container_width=True, hide_index=True
                        )
                except Exception as e:
                    st.error(f"Error checking strength level: {e}")