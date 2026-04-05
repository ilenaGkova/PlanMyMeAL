import streamlit as st

from AdministrativeFunctions import change_page
from Category import return_all_categories, create_category, validate_category
from Ingredient import create_ingredient, validate_ingredient, return_all_ingredients
from Meal import return_all_meals, validate_meal, create_meal
from MealCombination import return_all_meal_combinations, create_meal_combination, validate_meal_combination
from MealType import return_all_meal_types, create_meal_type, validate_meal_type
from Page_5 import today_schedule, update_statuses
from Rule import return_all_rules, create_rule, validate_rule
from UnitType import create_unit_type, validate_unit_type, return_all_unit_types
from User import validate_user
from Menu import menu

# Step 1: Initialize session state variables (first run only)

if 'page' not in st.session_state:
    st.session_state.page = 1  # Default page to load

if 'error_status' not in st.session_state:
    st.session_state.error_status = None  # Tracks whether an error message should be shown

if 'current_user' not in st.session_state:
    st.session_state.current_user = None  # Stores the CodeID of the signed-in user

if 'error' not in st.session_state:
    st.session_state.error = 'You are doing great! Keep going.'  # Stores the current error message


def page_3_layout():
    # Step 1: Validate current user
    # Ensures the user exists and is allowed to access this page
    message, entry, status = validate_user(st.session_state.current_user)

    if status:
        # Step 2: Render page UI and process grocery data

        # Step 2a: Render main navigation/menu
        menu(entry)

        # Step 2b: Page title
        st.title(f"Hello {entry[0]['Username']}")

        # Step 3: Update Statuses if needed
        counter = update_statuses()

        # Step 3a: Direct user to accountability page
        if counter >= 1:
            st.header('Go to Accountability Page')
            column_text, column_button = st.columns(2, vertical_alignment="center")
            with column_text:
                st.write(
                    f'Congratulations! You have passed {counter} meals since last time. Go to your accountability page and report if you reached your goals!')
                st.write("It is ok if you didn't, Life happens sometimes")
            with column_button:
                st.button(
                    f"Go to Accountability Page",
                    use_container_width=True,
                    on_click=change_page,
                    args=[6],
                    key=f"go_to_Accountability_page"
                )

        # Step 4: Determine if pre-made meals should be shown
        # If user already has meals → allow toggle
        # Otherwise → force showing pre-made options
        st.header("Pick one or more of our pre made meals to add to your meal plan.")
        column_checkbox, column_button_meal = st.columns(2, vertical_alignment="center")
        with column_checkbox:
            if len(return_all_meals({'UserID': st.session_state.current_user})) != 0:
                show_meals = st.checkbox("I want to add pre-made options")
            else:
                show_meals = True
        with column_button_meal:
            st.button(
                f"I want to add my own meals",
                use_container_width=True,
                on_click=change_page,
                args=[7],
                key=f"go_to_profile_page"
            )
        if show_meals:
            pick_pre_made_meal()

        # Step 5: Show week's schedule
        today_schedule()

    else:
        # Step 6: Handle validation failure
        # Store error for global error display system
        st.session_state.error, st.session_state.error_status = message, status


# --- ID System ---
# MEAxxx → Template Meal Pointer
# INGxxx → Template Ingredient Pointer
# CATxxx → Template Category Pointer
# CodeID → Database record ID (user-specific)


# -----------------------------
# Meal Types
# Static list used for UI grouping (order matters for display)
# -----------------------------
meal_types = ["Breakfast", "Lunch", "Dinner"]

# -----------------------------
# Categories (Template Layer)
# Pointer = template identifier (CATxxx)
# Used to assign category to meals (NOT ingredients)
# -----------------------------
categories = [
    {"Name": "Egg-based Breakfast", "Pointer": "CAT001", "Rule": None},
    {"Name": "Sweet Breakfast", "Pointer": "CAT002", "Rule": None},
    {"Name": "Sandwich Lunch", "Pointer": "CAT009", "Rule": None},
    {"Name": "Salad Lunch", "Pointer": "CAT010", "Rule": None},
    {"Name": "Pasta Lunch", "Pointer": "CAT011", "Rule": None},
    {"Name": "Rice Dinner", "Pointer": "CAT015", "Rule": None},
    {"Name": "Soup Dinner", "Pointer": "CAT016", "Rule": None},
    {"Name": "Fish Dinner", "Pointer": "CAT017", "Rule": None},
]

