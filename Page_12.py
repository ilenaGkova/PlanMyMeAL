import streamlit as st
from AdministrativeFunctions import change_page
from General_Functions import search_by_button, return_table, build_query, create_entry_user
from MealType import collection_name, return_all_meal_types, meal_type_codeID_label, meal_type_createdAt_label, \
    meal_type_name_label, make_meal_type, full_entry_meal_type, update_meal_type, meal_type_priority_label, \
    create_meal_type, delete_meal_type, validate_meal_type
from Menu import menu
from MongoDB_General_Functions import role_table
from Rule import rule_codeID_label, select_ruleID
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


def page_12_layout():
    # Step 2: Page entrypoint
    # Page 12: Meal Type search / management page.
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
            all_entries = return_all_meal_types({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete Meal Types
            alter_meal_type(selected_entry, all_entries)
            add_meal_type()
            remove_meal_type(selected_entry, all_entries)

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
        codeID = search_by_button(meal_type_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(meal_type_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "RuleID"
        ruleID = search_by_button(rule_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "Name"
        name = search_by_button(meal_type_name_label, return_table(attribute, entries, None, False), collection_name,
                                attribute, "Search")

        attribute = "Priority"
        priority = search_by_button(meal_type_priority_label, return_table(attribute, entries, None, False),
                                    collection_name, attribute, "Search")

        # Step 3e: Construct MealType-shaped object for query consistency
        query_like = make_meal_type(codeID, createdAt, userID, name, ruleID, priority)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_meal_types(query)
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
            full_entry_meal_type(outcome, pointer, True)

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


def alter_meal_type_officially(codeID: str, name: str, userID: str, ruleID: str = None, priority: int = None):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_meal_type(codeID, name, userID, ruleID, priority)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_meal_type(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        name_set, priority_set = "", 1
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        name_set, priority_set = entry['Name'], entry['Priority']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(meal_type_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(meal_type_codeID_label, value=entry['CodeID'], key="alter_meal_type_codeID",
                                   disabled=True)

        # Step 5: Pick/alter the rule for this Meal Type (pre-filled if entry exists, depending on alter_ruleID)
        ruleID = select_ruleID(entry, 1)

        # Step 6: Input for Meal Type name (pre-filled if entry exists)
        name = st.text_input(meal_type_name_label, value=name_set, key="alter_meal_type_name")

        # Step 7: Input for Meal Type priority (pre-filled if entry exists)
        priority = st.number_input(meal_type_priority_label, value=priority_set, min_value=1,
                                   key="alter_meal_type_priority")

        # Step 8: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_meal_type_officially,
            args=[codeID, name, st.session_state.current_user, ruleID, priority],
            key=f"alter_meal_type"
        )


def add_meal_type_officially(name: str, userID: str, ruleID: str = None, priority: int = None):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_meal_type(name, userID, ruleID, priority)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_meal_type():
    # Step 1: Page header for add flow
    st.header(f"Add {collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, collection_name, st.session_state.current_user)

        # Step 4: Pick rule for this new meal_type
        ruleID = select_ruleID(None, 2)

        # Step 5: Input for new Meal Type name
        name = st.text_input(meal_type_name_label, key="add_meal_type_name")

        # Step 6: Input for Meal Type priority (pre-filled if entry exists)
        priority = st.number_input(meal_type_priority_label, min_value=1, key="add_meal_type_priority")

        # Step 7: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_meal_type_officially,
            args=[name, userID, ruleID, priority],
            key=f"add_meal_type"
        )


def remove_meal_type_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_meal_type(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_meal_type(entry, entries):
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
            codeID = search_by_button(meal_type_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                meal_type_codeID_label,
                value=entry['CodeID'],
                key="delete_meal_type_codeID",
                disabled=True
            )

        # Step 5: Validate that this Meal Type exists / can be deleted, and fetch full entry data
        meal_type_message, meal_type_entry, meal_type_status = validate_meal_type(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if meal_type_status:
            full_entry_meal_type(meal_type_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_meal_type_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_meal_type"
            )


def manage_meal_types():

    # Step 5a: Retrieve all meal types belonging to the current user
    entries = return_all_meal_types({"UserID": st.session_state.current_user})

    # Step 5b: Present the search/action interface for meal type management
    option = search_by_button(meal_type_name_label,
                              return_table("Name", entries,
                                           ["Add", "Show All"], False), collection_name, "Name",
                              "Search")

    # Step 5c: Display all meal types if the user selects "Show All"
    if option == "Show All":
        display_results(entries)

    # Step 5d: Start the meal type creation workflow if the user selects "Add"
    elif option == "Add":
        add_meal_type()

    # Step 5e: Retrieve the selected meal type and allow modification or removal
    else:
        meal_type_entry = return_all_meal_types({"UserID": st.session_state.current_user, "Name": option})

        # Step 5f: Ensure the selected meal type exists before altering or removing it
        if len(meal_type_entry) >= 1:
            alter_meal_type(meal_type_entry[0], meal_type_entry)
            remove_meal_type(meal_type_entry[0], meal_type_entry)
