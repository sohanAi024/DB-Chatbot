import streamlit as st
import requests
import pandas as pd
import io
import altair as alt
from datetime import datetime, timedelta
import time
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

API_BASE_URL = "http://localhost:8000/api"

# Page config
st.set_page_config(
    page_title="User Management System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# CHATGPT STYLE CSS
# =============================================================================
st.markdown("""
<style>
    /* Hide default streamlit header */
    header {visibility:hidden}

    /* Sidebar like ChatGPT - LIGHT THEME */
    section[data-testid="stSidebar"] {
        width: 260px !important;
        background-color: #ffffff !important;
        border-right: 1px solid #e5e5e5 !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] .section-label,
    section[data-testid="stSidebar"] .date-label {
        color: #202123 !important;
    }

    /* Hide sidebar scrollbar */
    [data-testid="stSidebarContent"]::-webkit-scrollbar {
        display: none;
    }
    [data-testid="stSidebarContent"] {
        -ms-overflow-style: none;
        scrollbar-width: none;
        background-color: #ffffff !important;
    }
    
    /* Sidebar account area - contained within sidebar */
    .account-box-wrapper {
        margin-top: auto;
        padding: 0 10px 20px 10px;
    }

    /* Dropdown menu styling - LIGHT THEME */
    .dropdown-container {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 4px;
        margin-bottom: 8px;
        box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .dropdown-item button {
        width: 100% !important;
        padding: 10px 12px !important;
        background: transparent !important;
        color: #202123 !important;
        border: none !important;
        text-align: left !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        justify-content: flex-start !important;
    }
    
    .dropdown-item button:hover {
        background-color: #f7f7f8 !important;
    }

    /* Specific styling for sidebar buttons to match light theme */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        color: #202123;
        border: 1px solid #e5e5e5;
        text-align: left;
        justify-content: flex-start;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f7f7f8;
        border-color: #d1d1d1;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f0f0f0 !important;
        color: #202123 !important;
        border: 1px solid #e5e5e5 !important;
    }

    .divider-line {
        border-bottom: 1px solid #e5e5e5;
        margin: 1rem 0;
    }

    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #666666 !important;
        letter-spacing: 0.05em;
    }

    .date-label {
        font-size: 0.7rem;
        color: #888888 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Chat container center */
    .main .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "ai", "content": "Hello! I am your Universal Database Analyst. Connect a database in the sidebar, and I can help you analyze any table or generate reports. Try asking:\n• 'Show me the schema of this database'\n• 'List all tables available'"}
    ]

if 'users_data' not in st.session_state:
    st.session_state.users_data = []

if 'access_token' not in st.session_state:
    st.session_state.access_token = None

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None

if 'user_info' not in st.session_state:
    st.session_state.user_info = None

if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "Sign Up"

if 'conversations' not in st.session_state:
    st.session_state.conversations = []

if 'refresh_conversations' not in st.session_state:
    st.session_state.refresh_conversations = True

if 'current_page' not in st.session_state:
    st.session_state.current_page = "💬 AI Chat"

if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False

if 'show_user_dropdown' not in st.session_state:
    st.session_state.show_user_dropdown = False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def make_api_call(endpoint, method="GET", data=None):
    """Make API call to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = {}
        if 'access_token' in st.session_state and st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
            
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            # For login endpoint, use form data if it's the auth login
            if endpoint == "/auth/login":
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                # Try to get error details from JSON
                error_data = response.json()
                if isinstance(error_data, dict) and "detail" in error_data:
                    return False, error_data["detail"]
                return False, f"Error: {response.status_code} - {error_data}"
            except:
                return False, f"Error: {response.status_code}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def download_excel(data, filename):
    """Create downloadable Excel file"""
    df = pd.DataFrame(data)
    if 'id' in df.columns:
        df = df.drop('id', axis=1)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Users')

    return output.getvalue()

def fetch_conversation_history(thread_id):
    """Fetch all messages for a thread from the server"""
    success, resp = make_api_call(f"/conversations/{thread_id}/messages", "GET")
    if success:
        history = resp["messages"]
        if not history:
             return [{"role": "ai", "content": "Hello! I am your Universal Database Analyst. How can I help you today?"}]
        return history
    return [{"role": "ai", "content": "Welcome back! What would you like to analyze next?"}]


def load_conversations():
    """Fetch conversation list from API"""
    if 'refresh_conversations' not in st.session_state:
        st.session_state.refresh_conversations = True
        
    if st.session_state.refresh_conversations:
        success, resp = make_api_call("/conversations", "GET")
        if success:
            st.session_state.conversations = resp["conversations"]
            st.session_state.refresh_conversations = False


def group_conversations_by_date(conversations):
    """Group conversations into semantic date buckets"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    
    groups = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Older": []
    }
    
    for conv in conversations:
        created_at = conv.get('created_at')
        if isinstance(created_at, str):
            # Handle potential 'Z' or offset formats
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            dt = created_at
            
        conv_date = dt.date()
        
        if conv_date == today:
            groups["Today"].append(conv)
        elif conv_date == yesterday:
            groups["Yesterday"].append(conv)
        elif conv_date >= last_week:
            groups["Previous 7 Days"].append(conv)
        else:
            groups["Older"].append(conv)
            
    return {k: v for k, v in groups.items() if v}

# (No top navigation bar - using ChatGPT style sidebar)

# (Using ChatGPT style chat area below)

# =============================================================================
# PROFESSIONAL SIDEBAR LAYOUT
# =============================================================================

with st.sidebar:
    # ========================================
    # TOP SECTION - NAVIGATION
    # ========================================
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <p class="section-label">Quick Navigation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 AI Chat", use_container_width=True, type="primary" if st.session_state.current_page == "💬 AI Chat" else "secondary"):
            st.session_state.current_page = "💬 AI Chat"
            st.rerun()
    with col2:
        if st.button("📊 Reports", use_container_width=True, type="primary" if st.session_state.current_page == "📊 Reports" else "secondary"):
            st.session_state.current_page = "📊 Reports"
            st.rerun()
    
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

    # ========================================
    # MIDDLE SECTION - CHAT HISTORY (if logged in)
    # ========================================
    if st.session_state.access_token:
        st.markdown('<p class="section-label">Conversations</p>', unsafe_allow_html=True)
        
        # New Chat Button
        has_user_messages = any(m['role'] == 'user' for m in st.session_state.chat_history)
        if st.button("➕ New Chat", use_container_width=True, disabled=not has_user_messages, type="primary"):
            success, resp = make_api_call("/conversations/new", "POST")
            if success:
                st.session_state.thread_id = resp["thread_id"]
                st.session_state.chat_history = [{"role": "ai", "content": "Welcome to your new chat! How can I help you today?"}]
                st.session_state.refresh_conversations = True
                st.rerun()
        
        if not has_user_messages:
            st.caption("💡 Start chatting to save history")

        # Fetch and Group conversations
        load_conversations()
        
        if st.session_state.conversations:
            grouped_convs = group_conversations_by_date(st.session_state.conversations)
            
            # Scrollable History area
            history_container = st.container(height=450)
            with history_container:
                for group_name, convs in grouped_convs.items():
                    st.markdown(f'<div class="date-label">{group_name}</div>', unsafe_allow_html=True)
                    
                    for conv in convs:
                        thread_id = conv['thread_id']
                        is_active = st.session_state.thread_id == thread_id
                        
                        # Row container for list item
                        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
                        
                        with c1:
                            display_title = conv['title']
                            if len(display_title) > 22:
                                display_title = display_title[:19] + "..."
                                
                            btn_type = "primary" if is_active else "secondary"
                            if st.button(f"💬 {display_title}", key=f"btn_{thread_id}", use_container_width=True, type=btn_type):
                                st.session_state.thread_id = thread_id
                                st.session_state.chat_history = fetch_conversation_history(thread_id)
                                st.rerun()
                        
                        with c2:
                            if st.button("✏️", key=f"edit_{thread_id}", help="Rename", use_container_width=True):
                                st.session_state[f"renaming_{thread_id}"] = True
                        
                        with c3:
                            if st.button("🗑️", key=f"del_{thread_id}", help="Delete", use_container_width=True):
                                success, _ = make_api_call(f"/conversations/{thread_id}", "DELETE")
                                if success:
                                    if st.session_state.thread_id == thread_id:
                                        st.session_state.thread_id = None
                                        st.session_state.chat_history = []
                                    st.session_state.refresh_conversations = True
                                    st.rerun()
                        
                        # Renaming interaction overlay
                        if st.session_state.get(f"renaming_{thread_id}"):
                            with st.expander("📝 Rename Chat", expanded=True):
                                new_title = st.text_input("New Title", value=conv['title'], key=f"input_{thread_id}")
                                r_col1, r_col2 = st.columns(2)
                                with r_col1:
                                    if st.button("Save", key=f"save_{thread_id}", use_container_width=True, type="primary"):
                                        success, _ = make_api_call(f"/conversations/{thread_id}/title", "PATCH", {"title": new_title})
                                        if success:
                                            st.session_state[f"renaming_{thread_id}"] = False
                                            st.session_state.refresh_conversations = True
                                            st.rerun()
                                with r_col2:
                                    if st.button("Stop", key=f"cancel_{thread_id}", use_container_width=True):
                                        st.session_state[f"renaming_{thread_id}"] = False
                                        st.rerun()
        
        st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

    # ========================================
    # DATABASE CONNECTION SECTION
    # ========================================
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <p class="section-label">Database</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔌 Connection Settings", expanded=False):
        db_url = st.text_input("Database URL", placeholder="postgresql://...", type="password")
        if st.button("Connect", use_container_width=True, type="primary"):
            if db_url:
                with st.spinner("Connecting..."):
                    success, response = make_api_call("/connect-db", "POST", {"database_url": db_url})
                    if success:
                        st.success("✓ Connected!")
                        st.session_state.db_connected = True
                    else:
                        st.error(f"Failed: {response}")
            else:
                st.warning("Enter URL")
    
    # ========================================
    # BOTTOM SECTION - USER ACCOUNT / LOGOUT
    # ========================================
    if st.session_state.access_token:
        # Create account box with dropdown functionality
        col_dropdown = st.columns([1])[0]
        
        with col_dropdown:
            # Clickable account box (styled as button)
            if st.button(f"👤 {st.session_state.user_info['username']}\n🟢 Online", 
                        use_container_width=True, 
                        key="user_account_btn"):
                st.session_state.show_user_dropdown = not st.session_state.show_user_dropdown
        
        # Show dropdown menu if active
        if st.session_state.show_user_dropdown:
            st.markdown("""
            <div style="background: #ffffff; border: 1px solid #e5e5e5; border-radius: 8px; 
                        padding: 8px; margin-top: 8px; margin-bottom: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            """, unsafe_allow_html=True)
            
            col_logout = st.columns([1])[0]
            with col_logout:
                if st.button("🚪 Logout", use_container_width=True, key="logout_from_dropdown"):
                    st.session_state.access_token = None
                    st.session_state.user_info = None
                    st.session_state.chat_history = []
                    st.session_state.thread_id = None
                    st.session_state.conversations = []
                    st.session_state.show_user_dropdown = False
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # For guest mode, show account box
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e5e5e5; border-radius: 8px; 
                    padding: 12px; text-align: center;">
            <div style="font-weight: 600; font-size: 14px; color: #202123; margin-bottom: 4px;">👤 Guest Mode</div>
            <div style="font-size: 12px; color: #666666;">Sign in for history</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-spacer" style="height: 120px;"></div>', unsafe_allow_html=True)
    if not st.session_state.access_token:
        st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <p class="section-label">Account</p>
        </div>
        """, unsafe_allow_html=True)
        
        # LOGIN / SIGNUP FORMS
        if st.session_state.auth_mode == "Login":
            st.markdown('<div style="margin-bottom: 0.75rem;"><p style="color: #666; font-size: 0.85rem; margin: 0;">Sign in to your account</p></div>', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
            
            if st.button("🔓 Log In", use_container_width=True, type="primary"):
                success, resp = make_api_call("/auth/login", "POST", {"username": username, "password": password})
                if success:
                    st.session_state.access_token = resp["access_token"]
                    st.session_state.user_info = {"username": username}
                    st.success(f"✓ Welcome, {username}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {resp}")
            
            if st.button("📝 Create Account", use_container_width=True):
                st.session_state.auth_mode = "Sign Up"
                st.rerun()
                
        else:  # Sign Up Mode
            st.markdown('<div style="margin-bottom: 0.75rem;"><p style="color: #666; font-size: 0.85rem; margin: 0;">Create a new account</p></div>', unsafe_allow_html=True)
            new_username = st.text_input("Username", key="signup_user", placeholder="Choose a username")
            new_email = st.text_input("Email", key="signup_email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", key="signup_pass", placeholder="Create password")
            
            if st.button("✓ Sign Up", use_container_width=True, type="primary"):
                success, resp = make_api_call("/auth/register", "POST", {"username": new_username, "email": new_email, "password": new_password})
                if success:
                    st.success("✓ Success! Please login.")
                    st.session_state.auth_mode = "Login"
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {resp}")
            
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.auth_mode = "Login"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # Close sidebar-footer


# =============================================================================
# AI CHAT PAGE
# =============================================================================

if st.session_state.current_page == "💬 AI Chat":
    st.title("💬 AI Assistant")

    # Chat container
    # Display chat history using native components
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display persisted data if available (Hidden by default)
            if message.get("data"):
                with st.expander("📊 View Source Data & Export", expanded=False):
                    df = pd.DataFrame(message["data"])
                    if 'id' in df.columns:
                        df = df.drop('id', axis=1)
                    st.dataframe(df, use_container_width=True)
                    
                    # Display download link
                    if message.get("download_id"):
                        download_url = f"{API_BASE_URL}/download/{message['download_id']}"
                        st.markdown(
                            f'<a href="{download_url}" download="results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx">'
                            '📥 <b>Download Excel</b></a>',
                            unsafe_allow_html=True
                        )
                    else:
                        # Fallback to client-side generation
                        excel_data = download_excel(message["data"], "results.xlsx")
                        st.download_button(
                            label="📥 Download Excel",
                            data=excel_data,
                            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{int(time.time()*1000)}_{str(message.get('content'))[:10]}" 
                        )

    # Chat input
    if prompt := st.chat_input("Ask me about the database..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Make API call
        with st.chat_message("ai"):
            with st.spinner("Thinking..."):
                chat_data = {"message": prompt}
                if st.session_state.thread_id:
                    chat_data["thread_id"] = st.session_state.thread_id
                
                success, response = make_api_call("/chat", "POST", chat_data)
                
            if success:
                response_content = response["response"]
                # Save thread_id for continuity
                if response.get("thread_id"):
                    st.session_state.thread_id = response["thread_id"]
                
                # Refresh conversations to update sidebar titles immediately
                conv_success, conv_resp = make_api_call("/conversations", "GET")
                if conv_success:
                    st.session_state.conversations = conv_resp["conversations"]
                
                # Display and Save AI response to history
                st.markdown(response_content)
                new_message = {"role": "ai", "content": response_content}
                if response.get("has_data") and response.get("data"):
                    new_message["data"] = response["data"]
                    new_message["download_id"] = response.get("download_id")
                
                st.session_state.chat_history.append(new_message)
            else:
                error_msg = f"Sorry, I encountered an error: {response}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "ai", "content": error_msg})
        
        st.rerun()


# =============================================================================
# REPORTS PAGE
# =============================================================================

elif st.session_state.current_page == "📊 Reports":
    st.title("📊 Data Reports & Export")

    # Fetch schema to populate table selector
    with st.spinner("Fetching database schema..."):
        success, response = make_api_call("/schema")
        
    if success and "schema" in response:
        tables = response["schema"]
        table_names = [t["table_name"] for t in tables]
        
        if not table_names:
            st.warning("No tables found in the connected database.")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_table = st.selectbox("Select Table to Analyze", table_names)
                
            # Find selected table schema to check capabilities if needed
            selected_schema = next((t for t in tables if t["table_name"] == selected_table), None)
            
            # Fetch data for selected table
            with st.spinner(f"Loading data for {selected_table}..."):
                d_success, d_response = make_api_call(f"/data/{selected_table}")
                
            if d_success and "data" in d_response:
                data = d_response["data"]
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # --- METRICS SECTION ---
                    st.subheader(f"📈 Overview: {selected_table}")
                    
                    # Dynamic Metrics
                    m_cols = st.columns(4)
                    with m_cols[0]:
                        st.metric("Total Records", len(df))
                        
                    # Find numeric columns for stats
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    
                    # Display up to 3 numeric averages
                    for i, col in enumerate(numeric_cols[:3]):
                        with m_cols[i+1]:
                            avg_val = df[col].mean()
                            st.metric(f"Avg {col}", f"{avg_val:,.2f}")

                    # --- RAW DATA SECTION ---
                    st.subheader("📋 Raw Data Preview")
                    # Handle ID column if present (optional hide)
                    display_df = df.copy()
                    if 'id' in display_df.columns:
                        display_df = display_df.set_index('id')
                    st.dataframe(display_df, use_container_width=True)
                    
                    # --- EXPORT SECTION ---
                    st.subheader("📥 Export Options")
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                         # Download Excel
                        excel_data = download_excel(data, f"{selected_table}.xlsx")
                        st.download_button(
                            label=f"📊 Download {selected_table} Excel",
                            data=excel_data,
                            file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    with e_col2:
                         # Download CSV
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv_data,
                            file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )

                    # --- AUTO CHARTS SECTION ---
                    if numeric_cols:
                        st.subheader("📊 Data Visualizations")
                        # Allow user to pick columns for X and Y
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                             # Try to find a text column for labels (not ID)
                            text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
                            default_x = text_cols[0] if text_cols else numeric_cols[0]
                            x_axis = st.selectbox("X Axis", df.columns, index=df.columns.get_loc(default_x))
                        
                        with c_col2:
                            default_y = numeric_cols[0]
                            y_axis = st.selectbox("Y Axis (Numeric)", numeric_cols, index=numeric_cols.index(default_y))
                            
                        # Altair Chart
                        chart = alt.Chart(df).mark_bar().encode(
                            x=alt.X(x_axis, sort=None),
                            y=alt.Y(y_axis),
                            tooltip=[x_axis, y_axis]
                        ).interactive()
                        
                        st.altair_chart(chart, use_container_width=True)
                        
                else:
                    st.info(f"Table '{selected_table}' is empty.")
            else:
                st.error(f"Failed to load data for {selected_table}: {d_response}")
                    
    else:
        st.error(f"Failed to fetch schema. Make sure you are connected to a database. Error: {response}")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("""

""", unsafe_allow_html=True)