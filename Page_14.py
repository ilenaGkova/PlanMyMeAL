import streamlit as st
from AdministrativeFunctions import change_page
from Day import day_codeID_label, select_dayID
from General_Functions import search_by_button, return_table, build_query, create_entry_user
from Meal import meal_codeID_label, select_mealID
from MealType import meal_type_codeID_label, select_meal_type_id
from Menu import menu
from MongoDB_General_Functions import role_table
from Schedule import collection_name, schedule_codeID_label, schedule_createdAt_label, make_schedule, \
    return_all_schedules, schedule_outcome_label, schedule_notes_label, full_entry_schedule, update_schedule, \
    outcome_table, create_schedule, delete_schedule, validate_schedule
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


def page_14_layout():
    # Step 2: Page entrypoint
    # Page 14: Schedule search / management page.
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
            all_entries = return_all_schedules({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete Schedules
            alter_schedule(selected_entry, all_entries)
            add_schedule()
            remove_schedule(selected_entry, all_entries)

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
        codeID = search_by_button(schedule_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name, attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(schedule_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "MealTypeID"
        mealtypeID = search_by_button(meal_type_codeID_label, return_table(attribute, entries, None, False),
                                      collection_name,
                                      attribute, "Search")

        attribute = "MealID"
        mealID = search_by_button(meal_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")

        attribute = "DayID"
        dayID = search_by_button(day_codeID_label, return_table(attribute, entries, None, False),
                                 collection_name,
                                 attribute, "Search")

        attribute = "Outcome"
        outcome = search_by_button(schedule_outcome_label, return_table(attribute, entries, None, False),
                                   collection_name,
                                   attribute, "Search")

        attribute = "Notes"
        notes = search_by_button(schedule_notes_label, return_table(attribute, entries, None, False),
                                 collection_name,
                                 attribute, "Search")

        # Step 3e: Construct schedule-shaped object for query consistency
        query_like = make_schedule(codeID, createdAt, userID, mealtypeID, mealID, dayID, outcome, notes)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_schedules(query)
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
            full_entry_schedule(outcome, pointer, True)

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


def alter_schedule_officially(codeID: str, userID: str, mealTypeID: str, mealID: str, dayID: str, outcome: str,
                              notes: str = None):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_schedule(codeID, userID, mealTypeID, mealID,
                                                                               dayID, outcome, notes)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_schedule(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        outcome_set, notes_set = "", ""
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        outcome_set, notes_set = entry['Outcome'], entry['Notes']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(schedule_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(schedule_codeID_label, value=entry['CodeID'], key="alter_schedule_codeID",
                                   disabled=True)

        # Step 5: Input for schedule meal type (pre-filled if entry exists)
        mealtypeID = select_meal_type_id(entry, 1)

        # Step 6: Input for schedule meal (pre-filled if entry exists)
        mealID = select_mealID(entry, 1)

        # Step 7: Input for schedule day (pre-filled if entry exists)
        dayID = select_dayID(entry, 1)

        # Step 8: Input for schedule outcome (pre-filled if entry exists)
        outcome = st.selectbox(
            schedule_outcome_label,
            outcome_table,
            index=list(outcome_table).index(outcome_set) if outcome_set in outcome_table else 0,
            key="alter_schedule_outcome"
        )

        # Step 9: Input for schedule notes (pre-filled if entry exists)
        notes = st.text_input(schedule_notes_label, value=notes_set, key="alter_schedule_notes")

        # Step 10: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_schedule_officially,
            args=[codeID, st.session_state.current_user, mealtypeID, mealID, dayID, outcome, notes],
            key=f"alter_schedule"
        )


def add_schedule_officially(userID: str, mealTypeID: str, mealID: str, dayID: str, outcome: str = "Upcoming",
                            notes: str = None):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_schedule(userID, mealTypeID, mealID, dayID,
                                                                               outcome, notes)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_schedule():
    # Step 1: Page header for add flow
    st.header(f"Add {collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, collection_name, st.session_state.current_user)

        # Step 4: Input for schedule meal type (pre-filled if entry exists)
        mealtypeID = select_meal_type_id(None, 2)

        # Step 5: Input for schedule meal (pre-filled if entry exists)
        mealID = select_mealID(None, 2)

        # Step 6: Input for schedule day (pre-filled if entry exists)
        dayID = select_dayID(None, 2)

        # Step 7: Input for schedule outcome (pre-filled if entry exists)
        outcome = search_by_button(schedule_outcome_label, outcome_table, collection_name, "Outcome", "Add")

        # Step 8: Input for schedule notes (pre-filled if entry exists)
        notes = st.text_input(schedule_notes_label, key="add_schedule_notes")

        # Step 9: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_schedule_officially,
            args=[userID, mealtypeID, mealID, dayID, outcome, notes],
            key=f"add_schedule"
        )


def remove_schedule_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_schedule(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_schedule(entry, entries):
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
            codeID = search_by_button(schedule_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                schedule_codeID_label,
                value=entry['CodeID'],
                key="delete_schedule_codeID",
                disabled=True
            )

        # Step 5: Validate that this Rule exists / can be deleted, and fetch full entry data
        schedule_message, schedule_entry, schedule_status = validate_schedule(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if schedule_status:
            full_entry_schedule(schedule_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_schedule_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_schedule"
            )
