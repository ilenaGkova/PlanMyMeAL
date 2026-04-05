import streamlit as st
from User import new_username_question, old_username_question, sign_in_passcode_question, update_user, validate_user, \
    return_all_users, role_table
from AdministrativeFunctions import change_page
from General_Functions import generate_animal_username

# Step 1: Initialize session state variables (first run only)

if 'page' not in st.session_state:
    st.session_state.page = 1  # Default page to load

if 'error_status' not in st.session_state:
    st.session_state.error_status = None  # Tracks whether an error message should be shown

if 'current_user' not in st.session_state:
    st.session_state.current_user = None  # Stores the CodeID of the signed-in user

if 'error' not in st.session_state:
    st.session_state.error = 'You are doing great! Keep going.'  # Stores the current error message


def page_2_layout():
    # Step 1: Validate the currently signed-in user
    # Uses the CodeID stored in session state to confirm the user still exists
    # and is allowed to access this recovery flow
    message, entry, status = validate_user(st.session_state.current_user)

    if status:
        # Step 2: User validated successfully
        # Show the fallback username-recovery UI
        header_section(entry)
        update_username(entry)

    else:
        # Step 3: Validation failed
        # Store the error, so it can be displayed by the global error handler
        st.session_state.error, st.session_state.error_status = message, status


def header_section(entry):
    # Step 0 (exception handling):
    # This page is a safety net for resolving unexpected username collisions.
    # Normal validation should prevent reaching this state.
    # CodeID issues are escalated to administrative review.
    st.title(f"Hello {entry[0]['Username']}")

    st.header("We are so sorry, turns out your username is double booked.")
    st.write("Please kindly change it by filling in all the required fields.")


def update_user_username(entry, codeID: str, old_username: str, new_username: str):
    # Step 1: Verify identity
    # - CodeID re-entered by the user must match the currently signed-in user
    # - Old username must belong to that CodeID
    # - Old username must match what we loaded for the user on this page
    if (
            len(return_all_users({'Username': old_username, 'CodeID': codeID})) == 0
            or codeID != st.session_state.current_user
            or old_username != entry[0]['Username']
    ):
        st.session_state.error = "Credentials do not match. Please try again."
        st.session_state.error_status = False
        return

    # Step 2: Prevent no-op updates
    # The new username must be different from the old one
    if old_username == new_username:
        st.session_state.error = "You need to choose a different username."
        st.session_state.error_status = False
        return

    # Step 3: Update username and restore normal user role
    # If the update succeeds, redirect the user to the next page
    st.session_state.error, _, st.session_state.error_status = update_user(
        codeID,
        new_username,
        codeID,
        True,
        role_table["Plain User"]
    )

    if st.session_state.error_status:
        change_page(3)


def update_username(entry):
    # Step 1: Render the sign-up UI container
    with st.container(border=True):

        # Step 2: Ask the user to confirm identity and current username
        codeID = st.text_input(sign_in_passcode_question, key="passcode", type="password")
        old_username = st.text_input(old_username_question, key="username")

        # Step 3: Ask for the new username
        new_username = st.text_input(new_username_question, key="username")

        # Step 4: Offer a fun auto-generated suggestion (non-binding)
        st.write(f"Try {generate_animal_username()}! We think it would sound fun.")

        # Step 5: Attempt username update on confirmation
        st.button(
            f"Let's get started {new_username}",
            use_container_width=True,
            on_click=update_user_username,
            args=[entry, codeID, old_username, new_username],
            key="create_user"
        )
