import streamlit as st
from AdministrativeFunctions import change_page
from General_Functions import build_query, search_by_button, return_table, create_entry_user
from Menu import menu
from MongoDB_General_Functions import role_table
from User import validate_user, return_all_users, make_user, user_codeID_label, \
    user_createdAt_label, user_username_label, user_status_label, user_role_label, full_entry_user, update_user, \
    user_collection_name, create_user, delete_user, new_username_question, user_information

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


def page_16_layout():
    # Step 2: Page entrypoint
    # Page 16: User search / management page.
    # Validates user, renders menu, and loads search UI + results.

    # Step 2a: Validate the currently signed-in user
    # Uses the CodeID stored in session state
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2b: If valid, render menu and enforce permissions
    if status:
        menu(entry)

        # Step 2c: Permission gate (admin only)
        if entry[0]["Role"] == role_table["Administrator"]:
            st.title(f"Collection {user_collection_name} Management")

            # Step 2d: Fetch entries and render search workflow
            all_entries = return_all_users({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete Users
            alter_user(selected_entry, all_entries)
            add_user()
            remove_user(selected_entry, all_entries)

        else:
            # Step 2i: User valid, but not authorized
            st.session_state.error = f"[{user_collection_name}] Invalid Input: User does not have Administrator Privileges"
            st.session_state.error_status = False

    else:
        # Step 2f: Validation failed; store error for global handler
        st.session_state.error = message
        st.session_state.error_status = status


def search(entries):
    # Step 3: Search workflow (form + output)
    # Step 3a: Run search form and retrieve matching results
    outcome = search_form(entries)

    # Step 3b: Display search results
    display_results(outcome)

    # Step 3c: Return head result
    if len(outcome) >= 1:
        return outcome[0]
    else:
        return None


def search_form(entries):
    st.header("Search Form")

    # Step 3c: Build search UI layout
    with st.container(border=True):
        # Step 3d: Collect search filters from UI

        attribute = "CodeID"
        codeID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False),
                                  user_collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(user_createdAt_label, return_table(attribute, entries, None, True),
                                     user_collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False),
                                  user_collection_name,
                                  attribute, "Search")

        attribute = "Username"
        username = search_by_button(user_username_label, return_table(attribute, entries, None, False),
                                    user_collection_name,
                                    attribute, "Search")

        attribute = "Status"
        status = search_by_button(user_status_label, return_table(attribute, entries, None, False),
                                  user_collection_name,
                                  attribute, "Search")

        attribute = "Role"
        role = search_by_button(user_role_label, return_table(attribute, entries, None, False), user_collection_name,
                                attribute, "Search")

        # Step 3e: Construct user-shaped object for query consistency
        query_like = make_user(codeID, createdAt, userID, username, status, role)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_users(query)
        else:
            return {}


def display_results(outcome):
    # Step 4: Results rendering
    st.header("Results")

    # Step 4a: Handle empty results
    if len(outcome) == 0:
        st.write("No results Found")
        return

    # Step 4b: Display count
    st.write(f"You have {len(outcome)} result(s)")

    # Step 4c: Render each result card
    pointer = 0
    while pointer < len(outcome):

        with st.container(border=True):
            full_entry_user(outcome, pointer, True)

            # Step 4d: If first on list, marked as selected
            if pointer == 0:
                st.markdown(
                    """
                        <h1 style="text-align: center; font-size: 40px; font-weight: bold;"> Selected Entry </h1>
                    """,
                    unsafe_allow_html=True,
                )

        # Step 4e: Move pointer forward (prevents infinite loop)
        pointer += 1


def alter_user_officially(codeID: str, username: str, userID: str, status: bool = True,
                          role: str = role_table["Plain User"]):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_user(codeID, username, userID, status, role)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_user(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {user_collection_name} Item")
        username_set, status_set = "", False
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        username_set, status_set = entry['Username'], entry['Status']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(user_codeID_label, return_table(attribute, entries, [], False),
                                      user_collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(user_codeID_label, value=entry['CodeID'], key="alter_user_codeID",
                                   disabled=True)

        # Step 5: Input for user username (pre-filled if entry exists)
        username = st.text_input(user_username_label, value=username_set, key="alter_user_username")

        # Step 6: Input for user status (pre-filled if entry exists)
        status = st.checkbox("Status", value=status_set, key="alter_user_status")

        # Step 7: Submit button - triggers DB update via callback, passing the collected inputs
        if entry is not None:
            st.button(
                f"Update Entry {codeID}",
                use_container_width=True,
                on_click=alter_user_officially,
                args=[codeID, username, st.session_state.current_user, status, entry['Role']],
                key=f"alter_user"
            )

            if entry['Role'] == role_table["Plain User"] and status:
                st.button(
                    f"Make {codeID} {role_table["Administrator"]}",
                    use_container_width=True,
                    on_click=alter_user_officially,
                    args=[entry['CodeID'], entry[0]['Username'], st.session_state.current_user, status,
                          role_table["Administrator"]],
                    key=f"make_admin"
                )


def add_user_officially(username: str, userID: str = None, role: str = role_table["Plain User"]):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_user(username, userID, role)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_user():
    # Step 1: Page header for add flow
    st.header(f"Add {user_collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, user_collection_name, st.session_state.current_user)

        # Step 5: Input for user username (pre-filled if entry exists)
        username = st.text_input(user_username_label, key="add_user_username")

        # Step 5: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_user_officially,
            args=[username, userID, role_table["Plain User"]],
            key=f"add_user"
        )


def remove_user_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_user(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_user(entry, entries):
    # Step 1: Set page header based on whether we’re deleting a known entry or selecting one
    if entry is None:
        st.header(f"Delete {user_collection_name} Item")
    else:
        st.header(f"Delete Item {entry['CodeID']}")

    # Step 2: Wrap the delete flow in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to delete
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(user_codeID_label, return_table(attribute, entries, [], False),
                                      user_collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                user_codeID_label,
                value=entry['CodeID'],
                key="delete_user_codeID",
                disabled=True
            )

        # Step 5: Validate that this Rule exists / can be deleted, and fetch full entry data
        user_message, user_entry, user_status = validate_user(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if user_status:
            full_entry_user(user_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_user_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_user"
            )


def show_user_information(entry):

    # Step 3a: Create two columns for username management and user information display
    column_username, column_information = st.columns(2, vertical_alignment="center")

    # Step 3b: Display the username change interface
    with column_username:
        with st.container(border=True):

            # Step 3c: Allow the administrator to edit the username
            username = st.text_input(new_username_question, value=entry[0]['Username'])

            # Step 3d: Provide a button to officially update the username
            st.button(
                f"Change Username to {username}",
                use_container_width=True,
                on_click=alter_user_officially,
                args=[entry[0]['CodeID'], username, entry[0]['UserID'], entry[0]['Status'], entry[0]['Role']],
                key=f"change_username"
            )

    # Step 3e: Display the user information panel
    with column_information:
        with st.container(border=True):

            # Step 3f: Show detailed information about the primary user entry
            user_information(entry, 0, False, "Primary")