# -----------------------------
# Ingredients (Template Layer)
# Pointer = template identifier (INGxxx)
# UnitName = display unit (used to create UnitType in DB)
# No category → ingredients are standalone in current model
# -----------------------------
ingredients = [
    {"Name": "Egg", "Pointer": "ING001", "UnitName": "Unit", "Rule": None},
    {"Name": "Milk", "Pointer": "ING002", "UnitName": "Cup", "Rule": None},
    {"Name": "Bread", "Pointer": "ING003", "UnitName": "Slice", "Rule": None},
    {"Name": "Butter", "Pointer": "ING004", "UnitName": "Tablespoon", "Rule": None},
    {"Name": "Oats", "Pointer": "ING005", "UnitName": "Cup", "Rule": None},
    {"Name": "Banana", "Pointer": "ING006", "UnitName": "Unit", "Rule": None},
    {"Name": "Honey", "Pointer": "ING007", "UnitName": "Tablespoon", "Rule": None},
    {"Name": "Flour", "Pointer": "ING008", "UnitName": "Cup", "Rule": None},
    {"Name": "Baking Powder", "Pointer": "ING009", "UnitName": "Teaspoon", "Rule": None},
    {"Name": "Chicken Breast", "Pointer": "ING010", "UnitName": "Unit", "Rule": None},
    {"Name": "Lettuce", "Pointer": "ING011", "UnitName": "Cup", "Rule": None},
    {"Name": "Tomato", "Pointer": "ING012", "UnitName": "Unit", "Rule": None},
    {"Name": "Mayonnaise", "Pointer": "ING014", "UnitName": "Tablespoon", "Rule": None},
    {"Name": "Pasta", "Pointer": "ING015", "UnitName": "Cup", "Rule": None},
    {"Name": "Olive Oil", "Pointer": "ING016", "UnitName": "Tablespoon", "Rule": None},
    {"Name": "Cheese", "Pointer": "ING017", "UnitName": "Slice", "Rule": None},
    {"Name": "Cucumber", "Pointer": "ING018", "UnitName": "Unit", "Rule": None},
    {"Name": "Rice", "Pointer": "ING019", "UnitName": "Cup", "Rule": None},
    {"Name": "Salmon Fillet", "Pointer": "ING020", "UnitName": "Unit", "Rule": None},
    {"Name": "Carrot", "Pointer": "ING021", "UnitName": "Unit", "Rule": None},
    {"Name": "Onion", "Pointer": "ING022", "UnitName": "Unit", "Rule": None},
    {"Name": "Lemon", "Pointer": "ING023", "UnitName": "Unit", "Rule": None},
    {"Name": "Lentils", "Pointer": "ING024", "UnitName": "Cup", "Rule": None},
    {"Name": "Vegetable Broth", "Pointer": "ING025", "UnitName": "Cup", "Rule": None},
    {"Name": "Potato", "Pointer": "ING026", "UnitName": "Unit", "Rule": None},
]

