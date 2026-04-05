import streamlit as st
from AdministrativeFunctions import change_page
from Menu import menu
from MongoDB_General_Functions import get_now
from Page_10 import manage_ingredients
from Page_13 import manage_rules
from Page_15 import manage_unit_types
from Page_12 import manage_meal_types
from Page_16 import show_user_information
from Page_11 import manage_meals
from Page_8 import manage_categories
from Request import request_description_label, create_request
from User import validate_user

# Step 1: Initialize session state variables (first run only)
# Step 1a: Track the current page number
if "page" not in st.session_state:
    st.session_state.page = 1

# Step 1b: Track whether an error message should be shown
if "error_status" not in st.session_state:
    st.session_state.error_status = None

# Step 1c: Store the current signed-in user's CodeID
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Step 1d: Store the current error message (global handler reads this)
if "error" not in st.session_state:
    st.session_state.error = "You are doing great! Keep going."

# Step 1e: Store the CodeID to open in "full view"
if "open_code" not in st.session_state:
    st.session_state.open_code = None


def create_request_officially(description: str, itemID: str):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_request(description, itemID, get_now())

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def page_7_layout():
    # Step 2: Page entrypoint 
    # Page 7: Profile Page / Data Management page.
    # Validates user, renders menu, and loads search UI + results.

    # Step 2a: Validate the currently signed-in user
    # Uses the CodeID stored in session state
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2b: If valid, render menu and enforce permissions
    if status:
        menu(entry)

        st.header("User Information")
        # Step 3: Show User Profile
        with st.container(border=True):
            show_user_information(entry)

        st.header("The Recipe Book")

        # Step 4: Select collection to manage
        title, option = st.columns(2, vertical_alignment="center")

        with title:
            st.write("Manage my ")

        with option:
            collection = st.selectbox(
                "Collection",
                options=(key for key in manage_table),
                label_visibility="collapsed",
                key="pick_option",
            )

        # Step 5: Show collection options
        with st.container(border=True):
            manage_table[collection]()

        # Step 6: Make Request
        with st.container(border=True):
            st.header("Make Request")
            itemID = st.text_input("Subject: ", value=st.session_state.current_user, disabled=True)
            description = st.text_input(request_description_label)

            st.button(
                f"Make Request",
                use_container_width=True,
                on_click=create_request_officially,
                args=[description, itemID],
                key=f"make_request"
            )

    else:
        # Step 2c: Validation failed; store error for global handler
        st.session_state.error = message
        st.session_state.error_status = status


manage_table = {
    'Meals': manage_meals,
    'Meal Category': manage_categories,
    'Schedule Types': manage_meal_types,
    'Ingredients': manage_ingredients,
    'Unit Types': manage_unit_types,
    'Rules': manage_rules
}