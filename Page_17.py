from datetime import date
import streamlit as st
from AdministrativeFunctions import change_page
from General_Functions import search_by_button, build_query, return_table
from Menu import menu
from MongoDB_General_Functions import role_table
from Page_20 import full_entry_request
from Request import return_all_requests, make_request, request_codeID_label, collection_name, request_createdAt_label, \
    request_status_label, update_request, status_table, request_description_label
from User import validate_user, user_collection_name

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


def page_17_layout():
    # Step 2: Page entrypoint
    # Page 17: Request search / management page.
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
            all_entries = return_all_requests({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete Request
            alter_request(selected_entry, all_entries)

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
        codeID = search_by_button(request_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(request_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        when_column, for_column = st.columns(2, vertical_alignment="center")

        with when_column:
            attribute = "When"
            when = search_by_button("Request Made", return_table(attribute, entries, None, False),
                                    collection_name,
                                    attribute, "Search")

        with for_column:
            attribute = "For"
            itemid = search_by_button(attribute, return_table(attribute, entries, None, False),
                                      collection_name,
                                      attribute, "Search")

        attribute = "Description"
        description = search_by_button(request_description_label, return_table(attribute, entries, None, False),
                                       collection_name,
                                       attribute, "Search")
        attribute = "Status"
        status = search_by_button(request_status_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")

        # Step 3e: Construct request-shaped object for query consistency
        query_like = make_request(codeID, createdAt, description, when, itemid, status)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_requests(query)
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
            full_entry_request(outcome, pointer, True)

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


def alter_request_officially(codeID: str, status: str, userID: str):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_request(codeID, status, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_request(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        when_set = date.today()
        item_set, description_set, status_set = "", "", ""
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        when_set = str(entry['When'])
        item_set, description_set, status_set = entry['For'], entry['Description'], entry['Status']
        st.write(when_set, item_set, description_set, status_set)

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(request_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(request_codeID_label, value=entry['CodeID'], key="alter_request_codeID",
                                   disabled=True)

        # Step 5: Input for request frequency (pre-filled if entry exists)
        when_column, for_column = st.columns(2, vertical_alignment="center")

        with when_column:
            st.text_input("Request Made", value=when_set, key="alter_request_date", disabled=True)

        with for_column:
            st.text_input("For", value=item_set, key="alter_request_itemID",
                                 disabled=True)

        st.text_input(request_description_label, value=description_set, key="alter_request_description")

        status = st.selectbox(
            request_status_label,
            status_table,
            index=list(status_table).index(status_set) if status_set in status_table else 0,
            key="alter_request_status",
            disabled=("Closed" == status_set)
        )

        # Step 6: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_request_officially,
            args=[codeID, status, st.session_state.current_user],
            key=f"alter_request"
        )
