import streamlit as st
from AdministrativeFunctions import change_page
from Category import category_codeID_label, select_categoryID
from General_Functions import search_by_button, return_table, build_query, create_entry_user
from Ingredient import validate_ingredient_deep, get_ingredients_not_in_meal
from Meal import collection_name, return_all_meals, meal_codeID_label, meal_createdAt_label, meal_name_label, make_meal, \
    full_entry_meal, update_meal, meal_notes_label, validate_meal, create_meal, delete_meal
from MealCombination import update_meal_combination, delete_meal_combination, create_meal_combination, \
    return_all_meal_combinations, meal_combination_quantity_label, validate_combination
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


def page_11_layout():
    # Step 2: Page entrypoint
    # Page 11: Meal search / management page.
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
            all_entries = return_all_meals({})
            selected_entry = search(all_entries)

            # Step 2e: Alter, Add and Delete meals
            alter_meal(selected_entry, all_entries)
            add_meal()
            remove_meal(selected_entry, all_entries)

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
        codeID = search_by_button(meal_codeID_label, return_table(attribute, entries, None, False),
                                  collection_name,
                                  attribute, "Search")

        attribute = "CreatedAt"
        createdAt = search_by_button(meal_createdAt_label, return_table(attribute, entries, None, True),
                                     collection_name, attribute, "Search")

        attribute = "UserID"
        userID = search_by_button(user_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "CategoryID"
        categoryID = search_by_button(category_codeID_label, return_table(attribute, entries, None, False),
                                      collection_name,
                                      attribute, "Search")

        attribute = "RuleID"
        ruleID = search_by_button(rule_codeID_label, return_table(attribute, entries, None, False), collection_name,
                                  attribute, "Search")

        attribute = "Name"
        name = search_by_button(meal_name_label, return_table(attribute, entries, None, False), collection_name,
                                attribute, "Search")

        attribute = "Notes"
        notes = search_by_button(meal_notes_label, return_table(attribute, entries, None, False), collection_name,
                                 attribute, "Search")

        # Step 3e: Construct day-shaped object for query consistency
        query_like = make_meal(codeID, createdAt, userID, categoryID, name, notes, ruleID)

        # Step 3f: Show results
        show_result = st.checkbox("Show Results")

        # Step 3g: Build query and fetch matching results
        if show_result:
            query = build_query(query_like)
            return return_all_meals(query)
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
            full_entry_meal(outcome, pointer, True)

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


def alter_meal_officially(codeID: str, userID: str, name: str, categoryID: str, notes: str, ruleID: str = None):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_meal(codeID, userID, name, categoryID,
                                                                           notes, ruleID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_meal_combination_officially(codeID: str, userID: str, ingredientID: str, mealID: str, quantity: float):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = update_meal_combination(codeID, userID, ingredientID,
                                                                                       mealID,
                                                                                       quantity)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_meal_combination_officially(codeID: str, userID: str):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_meal_combination(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_meal_combination_officially(userID: str, ingredientID: str, mealID: str, quantity: float):
    # Step 1: Persist the update to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_meal_combination(userID, ingredientID,
                                                                                       mealID,
                                                                                       quantity)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def alter_meal(entry, entries):
    # Step 1: Set page header based on whether we’re editing a known entry or selecting one
    if entry is None:
        st.header(f"Alter {collection_name} Item")
        name_set, notes_set = "", ""
    else:
        st.header(f"Alter Item {entry['CodeID']}")
        name_set, notes_set = entry['Name'], entry['Notes']

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):

        # Step 3: If no entry was provided, ask the user which CodeID they want to alter
        if entry is None:
            attribute = "CodeID"
            codeID = search_by_button(meal_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Alter")
        # Step 4: Otherwise, CodeID is already known from entry
        else:

            codeID = st.text_input(meal_codeID_label, value=entry['CodeID'], key="alter_meal_codeID",
                                   disabled=True)

        # Step 5: Alter the Category for this meal (pre-filled if entry exists, depending on alter_ruleID)
        categoryID = select_categoryID(entry, 1)

        # Step 6: Pick/alter the rule for this meal (pre-filled if entry exists, depending on alter_ruleID)
        ruleID = select_ruleID(entry, 1)

        # Step 7: Input for meal name (pre-filled if entry exists)
        name = st.text_input(meal_name_label, value=name_set, key="alter_meal_name")

        # Step 8: Input for meal name (pre-filled if entry exists)
        notes = st.text_input(meal_notes_label, value=notes_set, key="alter_meal_notes")

        # Step 9: Validate meal exists
        meal_message, meal_entry, meal_status = validate_meal(codeID)

        if meal_status:

            # Step 10: Show and alter ingredients
            st.subheader(f"Ingredients for {name_set}")

            # Step 11: Gather existing ingredients
            existing_ingredients = return_all_meal_combinations({'MealID': codeID})

            for combination in existing_ingredients:

                # Step 12: Validate ingredient existence through combination
                status, message, unit_type, ingredient = validate_combination(combination)

                if status:

                    # Step 13: Show existing ingredient to be altered or deleted
                    show_ingredient(combination, ingredient, unit_type, codeID, "Exists")

                else:

                    st.write(message)

            # Step 14: Gather new ingredients
            other_ingredients = get_ingredients_not_in_meal(existing_ingredients)

            for other_ingredient in other_ingredients:

                # Step 15: Validate ingredient existence
                status, message, unit_type, ingredient = validate_ingredient_deep(other_ingredient)

                if status:

                    # Step 16: Show ingredient to be added
                    show_ingredient(None, ingredient, unit_type, codeID, "New")

                else:

                    st.write(message)

        # Step 18: Submit button - triggers DB update via callback, passing the collected inputs
        st.button(
            f"Update Entry {codeID}",
            use_container_width=True,
            on_click=alter_meal_officially,
            args=[codeID, st.session_state.current_user, name, categoryID, notes, ruleID],
            key=f"alter_meal"
        )


def show_ingredient(entry, ingredient, unit_type: str, meal: str, action: str):
    if action == "Exists":
        codeID = entry['CodeID']
        text_input_column, text_column, update_column, delete_column = st.columns(4,
                                                                                  vertical_alignment="center")
        quantity_set = float(entry['Quantity'])
    else:
        codeID = ingredient['CodeID']
        text_input_column, text_column, add_column = st.columns(3, vertical_alignment="center")
        quantity_set = 0.00

    with text_input_column:
        quantity = st.number_input(
            meal_combination_quantity_label,
            label_visibility="collapsed",
            value=quantity_set,
            min_value=0.00,
            step=0.05,
            key=f"{meal}_{action}_{codeID}_quantity",
        )

    with text_column:
        st.write(f"{unit_type}(s) of {ingredient['Name']}")

    if action == "Exists":
        with update_column:
            st.button(
                f"Update {codeID}",
                use_container_width=True,
                on_click=alter_meal_combination_officially,
                args=[codeID, st.session_state.current_user, entry['IngredientID'],
                      entry['MealID'], quantity],
                key=f"update_{meal}_{action}_{codeID}"
            )
        with delete_column:
            st.button(
                f"Delete {codeID}",
                use_container_width=True,
                on_click=remove_meal_combination_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_{meal}_{action}_{codeID}"
            )

    else:

        with add_column:
            st.button(
                f"Add {codeID}",
                use_container_width=True,
                on_click=add_meal_combination_officially,
                args=[st.session_state.current_user, ingredient['CodeID'], meal, quantity],
                key=f"add_{meal}_{action}_{codeID}"
            )


def add_meal_officially(name: str, userID: str, categoryID: str, notes: str, ruleID: str = None):
    # Step 1: Persist the create operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = create_meal(name, userID, categoryID, notes, ruleID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def add_meal():
    # Step 1: Page header for add flow
    st.header(f"Add {collection_name} Item")

    # Step 2: Wrap the form in a bordered container for UI grouping
    with st.container(border=True):
        # Step 3: Show userID (current user) but disable editing
        userID = create_entry_user(user_codeID_label, collection_name, st.session_state.current_user)

        # Step 4: Alter the Category for this meal (pre-filled if entry exists, depending on alter_ruleID)
        categoryID = select_categoryID(None, 2)

        # Step 5: Pick rule for this new ingredient
        ruleID = select_ruleID(None, 2)

        # Step 6: Input for meal name (pre-filled if entry exists)
        name = st.text_input(meal_name_label, key="add_meal_name")

        # Step 7: Input for meal name (pre-filled if entry exists)
        notes = st.text_input(meal_notes_label, key="add_meal_notes")

        # Step 8: Submit button - should create a new entry
        st.button(
            f"Add Entry",
            use_container_width=True,
            on_click=add_meal_officially,
            args=[name, userID, categoryID, notes, ruleID],
            key=f"add_meal"
        )


def remove_meal_officially(codeID: str, userID: str):
    # Step 1: Persist the delete operation to the database (and capture status into session_state)
    st.session_state.error, _, st.session_state.error_status = delete_meal(codeID, userID)

    # Step 2: Renew Page to clean out error status if positive
    if st.session_state.error_status:
        change_page(st.session_state.page)


def remove_meal(entry, entries):
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
            codeID = search_by_button(meal_codeID_label, return_table(attribute, entries, [], False),
                                      collection_name, attribute, "Delete")

        # Step 4: Otherwise show CodeID as read-only (already known)
        else:
            codeID = st.text_input(
                meal_codeID_label,
                value=entry['CodeID'],
                key="delete_ingredient_codeID",
                disabled=True
            )

        # Step 5: Validate that this ingredient exists / can be deleted, and fetch full entry data
        ingredient_message, ingredient_entry, ingredient_status = validate_meal(codeID)

        # Step 6: If valid, show full entry preview and present delete button
        if ingredient_status:
            full_entry_meal(ingredient_entry, 0, False)

            # Step 7: Confirm delete action with a button; calls delete callback with CodeID and current user
            st.button(
                f"Delete Entry {codeID}",
                use_container_width=True,
                on_click=remove_meal_officially,
                args=[codeID, st.session_state.current_user],
                key=f"delete_meal"
            )


def manage_meals():
    # Step 5a: Retrieve all meals belonging to the current user
    entries = return_all_meals({"UserID": st.session_state.current_user})

    # Step 5b: Present the search/action interface for meal management
    option = search_by_button(meal_name_label,
                              return_table("Name", entries,
                                           ["Add", "Show All"], False), collection_name, "Name",
                              "Search")

    # Step 5c: Display all meals if the user selects "Show All"
    if option == "Show All":
        display_results(entries)

    # Step 5d: Start the meal creation workflow if the user selects "Add"
    elif option == "Add":
        add_meal()

    # Step 5e: Retrieve the selected meal and allow modification or removal
    else:
        meal_entry = return_all_meals({"UserID": st.session_state.current_user, "Name": option})

        # Step 5f: Ensure the selected meal exists before altering or removing it
        if len(meal_entry) >= 1:
            alter_meal(meal_entry[0], meal_entry)
            remove_meal(meal_entry[0], meal_entry)
