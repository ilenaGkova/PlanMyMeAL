import streamlit as st
from AdministrativeFunctions import open_new_code
from General_Functions import search_by_button, return_table, build_query, do_not_include
from Menu import menu
from MongoDB_General_Functions import role_table
from Record import find_all_records, collection_name, record_codeID_label, record_createdAt_label, record_itemID_label, \
    record_action_label, record_information
from User import validate_user, user_collection_name, user_codeID_label, user_information

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


def page_18_layout():
    # Step 2: Page entrypoint
    # Page 18: Request search / management page.
    # Validates request, renders menu, and loads search UI + results.

    # Step 2a: Validate the currently signed-in request
    # Uses the CodeID stored in session state
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2b: If valid, render menu and enforce permissions
    if status:
        menu(entry)

        # Step 2c: Permission gate (admin only)
        if entry[0]["Role"] == role_table["Administrator"]:
            st.title(f"Collection {user_collection_name} Management")

            # Step 2d: Fetch entries and render search workflow
            all_entries = find_all_records({})
            search(all_entries)

        else:
            # Step 2c: User valid, but not authorized
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


def search_form(entries):
    st.header("Search Form")

    # Step 3c: Build search UI layout
    with st.container(border=True):
        # Step 3d: Collect search filters from UI

        attribute = "CodeID"
        codeID = search_by_button(record_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(record_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "ItemID"
        itemID = search_by_button(record_itemID_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")
        attribute = "Action"
        action = search_by_button(record_action_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")

        # Step 3e: Construct request-shaped object for query consistency
        query_like = {
            'CodeID': codeID,
            'CreatedAt': createdAt,
            'UserID': userID,
            'ItemID': itemID,
            'Action': action,
            'Item': do_not_include
        }

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return find_all_records(query)
        else:
            return {}


def full_entry_record(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display record-related information
    #         - Item details (Record-specific fields)
    #         - Creator/user information
    #         - Item information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render record/item information in the first column
    with item_column:
        with st.container(border=True):
            record_information(outcome, pointer, status)

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")


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
            full_entry_record(outcome, pointer, True)

            st.button(
                f"Open {outcome[pointer]['ItemID']}",
                use_container_width=True,
                on_click=open_new_code,
                args=[outcome[pointer]['ItemID']],
                key=f"open_{user_collection_name}_{pointer}_Item"
            )

        # Step 4d: Move pointer forward (prevents infinite loop)
        pointer += 1
