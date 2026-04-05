import streamlit as st  # Streamlit framework

# Step 1: Initialize session state variables (first run only)

# Step 1a: Track the currently active page
if 'page' not in st.session_state:
    st.session_state.page = 1  # Default page to load

# Step 1b: Track whether an error message should be shown
if 'error_status' not in st.session_state:
    st.session_state.error_status = None

# Step 1c: Store the currently selected CodeID (generic context)
if 'current_code' not in st.session_state:
    st.session_state.current_code = None

# Step 1d: Store the CodeID of the signed-in user
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Step 1e: Store the CodeID that should be opened in full view
if 'open_code' not in st.session_state:
    st.session_state.open_code = None


# Step 2: Page navigation helpers

def change_page(new_page):
    # Navigate to a different page and reset error state.
    # Step 2a: Update the active page number
    st.session_state.page = new_page

    # Step 2b: Reset error status so it does not persist across pages
    st.session_state.error_status = True


def change_code(new_code):
    # Change the currently active CodeID in context.
    # Step 3a: Update the currently active CodeID
    st.session_state.current_code = new_code

    # Step 3b: Reset error status so it does not persist
    st.session_state.error_status = True


def user_online(new_code):
    # Register a user as currently connected / signed in.
    # Step 4a: Register the connected user CodeID
    st.session_state.current_user = new_code

    # Step 4b: Update error status to allow messages to display if needed
    st.session_state.error_status = False


def open_new_code(new_code):
    # Open a CodeID in full view and navigate to its page.
    # Step 5a: Store the CodeID to be opened
    st.session_state.open_code = new_code

    # Step 5b: Navigate to the full-view page
    change_page(20)
