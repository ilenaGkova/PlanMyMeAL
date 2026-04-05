import streamlit as st
from User import return_all_users, sign_in_username_question, sign_up_username_question, \
    sign_in_passcode_question, create_admin, create_user, role_table
from AdministrativeFunctions import change_page, user_online
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


def page_1_layout():
    # Step 2: Ensure an admin exists (first ever run of the database)
    if len(return_all_users({})) == 0:
        st.session_state.error, _, st.session_state.error_status = create_admin("Admin123")

    # Step 3: Render the existing-user login section
    existing_user()

    # Step 4: Render the page header / instructions section
    header_section()

    # Step 5: Render the new-user sign-up section
    new_user()


def log_in(username: str, codeID: str):
    # Step 1: Fetch user entry matching credentials
    entry = len(return_all_users({'Username': username, 'CodeID': codeID}))

    # Step 2: If no match is found, show an error
    if entry == 0:
        st.session_state.error, st.session_state.error_status = "Credentials do not Match. Try Again Later", False

    # Step 3: If a match is found, register the user as online and route to the correct page
    else:
        user_online(codeID)
        # Step 3a: Route based on result count
        if entry == 1:
            change_page(3)
        else:
            change_page(2)


def existing_user():
    # Step 1: Render login UI in the sidebar
    st.sidebar.header('Already have an account? Sign in!')

    # Step 2: Collect username input
    username = st.sidebar.text_input(sign_in_username_question, key="username")

    # Step 3: Collect passcode input
    passcode = st.sidebar.text_input(sign_in_passcode_question, key="codeID", type="password")

    # Step 4: Trigger login on button click
    st.sidebar.button(
        'Log in',
        use_container_width=True,
        on_click=log_in,
        args=[username, passcode],
        key="sign_in_user"
    )


def header_section():
    # Step 1: Render page title and instructions
    st.title('Wellcome to Plan My Meal!')
    st.header('Your first stop to taking charge of your nutrition journey')
    st.write('If you have an account log in on the left side of the page.')
    st.write('If the log in form is not visible and you are on your phone click the :material/arrow_forward_ios: icon.')
    st.write("New here? Please answer the following questions and we'll create your account. Start with your username and we will move on.")


def create_new_user(username: str):
    # Step 1: Create a new plain user in the database
    st.session_state.error, entry, st.session_state.error_status = create_user(username, None, role_table["Plain User"])

    # Step 2: Route to the next page if creation succeeded
    if st.session_state.error_status:
        user_online(entry['CodeID'])
        change_page(3)


def new_user():
    # Step 1: Render the sign-up UI container
    with st.container(border=True):

        # Step 2: Collect requested new username input
        new_username = st.text_input(sign_up_username_question, key="new_username")

        # Step 3: Display a suggested auto-generated username
        st.write(f"Try {str(generate_animal_username())}! We think it would sound fun.")

        # Step 4: Trigger account creation on button click
        st.button(
            f"Let's get started {new_username}",
            use_container_width=True,
            on_click=create_new_user,
            args=[new_username],
            key="create_user"
        )