# -----------------------------
# Meals (Template Layer)
# Pointer = template identifier (MEAxxx)
# Category = category pointer (CATxxx)
# MealType = used for grouping (Breakfast/Lunch/Dinner)
# Notes = optional user-facing description
# -----------------------------
meals = [
    {
        "Name": "Scrambled Eggs on Toast",
        "Pointer": "MEA001",
        "Category": "CAT001",
        "MealType": "Breakfast",
        "Rule": None,
        "Notes": "Quick high-protein breakfast, ready in under 10 minutes."
    },
    {
        "Name": "Banana Oatmeal",
        "Pointer": "MEA002",
        "Category": "CAT002",
        "MealType": "Breakfast",
        "Rule": None,
        "Notes": "Warm and filling option, naturally sweet and great for energy."
    },
    {
        "Name": "Pancakes",
        "Pointer": "MEA003",
        "Category": "CAT002",
        "MealType": "Breakfast",
        "Rule": None,
        "Notes": "Comfort breakfast, slightly longer prep but very satisfying."
    },
    {
        "Name": "Chicken Sandwich",
        "Pointer": "MEA004",
        "Category": "CAT009",
        "MealType": "Lunch",
        "Rule": None,
        "Notes": "Balanced and portable meal, ideal for quick lunches."
    },
    {
        "Name": "Chicken Salad",
        "Pointer": "MEA005",
        "Category": "CAT010",
        "MealType": "Lunch",
        "Rule": None,
        "Notes": "Light and fresh option, good for a low-carb lunch."
    },
    {
        "Name": "Tomato Pasta",
        "Pointer": "MEA006",
        "Category": "CAT011",
        "MealType": "Lunch",
        "Rule": None,
        "Notes": "Simple and comforting meal, easy to prepare in batches."
    },
    {
        "Name": "Salmon and Rice",
        "Pointer": "MEA007",
        "Category": "CAT017",
        "MealType": "Dinner",
        "Rule": None,
        "Notes": "Well-balanced dinner with healthy fats and protein."
    },
    {
        "Name": "Lentil Soup",
        "Pointer": "MEA008",
        "Category": "CAT016",
        "MealType": "Dinner",
        "Rule": None,
        "Notes": "Hearty and nutritious, great for meal prep and leftovers."
    },
    {
        "Name": "Vegetable Rice Bowl",
        "Pointer": "MEA009",
        "Category": "CAT015",
        "MealType": "Dinner",
        "Rule": None,
        "Notes": "Simple plant-based option, flexible with available vegetables."
    },
]

