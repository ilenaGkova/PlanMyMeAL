import streamlit as st
from Day import return_all_days
from Ingredient import validate_ingredient
from Meal import validate_meal
from MealCombination import return_all_meal_combinations
from Menu import menu
from Page_6 import get_table
from Schedule import return_all_schedules
from UnitType import validate_unit_type
from User import validate_user

# Step 1: Initialize session state variables (first run only)

if 'page' not in st.session_state:
    st.session_state.page = 1  # Default page to load

if 'error_status' not in st.session_state:
    st.session_state.error_status = None  # Tracks whether an error message should be shown

if 'current_user' not in st.session_state:
    st.session_state.current_user = None  # Stores the CodeID of the signed-in user

if 'error' not in st.session_state:
    st.session_state.error = 'You are doing great! Keep going.'  # Stores the current error message


def page_4_layout():
    # Step 1: Validate current user
    # Ensures the user exists and is allowed to access this page
    message, entry, status = validate_user(st.session_state.current_user)

    if status:
        # Step 2: Render page UI and process grocery data

        # Step 2a: Render main navigation/menu
        menu(entry)

        # Step 2b: Page title
        st.title("My grocery List")

        # Step 3: Date selection input
        st.header("Date Selection")
        date_table = get_table()

        if len(date_table) >= 1:

            # Step 4: Build meal + ingredient data and display meal breakdown

            # Step 4a: Convert selected dates → aggregated meals
            meal_table = make_meal_table(date_table)

            if len(meal_table) >= 1:

                with st.container(border=True):

                    st.header("This grocery list corresponds to:")

                    # Step 4b: Convert meals → ingredients (also displays meal summary)
                    ingredient_table = make_ingredient_table(meal_table)

                    # Step 5: Render final grocery list
                    with st.container(border=True):
                        st.header("Grocery List")
                        for entry in ingredient_table:
                            st.write(f"🛒 {entry['Quantity']} {entry['Unit']}(s) of {entry['Name']}")

            else:

                st.write('You have no meals planed for this duration of time')

    else:
        # Step 5: Handle validation failure
        # Store error for global error display system
        st.session_state.error, st.session_state.error_status = message, status


def make_meal_table(date_table):
    # Step 1: Transform selected dates → meal table

    meal_table = []

    for entry in date_table:
        # Step 2: Resolve date into system Day record
        date_data = return_all_days({'Date': entry})

        # Step 3: If valid day found, fetch scheduled meals
        if len(date_data) == 1:
            data = return_all_schedules({'DayID': date_data[0]['CodeID'], 'UserID': st.session_state.current_user})

            # Step 4: Aggregate meals into meal_table
            for meal in data:
                meal_table = add_to_table(meal_table, meal['MealID'], 1, 'Meal')

    # Step 1d: Return aggregated meals
    return meal_table


def make_ingredient_table(meal_table):
    # Step 1: Transform meal table → ingredient table

    ingredient_table = []

    for entry in meal_table:
        # Step 2: Fetch ingredient list for each meal
        data = return_all_meal_combinations({'MealID': entry['CodeID']})

        # Step 3: Display meal breakdown (for user context)
        st.write(f"-> {entry['Quantity']} Portion(s) of {entry['Name']} - {len(data)} Ingredients Each")

        # Step 4: Aggregate ingredients (scaled by meal quantity)
        for ingredient in data:
            ingredient_table = add_to_table(
                ingredient_table,
                ingredient['IngredientID'],
                ingredient['Quantity'] * entry['Quantity'],
                'Ingredient'
            )

    # Step 5: Return aggregated ingredients
    return ingredient_table


# Mapping item types to their validation functions
validate_item = {
    'Meal': validate_meal,
    'Ingredient': validate_ingredient
}


def add_to_table(table, entry: str, quantity: float, item: str):
    # Step 1: Check if entry already exists in table
    for row in table:
        if row['CodeID'] == entry:
            row['Quantity'] += quantity
            return table

    # Step 2: Create new entry if not found
    new_row = {'CodeID': entry, 'Quantity': quantity, 'Name': None, 'Unit': None}

    # Step 3: Retrieve name using validation function
    message, data, status = validate_item[item](entry)
    if not status:
        new_row['Name'] = message
    else:
        new_row['Name'] = data[0]['Name']

    # Step 4: Retrieve unit only for ingredients
    if item == 'Ingredient':
        message, unitType, status = validate_unit_type(data[0]['UnitTypeID'])
        if not status:
            new_row['Unit'] = message
        else:
            new_row['Unit'] = unitType[0]['Name']

    # Step 5: Add new entry to table
    table.append(new_row)
    return table
