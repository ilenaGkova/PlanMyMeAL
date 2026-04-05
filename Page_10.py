import streamlit as st
from AdministrativeFunctions import change_page
from General_Functions import search_by_button, return_table, build_query, create_entry_user
from Ingredient import collection_name, return_all_ingredients, ingredient_codeID_label, ingredient_createdAt_label, \
    make_ingredient, ingredient_name_label, full_entry_ingredient, update_ingredient, create_ingredient, \
    validate_ingredient, delete_ingredient
from Menu import menu
from MongoDB_General_Functions import role_table
from Rule import rule_codeID_label, select_ruleID
from UnitType import select_unitTypeID
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


def page_10_layout():
    # Step 2: Page entrypoint
    # Page 10: Ingredient search / management page.
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
            all_entries = return_all_ingredients({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete ingredients
            alter_ingredient(selected_entry, all_entries)
            add_ingredient()
            remove_ingredient(selected_entry, all_entries)

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
        codeID = search_by_button(ingredient_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(ingredient_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "UnitTypeID"
        unitTypeID = search_by_button(ingredient_codeID_label, return_table(attribute, entries, None, False),
                                      collection_name,
                                      attribute, "Search")

        attribute = "RuleID"
        ruleID = search_by_button(rule_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "Name"
        name = search_by_button(ingredient_name_label, return_table(attribute, entries, None, False), collection_name,
                                attribute, "Search")

        # Step 3e: Construct day-shaped object for query consistency
        query_like = make_ingredient(codeID, createdAt, userID, unitTypeID, name, ruleID)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_ingredients(query)
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
            full_entry_ingredient(outcome, pointer, True)

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


def alter_ingredient_officially(codeID: str, userID: str, name: str, unitTypeID: str, ruleID: str = None):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_ingredient(codeID, userID, name, unitTypeID,
                                                                                 ruleID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_ingredient(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        name_set = ""
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        name_set = entry['Name']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(ingredient_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(ingredient_codeID_label, value=entry['CodeID'], key="alter_ingredient_codeID",
                                   disabled=True)

        # Step 6: Alter the Unit Type for this ingredient (pre-filled if entry exists, depending on alter_ruleID)
        unitTypeID = select_unitTypeID(entry, 1)

        # Step 6: Pick/alter the rule for this ingredient (pre-filled if entry exists, depending on alter_ruleID)
        ruleID = select_ruleID(entry, 1)

        # Step 7: Input for ingredient name (pre-filled if entry exists)
        name = st.text_input(ingredient_name_label, value=name_set, key="alter_ingredient_name")

        # Step 8: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_ingredient_officially,
            args=[codeID, st.session_state.current_user, name, unitTypeID, ruleID],
            key=f"alter_ingredient"
        )


def add_ingredient_officially(name: str, userID: str, unitTypeID: str, ruleID: str = None):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_ingredient(name, userID, unitTypeID, ruleID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_ingredient():
    # Step 1: Page header for add flow
    st.header(f"Add {collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, collection_name, st.session_state.current_user)

        # Step 4: Pick Unit Type for this new ingredient
        unitTypeID = select_unitTypeID(None, 2)

        # Step 5: Pick rule for this new ingredient
        ruleID = select_ruleID(None, 2)

        # Step 6: Input for new ingredient name
        name = st.text_input(ingredient_name_label, key="add_ingredient_name")

        # Step 7: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_ingredient_officially,
            args=[name, userID, unitTypeID, ruleID],
            key=f"add_ingredient"
        )


def remove_ingredient_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_ingredient(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_ingredient(entry, entries):
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
            codeID = search_by_button(ingredient_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                ingredient_codeID_label,
                value=entry['CodeID'],
                key="delete_ingredient_codeID",
                disabled=True
            )

        # Step 5: Validate that this ingredient exists / can be deleted, and fetch full entry data
        ingredient_message, ingredient_entry, ingredient_status = validate_ingredient(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if ingredient_status:
            full_entry_ingredient(ingredient_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_ingredient_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_ingredient"
            )


def manage_ingredients():

    # Step 5a: Retrieve all ingredients belonging to the current user
    entries = return_all_ingredients({"UserID": st.session_state.current_user})

    # Step 5b: Present the search/action interface for ingredient management
    option = search_by_button(ingredient_name_label,
                              return_table("Name", entries,
                                           ["Add", "Show All"], False), collection_name, "Name",
                              "Search")

    # Step 5c: Display all ingredients if the user selects "Show All"
    if option == "Show All":
        display_results(entries)

    # Step 5d: Start the ingredient creation workflow if the user selects "Add"
    elif option == "Add":
        add_ingredient()

    # Step 5e: Retrieve the selected ingredient and allow modification or removal
    else:
        ingredient_entry = return_all_ingredients({"UserID": st.session_state.current_user, "Name": option})

        # Step 5f: Ensure the selected ingredient exists before altering or removing it
        if len(ingredient_entry) >= 1:
            alter_ingredient(ingredient_entry[0], ingredient_entry)
            remove_ingredient(ingredient_entry[0], ingredient_entry)