# -----------------------------
# Meal Combinations (Template Layer)
# Defines which ingredients belong to each meal
# Meal = MEAxxx pointer
# Ingredient = INGxxx pointer
# Quantity = amount of ingredient used in meal
# -----------------------------
combinations = [

    {"Meal": "MEA001", "Quantity": 2, "Ingredient": "ING001"},  # Egg
    {"Meal": "MEA001", "Quantity": 0.25, "Ingredient": "ING002"},  # Milk
    {"Meal": "MEA001", "Quantity": 2, "Ingredient": "ING003"},  # Bread
    {"Meal": "MEA001", "Quantity": 1, "Ingredient": "ING004"},  # Butter

    {"Meal": "MEA002", "Quantity": 0.5, "Ingredient": "ING005"},  # Oats
    {"Meal": "MEA002", "Quantity": 1, "Ingredient": "ING002"},  # Milk
    {"Meal": "MEA002", "Quantity": 1, "Ingredient": "ING006"},  # Banana
    {"Meal": "MEA002", "Quantity": 1, "Ingredient": "ING007"},  # Honey

    {"Meal": "MEA003", "Quantity": 1, "Ingredient": "ING008"},  # Flour
    {"Meal": "MEA003", "Quantity": 1, "Ingredient": "ING002"},  # Milk
    {"Meal": "MEA003", "Quantity": 1, "Ingredient": "ING001"},  # Egg
    {"Meal": "MEA003", "Quantity": 1, "Ingredient": "ING004"},  # Butter
    {"Meal": "MEA003", "Quantity": 1, "Ingredient": "ING009"},  # Baking Powder

    {"Meal": "MEA004", "Quantity": 1, "Ingredient": "ING010"},  # Chicken
    {"Meal": "MEA004", "Quantity": 2, "Ingredient": "ING003"},  # Bread (FIXED)
    {"Meal": "MEA004", "Quantity": 1, "Ingredient": "ING011"},  # Lettuce
    {"Meal": "MEA004", "Quantity": 1, "Ingredient": "ING012"},  # Tomato
    {"Meal": "MEA004", "Quantity": 1, "Ingredient": "ING014"},  # Mayo

    {"Meal": "MEA005", "Quantity": 1, "Ingredient": "ING010"},  # Chicken
    {"Meal": "MEA005", "Quantity": 2, "Ingredient": "ING011"},  # Lettuce
    {"Meal": "MEA005", "Quantity": 1, "Ingredient": "ING012"},  # Tomato
    {"Meal": "MEA005", "Quantity": 1, "Ingredient": "ING018"},  # Cucumber
    {"Meal": "MEA005", "Quantity": 1, "Ingredient": "ING016"},  # Olive Oil

    {"Meal": "MEA006", "Quantity": 1, "Ingredient": "ING015"},  # Pasta
    {"Meal": "MEA006", "Quantity": 2, "Ingredient": "ING012"},  # Tomato
    {"Meal": "MEA006", "Quantity": 1, "Ingredient": "ING016"},  # Olive Oil
    {"Meal": "MEA006", "Quantity": 1, "Ingredient": "ING017"},  # Cheese

    {"Meal": "MEA007", "Quantity": 1, "Ingredient": "ING020"},  # Salmon Fillet
    {"Meal": "MEA007", "Quantity": 1, "Ingredient": "ING019"},  # Rice
    {"Meal": "MEA007", "Quantity": 1, "Ingredient": "ING021"},  # Carrot
    {"Meal": "MEA007", "Quantity": 1, "Ingredient": "ING023"},  # Lemon
    {"Meal": "MEA007", "Quantity": 1, "Ingredient": "ING016"},  # Olive Oil

    {"Meal": "MEA008", "Quantity": 1, "Ingredient": "ING024"},  # Lentils
    {"Meal": "MEA008", "Quantity": 1, "Ingredient": "ING022"},  # Onion
    {"Meal": "MEA008", "Quantity": 1, "Ingredient": "ING021"},  # Carrot
    {"Meal": "MEA008", "Quantity": 2, "Ingredient": "ING025"},  # Vegetable Broth
    {"Meal": "MEA008", "Quantity": 1, "Ingredient": "ING016"},  # Olive Oil

    {"Meal": "MEA009", "Quantity": 1, "Ingredient": "ING019"},  # Rice
    {"Meal": "MEA009", "Quantity": 1, "Ingredient": "ING021"},  # Carrot
    {"Meal": "MEA009", "Quantity": 1, "Ingredient": "ING022"},  # Onion
    {"Meal": "MEA009", "Quantity": 1, "Ingredient": "ING026"},  # Potato
    {"Meal": "MEA009", "Quantity": 1, "Ingredient": "ING016"},  # Olive Oil
]

# -----------------------------
# Lookup Tables (Performance Optimization)
# Convert lists into dictionaries for O(1) access
# Pointer → full object mapping
# -----------------------------
meal_lookup = {meal["Pointer"]: meal for meal in meals}
category_lookup = {category["Pointer"]: category for category in categories}
ingredient_lookup = {ingredient["Pointer"]: ingredient for ingredient in ingredients}


def pick_pre_made_meal():
    # Step 1: Render container and title
    with st.container(border=True):

        # Step 2: Loop through meal types (Breakfast, Lunch, Dinner)
        for entry in meal_types:
            st.subheader(entry)

            # Step 3: Collect all meals for this type
            table = []
            counter = 0
            for meal_entry in meals:
                if entry == meal_entry['MealType']:
                    table.append(meal_entry['Pointer'])  # store meal pointer
                    counter += 1
                    if counter == 3:
                        # Step 4: Display meals in columns
                        cols = st.columns(len(table))
                        for i, val in enumerate(table):
                            with cols[i]:
                                show_meal(table[i])
                        table = []
                        counter = 0

            if len(table) >= 1:
                cols = st.columns(len(table))
                for i, val in enumerate(table):
                    with cols[i]:
                        show_meal(table[i])


