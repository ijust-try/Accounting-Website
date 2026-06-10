import streamlit as st
from datetime import date, timedelta
from backend import (
    login_user, register_user, reset_password,
    send_otp, verify_otp, is_email_allowed, is_email_registered,
)

st.set_page_config(
    page_title="Hostel Management",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .auth-title { text-align: center; margin-bottom: 0.25rem; }
    .auth-subtitle { text-align: center; color: #6b7280; font-size: 0.95rem; margin-bottom: 1.25rem; }
    .auth-caption { text-align: center; color: #6b7280; font-size: 0.85rem; margin: 0.5rem 0 0.75rem; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

def go_to(page):
    st.session_state.page = page
    st.rerun()

# ════════════════════════════════════════════════════════════
# AUTH PAGES
# ════════════════════════════════════════════════════════════
if not st.session_state.logged_in:

    if st.session_state.page == "login":
        _, center, _ = st.columns([1, 2, 1])
        with center:
            with st.container(border=True):
                st.markdown('<h2 class="auth-title">Login</h2>', unsafe_allow_html=True)
                st.markdown('<p class="auth-subtitle">Sign in with your account</p>', unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter your user ID")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                _, login_col, _ = st.columns([1, 1.4, 1])
                with login_col:
                    if st.button("Login", type="primary", use_container_width=True):
                        if login_user(username, password):
                            st.session_state.logged_in = True
                            st.success("Login successful")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                if st.button("Forgot password?", use_container_width=True):
                    go_to("forgot_password")
                st.divider()
                st.markdown('<p class="auth-caption">Don\'t have an account?</p>', unsafe_allow_html=True)
                _, register_col, _ = st.columns([1, 1.4, 1])
                with register_col:
                    if st.button("Create new account", use_container_width=True):
                        go_to("register")

    elif st.session_state.page == "forgot_password":
        if "fp_otp_sent" not in st.session_state:
            st.session_state.fp_otp_sent = False
        if "fp_email" not in st.session_state:
            st.session_state.fp_email = ""
        if "fp_user_id" not in st.session_state:
            st.session_state.fp_user_id = ""

        _, center, _ = st.columns([1, 2, 1])
        with center:
            with st.container(border=True):
                st.markdown('<h2 class="auth-title">Reset Password</h2>', unsafe_allow_html=True)

                if not st.session_state.fp_otp_sent:
                    st.markdown('<p class="auth-subtitle">Enter your username and email to receive an OTP</p>', unsafe_allow_html=True)
                    fp_user_id = st.text_input("Username", placeholder="Your login username")
                    fp_email   = st.text_input("Email", placeholder="Your registered email")
                    if st.button("Send OTP", type="primary", use_container_width=True):
                        if not fp_user_id or not fp_email:
                            st.error("Please fill in all fields.")
                        else:
                            result = reset_password(fp_user_id, fp_email, None, check_only=True)
                            if result != "ok":
                                st.error(result)
                            else:
                                ok, err = send_otp(fp_email)
                                if ok:
                                    st.session_state.fp_otp_sent = True
                                    st.session_state.fp_email    = fp_email.strip().lower()
                                    st.session_state.fp_user_id  = fp_user_id
                                    st.rerun()
                                else:
                                    st.error(f"Failed to send OTP: {err}")
                else:
                    st.markdown(f'<p class="auth-subtitle">OTP sent to {st.session_state.fp_email}</p>', unsafe_allow_html=True)
                    fp_otp      = st.text_input("Enter OTP", placeholder="6-digit code from email")
                    fp_new_pass = st.text_input("New Password", type="password", placeholder="Choose a new password")
                    fp_confirm  = st.text_input("Confirm Password", type="password", placeholder="Re-enter new password")
                    if st.button("Reset Password", type="primary", use_container_width=True):
                        if not fp_otp or not fp_new_pass:
                            st.error("All fields are required.")
                        elif fp_new_pass != fp_confirm:
                            st.error("Passwords do not match.")
                        else:
                            otp_ok, otp_err = verify_otp(st.session_state.fp_email, fp_otp)
                            if not otp_ok:
                                st.error(otp_err)
                            else:
                                result = reset_password(st.session_state.fp_user_id,
                                                        st.session_state.fp_email,
                                                        fp_new_pass)
                                if result == "Password reset successfully":
                                    st.success("Password reset! Please login.")
                                    st.session_state.fp_otp_sent = False
                                    st.session_state.fp_email    = ""
                                    st.session_state.fp_user_id  = ""
                                    go_to("login")
                                else:
                                    st.error(result)
                    if st.button("Resend OTP", use_container_width=True):
                        ok, err = send_otp(st.session_state.fp_email)
                        if ok:
                            st.success("New OTP sent!")
                        else:
                            st.error(f"Failed: {err}")

                st.divider()
                if st.button("Back to login", use_container_width=True):
                    st.session_state.fp_otp_sent = False
                    st.session_state.fp_email    = ""
                    st.session_state.fp_user_id  = ""
                    go_to("login")

    elif st.session_state.page == "register":
        if "reg_otp_sent" not in st.session_state:
            st.session_state.reg_otp_sent = False
        if "reg_email" not in st.session_state:
            st.session_state.reg_email = ""

        _, center, _ = st.columns([1, 2, 1])
        with center:
            with st.container(border=True):
                st.markdown('<h2 class="auth-title">Create Account</h2>', unsafe_allow_html=True)

                if not st.session_state.reg_otp_sent:
                    st.markdown('<p class="auth-subtitle">Register with an authorized email</p>', unsafe_allow_html=True)
                    reg_email = st.text_input("Email", placeholder="Your authorized email")
                    if st.button("Send OTP", type="primary", use_container_width=True):
                        if not reg_email:
                            st.error("Please enter your email.")
                        elif not is_email_allowed(reg_email):
                            st.error("This email is not authorized to register.")
                        elif is_email_registered(reg_email):
                            st.error("This email is already registered.")
                        else:
                            ok, err = send_otp(reg_email)
                            if ok:
                                st.session_state.reg_otp_sent = True
                                st.session_state.reg_email    = reg_email.strip().lower()
                                st.rerun()
                            else:
                                st.error(f"Failed to send OTP: {err}")
                else:
                    st.markdown(f'<p class="auth-subtitle">OTP sent to {st.session_state.reg_email}</p>', unsafe_allow_html=True)
                    reg_otp      = st.text_input("Enter OTP", placeholder="6-digit code from email")
                    reg_username = st.text_input("Choose Username", placeholder="Your login username")
                    reg_password = st.text_input("Password", type="password", placeholder="Choose a password")
                    reg_confirm  = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                    if st.button("Create Account", type="primary", use_container_width=True):
                        if not reg_otp or not reg_username or not reg_password:
                            st.error("All fields are required.")
                        elif reg_password != reg_confirm:
                            st.error("Passwords do not match.")
                        else:
                            otp_ok, otp_err = verify_otp(st.session_state.reg_email, reg_otp)
                            if not otp_ok:
                                st.error(otp_err)
                            else:
                                result = register_user(reg_username, st.session_state.reg_email, reg_password)
                                if result == "Registered successfully":
                                    st.success("Account created! Please login.")
                                    st.session_state.reg_otp_sent = False
                                    st.session_state.reg_email    = ""
                                    go_to("login")
                                else:
                                    st.error(result)
                    if st.button("Resend OTP", use_container_width=True):
                        ok, err = send_otp(st.session_state.reg_email)
                        if ok:
                            st.success("New OTP sent!")
                        else:
                            st.error(f"Failed: {err}")

                st.divider()
                if st.button("Back to login", use_container_width=True):
                    st.session_state.reg_otp_sent = False
                    st.session_state.reg_email    = ""
                    go_to("login")

# ════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════
else:
    if "dashboard_section" not in st.session_state:
        st.session_state.dashboard_section = "Guest Management"

    NAV_ITEMS = [
        ("Guest Management", "👤"),
        ("Room Status",      "🛏️"),
        ("Payments",         "💰"),
        ("Employees",        "🧑‍💼"),
        ("Expenses",         "💸"),
        ("Reports",          "📊"),
    ]

    st.markdown("""
        <style>
        /* ── hide sidebar always ── */
        section[data-testid="stSidebar"] { display: none; }

        /* ══════════════════════════════════════════
           SHARED NAV WRAPPER
        ══════════════════════════════════════════ */
        .nav-wrapper {
            background: linear-gradient(135deg, #0a0f1e 0%, #0f172a 40%, #1a1040 100%);
            border-bottom: 1px solid rgba(168,85,247,0.25);
            box-shadow: 0 2px 20px rgba(0,0,0,0.4);
            margin: -1rem -1rem 1.75rem -1rem;
            padding: 0;
        }

        /* ── Row 1: brand + logout ── */
        .nav-row1 {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 1.25rem 0.4rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .nav-brand {
            display: flex; align-items: center; gap: 0.5rem;
        }
        .nav-brand-icon {
            font-size: 1.3rem;
            background: linear-gradient(135deg,#a855f7,#6366f1);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 8px rgba(168,85,247,0.5));
        }
        .nav-brand-text {
            font-size: 1.1rem; font-weight: 800; letter-spacing: 0.04em;
            background: linear-gradient(90deg,#f8fafc,#c4b5fd);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .nav-brand-sub {
            font-size: 0.62rem; color: #64748b;
            text-transform: uppercase; letter-spacing: 0.1em;
            margin-top: -2px;
        }

        /* ── Row 2: nav items ── */
        .nav-row2 {
            display: flex;
            align-items: stretch;
            padding: 0 0.5rem;
            gap: 0.1rem;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .nav-row2::-webkit-scrollbar { display: none; }

        /* ══════════════════════════════════════════
           DESKTOP nav buttons (Streamlit columns)
        ══════════════════════════════════════════ */
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker) {
            background: linear-gradient(135deg,#0a0f1e 0%,#0f172a 40%,#1a1040 100%);
            padding: 0.5rem 1.25rem 0.45rem;
            margin: -1rem -1rem 1.75rem -1rem;
            border-bottom: 1px solid rgba(168,85,247,0.25);
            box-shadow: 0 2px 20px rgba(0,0,0,0.4);
            align-items: center;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker) h3 {
            color: #f8fafc !important; margin: 0 !important;
            font-size: 1.1rem !important; white-space: nowrap;
            background: linear-gradient(90deg,#f8fafc,#c4b5fd);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker)
            > div[data-testid="column"]:not(:first-child):not(:last-child) button {
            background: transparent !important; border: none !important;
            border-radius: 0 !important; box-shadow: none !important;
            color: #94a3b8 !important; font-weight: 500 !important;
            font-size: 0.88rem !important; padding: 0.4rem 0.2rem !important;
            min-height: auto !important; border-bottom: 2px solid transparent !important;
            transition: color 0.2s, border-color 0.2s !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker)
            > div[data-testid="column"]:not(:first-child):not(:last-child) button:hover {
            color: #e2e8f0 !important;
            border-bottom: 2px solid rgba(168,85,247,0.5) !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker)
            > div[data-testid="column"]:not(:first-child):not(:last-child) button[kind="primary"] {
            color: #e9d5ff !important; background: transparent !important;
            border-bottom: 2px solid #a855f7 !important; font-weight: 700 !important;
            text-shadow: 0 0 12px rgba(168,85,247,0.6) !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker)
            > div[data-testid="column"]:last-child button {
            background: rgba(239,68,68,0.12) !important;
            border: 1px solid rgba(248,113,113,0.35) !important;
            border-radius: 6px !important;
            color: #fca5a5 !important; font-size: 0.83rem !important;
            transition: background 0.2s !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker)
            > div[data-testid="column"]:last-child button:hover {
            background: rgba(239,68,68,0.25) !important;
        }

        /* ══════════════════════════════════════════
           MOBILE overrides  (≤ 768 px)
        ══════════════════════════════════════════ */
        @media (max-width: 768px) {

            /* hide the desktop Streamlit columns navbar */
            div[data-testid="stHorizontalBlock"]:has(.primary-nav-marker) {
                display: none !important;
            }

            /* show the HTML mobile navbar */
            .mobile-nav { display: block !important; }

            /* main content padding */
            .main .block-container {
                padding-top: 0.5rem !important;
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }

            /* single-column forms */
            div[data-testid="stHorizontalBlock"]:not(:has(.primary-nav-marker)) {
                flex-wrap: wrap !important;
            }
            div[data-testid="stHorizontalBlock"]:not(:has(.primary-nav-marker))
                > div[data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }

            /* bigger tap targets */
            .stButton > button {
                min-height: 2.6rem !important;
                font-size: 0.95rem !important;
            }

            /* metric cards smaller font */
            div[data-testid="stMetric"] label { font-size: 0.72rem !important; }
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                font-size: 1.1rem !important;
            }
        }

        /* mobile nav hidden by default (desktop) */
        .mobile-nav { display: none; }

        /* ── mobile nav styles ── */
        .mobile-nav {
            background: linear-gradient(135deg,#0a0f1e 0%,#0f172a 40%,#1a1040 100%);
            border-bottom: 1px solid rgba(168,85,247,0.25);
            box-shadow: 0 2px 20px rgba(0,0,0,0.4);
            margin: -1rem -1rem 1.25rem -1rem;
            padding: 0;
        }
        .mob-row1 {
            display: flex; align-items: center;
            justify-content: space-between;
            padding: 0.65rem 1rem 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .mob-brand {
            font-size: 1.05rem; font-weight: 800;
            background: linear-gradient(90deg,#f8fafc,#c4b5fd);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .mob-row2 {
            display: flex; overflow-x: auto;
            scrollbar-width: none; gap: 0;
            padding: 0 0.25rem 0;
        }
        .mob-row2::-webkit-scrollbar { display: none; }
        .mob-nav-btn {
            flex: 0 0 auto;
            padding: 0.55rem 0.7rem;
            font-size: 0.78rem; font-weight: 600;
            color: #64748b; white-space: nowrap;
            border-bottom: 2.5px solid transparent;
            cursor: pointer; transition: all 0.18s;
            text-align: center;
        }
        .mob-nav-btn.active {
            color: #e9d5ff;
            border-bottom: 2.5px solid #a855f7;
            text-shadow: 0 0 10px rgba(168,85,247,0.5);
        }
        </style>
    """, unsafe_allow_html=True)

    # ── MOBILE navbar (HTML — hidden on desktop via CSS) ──────
    current_section = st.session_state.dashboard_section
    mob_items_html  = ""
    for name, icon in NAV_ITEMS:
        active_cls = "active" if current_section == name else ""
        mob_items_html += (
            f'<div class="mob-nav-btn {active_cls}">'
            f'{icon} {name}</div>'
        )

    st.markdown(f"""
        <div class="mobile-nav">
            <div class="mob-row1">
                <span class="mob-brand">🏠 Hostel Management</span>
            </div>
            <div class="mob-row2">{mob_items_html}</div>
        </div>
    """, unsafe_allow_html=True)

    # ── DESKTOP navbar (Streamlit columns — hidden on mobile via CSS) ──
    st.markdown('<span class="primary-nav-marker" style="display:none"></span>', unsafe_allow_html=True)
    nav_cols = st.columns([1.2, 1.05, 1.0, 0.95, 1.0, 0.95, 0.95, 0.75])
    with nav_cols[0]:
        st.markdown("### 🏠 Hostel")
    for idx, (name, icon) in enumerate(NAV_ITEMS):
        with nav_cols[idx + 1]:
            selected = st.session_state.dashboard_section == name
            if st.button(f"{icon} {name}", key=f"nav_{name}",
                         type="primary" if selected else "secondary",
                         use_container_width=True):
                st.session_state.dashboard_section = name
                st.rerun()
    with nav_cols[-1]:
        if st.button("Logout", key="logout_top", use_container_width=True):
            for key in ["logged_in", "page", "dashboard_section",
                        "gm_view", "gm_selected_cid",
                        "gm_show_add_customer", "gm_show_add_stay"]:
                st.session_state.pop(key, None)
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()

    section = st.session_state.dashboard_section

    # ════════════════════════════════════════════════════════════
    # GUEST MANAGEMENT
    # ════════════════════════════════════════════════════════════
    if section == "Guest Management":
        from backend import (
            GUEST_GENDERS, GUEST_LOCATIONS, PAYMENT_TYPES, PAYMENT_MODES,
            get_all_customers, get_customer_by_cid, get_customer_by_phone,
            add_customer, update_customer, delete_customer, check_duplicate_customer,
            get_stays_for_customer, add_stay, update_stay, delete_stay,
            get_payments_for_customer, add_payment,
            get_total_paid_by_customer, get_total_paid_for_stay,
            get_remarks_for_customer, add_remark, delete_remark,
            validate_dates,
        )

        if "gm_view" not in st.session_state:
            st.session_state.gm_view = "list"
        if "gm_selected_cid" not in st.session_state:
            st.session_state.gm_selected_cid = None
        if "gm_show_add_customer" not in st.session_state:
            st.session_state.gm_show_add_customer = False
        if "gm_show_add_stay" not in st.session_state:
            st.session_state.gm_show_add_stay = False

        # ── LIST VIEW ────────────────────────────────────────────
        if st.session_state.gm_view == "list":
            st.header("👤 Guest Management")

            if st.button("➕ New Customer", key="btn_new_customer"):
                st.session_state.gm_show_add_customer = not st.session_state.gm_show_add_customer

            if st.session_state.gm_show_add_customer:
                with st.container(border=True):
                    st.subheader("New Customer")
                    c1, c2 = st.columns(2)
                    nc_first  = c1.text_input("First Name*", key="nc_first")
                    nc_last   = c2.text_input("Last Name",   key="nc_last")
                    nc_phone  = c1.text_input("Phone*",      key="nc_phone")
                    nc_aadhar = c2.text_input("Aadhaar",     key="nc_aadhar")
                    nc_emerg  = c1.text_input("Emergency Contact", key="nc_emerg")
                    nc_gender = c2.selectbox("Gender", GUEST_GENDERS, key="nc_gender")
                    st.markdown("**Initial Stay**")
                    s1, s2, s3 = st.columns(3)
                    nc_loc    = s1.selectbox("Location", GUEST_LOCATIONS, key="nc_loc")
                    nc_room   = s2.text_input("Room Number", key="nc_room")
                    nc_rent   = s3.number_input("Base Rent (₹)", min_value=0.0, step=500.0, key="nc_rent")
                    nc_in     = s1.date_input("Check-in",  key="nc_checkin",
                                              min_value=date.today() - timedelta(days=7))
                    nc_out    = s2.date_input("Check-out", key="nc_checkout",
                                              min_value=date.today() - timedelta(days=7))
                    if st.button("Save Customer", type="primary", key="btn_save_new_customer"):
                        if not nc_first or not nc_phone:
                            st.error("First Name and Phone are required.")
                        else:
                            dup = check_duplicate_customer(nc_first, nc_last, nc_phone)
                            if dup:
                                st.error(f"Customer already exists — {dup}")
                            else:
                                ok, err = validate_dates(nc_in, nc_out)
                                if not ok:
                                    st.error(err)
                                else:
                                    existing_cid = get_customer_by_phone(nc_phone)
                                    if existing_cid:
                                        add_stay(existing_cid, nc_loc, nc_room, nc_in, nc_out,
                                                 rent_amount=nc_rent)
                                        st.success(f"Returning customer (CID {existing_cid}). New stay added.")
                                    else:
                                        cid = add_customer(nc_first, nc_last, nc_phone,
                                                           nc_aadhar, nc_emerg, nc_gender)
                                        add_stay(cid, nc_loc, nc_room, nc_in, nc_out,
                                                 rent_amount=nc_rent)
                                        st.success(f"Customer added (CID {cid})")
                                    st.session_state.gm_show_add_customer = False
                                    st.rerun()

            st.divider()
            f1, f2, f3 = st.columns([2, 1.5, 1.2])
            search_name = f1.text_input("Search by name or phone", key="gm_search",
                                        placeholder="Type to filter...")
            filter_loc  = f2.selectbox("Location", ["All"] + GUEST_LOCATIONS, key="gm_loc_filter")
            filter_gen  = f3.selectbox("Gender",   ["All"] + GUEST_GENDERS,   key="gm_gen_filter")

            import pandas as pd
            all_df = get_all_customers()

            if not all_df.empty:
                if search_name:
                    mask = (
                        all_df["first_name"].astype(str).str.lower().str.contains(search_name.lower(), na=False)
                        | all_df["last_name"].astype(str).str.lower().str.contains(search_name.lower(), na=False)
                        | all_df["phone"].astype(str).str.contains(search_name, na=False)
                    )
                    all_df = all_df[mask]
                if filter_loc != "All":
                    all_df = all_df[all_df["location"] == filter_loc]
                if filter_gen != "All":
                    all_df = all_df[all_df["gender"] == filter_gen]

            if all_df.empty:
                st.info("No customers found.")
            else:
                header = st.columns([0.6, 1.8, 1.5, 1.5, 1.5, 1.5, 1.2])
                for col, label in zip(header, ["CID","Name","Phone","Location","Room","Check-in","  "]):
                    col.markdown(f"**{label}**")
                st.divider()
                for _, row in all_df.iterrows():
                    cols = st.columns([0.6, 1.8, 1.5, 1.5, 1.5, 1.5, 1.2])
                    cols[0].write(int(row["cid"]))
                    cols[1].write(f"{row['first_name']} {row.get('last_name','')}")
                    cols[2].write(row.get("phone", ""))
                    cols[3].write(row.get("location", "—"))
                    cols[4].write(row.get("room_number", "—"))
                    cols[5].write(str(row.get("checkin", "—")))
                    if cols[6].button("View →", key=f"view_{row['cid']}"):
                        st.session_state.gm_selected_cid = int(row["cid"])
                        st.session_state.gm_view = "detail"
                        st.rerun()

        # ── DETAIL VIEW ──────────────────────────────────────────
        elif st.session_state.gm_view == "detail":
            cid      = st.session_state.gm_selected_cid
            customer = get_customer_by_cid(cid)

            if not customer:
                st.error("Customer not found.")
                st.session_state.gm_view = "list"
                st.rerun()

            if st.button("← Back to list", key="btn_back"):
                st.session_state.gm_view = "list"
                st.session_state.gm_selected_cid = None
                st.rerun()

            st.header(f"👤 {customer['first_name']} {customer.get('last_name','')}  —  CID {cid}")

            total_paid = get_total_paid_by_customer(cid)
            stays_df   = get_stays_for_customer(cid)
            m1, m2, m3 = st.columns(3)
            m1.metric("CID", cid)
            m2.metric("Total Paid", f"₹{total_paid:,.0f}")
            m3.metric("Total Stays", len(stays_df))
            st.divider()

            tab_profile, tab_stays, tab_payments, tab_remarks = st.tabs([
                "📋 Profile", "🛏️ Stay History", "💰 Payments", "📝 Remarks"
            ])

            with tab_profile:
                with st.form("edit_profile_form"):
                    c1, c2 = st.columns(2)
                    fn = c1.text_input("First Name", value=customer["first_name"])
                    ln = c2.text_input("Last Name",  value=customer.get("last_name",""))
                    ph = c1.text_input("Phone",      value=customer.get("phone",""))
                    aa = c2.text_input("Aadhaar",    value=customer.get("aadhar",""))
                    em = c1.text_input("Emergency Contact", value=customer.get("emergency_contact",""))
                    gn = c2.selectbox("Gender", GUEST_GENDERS,
                                      index=GUEST_GENDERS.index(customer["gender"])
                                      if customer.get("gender") in GUEST_GENDERS else 0)
                    if st.form_submit_button("💾 Save Profile", type="primary"):
                        dup = check_duplicate_customer(fn, ln, ph, exclude_cid=cid)
                        if dup:
                            st.error(dup)
                        else:
                            update_customer(cid, fn, ln, ph, aa, em, gn)
                            st.success("Profile updated.")
                            st.rerun()

            with tab_stays:
                if st.button("➕ Add New Stay", key="btn_add_stay"):
                    st.session_state.gm_show_add_stay = not st.session_state.gm_show_add_stay

                if st.session_state.gm_show_add_stay:
                    with st.container(border=True):
                        st.subheader("New Stay")
                        a1, a2, a3 = st.columns(3)
                        ns_loc    = a1.selectbox("Location", GUEST_LOCATIONS, key="ns_loc")
                        ns_room   = a2.text_input("Room Number", key="ns_room")
                        ns_rent   = a3.number_input("Base Rent (₹)", min_value=0.0, step=500.0, key="ns_rent")
                        ns_in     = a1.date_input("Check-in",  key="ns_in",
                                                  min_value=date.today() - timedelta(days=7))
                        ns_out    = a2.date_input("Check-out", key="ns_out",
                                                  min_value=date.today() - timedelta(days=7))
                        ns_stat   = a1.selectbox("Status", ["active","checked_out","cancelled"],
                                                 key="ns_status")
                        if st.button("Save Stay", type="primary", key="btn_save_stay"):
                            ok, err = validate_dates(ns_in, ns_out)
                            if not ok:
                                st.error(err)
                            else:
                                add_stay(cid, ns_loc, ns_room, ns_in, ns_out, ns_stat,
                                         rent_amount=ns_rent)
                                st.success("Stay added.")
                                st.session_state.gm_show_add_stay = False
                                st.rerun()

                if stays_df.empty:
                    st.info("No stays recorded.")
                else:
                    for _, stay in stays_df.iterrows():
                        paid_for_stay = get_total_paid_for_stay(int(stay["sid"]))
                        rent_due      = float(stay.get("rent_amount") or 0)
                        with st.expander(
                            f"🛏️ {stay.get('location','?')}  |  "
                            f"{stay.get('checkin','?')} → {stay.get('checkout','?')}  |  "
                            f"₹{paid_for_stay:,.0f} paid  |  [{stay.get('status','?')}]"
                        ):
                            e1, e2, e3 = st.columns(3)
                            upd_loc  = e1.selectbox("Location", GUEST_LOCATIONS,
                                                    index=GUEST_LOCATIONS.index(stay["location"])
                                                    if stay.get("location") in GUEST_LOCATIONS else 0,
                                                    key=f"upd_loc_{stay['sid']}")
                            upd_room = e2.text_input("Room", value=stay.get("room_number",""),
                                                     key=f"upd_room_{stay['sid']}")
                            upd_rent = e3.number_input("Base Rent (₹)", min_value=0.0, step=500.0,
                                                       value=float(stay.get("rent_amount") or 0),
                                                       key=f"upd_rent_{stay['sid']}")
                            upd_in   = e1.date_input("Check-in",
                                                      value=stay["checkin"] or date.today(),
                                                      min_value=date.today() - timedelta(days=7),
                                                      key=f"upd_in_{stay['sid']}")
                            upd_out  = e2.date_input("Check-out",
                                                      value=stay["checkout"] or date.today(),
                                                      min_value=date.today() - timedelta(days=7),
                                                      key=f"upd_out_{stay['sid']}")
                            upd_stat = e1.selectbox("Status",
                                                    ["active","checked_out","cancelled"],
                                                    index=["active","checked_out","cancelled"].index(
                                                        stay.get("status","active")),
                                                    key=f"upd_stat_{stay['sid']}")

                            # Rent balance breakdown
                            from backend import get_payments_for_stay
                            stay_pays = get_payments_for_stay(int(stay["sid"]))
                            rent_paid_so_far = stay_pays[stay_pays["payment_type"]=="rent"]["amount"].sum() if not stay_pays.empty else 0
                            rent_balance     = max(0, rent_due - rent_paid_so_far)
                            rb1, rb2, rb3 = st.columns(3)
                            rb1.metric("Rent Due", f"₹{rent_due:,.0f}")
                            rb2.metric("Rent Paid", f"₹{rent_paid_so_far:,.0f}")
                            rb3.metric("Rent Balance", f"₹{rent_balance:,.0f}",
                                       delta=f"-₹{rent_balance:,.0f}" if rent_balance > 0 else "✓ Cleared",
                                       delta_color="inverse" if rent_balance > 0 else "normal")

                            col_save, col_del = st.columns(2)
                            if col_save.button("💾 Update Stay", key=f"save_stay_{stay['sid']}"):
                                ok, err = validate_dates(upd_in, upd_out)
                                if not ok:
                                    st.error(err)
                                else:
                                    update_stay(int(stay["sid"]), upd_loc, upd_room,
                                                upd_in, upd_out, upd_stat,
                                                rent_amount=upd_rent)
                                    st.success("Stay updated.")
                                    st.rerun()
                            if col_del.button("🗑️ Delete Stay", key=f"del_stay_{stay['sid']}"):
                                delete_stay(int(stay["sid"]))
                                st.warning("Stay deleted.")
                                st.rerun()

            with tab_payments:
                if stays_df.empty:
                    st.info("Add a stay before recording payments.")
                else:
                    with st.container(border=True):
                        st.subheader("Record Payment")
                        stay_options = {
                            f"SID {s['sid']} — {s.get('location','?')} "
                            f"({s.get('checkin','?')} → {s.get('checkout','?')})": s["sid"]
                            for _, s in stays_df.iterrows()
                        }
                        p1, p2 = st.columns(2)
                        sel_stay_label = p1.selectbox("Stay", list(stay_options.keys()), key="pay_stay")
                        sel_sid        = stay_options[sel_stay_label]
                        pay_amount     = p2.number_input("Amount (₹)", min_value=0.0,
                                                         step=100.0, key="pay_amount")
                        pay_type       = p1.selectbox("Type", PAYMENT_TYPES, key="pay_type")
                        pay_mode       = p2.selectbox("Mode", PAYMENT_MODES, key="pay_mode")
                        pay_date       = p1.date_input("Date", value=date.today(), key="pay_date")
                        pay_notes      = p2.text_input("Notes", key="pay_notes")
                        if st.button("💾 Record Payment", type="primary", key="btn_record_pay"):
                            if pay_amount <= 0:
                                st.error("Amount must be greater than 0.")
                            else:
                                add_payment(cid, int(sel_sid), pay_amount,
                                            pay_type, pay_date, pay_mode, pay_notes)
                                st.success("Payment recorded.")
                                st.rerun()

                st.divider()
                st.subheader("Payment History")
                pay_df = get_payments_for_customer(cid)
                if pay_df.empty:
                    st.info("No payments recorded.")
                else:
                    st.dataframe(pay_df.rename(columns={
                        "payment_id":"ID","sid":"Stay ID","amount":"Amount (₹)",
                        "payment_type":"Type","payment_date":"Date",
                        "payment_mode":"Mode","notes":"Notes",
                        "location":"Location","room_number":"Room",
                    }), use_container_width=True, hide_index=True)
                    st.metric("Total Paid", f"₹{get_total_paid_by_customer(cid):,.0f}")

            with tab_remarks:
                with st.container(border=True):
                    new_note = st.text_area("Add a remark",
                                            placeholder="Type your note here...",
                                            key="new_remark_text")
                    if st.button("➕ Add Remark", type="primary", key="btn_add_remark"):
                        if new_note.strip():
                            add_remark(cid, new_note.strip())
                            st.success("Remark added.")
                            st.rerun()
                        else:
                            st.warning("Remark cannot be empty.")
                st.divider()
                remarks_df = get_remarks_for_customer(cid)
                if remarks_df.empty:
                    st.info("No remarks yet.")
                else:
                    for _, rem in remarks_df.iterrows():
                        r1, r2 = st.columns([8, 1])
                        r1.markdown(f"📝 **{rem['created_at']}** — {rem['note']}")
                        if r2.button("🗑️", key=f"del_rem_{rem['rid']}"):
                            delete_remark(int(rem["rid"]))
                            st.rerun()

    # ════════════════════════════════════════════════════════════
    # ROOM STATUS
    # ════════════════════════════════════════════════════════════
    elif section == "Room Status":
        from backend import get_room_occupancy

        st.header("🛏️ Room Status")

        building = st.selectbox(
            "Select Building",
            ["PKR Prime", "Matsaya", "Navalur"],
            key="rs_building",
        )

        today = date.today()

        if building == "PKR Prime":
            FLOOR_DEFS = {
                "Floor A": [
                    ("Single rooms  A1–A10",  [(f"A{i}", 1) for i in range(1, 11)]),
                    ("Double rooms  A11–A14", [(f"A{i}", 2) for i in range(11, 15)]),
                ],
                "Floor B": [
                    ("Single rooms  B1–B10",  [(f"B{i}", 1) for i in range(1, 11)]),
                    ("Single rooms  B11–B18", [(f"B{i}", 1) for i in range(11, 19)]),
                ],
                "Floor C": [
                    ("Single rooms  C1–C10",  [(f"C{i}", 1) for i in range(1, 11)]),
                    ("Single rooms  C11–C18", [(f"C{i}", 1) for i in range(11, 19)]),
                    ("Double room   C19",     [("C19", 2)]),
                ],
            }
        elif building == "Matsaya":
            FLOOR_DEFS = {
                "Matsaya Rooms": [
                    ("Double room",  [("F2", 2)]),
                    ("Quad rooms",   [("S1", 4), ("S2", 4), ("S3", 4)]),
                ],
            }
        else:
            FLOOR_DEFS = {
                "Navalur Rooms": [
                    ("Rooms", [("A1", 1), ("A2", 1), ("A3", 1)]),
                ],
            }

        occupancy = get_room_occupancy(building)

        total_beds, occupied_beds, checkout_due = 0, 0, 0
        for floor_rows in FLOOR_DEFS.values():
            for _lbl, rooms in floor_rows:
                for room_key, beds in rooms:
                    total_beds += beds
                    for bed_idx in range(1, beds + 1):
                        cell_key = f"{room_key}.{bed_idx}" if beds > 1 else room_key
                        guests = occupancy.get(cell_key, [])
                        if guests:
                            occupied_beds += 1
                            co = guests[0].get("checkout")
                            if co and co <= today:
                                checkout_due += 1

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Beds", total_beds)
        m2.metric("🔴 Occupied", occupied_beds)
        m3.metric("🟢 Vacant", total_beds - occupied_beds)
        m4.metric("🟠 Checkout Due", checkout_due)
        st.divider()

        st.markdown(
            '<div style="display:flex;gap:1.5rem;margin-bottom:1.25rem;font-size:0.82rem;color:#94a3b8;flex-wrap:wrap;">'
            '<span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#166534;border:1.5px solid #22c55e;margin-right:5px;vertical-align:middle;"></span>Vacant</span>'
            '<span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#991b1b;border:1.5px solid #ef4444;margin-right:5px;vertical-align:middle;"></span>Occupied</span>'
            '<span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#c2410c;border:1.5px solid #f97316;margin-right:5px;vertical-align:middle;"></span>Checkout today / overdue</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        for floor_name, floor_rows in FLOOR_DEFS.items():
            html = (
                '<div style="border:1px solid #1e293b;border-radius:12px;'
                'padding:1rem 1.25rem 1rem;background:#070d1a;margin-bottom:1.5rem;">'
                f'<div style="font-size:0.72rem;font-weight:800;letter-spacing:0.14em;'
                f'text-transform:uppercase;color:#a855f7;margin-bottom:0.85rem;">🏢 {floor_name}</div>'
            )

            for row_label, rooms in floor_rows:
                html += (
                    f'<div style="font-size:0.7rem;color:#475569;text-transform:uppercase;'
                    f'letter-spacing:0.08em;margin-bottom:0.45rem;margin-top:0.1rem;">{row_label}</div>'
                    '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:1rem;">'
                )

                for room_key, beds in rooms:
                    for bed_idx in range(1, beds + 1):
                        cell_key = f"{room_key}.{bed_idx}" if beds > 1 else room_key
                        guests   = occupancy.get(cell_key, [])

                        if not guests:
                            html += (
                                f'<div title="Vacant" style="display:inline-flex;flex-direction:column;'
                                f'align-items:center;justify-content:center;min-width:64px;padding:8px 10px;'
                                f'border-radius:8px;background:#052e16;border:1.5px solid #166534;text-align:center;">'
                                f'<span style="font-size:0.8rem;font-weight:700;color:#86efac;">{cell_key}</span>'
                                f'<span style="width:7px;height:7px;border-radius:50%;background:#22c55e;'
                                f'margin-top:5px;display:inline-block;"></span>'
                                f'</div>'
                            )
                        else:
                            g      = guests[0]
                            co     = g.get("checkout")
                            ci     = g.get("checkin")
                            is_co  = bool(co and co <= today)
                            bg     = "#431407" if is_co else "#3b0000"
                            bdr    = "#c2410c" if is_co else "#991b1b"
                            id_col = "#fdba74" if is_co else "#fca5a5"
                            nm_col = "#fed7aa" if is_co else "#fda4af"
                            dot_bg = "#f97316" if is_co else "#ef4444"
                            warn   = " CHECKOUT DUE" if is_co else ""
                            nm_safe = g["name"].replace('"', "").replace("'", "")
                            ph_safe = str(g.get("phone", "")).replace('"', "")
                            tip    = f"{nm_safe} | CID {g['cid']} | {ph_safe} | In:{ci} Out:{co}{warn}"
                            short  = (g["name"][:9] + "…") if len(g["name"]) > 9 else g["name"]
                            html += (
                                f'<div title="{tip}" style="display:inline-flex;flex-direction:column;'
                                f'align-items:center;justify-content:center;min-width:64px;padding:8px 10px;'
                                f'border-radius:8px;background:{bg};border:1.5px solid {bdr};'
                                f'text-align:center;cursor:pointer;">'
                                f'<span style="font-size:0.8rem;font-weight:700;color:{id_col};">{cell_key}</span>'
                                f'<span style="font-size:0.65rem;color:{nm_col};max-width:72px;white-space:nowrap;'
                                f'overflow:hidden;text-overflow:ellipsis;margin-top:3px;">{short}</span>'
                                f'<span style="width:7px;height:7px;border-radius:50%;background:{dot_bg};'
                                f'margin-top:5px;display:inline-block;"></span>'
                                f'</div>'
                            )

                html += '</div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        st.caption(
            "Hover over a red/orange cell to see guest name, CID, phone and dates. "
            "Orange = checkout date reached. Green = vacant."
        )

    # ════════════════════════════════════════════════════════════
    # PAYMENTS
    # ════════════════════════════════════════════════════════════
    elif section == "Payments":
        from backend import (
            get_all_payment_summaries,
            get_payments_for_customer,
            get_stays_for_customer,
            add_payment,
            PAYMENT_MODES,
            get_customer_by_cid,
        )

        st.header("💰 Payments")

        # ── Filters ──────────────────────────────────────────────
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
        sort_by = fc1.selectbox(
            "Sort by",
            ["Priority (Due first)", "Last Payment Date", "Check-in Date", "Name"],
            key="pay_sort_by",
        )
        show_filter = fc2.selectbox(
            "Show",
            ["All", "Due only", "Paid only"],
            key="pay_show_filter",
        )
        mode_filter = fc3.selectbox(
            "Payment Mode",
            ["All"] + PAYMENT_MODES,
            key="pay_mode_filter",
        )
        loc_filter = fc4.selectbox(
            "Location",
            ["All", "PKR Prime", "Matsaya", "Navalur", "Palavakkam"],
            key="pay_loc_filter",
        )

        summary_df = get_all_payment_summaries(
            payment_mode_filter=mode_filter if mode_filter != "All" else None
        )

        if summary_df.empty:
            st.info("No active stays found.")
        else:
            # Location filter
            if loc_filter != "All":
                summary_df = summary_df[summary_df["location"] == loc_filter]

            if show_filter == "Due only":
                summary_df = summary_df[summary_df["alert"] == "red"]
            elif show_filter == "Paid only":
                summary_df = summary_df[summary_df["alert"] == "green"]

            if sort_by == "Priority (Due first)":
                summary_df = summary_df.sort_values(
                    ["alert", "deposit_overdue", "days_since_checkin"],
                    ascending=[True, False, False],
                )
            elif sort_by == "Last Payment Date":
                summary_df = summary_df.sort_values("last_payment_date", ascending=False, na_position="first")
            elif sort_by == "Check-in Date":
                summary_df = summary_df.sort_values("checkin", ascending=False)
            elif sort_by == "Name":
                summary_df = summary_df.sort_values(["first_name", "last_name"], ascending=True)

            total_due   = len(summary_df[summary_df["alert"] == "red"])
            total_clear = len(summary_df[summary_df["alert"] == "green"])
            overdue     = len(summary_df[summary_df["deposit_overdue"] == True])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Active Guests", len(summary_df))
            m2.metric("🔴 Payments Due", total_due)
            m3.metric("🟢 Fully Paid", total_clear)
            m4.metric("⚠️ Deposit Overdue (5d+)", overdue)
            st.divider()

            for _, row in summary_df.iterrows():
                is_red     = row["alert"] == "red"
                is_overdue = row["deposit_overdue"]

                rent_due     = float(row.get("rent_due", 0))
                rent_paid    = float(row.get("rent_paid", 0))
                rent_balance = float(row.get("rent_balance", 0))

                border_color  = "#ef4444" if is_red else "#22c55e"
                bg_color      = "rgba(239,68,68,0.08)" if is_red else "rgba(34,197,94,0.08)"
                badge_color   = "#ef4444" if is_red else "#22c55e"
                badge_text    = "⚠️ OVERDUE" if is_overdue else ("🔴 DUE" if is_red else "🟢 PAID")
                deposit_color = "#ef4444" if row["deposit_paid"] == 0 else "#22c55e"
                rent_color    = "#ef4444" if rent_balance > 0 else "#22c55e"
                food_color    = "#94a3b8"

                days_info = ""
                if is_overdue:
                    days_info = f"<span style='color:#ef4444;font-weight:600'> ⚠️ Deposit overdue by {row['days_since_checkin'] - 5}d</span>"
                elif is_red and row["days_since_checkin"] > 0:
                    days_info = f"<span style='color:#f97316'> ({row['days_since_checkin']}d since check-in)</span>"

                last_pay = row["last_payment_date"] or "No payments yet"

                # Rent display: show paid / due / balance
                if rent_due > 0:
                    rent_display = f"₹{rent_paid:,.0f} / ₹{rent_due:,.0f}"
                    rent_suffix  = f" (bal: ₹{rent_balance:,.0f})" if rent_balance > 0 else " ✓"
                else:
                    rent_display = f"₹{rent_paid:,.0f}"
                    rent_suffix  = ""

                st.markdown(f"""
                    <div style="border:1.5px solid {border_color};background:{bg_color};
                        border-radius:10px;padding:1rem 1.25rem;margin-bottom:0.75rem;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
                            <div>
                                <span style="font-size:1.05rem;font-weight:700;color:#f1f5f9">{row['first_name']} {row.get('last_name','')}</span>
                                <span style="color:#94a3b8;margin-left:0.75rem;font-size:0.9rem">CID {row['cid']}</span>
                                <span style="color:#94a3b8;margin-left:0.75rem;font-size:0.9rem">📞 {row['phone']}</span>
                            </div>
                            <span style="background:{badge_color};color:white;padding:0.2rem 0.65rem;
                                border-radius:999px;font-size:0.8rem;font-weight:600">{badge_text}</span>
                        </div>
                        <div style="color:#94a3b8;font-size:0.88rem;margin-bottom:0.5rem">
                            📍 {row.get('location','—')} &nbsp;|&nbsp;
                            🛏️ Room {row.get('room_number','—')} &nbsp;|&nbsp;
                            📅 Check-in: {row['checkin']} {days_info} &nbsp;|&nbsp;
                            🕐 Last payment: {last_pay}
                        </div>
                        <div style="display:flex;gap:2rem;margin-top:0.4rem;flex-wrap:wrap;">
                            <span><span style="color:#94a3b8;font-size:0.85rem">Deposit: </span>
                                <span style="color:{deposit_color};font-weight:600">₹{row['deposit_paid']:,.0f} {'✓' if row['deposit_paid'] > 0 else '✗'}</span></span>
                            <span><span style="color:#94a3b8;font-size:0.85rem">Rent: </span>
                                <span style="color:{rent_color};font-weight:600">{rent_display}{rent_suffix}</span></span>
                            <span><span style="color:#94a3b8;font-size:0.85rem">Food: </span>
                                <span style="color:{food_color};font-weight:600">₹{row['food_paid']:,.0f}</span></span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander(f"➕ Add Payment — {row['first_name']} {row.get('last_name', '')}"):
                    pay_cols = st.columns([1.5, 1.5, 1.5, 2, 1.5])
                    pay_type   = pay_cols[0].selectbox("Type", ["deposit", "rent", "food", "misc"], key=f"ptype_{row['sid']}")
                    pay_amount = pay_cols[1].number_input("Amount (₹)", min_value=0.0, step=100.0, key=f"pamt_{row['sid']}")
                    pay_mode   = pay_cols[2].selectbox("Mode", PAYMENT_MODES, key=f"pmode_{row['sid']}")
                    pay_date   = pay_cols[3].date_input("Date", value=date.today(), key=f"pdate_{row['sid']}")
                    pay_notes  = pay_cols[4].text_input("Notes", key=f"pnotes_{row['sid']}")
                    if st.button("💾 Record", type="primary", key=f"rec_pay_{row['sid']}"):
                        if pay_amount <= 0:
                            st.error("Amount must be greater than 0.")
                        else:
                            add_payment(int(row["cid"]), int(row["sid"]), pay_amount, pay_type, pay_date, pay_mode, pay_notes)
                            st.success(f"₹{pay_amount:,.0f} {pay_type} recorded for {row['first_name']}.")
                            st.rerun()

            st.divider()

            with st.expander("📋 Full Payment History (all guests)"):
                import pandas as pd
                from backend import get_conn, _parse_date

                conn = get_conn()
                full_pay = pd.read_sql_query("""
                    SELECT c.cid, c.first_name || ' ' || COALESCE(c.last_name,'') AS name,
                        c.phone, s.location, s.room_number,
                        p.payment_type AS type, p.amount, p.payment_date AS date,
                        p.payment_mode AS mode, p.notes
                    FROM payments p
                    JOIN customers c ON c.cid = p.cid
                    JOIN stays s ON s.sid = p.sid
                    ORDER BY p.payment_date DESC
                """, conn)
                conn.close()

                if full_pay.empty:
                    st.info("No payments recorded yet.")
                else:
                    fh1, fh2 = st.columns(2)
                    sort_hist = fh1.selectbox("Sort by",
                        ["Date (newest)", "Date (oldest)", "Name", "Amount"], key="hist_sort")
                    mode_hist = fh2.selectbox("Filter by mode",
                        ["All"] + PAYMENT_MODES, key="hist_mode_filter")
                    if sort_hist == "Date (newest)":
                        full_pay = full_pay.sort_values("date", ascending=False)
                    elif sort_hist == "Date (oldest)":
                        full_pay = full_pay.sort_values("date", ascending=True)
                    elif sort_hist == "Name":
                        full_pay = full_pay.sort_values("name", ascending=True)
                    elif sort_hist == "Amount":
                        full_pay = full_pay.sort_values("amount", ascending=False)
                    if mode_hist != "All":
                        full_pay = full_pay[full_pay["mode"] == mode_hist]
                    st.dataframe(full_pay.rename(columns={
                        "cid":"CID","name":"Name","phone":"Phone","location":"Location",
                        "room_number":"Room","type":"Type","amount":"Amount (₹)",
                        "date":"Date","mode":"Mode","notes":"Notes",
                    }), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════
    # EMPLOYEES
    # ════════════════════════════════════════════════════════════
    elif section == "Employees":
        from backend import (
            EMPLOYEE_PROPERTIES, EMPLOYEE_PAY_TYPES,
            get_all_employees, get_employee_by_eid,
            add_employee, update_employee, delete_employee,
            get_payments_for_employee, add_employee_payment, delete_employee_payment,
            get_leaves_for_employee, add_employee_leave, delete_employee_leave,
            get_employee_salary_this_month,
        )

        if "emp_view" not in st.session_state:
            st.session_state.emp_view = "list"
        if "emp_selected_eid" not in st.session_state:
            st.session_state.emp_selected_eid = None
        if "emp_show_add" not in st.session_state:
            st.session_state.emp_show_add = False

        if st.session_state.emp_view == "list":
            st.header("🧑‍💼 Employees")

            if st.button("➕ Add Employee", key="btn_add_emp"):
                st.session_state.emp_show_add = not st.session_state.emp_show_add

            if st.session_state.emp_show_add:
                with st.container(border=True):
                    st.subheader("New Employee")
                    c1, c2 = st.columns(2)
                    ne_name   = c1.text_input("Full Name*",        key="ne_name")
                    ne_phone  = c2.text_input("Phone",             key="ne_phone")
                    ne_aadhar = c1.text_input("Aadhaar",           key="ne_aadhar")
                    ne_prop   = c2.selectbox("Property", EMPLOYEE_PROPERTIES, key="ne_prop")
                    ne_addr   = c1.text_input("Address",           key="ne_addr")
                    ne_sal    = c2.number_input("Base Salary (₹)", min_value=0.0, step=500.0, key="ne_sal")
                    if st.button("Save Employee", type="primary", key="btn_save_emp"):
                        if not ne_name:
                            st.error("Name is required.")
                        else:
                            eid = add_employee(ne_name, ne_phone, ne_aadhar, ne_addr, ne_prop, ne_sal)
                            st.success(f"Employee added (EID {eid})")
                            st.session_state.emp_show_add = False
                            st.rerun()

            st.divider()

            fc1, fc2 = st.columns([2, 1.5])
            emp_search      = fc1.text_input("Search by name or phone", placeholder="Type to filter...", key="emp_search")
            emp_filter_prop = fc2.selectbox("Property", ["All"] + EMPLOYEE_PROPERTIES, key="emp_prop_filter")

            import pandas as pd
            emp_df = get_all_employees()

            if not emp_df.empty:
                if emp_search:
                    mask = (
                        emp_df["name"].astype(str).str.lower().str.contains(emp_search.lower(), na=False)
                        | emp_df["phone"].astype(str).str.contains(emp_search, na=False)
                    )
                    emp_df = emp_df[mask]
                if emp_filter_prop != "All":
                    emp_df = emp_df[emp_df["property"] == emp_filter_prop]

            if emp_df.empty:
                st.info("No employees found.")
            else:
                today = date.today()
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Employees", len(emp_df))
                m2.metric("Total Salary Paid", f"₹{emp_df['salary_paid'].sum():,.0f}")
                m3.metric("Total Advances", f"₹{emp_df['advance_paid'].sum():,.0f}")
                st.divider()

                hcols = st.columns([0.4, 1.6, 1.2, 1.2, 1.1, 1.2, 1.2, 1.0, 0.8])
                for col, lbl in zip(hcols, ["EID","Name","Phone","Property","Base Sal","This Month Sal","Sal Paid Total","Leaves","  "]):
                    col.markdown(f"**{lbl}**")
                st.divider()

                for _, row in emp_df.iterrows():
                    this_month_sal = get_employee_salary_this_month(int(row["eid"]), today.month, today.year)
                    rc = st.columns([0.4, 1.6, 1.2, 1.2, 1.1, 1.2, 1.2, 1.0, 0.8])
                    rc[0].write(int(row["eid"]))
                    rc[1].write(row["name"])
                    rc[2].write(row.get("phone", "—"))
                    rc[3].write(row.get("property", "—"))
                    rc[4].write(f"₹{row['base_salary']:,.0f}")
                    sal_color = "🟢" if this_month_sal >= row["base_salary"] else ("🟡" if this_month_sal > 0 else "🔴")
                    rc[5].write(f"{sal_color} ₹{this_month_sal:,.0f}")
                    rc[6].write(f"₹{row['salary_paid']:,.0f}")
                    rc[7].write(int(row["total_leaves"]))
                    if rc[8].button("View →", key=f"emp_view_{row['eid']}"):
                        st.session_state.emp_selected_eid = int(row["eid"])
                        st.session_state.emp_view = "detail"
                        st.rerun()

        elif st.session_state.emp_view == "detail":
            eid      = st.session_state.emp_selected_eid
            employee = get_employee_by_eid(eid)

            if not employee:
                st.error("Employee not found.")
                st.session_state.emp_view = "list"
                st.rerun()

            if st.button("← Back to list", key="btn_emp_back"):
                st.session_state.emp_view = "list"
                st.session_state.emp_selected_eid = None
                st.rerun()

            st.header(f"🧑‍💼 {employee['name']}  —  EID {eid}")

            pay_df   = get_payments_for_employee(eid)
            leave_df = get_leaves_for_employee(eid)

            today = date.today()
            sal_total      = pay_df[pay_df["pay_type"] == "salary"]["amount"].sum()  if not pay_df.empty else 0
            adv_total      = pay_df[pay_df["pay_type"] == "advance"]["amount"].sum() if not pay_df.empty else 0
            bon_total      = pay_df[pay_df["pay_type"] == "bonus"]["amount"].sum()   if not pay_df.empty else 0
            this_month_sal = get_employee_salary_this_month(eid, today.month, today.year)
            sal_balance    = max(0, float(employee["base_salary"]) - this_month_sal)

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Base Salary",       f"₹{employee['base_salary']:,.0f}")
            m2.metric("This Month Paid",   f"₹{this_month_sal:,.0f}")
            m3.metric("This Month Balance",f"₹{sal_balance:,.0f}",
                      delta=f"-₹{sal_balance:,.0f}" if sal_balance > 0 else "✓ Cleared",
                      delta_color="inverse" if sal_balance > 0 else "normal")
            m4.metric("Total Salary Paid", f"₹{sal_total:,.0f}")
            m5.metric("Advance",           f"₹{adv_total:,.0f}")
            m6.metric("Leaves Taken",      len(leave_df))
            st.divider()

            tab_profile, tab_payments, tab_leaves = st.tabs([
                "📋 Profile", "💰 Payments", "📅 Leaves"
            ])

            with tab_profile:
                with st.form("emp_profile_form"):
                    c1, c2 = st.columns(2)
                    ep_name   = c1.text_input("Full Name",  value=employee["name"])
                    ep_phone  = c2.text_input("Phone",      value=employee.get("phone", ""))
                    ep_aadhar = c1.text_input("Aadhaar",    value=employee.get("aadhar", ""))
                    ep_prop   = c2.selectbox("Property", EMPLOYEE_PROPERTIES,
                                             index=EMPLOYEE_PROPERTIES.index(employee["property"])
                                             if employee.get("property") in EMPLOYEE_PROPERTIES else 0)
                    ep_addr   = c1.text_input("Address",    value=employee.get("address", ""))
                    ep_sal    = c2.number_input("Base Salary (₹)", min_value=0.0, step=500.0,
                                                value=float(employee["base_salary"]))
                    if st.form_submit_button("💾 Save Profile", type="primary"):
                        update_employee(eid, ep_name, ep_phone, ep_aadhar, ep_addr, ep_prop, ep_sal)
                        st.success("Profile updated.")
                        st.rerun()
                st.divider()
                if st.button("🗑️ Delete Employee", key="btn_del_emp"):
                    delete_employee(eid)
                    st.warning("Employee deleted.")
                    st.session_state.emp_view = "list"
                    st.session_state.emp_selected_eid = None
                    st.rerun()

            with tab_payments:
                with st.container(border=True):
                    st.subheader("Record Payment")
                    st.info(f"Base salary: ₹{employee['base_salary']:,.0f} | This month paid: ₹{this_month_sal:,.0f} | Balance: ₹{sal_balance:,.0f}")
                    p1, p2, p3, p4 = st.columns(4)
                    ep_type   = p1.selectbox("Type", EMPLOYEE_PAY_TYPES, key="ep_type")
                    ep_amount = p2.number_input("Amount (₹)", min_value=0.0, step=500.0, key="ep_amount")
                    ep_date   = p3.date_input("Date", value=date.today(), key="ep_date")
                    ep_notes  = p4.text_input("Notes", key="ep_notes")
                    if st.button("💾 Record Payment", type="primary", key="btn_rec_emp_pay"):
                        if ep_amount <= 0:
                            st.error("Amount must be greater than 0.")
                        else:
                            add_employee_payment(eid, ep_amount, ep_type, ep_date, ep_notes)
                            st.success(f"₹{ep_amount:,.0f} {ep_type} recorded. (Auto-added to Expenses)")
                            st.rerun()
                st.divider()
                st.subheader("Payment History")

                # Month filter for payment history
                import pandas as pd
                ph_col1, ph_col2 = st.columns(2)
                ph_month = ph_col1.selectbox("Month", ["All"] + [date(2000, m, 1).strftime("%B") for m in range(1, 13)], key="ph_month")
                ph_year  = ph_col2.number_input("Year", min_value=2020, max_value=2100,
                                                value=date.today().year, step=1, key="ph_year")

                if pay_df.empty:
                    st.info("No payments recorded.")
                else:
                    filtered_pay = pay_df.copy()
                    if ph_month != "All":
                        month_num = list(range(1, 13))[[date(2000, m, 1).strftime("%B") for m in range(1, 13)].index(ph_month)] + 1
                        filtered_pay["pay_date_parsed"] = pd.to_datetime(filtered_pay["pay_date"], errors="coerce")
                        filtered_pay = filtered_pay[
                            (filtered_pay["pay_date_parsed"].dt.month == month_num) &
                            (filtered_pay["pay_date_parsed"].dt.year == ph_year)
                        ]

                    for _, pr in filtered_pay.iterrows():
                        pc1, pc2 = st.columns([9, 1])
                        badge = {"salary": "🟢", "advance": "🟡", "bonus": "🔵", "misc": "⚪"}.get(pr["pay_type"], "⚪")
                        pc1.markdown(
                            f"{badge} **{pr['pay_type'].upper()}** &nbsp;|&nbsp; "
                            f"₹{pr['amount']:,.0f} &nbsp;|&nbsp; "
                            f"{pr['pay_date']} &nbsp;|&nbsp; {pr['notes'] or '—'}"
                        )
                        if pc2.button("🗑️", key=f"del_ep_{pr['epid']}"):
                            delete_employee_payment(int(pr["epid"]))
                            st.rerun()

            with tab_leaves:
                with st.container(border=True):
                    st.subheader("Mark Leave")
                    lc1, lc2 = st.columns(2)
                    el_date   = lc1.date_input("Leave Date", value=date.today(), key="el_date")
                    el_reason = lc2.text_input("Reason", key="el_reason")
                    if st.button("➕ Add Leave", type="primary", key="btn_add_leave"):
                        add_employee_leave(eid, el_date, el_reason)
                        st.success("Leave recorded.")
                        st.rerun()
                st.divider()
                st.subheader(f"Leave History  ({len(leave_df)} days)")
                if leave_df.empty:
                    st.info("No leaves recorded.")
                else:
                    for _, lr in leave_df.iterrows():
                        lrc1, lrc2 = st.columns([9, 1])
                        lrc1.markdown(f"📅 **{lr['leave_date']}** — {lr['reason'] or '—'}")
                        if lrc2.button("🗑️", key=f"del_el_{lr['elid']}"):
                            delete_employee_leave(int(lr["elid"]))
                            st.rerun()

    # ════════════════════════════════════════════════════════════
    # EXPENSES
    # ════════════════════════════════════════════════════════════
    elif section == "Expenses":
        from backend import (
            EXPENSE_CATEGORIES, EXPENSE_SUB_CATEGORIES, EXPENSE_PROPERTIES,
            add_expense, delete_expense, get_expenses,
            get_expense_summary_by_category, get_food_revenue_vs_cost,
            get_all_employees,
        )
        import pandas as pd

        st.header("💸 Expenses")

        fc1, fc2, fc3 = st.columns(3)
        sel_month = fc1.selectbox("Month", list(range(1, 13)),
                                  index=date.today().month - 1,
                                  format_func=lambda m: date(2000, m, 1).strftime("%B"),
                                  key="exp_month")
        sel_year  = fc2.number_input("Year", min_value=2020, max_value=2100,
                                     value=date.today().year, step=1, key="exp_year")
        sel_prop  = fc3.selectbox("Property", ["All"] + EXPENSE_PROPERTIES, key="exp_prop")

        st.divider()

        # ── Add expense form (manual — non-salary) ───────────────
        with st.expander("➕ Add Expense", expanded=False):
            with st.container(border=True):
                c1, c2 = st.columns(2)
                exp_cat  = c1.selectbox("Category",
                                        [c for c in EXPENSE_CATEGORIES if c != "Employee Salary"],
                                        key="exp_cat")
                exp_sub  = c2.selectbox("Sub-category",
                                        EXPENSE_SUB_CATEGORIES.get(exp_cat, [exp_cat]),
                                        key="exp_sub")
                if exp_cat == "Rent":
                    exp_prop_val = "PKR Prime"
                    c1.info("Rent is mapped to PKR Prime only.")
                else:
                    exp_prop_val = c1.selectbox("Property", EXPENSE_PROPERTIES, key="exp_prop_add")

                exp_amount = c2.number_input("Amount (₹)", min_value=0.0, step=100.0, key="exp_amount")
                exp_date   = c1.date_input("Date", value=date.today(), key="exp_date")
                exp_notes  = c2.text_input("Notes", key="exp_notes")

                if st.button("💾 Save Expense", type="primary", key="btn_save_exp"):
                    if exp_amount <= 0:
                        st.error("Amount must be greater than 0.")
                    else:
                        add_expense(exp_cat, exp_sub, exp_prop_val, exp_amount, exp_date, exp_notes)
                        st.success(f"₹{exp_amount:,.0f} {exp_cat} expense recorded.")
                        st.rerun()

        st.info("💡 Employee salary, advance and bonus payments are automatically recorded here when added via the Employees section.")

        # ── Summary metrics ──────────────────────────────────────
        exp_df    = get_expenses(month=sel_month, year=sel_year,
                                 property_=None if sel_prop == "All" else sel_prop)
        total_exp = exp_df["amount"].sum() if not exp_df.empty else 0
        food_data = get_food_revenue_vs_cost(sel_month, sel_year)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Expenses", f"₹{total_exp:,.0f}")
        m2.metric("🍽️ Food Revenue", f"₹{food_data['total_food_revenue']:,.0f}")
        m3.metric("🍳 Kitchen Cost", f"₹{food_data['kitchen_cost']:,.0f}")
        m4.metric("🍽️ Food P&L",    f"₹{food_data['food_profit']:,.0f}")

        st.divider()

        # ── Category breakdown ───────────────────────────────────
        st.subheader(f"Breakdown — {date(2000, sel_month, 1).strftime('%B')} {sel_year}")
        summary_df = get_expense_summary_by_category(
            sel_month, sel_year,
            property_=None if sel_prop == "All" else sel_prop
        )

        if not summary_df.empty:
            for _, srow in summary_df.iterrows():
                pct = (srow["total"] / total_exp * 100) if total_exp > 0 else 0
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:0.4rem 0.75rem;border-radius:6px;background:#0f172a;'
                    f'border:1px solid #1e293b;margin-bottom:6px;">'
                    f'<span style="color:#e2e8f0;font-weight:600;">{srow["category"]}</span>'
                    f'<span style="color:#94a3b8;">₹{srow["total"]:,.0f}'
                    f' &nbsp;<span style="color:#475569;font-size:0.8rem;">({pct:.1f}%)</span></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No expenses recorded for this period.")

        # ── Food P&L detail ──────────────────────────────────────
        if not food_data["revenue_by_property"].empty:
            st.divider()
            st.subheader("🍽️ Food Revenue by Property")
            for _, fr in food_data["revenue_by_property"].iterrows():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:0.4rem 0.75rem;border-radius:6px;background:#0f172a;'
                    f'border:1px solid #1e293b;margin-bottom:6px;">'
                    f'<span style="color:#e2e8f0;font-weight:600;">📍 {fr["location"]}</span>'
                    f'<span style="color:#4ade80;font-weight:600;">₹{fr["food_revenue"]:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            pnl_color = "#4ade80" if food_data["food_profit"] >= 0 else "#ef4444"
            pnl_label = "PROFIT" if food_data["food_profit"] >= 0 else "LOSS"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:0.5rem 0.75rem;border-radius:6px;background:#0f172a;'
                f'border:1.5px solid {pnl_color};margin-top:4px;">'
                f'<span style="color:{pnl_color};font-weight:700;">Food {pnl_label}</span>'
                f'<span style="color:{pnl_color};font-weight:700;">₹{abs(food_data["food_profit"]):,.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Full expense log ─────────────────────────────────────
        st.subheader("Expense Log")
        cat_filter = st.selectbox("Filter by category",
                                  ["All"] + EXPENSE_CATEGORIES, key="exp_log_cat")
        log_df = get_expenses(month=sel_month, year=sel_year,
                              category=None if cat_filter == "All" else cat_filter,
                              property_=None if sel_prop == "All" else sel_prop)

        if log_df.empty:
            st.info("No expenses for this selection.")
        else:
            for _, xrow in log_df.iterrows():
                xc1, xc2 = st.columns([9, 1])
                source_tag = " 🔗 auto" if xrow.get("source_type") == "employee_payment" else ""
                xc1.markdown(
                    f"**{xrow['category']}** › {xrow['sub_category'] or '—'} &nbsp;|&nbsp; "
                    f"₹{xrow['amount']:,.0f} &nbsp;|&nbsp; "
                    f"📍 {xrow['property'] or '—'} &nbsp;|&nbsp; "
                    f"📅 {xrow['expense_date']} &nbsp;|&nbsp; {xrow['notes'] or '—'}{source_tag}"
                )
                if xc2.button("🗑️", key=f"del_exp_{xrow['xid']}"):
                    delete_expense(int(xrow["xid"]))
                    st.rerun()

    # ════════════════════════════════════════════════════════════
    # REPORTS
    # ════════════════════════════════════════════════════════════
    elif section == "Reports":
        from backend import (
            get_monthly_revenue, get_monthly_expenses_total,
            get_expense_summary_by_category, get_food_revenue_vs_cost,
            get_period_summary, get_yearly_summary,
        )
        import pandas as pd
        import plotly.graph_objects as go
        import plotly.express as px

        st.header("📊 Reports")

        report_tab1, report_tab2, report_tab3 = st.tabs([
            "📅 Monthly P&L", "📈 Period Comparison", "📆 Yearly Report"
        ])

        PROPERTIES = ["PKR Prime", "Matsaya", "Navalur", "Palavakkam"]

        # ════════════════════════════════════════════════
        # TAB 1 — Monthly P&L (existing)
        # ════════════════════════════════════════════════
        with report_tab1:
            rc1, rc2 = st.columns(2)
            rep_month = rc1.selectbox("Month", list(range(1, 13)),
                                      index=date.today().month - 1,
                                      format_func=lambda m: date(2000, m, 1).strftime("%B"),
                                      key="rep_month")
            rep_year  = rc2.number_input("Year", min_value=2020, max_value=2100,
                                         value=date.today().year, step=1, key="rep_year")

            month_label = f"{date(2000, rep_month, 1).strftime('%B')} {rep_year}"
            st.divider()

            st.subheader(f"Property P&L — {month_label}")
            prop_data = []
            for prop in PROPERTIES:
                rev_df   = get_monthly_revenue(rep_month, rep_year, property_=prop)
                revenue  = rev_df["amount"].sum() if not rev_df.empty else 0
                expenses = get_monthly_expenses_total(rep_month, rep_year, property_=prop)
                prop_data.append({
                    "property": prop, "revenue": revenue,
                    "expenses": expenses, "profit": revenue - expenses,
                })

            pnl_df = pd.DataFrame(prop_data)

            cols = st.columns(len(PROPERTIES))
            for i, row in pnl_df.iterrows():
                pnl_val = row["profit"]
                cols[i].metric(
                    row["property"],
                    f"₹{row['revenue']:,.0f}",
                    delta=f"{'▲' if pnl_val >= 0 else '▼'} ₹{abs(pnl_val):,.0f} {'profit' if pnl_val >= 0 else 'loss'}",
                    delta_color="normal" if pnl_val >= 0 else "inverse",
                )

            st.divider()

            # Total row
            total_rev  = pnl_df["revenue"].sum()
            total_exp  = pnl_df["expenses"].sum()
            total_prof = pnl_df["profit"].sum()
            tm1, tm2, tm3 = st.columns(3)
            tm1.metric("Total Revenue",  f"₹{total_rev:,.0f}")
            tm2.metric("Total Expenses", f"₹{total_exp:,.0f}")
            tm3.metric("Net Profit/Loss", f"₹{total_prof:,.0f}",
                       delta_color="normal" if total_prof >= 0 else "inverse")

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name="Revenue", x=pnl_df["property"], y=pnl_df["revenue"],
                                     marker_color="#4ade80",
                                     text=[f"₹{v:,.0f}" for v in pnl_df["revenue"]], textposition="outside"))
            fig_bar.add_trace(go.Bar(name="Expenses", x=pnl_df["property"], y=pnl_df["expenses"],
                                     marker_color="#f87171",
                                     text=[f"₹{v:,.0f}" for v in pnl_df["expenses"]], textposition="outside"))
            fig_bar.update_layout(barmode="group", title=f"Revenue vs Expenses — {month_label}",
                                  plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                  font_color="#e2e8f0", legend=dict(bgcolor="#1e293b"),
                                  yaxis=dict(gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"), height=380)
            st.plotly_chart(fig_bar, use_container_width=True)

            fig_profit = go.Figure(go.Bar(
                x=pnl_df["property"], y=pnl_df["profit"],
                marker_color=["#4ade80" if v >= 0 else "#f87171" for v in pnl_df["profit"]],
                text=[f"₹{v:,.0f}" for v in pnl_df["profit"]], textposition="outside"))
            fig_profit.update_layout(title=f"Net Profit / Loss by Property — {month_label}",
                                     plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                     font_color="#e2e8f0", yaxis=dict(gridcolor="#1e293b"),
                                     xaxis=dict(gridcolor="#1e293b"), height=340)
            st.plotly_chart(fig_profit, use_container_width=True)

            st.divider()
            st.subheader(f"Expense Breakdown — {month_label}")
            pie_prop   = st.selectbox("Property for breakdown", ["All"] + PROPERTIES, key="rep_pie_prop")
            exp_summary = get_expense_summary_by_category(
                rep_month, rep_year, property_=None if pie_prop == "All" else pie_prop)

            if exp_summary.empty:
                st.info("No expense data for this period.")
            else:
                fig_pie = px.pie(exp_summary, names="category", values="total",
                                 title=f"Expenses by Category — {pie_prop} — {month_label}",
                                 color_discrete_sequence=px.colors.qualitative.Set3)
                fig_pie.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                      font_color="#e2e8f0", height=420)
                fig_pie.update_traces(textinfo="label+percent+value",
                                      texttemplate="%{label}<br>₹%{value:,.0f}<br>%{percent}")
                st.plotly_chart(fig_pie, use_container_width=True)

            st.divider()
            st.subheader(f"🍽️ Food P&L — {month_label}")
            food = get_food_revenue_vs_cost(rep_month, rep_year)
            fm1, fm2, fm3 = st.columns(3)
            fm1.metric("Food Revenue", f"₹{food['total_food_revenue']:,.0f}")
            fm2.metric("Kitchen Cost", f"₹{food['kitchen_cost']:,.0f}")
            fm3.metric("Food Profit",  f"₹{food['food_profit']:,.0f}",
                       delta_color="normal" if food["food_profit"] >= 0 else "inverse")

            if not food["revenue_by_property"].empty:
                fig_food = go.Figure(go.Bar(
                    x=food["revenue_by_property"]["location"],
                    y=food["revenue_by_property"]["food_revenue"],
                    marker_color="#60a5fa",
                    text=[f"₹{v:,.0f}" for v in food["revenue_by_property"]["food_revenue"]],
                    textposition="outside", name="Food Revenue"))
                fig_food.add_hline(y=food["kitchen_cost"], line_dash="dash", line_color="#f97316",
                                   annotation_text=f"Kitchen Cost ₹{food['kitchen_cost']:,.0f}",
                                   annotation_position="top right")
                fig_food.update_layout(title="Food Revenue vs Kitchen Cost",
                                       plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                       font_color="#e2e8f0", yaxis=dict(gridcolor="#1e293b"),
                                       xaxis=dict(gridcolor="#1e293b"), height=340)
                st.plotly_chart(fig_food, use_container_width=True)

        # ════════════════════════════════════════════════
        # TAB 2 — Period Comparison
        # ════════════════════════════════════════════════
        with report_tab2:
            st.subheader("📈 Period Comparison")

            pc1, pc2 = st.columns(2)
            period_choice = pc1.selectbox(
                "Compare period",
                ["Last 3 months", "Last 6 months", "Last 12 months"],
                key="period_choice"
            )
            period_prop = pc2.selectbox(
                "Property", ["All"] + PROPERTIES, key="period_prop"
            )

            months_map = {"Last 3 months": 3, "Last 6 months": 6, "Last 12 months": 12}
            n_months   = months_map[period_choice]
            prop_arg   = None if period_prop == "All" else period_prop

            period_data = get_period_summary(months_back=n_months, property_=prop_arg)
            period_df   = pd.DataFrame(period_data)

            if period_df.empty or period_df["revenue"].sum() == 0 and period_df["expenses"].sum() == 0:
                st.info("No data available for this period.")
            else:
                # Metrics row: current vs previous month
                if len(period_df) >= 2:
                    curr = period_df.iloc[-1]
                    prev = period_df.iloc[-2]
                    rev_delta  = curr["revenue"]  - prev["revenue"]
                    exp_delta  = curr["expenses"] - prev["expenses"]
                    prof_delta = curr["profit"]   - prev["profit"]

                    pm1, pm2, pm3 = st.columns(3)
                    pm1.metric(f"Revenue ({curr['label']})", f"₹{curr['revenue']:,.0f}",
                               delta=f"{'▲' if rev_delta >= 0 else '▼'} ₹{abs(rev_delta):,.0f} vs {prev['label']}",
                               delta_color="normal" if rev_delta >= 0 else "inverse")
                    pm2.metric(f"Expenses ({curr['label']})", f"₹{curr['expenses']:,.0f}",
                               delta=f"{'▲' if exp_delta >= 0 else '▼'} ₹{abs(exp_delta):,.0f} vs {prev['label']}",
                               delta_color="inverse" if exp_delta >= 0 else "normal")
                    pm3.metric(f"Profit ({curr['label']})", f"₹{curr['profit']:,.0f}",
                               delta=f"{'▲' if prof_delta >= 0 else '▼'} ₹{abs(prof_delta):,.0f} vs {prev['label']}",
                               delta_color="normal" if prof_delta >= 0 else "inverse")

                    # Profit % change
                    if prev["revenue"] > 0:
                        pct_change = ((curr["profit"] - prev["profit"]) / abs(prev["revenue"])) * 100
                        pct_color  = "#4ade80" if pct_change >= 0 else "#ef4444"
                        st.markdown(
                            f'<div style="text-align:center;padding:0.5rem;border-radius:8px;'
                            f'background:#0f172a;border:1px solid #1e293b;margin-bottom:1rem;">'
                            f'<span style="color:#94a3b8;font-size:0.85rem;">Profit % change vs previous month: </span>'
                            f'<span style="color:{pct_color};font-weight:700;font-size:1rem;">'
                            f'{"▲" if pct_change >= 0 else "▼"} {abs(pct_change):.1f}%</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                st.divider()

                # Line chart: Revenue, Expenses, Profit over period
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=period_df["label"], y=period_df["revenue"],
                    name="Revenue", mode="lines+markers+text",
                    line=dict(color="#4ade80", width=2.5),
                    text=[f"₹{v:,.0f}" for v in period_df["revenue"]],
                    textposition="top center", marker=dict(size=7)))
                fig_line.add_trace(go.Scatter(
                    x=period_df["label"], y=period_df["expenses"],
                    name="Expenses", mode="lines+markers+text",
                    line=dict(color="#f87171", width=2.5),
                    text=[f"₹{v:,.0f}" for v in period_df["expenses"]],
                    textposition="top center", marker=dict(size=7)))
                fig_line.add_trace(go.Scatter(
                    x=period_df["label"], y=period_df["profit"],
                    name="Profit/Loss", mode="lines+markers+text",
                    line=dict(color="#a78bfa", width=2.5, dash="dot"),
                    text=[f"₹{v:,.0f}" for v in period_df["profit"]],
                    textposition="top center", marker=dict(size=7)))
                fig_line.add_hline(y=0, line_dash="dash", line_color="#475569")
                fig_line.update_layout(
                    title=f"Revenue, Expenses & Profit — {period_choice}",
                    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                    font_color="#e2e8f0", legend=dict(bgcolor="#1e293b"),
                    yaxis=dict(gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
                    height=420)
                st.plotly_chart(fig_line, use_container_width=True)

                # Bar: profit per month
                fig_pbar = go.Figure(go.Bar(
                    x=period_df["label"], y=period_df["profit"],
                    marker_color=["#4ade80" if v >= 0 else "#f87171" for v in period_df["profit"]],
                    text=[f"₹{v:,.0f}" for v in period_df["profit"]], textposition="outside"))
                fig_pbar.add_hline(y=0, line_dash="dash", line_color="#475569")
                fig_pbar.update_layout(title=f"Monthly Profit/Loss — {period_choice}",
                                       plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                       font_color="#e2e8f0", yaxis=dict(gridcolor="#1e293b"),
                                       xaxis=dict(gridcolor="#1e293b"), height=340)
                st.plotly_chart(fig_pbar, use_container_width=True)

                st.divider()

                # Downloadable table
                st.subheader("📋 Period Summary Table")
                display_df = period_df[["label","revenue","expenses","profit"]].copy()
                display_df.columns = ["Month", "Revenue (₹)", "Expenses (₹)", "Profit/Loss (₹)"]
                display_df["Revenue (₹)"]     = display_df["Revenue (₹)"].apply(lambda x: f"₹{x:,.0f}")
                display_df["Expenses (₹)"]    = display_df["Expenses (₹)"].apply(lambda x: f"₹{x:,.0f}")
                display_df["Profit/Loss (₹)"] = display_df["Profit/Loss (₹)"].apply(lambda x: f"₹{x:,.0f}")
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # CSV download
                csv_df = period_df[["label","revenue","expenses","profit"]].copy()
                csv_df.columns = ["Month","Revenue","Expenses","Profit/Loss"]
                csv_bytes = csv_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download as CSV",
                    data=csv_bytes,
                    file_name=f"hostel_report_{period_choice.replace(' ','_')}.csv",
                    mime="text/csv",
                )

        # ════════════════════════════════════════════════
        # TAB 3 — Yearly Report
        # ════════════════════════════════════════════════
        with report_tab3:
            st.subheader("📆 Yearly Report")

            yc1, yc2 = st.columns(2)
            yr_year = yc1.number_input("Year", min_value=2020, max_value=2100,
                                       value=date.today().year, step=1, key="yr_year")
            yr_prop = yc2.selectbox("Property", ["All"] + PROPERTIES, key="yr_prop")

            yr_prop_arg  = None if yr_prop == "All" else yr_prop
            yearly_data  = get_yearly_summary(yr_year, property_=yr_prop_arg)
            yearly_df    = pd.DataFrame(yearly_data)

            total_rev  = yearly_df["revenue"].sum()
            total_exp  = yearly_df["expenses"].sum()
            total_prof = total_rev - total_exp
            best_month = yearly_df.loc[yearly_df["profit"].idxmax()]
            worst_month= yearly_df.loc[yearly_df["profit"].idxmin()]

            ym1, ym2, ym3 = st.columns(3)
            ym1.metric(f"Total Revenue {yr_year}",  f"₹{total_rev:,.0f}")
            ym2.metric(f"Total Expenses {yr_year}", f"₹{total_exp:,.0f}")
            ym3.metric(f"Net Profit/Loss {yr_year}", f"₹{total_prof:,.0f}",
                       delta_color="normal" if total_prof >= 0 else "inverse")

            bm1, bm2 = st.columns(2)
            bm1.metric("🏆 Best Month",  f"{best_month['label']}",
                       delta=f"₹{best_month['profit']:,.0f} profit",
                       delta_color="normal")
            bm2.metric("📉 Worst Month", f"{worst_month['label']}",
                       delta=f"₹{worst_month['profit']:,.0f}",
                       delta_color="normal" if worst_month["profit"] >= 0 else "inverse")

            st.divider()

            # Yearly area chart
            fig_yr = go.Figure()
            fig_yr.add_trace(go.Bar(name="Revenue", x=yearly_df["label"], y=yearly_df["revenue"],
                                    marker_color="#4ade80",
                                    text=[f"₹{v:,.0f}" for v in yearly_df["revenue"]], textposition="outside"))
            fig_yr.add_trace(go.Bar(name="Expenses", x=yearly_df["label"], y=yearly_df["expenses"],
                                    marker_color="#f87171",
                                    text=[f"₹{v:,.0f}" for v in yearly_df["expenses"]], textposition="outside"))
            fig_yr.add_trace(go.Scatter(name="Profit/Loss", x=yearly_df["label"], y=yearly_df["profit"],
                                        mode="lines+markers",
                                        line=dict(color="#a78bfa", width=2.5),
                                        marker=dict(size=7)))
            fig_yr.add_hline(y=0, line_dash="dash", line_color="#475569")
            fig_yr.update_layout(barmode="group", title=f"Full Year Overview — {yr_year}",
                                  plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                  font_color="#e2e8f0", legend=dict(bgcolor="#1e293b"),
                                  yaxis=dict(gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
                                  height=450)
            st.plotly_chart(fig_yr, use_container_width=True)

            st.divider()

            # Profit % month-over-month
            st.subheader("📊 Month-over-Month Profit % Change")
            yearly_df["profit_pct_change"] = yearly_df["profit"].pct_change() * 100
            fig_pct = go.Figure(go.Bar(
                x=yearly_df["label"][1:],
                y=yearly_df["profit_pct_change"][1:],
                marker_color=["#4ade80" if v >= 0 else "#f87171"
                              for v in yearly_df["profit_pct_change"][1:]],
                text=[f"{v:+.1f}%" for v in yearly_df["profit_pct_change"][1:]],
                textposition="outside"))
            fig_pct.add_hline(y=0, line_dash="dash", line_color="#475569")
            fig_pct.update_layout(title="Profit % Change Month-over-Month",
                                  plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                                  font_color="#e2e8f0", yaxis=dict(gridcolor="#1e293b"),
                                  xaxis=dict(gridcolor="#1e293b"), height=320)
            st.plotly_chart(fig_pct, use_container_width=True)

            st.divider()

            # Yearly table + download
            st.subheader("📋 Yearly Summary Table")
            yr_display = yearly_df[["label","revenue","expenses","profit"]].copy()
            yr_display.columns = ["Month","Revenue (₹)","Expenses (₹)","Profit/Loss (₹)"]
            yr_display["Revenue (₹)"]     = yr_display["Revenue (₹)"].apply(lambda x: f"₹{x:,.0f}")
            yr_display["Expenses (₹)"]    = yr_display["Expenses (₹)"].apply(lambda x: f"₹{x:,.0f}")
            yr_display["Profit/Loss (₹)"] = yr_display["Profit/Loss (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(yr_display, use_container_width=True, hide_index=True)

            csv_yr = yearly_df[["label","revenue","expenses","profit"]].copy()
            csv_yr.columns = ["Month","Revenue","Expenses","Profit/Loss"]
            st.download_button(
                "⬇️ Download Yearly Report as CSV",
                data=csv_yr.to_csv(index=False).encode("utf-8"),
                file_name=f"hostel_yearly_report_{yr_year}.csv",
                mime="text/csv",
            )
