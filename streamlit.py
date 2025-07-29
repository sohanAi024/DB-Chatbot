import streamlit as st
import requests
import pandas as pd
import io
from datetime import datetime
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
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .user-message {
        background-color: #667eea;
        color: white;
        margin-left: 20%;
    }
    
    .ai-message {
        background-color: #f1f3f4;
        color: #333;
        margin-right: 20%;
    }
    
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_api_call(endpoint, method="GET", data=None):
    """Make API call to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return True, response.json()
        else:
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

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "ai", "content": "Hello! I can help you search for users or download data. Try asking:\n• 'Show me data for john'\n• 'Download excel for sara'"}
    ]

if 'users_data' not in st.session_state:
    st.session_state.users_data = []

if 'search_results' not in st.session_state:
    st.session_state.search_results = []



# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 User Management System</h1>
    <p>AI-Powered User Management with Smart Chat</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🔧 Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["💬 AI Chat", "👥 User Management", "📊 Reports"]
)

# =============================================================================
# AI CHAT PAGE
# =============================================================================

if page == "💬 AI Chat":
    st.title("💬 AI Assistant")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>AI:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Ask me about users...", key="chat_input")
    
    with col2:
        send_button = st.button("Send", type="primary")
    
    # Process chat message
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Make API call
        success, response = make_api_call("/chat", "POST", {"message": user_input})
        
        if success:
            # Add AI response to history
            st.session_state.chat_history.append({"role": "ai", "content": response["response"]})
            
            # Store search results if available
            if response.get("has_data") and response.get("data"):
                st.session_state.search_results = response["data"]
                st.session_state.download_id = response.get("download_id")
            else:
                st.session_state.search_results = []
                st.session_state.download_id = None
        else:
            st.session_state.chat_history.append({"role": "ai", "content": f"Sorry, I encountered an error: {response}"})
        
        # Rerun to update chat display
        st.rerun()

# Always show last search results table if available
if page == "💬 AI Chat" and st.session_state.search_results:
    st.markdown("### 🔍 Search Results")
    df = pd.DataFrame(st.session_state.search_results)
    if 'id' in df.columns:
        df = df.drop('id', axis=1)
    st.dataframe(df, use_container_width=True)
    # Download button (use backend-generated Excel if available)
    if st.session_state.get("download_id"):
        download_url = f"{API_BASE_URL}/download/{st.session_state.download_id}"
        st.markdown(
            f'<a href="{download_url}" download="search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx">'
            '📥 <b>Download Excel</b></a>',
            unsafe_allow_html=True
        )
    else:
        excel_data = download_excel(st.session_state.search_results, "search_results.xlsx")
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =============================================================================
# USER MANAGEMENT PAGE
# =============================================================================

elif page == "👥 User Management":
    st.title("👥 User Management")
    
    # Two columns layout
    col1, col2 = st.columns([1, 1])
    
    # Left column - Add User Form
    with col1:
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form"):
            name = st.text_input("Name *", placeholder="Enter full name")
            email = st.text_input("Email *", placeholder="user@example.com")
            phone = st.text_input("Phone", placeholder="+1-555-0123")
            address = st.text_area("Address", placeholder="Enter address")
            salary = st.number_input("Salary", min_value=0, value=0, step=1000)
            
            submitted = st.form_submit_button("Add User", type="primary")
            
            if submitted:
                if name and email:
                    user_data = {
                        "name": name,
                        "email": email,
                        "phone": phone if phone else "",
                        "address": address if address else "",
                        "salary": salary if salary > 0 else None
                    }
                    
                    success, response = make_api_call("/users", "POST", user_data)
                    
                    if success:
                        st.markdown("""
                        <div class="success-box">
                            ✅ User added successfully!
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown(f"""
                        <div class="error-box">
                            ❌ Error adding user: {response}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Name and Email are required!")
    
    # Right column - Users List
    with col2:
        st.subheader("📋 Users List")

        # Refresh button
        refresh = st.button("🔄 Refresh List", type="secondary")

        # Always reload users if refresh is clicked or after adding a user
        if refresh or st.session_state.get("force_reload_users", False):
            success, response = make_api_call("/users")
            if success:
                if isinstance(response, list):
                    st.session_state.users_data = response
                else:
                    st.session_state.users_data = response.get("users", [])
            else:
                st.session_state.users_data = []
            st.session_state.force_reload_users = False

        # Always load users if not already loaded
        if not st.session_state.users_data:
            success, response = make_api_call("/users")
            if success:
                if isinstance(response, list):
                    st.session_state.users_data = response
                else:
                    st.session_state.users_data = response.get("users", [])
            else:
                st.session_state.users_data = []

        # Display users
        if st.session_state.users_data:
            df = pd.DataFrame(st.session_state.users_data)
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            st.dataframe(df, use_container_width=True, height=400)
            st.markdown(f"**Total Users:** {len(st.session_state.users_data)}")
        else:
            st.info("No users found. Add some users to get started!")

# =============================================================================
# REPORTS PAGE
# =============================================================================

elif page == "📊 Reports":
    st.title("📊 Data Reports & Export")
    
    # Users overview
    st.subheader("👥 Users Overview")
    
    # Load users data
    success, response = make_api_call("/users")
    if success:
        users_data = response.get("users", [])
        
        if users_data:
            df = pd.DataFrame(users_data)
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Users", len(users_data))
            
            with col2:
                avg_salary = df['salary'].mean() if 'salary' in df.columns and df['salary'].notna().sum() > 0 else 0
                st.metric("Average Salary", f"${avg_salary:,.0f}")
            
            with col3:
                with_phone = df['phone'].notna().sum() if 'phone' in df.columns else 0
                st.metric("Users with Phone", with_phone)
            
            with col4:
                with_address = df['address'].notna().sum() if 'address' in df.columns else 0
                st.metric("Users with Address", with_address)
            
            # Data table
            st.subheader("📋 All Users Data")
            display_df = df.drop('id', axis=1) if 'id' in df.columns else df
            st.dataframe(display_df, use_container_width=True)
            
            # Download options
            st.subheader("📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download all users
                excel_data = download_excel(users_data, "all_users.xlsx")
                st.download_button(
                    label="📊 Download All Users Excel",
                    data=excel_data,
                    file_name=f"all_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            
            with col2:
                # Download CSV
                csv_data = display_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Salary distribution chart (if salary data exists)
            if 'salary' in df.columns and df['salary'].notna().sum() > 0:
                st.subheader("💰 Salary Distribution")
                salary_data = df[df['salary'].notna()]['salary']
                st.bar_chart(salary_data)
        
        else:
            st.info("No users data available. Add some users first!")
    
    else:
        st.error(f"Failed to load users data: {response}")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🤖 User Management System | Powered by Streamlit & FastAPI
</div>
""", unsafe_allow_html=True)

# Auto-refresh option in sidebar
st.sidebar.markdown("---")
if st.sidebar.checkbox("🔄 Auto-refresh data"):
    st.sidebar.info("Data will refresh every 30 seconds")
    # You can add auto-refresh logic here if needed