def show_meal(mealID: str):
    # Step 1: Retrieve meal data from lookup
    meal_name = meal_lookup[mealID]["Name"]
    categoryID = meal_lookup[mealID]["Category"]
    category_name = category_lookup[categoryID]["Name"]
    notes = meal_lookup[mealID]["Notes"]

    # Step 2: Display meal info
    st.write(meal_name)
    st.write(f"Category: {category_name}")
    st.write(notes)

    st.write(f"Ingredients for {meal_name}")

    # Step 3: Display ingredient list
    for entry in combinations:
        if entry['Meal'] == mealID:
            ingredientID = entry['Ingredient']

            st.write(
                f"-> {entry['Quantity']} {ingredient_lookup[ingredientID]['UnitName']}(s) "
                f"of {ingredient_lookup[ingredientID]['Name']}"
            )

    # Step 4: Show add button only if meal does not already exist for user
    if len(return_all_meals({'Name': meal_name})) == 0:
        st.button(
            f"Add {meal_name} to my plan!",
            use_container_width=True,
            on_click=add_data,
            args=[mealID],
            key=f"add_{mealID}"
        )


def add_data(mealID: str):
    # Step 1: Ensure rule exists (default: 1 per Day)
    ruleID, move_on = add_rule(1, "Day")
    if not move_on:
        return

    # Step 2: Ensure meal type exists
    mealTypeID, move_on = add_meal_type(mealID, ruleID)
    if not move_on:
        return

    # Step 3: Ensure category exists
    categoryID, move_on = add_category(meal_lookup[mealID]['Category'])
    if not move_on:
        return

    # Step 4: Create or retrieve meal
    meal_code_ID, move_on = add_meal(mealID, categoryID, meal_lookup[mealID]['Notes'])
    if not move_on:
        return

    # Step 5: Process all ingredient combinations
    for entry in combinations:
        if entry['Meal'] == mealID:

            # Step 5a: Ensure unit type exists
            unitTypeID, move_on = add_unit_type(
                ingredient_lookup[entry['Ingredient']]['UnitName']
            )
            if not move_on:
                return

            # Step 5b: Ensure ingredient exists
            ingredientID, move_on = add_ingredient(
                ingredient_lookup[entry['Ingredient']]['Name'],
                unitTypeID
            )
            if not move_on:
                return

            # Step 5c: Create meal combination
            mealCombinationID, move_on = add_meal_combination(
                ingredientID,
                meal_code_ID,
                float(entry['Quantity'])
            )
            if not move_on:
                return


