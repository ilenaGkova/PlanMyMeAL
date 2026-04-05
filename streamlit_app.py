import streamlit as st

# Step 1: Configure the Streamlit page
st.set_page_config(
    page_title="Plan My Week",
    page_icon="👋",
)

# Step 2: Initialize global session state variables (first run only)
if 'page' not in st.session_state:
    st.session_state.page = 1  # Default page to load

if 'error' not in st.session_state:
    st.session_state.error = 'You are doing great! Keep going.'  # Default error message

if 'error_status' not in st.session_state:
    st.session_state.error_status = True  # True means "no error to show"

# Step 4: Render the page layout based on the current page number
# Step 4a: st.session_state.page controls which layout loads
# Step 4b: Each page layout is stored in a separate file (Page_{N}.py)

# Step 5: Enforce login rules (project convention)
# Step 5a: Page 1 is the login / sign-up page
# Step 5b: All other pages require a valid signed-in user

# Step 6: UI conventions used across the project
# Step 6a: Buttons and inputs must use unique keys (key="...")
# Step 6b: Button actions use on_click=... and optional args=[...]
# Step 6c: Text output uses st.write/st.header/st.title OR st.markdown for HTML
# Step 6d: Layout grouping uses containers, columns, and "with ..." blocks

# Step 7: Database logging convention (project convention)
# Step 7a: Deletions are logged via the Record collection
# Step 7b: Other actions are also logged with an action letter
# Step 7c: See collection files for details (User.py, Schedule.py, Rule.py, Record.py, etc.)

# Step 8: Terminology note (project convention)
# Step 8a: Database fields refer to "recommendations"
# Step 8b: UI text shows the word "task"

# Step 9: Load the correct page layout
if st.session_state.page == 1:
    # Step 9a: Import and render Page 1 (login / sign-up)
    from Page_1 import page_1_layout
    page_1_layout()

elif st.session_state.page == 2:
    # Step 9b: Import and render Page 2 (Change Username)
    from Page_2 import page_2_layout
    page_2_layout()

elif st.session_state.page == 3:
    # Step 9c: Import and render Page 3 (Home page)
    from Page_3 import page_3_layout
    page_3_layout()

elif st.session_state.page == 4:
    # Step 9d: Import and render Page 4 (Grocery page)
    from Page_4 import page_4_layout
    page_4_layout()

elif st.session_state.page == 5:
    # Step 9e: Import and render Page 5 (Meal Plan page)
    from Page_5 import page_5_layout
    page_5_layout()

elif st.session_state.page == 6:
    # Step 10a: Import and render Page 6 (Accountability page)
    from Page_6 import page_6_layout
    page_6_layout()

elif st.session_state.page == 7:
    # Step 10b: Import and render Page 7 (Profile page)
    from Page_7 import page_7_layout
    page_7_layout()

elif st.session_state.page == 8:
    # Step 11a: Import and render Page 8 (Category page)
    from Page_8 import page_8_layout
    page_8_layout()

elif st.session_state.page == 9:
    # Step 11b: Import and render Page 9 (Day page)
    from Page_9 import page_9_layout
    page_9_layout()

elif st.session_state.page == 10:
    # Step 11c: Import and render Page 10 (Ingredient page)
    from Page_10 import page_10_layout
    page_10_layout()

elif st.session_state.page == 11:
    # Step 11d: Import and render Page 11 (Meal page)
    from Page_11 import page_11_layout
    page_11_layout()

elif st.session_state.page == 12:
    # Step 11e: Import and render Page 12 (MealType page)
    from Page_12 import page_12_layout
    page_12_layout()

elif st.session_state.page == 13:
    # Step 11f: Import and render Page 13 (Rule page)
    from Page_13 import page_13_layout
    page_13_layout()

elif st.session_state.page == 14:
    # Step 11g: Import and render Page 14 (Schedule page)
    from Page_14 import page_14_layout
    page_14_layout()

elif st.session_state.page == 15:
    # Step 11h: Import and render Page 15 (Unit Type page)
    from Page_15 import page_15_layout
    page_15_layout()

elif st.session_state.page == 16:
    # Step 11i: Import and render Page 16 (User page)
    from Page_16 import page_16_layout
    page_16_layout()

elif st.session_state.page == 17:
    # Step 11j: Import and render Page 17 (Request page)
    from Page_17 import page_17_layout
    page_17_layout()

elif st.session_state.page == 18:
    # Step 11k: Import and render Page 18 (Record page)
    from Page_18 import page_18_layout
    page_18_layout()

elif st.session_state.page == 20:
    # Step 11l: Import and render Page 20 (Open Code page)
    from Page_20 import page_20_layout
    page_20_layout()

else:
    # Step 12: Temporary fallback output for non-page-1 routes
    st.session_state.error, st.session_state.error_status = f"You are on page {st.session_state.page}. It is under construction, but we promise it is coming. See you soon!", False

# Step 13: Show the error container if an error is active
# Any function that returns a status returns False on non-completion. Errors are displayed only when status is False, except for return-all functions which return data only
if not st.session_state.error_status:
    with st.container(border=True):
        st.header(st.session_state.error)