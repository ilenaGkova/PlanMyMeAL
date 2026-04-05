import streamlit as st
from AdministrativeFunctions import change_page
from General_Functions import search_by_button, return_table, build_query, create_entry_user
from Menu import menu
from MongoDB_General_Functions import role_table
from Rule import collection_name, return_all_rules, rule_codeID_label, rule_createdAt_label, make_rule, \
    rule_frequency_label, full_entry_rule, update_rule, per_table, create_rule, delete_rule, validate_rule
from User import validate_user, user_collection_name, user_codeID_label

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


def page_13_layout():
    # Step 2: Page entrypoint
    # Page 13: Rule search / management page.
    # Validates user, renders menu, and loads search UI + results.

    # Step 2a: Validate the currently signed-in user
    # Uses the CodeID stored in session state
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2b: If valid, render menu and enforce permissions
    if status:
        menu(entry)

        # Step 2c: Permission gate (admin only)
        if entry[0]["Role"] == role_table["Administrator"]:
            st.title(f"Collection {collection_name} Management")

            # Step 2d: Fetch entries and render search workflow
            all_entries = return_all_rules({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete Rules
            alter_rule(selected_entry, all_entries)
            add_rule()
            remove_rule(selected_entry, all_entries)

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
        codeID = search_by_button(rule_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(rule_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        quantity_column, per_column = st.columns(2, vertical_alignment="center")

        with quantity_column:
            attribute = "Quantity"
            quantity = search_by_button(rule_frequency_label, return_table(attribute, entries, None, False),
                                        collection_name,
                                        attribute, "Search")

        with per_column:
            attribute = "Per"
            per = search_by_button("Per", return_table(attribute, entries, None, False),
                                   collection_name,
                                   attribute, "Search")

        # Step 3e: Construct rule-shaped object for query consistency
        query_like = make_rule(codeID, createdAt, userID, quantity, per)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_rules(query)
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
            full_entry_rule(outcome, pointer, True)

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


def alter_rule_officially(codeID: str, quantity: int, per: str, userID: str):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_rule(codeID, quantity, per, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_rule(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        quantity_set, per_set = 1, ""
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        quantity_set, per_set = entry['Quantity'], entry['Per']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(rule_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(rule_codeID_label, value=entry['CodeID'], key="alter_rule_codeID",
                                   disabled=True)

        # Step 5: Input for rule frequency (pre-filled if entry exists)
        quantity_column, per_column = st.columns(2, vertical_alignment="center")

        with quantity_column:
            quantity = st.number_input(rule_frequency_label, value=quantity_set, min_value=1, key="alter_rule_quantity")

        with per_column:
            per = st.selectbox(
                "Per",
                per_table,
                index=list(per_table).index(per_set) if per_set in per_table else 0,
                key="alter_rule_per"
            )

        # Step 6: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_rule_officially,
            args=[codeID, quantity, per, st.session_state.current_user],
            key=f"alter_rule"
        )


def add_rule_officially(quantity: int, per: str, userID: str):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_rule(quantity, per, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_rule():
    # Step 1: Page header for add flow
    st.header(f"Add {collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, collection_name, st.session_state.current_user)

        # Step 4: Input for rule frequency (pre-filled if entry exists)
        quantity_column, per_column = st.columns(2, vertical_alignment="center")

        with quantity_column:
            quantity = st.number_input(rule_frequency_label, min_value=1, key="add_rule_quantity")

        with per_column:
            per = st.selectbox(
                "Per",
                per_table,
                key="add_rule_per"
            )

        # Step 5: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_rule_officially,
            args=[quantity, per, userID],
            key=f"add_rule"
        )


def remove_rule_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_rule(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_rule(entry, entries):
    # Step 1: Set page header based on whether we’re deleting a known entry or selecting one
    if entry is None:
        st.header(f"Delete {collection_name} Item")
    else:
        st.header(f"Delete Item {entry['CodeID']}")

    # Step 2: Wrap the delete flow in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to delete
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(rule_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                rule_codeID_label,
                value=entry['CodeID'],
                key="delete_rule_codeID",
                disabled=True
            )

        # Step 5: Validate that this Rule exists / can be deleted, and fetch full entry data
        rule_message, rule_entry, rule_status = validate_rule(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if rule_status:
            full_entry_rule(rule_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_rule_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_rule"
            )


def manage_rules():

    # Step 5a: Retrieve all rules belonging to the current user
    entries = return_all_rules({"UserID": st.session_state.current_user})

    # Step 5b: Create two columns for separate rule search filters
    quantity_column, per_column = st.columns(2, vertical_alignment="center")

    # Step 5c: Display the search interface for rule quantity
    with quantity_column:
        quantity = search_by_button(rule_frequency_label, return_table("Quantity", entries, None, False),
                                    collection_name,
                                    "Quantity", "Search")

    # Step 5d: Display the search interface for rule period
    with per_column:
        per = search_by_button("Per", return_table("Per", entries, None, False),
                               collection_name,
                               "Per", "Search")

    # Step 5e: Provide the option to add a new rule
    add = st.checkbox("Add a Rule")

    # Step 5f: Start the rule creation workflow if the user selects the add option
    if add:
        add_rule()

    # Step 5g: Retrieve and display rules based on the selected search filters
    else:
        if per is None and quantity is not None:
            rule_entry = return_all_rules({"UserID": st.session_state.current_user, "Quantity": quantity})

        elif per is not None and quantity is None:
            rule_entry = return_all_rules({"UserID": st.session_state.current_user, "Per": per})

        elif per is None and quantity is None:
            rule_entry = return_all_rules({"UserID": st.session_state.current_user})

        elif per is not None and quantity is not None:
            rule_entry = return_all_rules({"UserID": st.session_state.current_user, "Quantity": quantity, "Per": per})

        # Step 5h: Display the filtered rule results
        display_results(rule_entry)

        # Step 5i: Continue with alter/remove logic only if at least one rule was found
        if len(rule_entry) >= 1:
            alter_rule(rule_entry[0], rule_entry)
            remove_rule(rule_entry[0], rule_entry)