def add_rule(quantity: int, per: str):
    # Step 1: Check if rule already exists for user
    rule = return_all_rules({
        'UserID': st.session_state.current_user,
        'Quantity': quantity,
        'Per': per
    })

    # Step 2: Create rule if not found
    if len(rule) == 0:
        message, rule, status = create_rule(quantity, per, st.session_state.current_user)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        ruleID = rule['CodeID']

    # Step 3: Validate existing rule
    else:
        ruleID = rule[0]['CodeID']
        message, rule, status = validate_rule(ruleID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    return ruleID, True


def add_meal_type(mealID: str, ruleID: str):
    # Step 1: Get meal type name from template meal
    # mealID = template meal pointer (e.g. MEA001)
    # ruleID = database CodeID for the rule to attach
    mealType_name = meal_lookup[mealID]['MealType']

    # Step 2: Check if this meal type already exists for the current user
    mealType = return_all_meal_types({
        'Name': mealType_name,
        'UserID': st.session_state.current_user
    })

    # Step 3: Create or validate meal type
    if len(mealType) == 0:
        message, mealType, status = create_meal_type(
            mealType_name,
            st.session_state.current_user,
            ruleID,
            None
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        mealTypeID = mealType['CodeID']  # database CodeID
    else:
        mealTypeID = mealType[0]['CodeID']
        message, mealType, status = validate_meal_type(mealTypeID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    return mealTypeID, True


def add_category(categoryID: str):
    # Step 1: Resolve template category pointer to category name
    # categoryID = template category pointer (e.g. CAT001)
    category_name = category_lookup[categoryID]['Name']

    # Step 2: Check if this category already exists for the current user
    category = return_all_categories({
        'Name': category_name,
        'UserID': st.session_state.current_user
    })

    # Step 3: Create or validate category
    if len(category) == 0:
        message, category, status = create_category(
            category_name,
            st.session_state.current_user,
            None
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        categoryID = category['CodeID']  # database CodeID
    else:
        categoryID = category[0]['CodeID']
        message, category, status = validate_category(categoryID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    return categoryID, True


def add_meal(mealID: str, categoryID: str, notes: str):
    # Step 1: Resolve template meal pointer to meal name
    # mealID = template meal pointer
    # categoryID = database CodeID for category
    # notes = pre-made notes from template
    meal_name = meal_lookup[mealID]['Name']

    # Step 2: Check if this meal already exists for the current user
    meal = return_all_meals({
        'Name': meal_name,
        'UserID': st.session_state.current_user
    })

    # Step 3: Create or validate meal
    if len(meal) == 0:
        message, meal, status = create_meal(
            meal_name,
            st.session_state.current_user,
            categoryID,
            notes,
            None
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        mealID = meal['CodeID']  # database CodeID
    else:
        mealID = meal[0]['CodeID']
        message, meal, status = validate_meal(mealID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    return mealID, True


def add_unit_type(unit_type_name: str):
    # Step 1: Check if this unit type already exists for the current user
    # unit_type_name = display unit such as Cups, Units, Slices
    unit_type = return_all_unit_types({
        'Name': unit_type_name,
        'UserID': st.session_state.current_user
    })

    # Step 2: Create or validate unit type
    if len(unit_type) == 0:
        message, unit_type, status = create_unit_type(
            unit_type_name,
            st.session_state.current_user
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        unit_typeID = unit_type['CodeID']  # database CodeID
    else:
        unit_typeID = unit_type[0]['CodeID']
        message, unit_type, status = validate_unit_type(unit_typeID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    # Step 3: Return usable unit type ID
    return unit_typeID, True


def add_ingredient(ingredient_name: str, unitTypeID: str):
    # Step 1: Check if this ingredient already exists for the current user
    # ingredient_name = template ingredient name
    # unitTypeID = database CodeID for associated unit type
    ingredient = return_all_ingredients({
        'Name': ingredient_name,
        'UserID': st.session_state.current_user
    })

    # Step 2: Create or validate ingredient
    if len(ingredient) == 0:
        message, ingredient, status = create_ingredient(
            ingredient_name,
            st.session_state.current_user,
            unitTypeID,
            None
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        ingredientID = ingredient['CodeID']  # database CodeID
    else:
        ingredientID = ingredient[0]['CodeID']
        message, ingredient, status = validate_ingredient(ingredientID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    # Step 3: Return usable ingredient ID
    return ingredientID, True


def add_meal_combination(ingredientID: str, mealID: str, quantity: float):
    # Step 1: Check if this exact meal combination already exists
    # ingredientID = database CodeID for ingredient
    # mealID = database CodeID for meal
    # quantity = amount of ingredient in meal
    meal_combination = return_all_meal_combinations({
        'IngredientID': ingredientID,
        'MealID': mealID,
        'Quantity': quantity,
        'UserID': st.session_state.current_user
    })

    # Step 2: Create or validate meal combination
    if len(meal_combination) == 0:
        message, meal_combination, status = create_meal_combination(
            st.session_state.current_user,
            ingredientID,
            mealID,
            quantity
        )
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False
        meal_combinationID = meal_combination['CodeID']  # database CodeID
    else:
        meal_combinationID = meal_combination[0]['CodeID']
        message, meal_combination, status = validate_meal_combination(meal_combinationID)
        if not status:
            st.session_state.error, st.session_state.error_status = message, status
            return None, False

    # Step 3: Return usable meal combination ID
    return meal_combinationID, True
