from AdministrativeFunctions import open_new_code
from Menu import menu
from MongoDB_General_Functions import table_codes
from Record import find_record_products, validate_record, record_information
from Request import request_information, validate_request, find_request_products
from UnitType import full_entry_unit_type, validate_unit_type, find_unit_type_products
from Schedule import full_entry_schedule, validate_schedule, find_schedule_products
from Rule import find_rule_products, full_entry_rule, validate_rule
from MealType import find_meal_type_products, full_entry_meal_type, validate_meal_type
from Meal import find_meal_products, full_entry_meal, validate_meal
from Ingredient import find_ingredient_products, full_entry_ingredient, validate_ingredient
from Day import find_day_products, full_entry_day, validate_day
from Category import find_category_products, full_entry_category, validate_category
import streamlit as st
from User import validate_user, find_user_products, full_entry_user

# Reverse the code table to find the collection
reverse_table = {v: k for k, v in table_codes.items()}


def full_entry_request(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display category-related information
    #         - Item details (request-specific fields)
    #         - item information

    # Step 2: Render request/item information
    with st.container(border=True):
        request_information(outcome, pointer, status)

    # Step 3: Render item metadata
    request_message, request_entry, request_status = validate_request(outcome[pointer]["CodeID"])
    if request_entry:
        for_code = request_entry[0]["For"]
        prefix = for_code[:2] if len(for_code) >= 2 else None

        collection = reverse_table.get(prefix) if prefix else None
        if collection:
            message, entry, entry_status = table_codes[collection]["validate"](for_code)
            if entry_status:
                table_codes[collection]["full_entry"](entry, 0, status)
            else:
                st.write(message)
        else:
            st.write(f"Collection not found for code {for_code}")
    else:
        st.write(request_message)


# Functions to build the individual pages for each code
table_codes = {
    "User": {"validate": validate_user, "full_entry": full_entry_user, "find_products": find_user_products},
    "UnitType": {"validate": validate_unit_type, "full_entry": full_entry_unit_type,
                 "find_products": find_unit_type_products},
    "Ingredient": {"validate": validate_ingredient, "full_entry": full_entry_ingredient,
                   "find_products": find_ingredient_products},
    "Category": {"validate": validate_category, "full_entry": full_entry_category,
                 "find_products": find_category_products},
    "Day": {"validate": validate_day, "full_entry": full_entry_day, "find_products": find_day_products},
    "Rule": {"validate": validate_rule, "full_entry": full_entry_rule, "find_products": find_rule_products},
    "Meal": {"validate": validate_meal, "full_entry": full_entry_meal, "find_products": find_meal_products},
    "Schedule": {"validate": validate_schedule, "full_entry": full_entry_schedule,
                 "find_products": find_schedule_products},
    "MealType": {"validate": validate_meal_type, "full_entry": full_entry_meal_type,
                 "find_products": find_meal_type_products},
    "Request": {"validate": validate_request, "full_entry": full_entry_request,
                "find_products": find_request_products},
    "Record": {"validate": validate_record, "full_entry": record_information, "find_products": find_record_products},
    "MealCombination": {"validate": None, "full_entry": None, "find_products": None}
}

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


def page_20_layout():
    # Step 1: Validate the currently signed-in user
    # Uses the CodeID stored in session state
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2: If user validation fails, store error for global handler and exit
    if not status:
        st.session_state.error = message
        st.session_state.error_status = status
        return

    # Step 3: Render the menu for the validated user
    menu(entry)

    # Step 4: Determine the collection from the open code prefix
    open_code = st.session_state.open_code
    collection = reverse_table.get(open_code[:2])

    # Step 5: Handle missing collection
    if not collection:
        st.session_state.error = f"Invalid Input: Item's {open_code} Collection Can't Be Found"
        st.session_state.error_status = False
        return

    # Step 6: Render page title
    st.title(f"{collection} {open_code}")
    st.title("")

    # Step 7: Validate the open code inside its collection
    if table_codes[collection]["validate"] is None:
        st.session_state.error = (
            f"Invalid Input: Item {open_code} of {collection} Collection Can't be Displayed"
        )
        st.session_state.error_status = False
        return

    message, entry, entry_status = table_codes[collection]["validate"](open_code)

    # Step 8: Handle invalid item
    if not entry_status:
        st.session_state.error = f"Invalid Input: Item {open_code} Can't Be Found"
        st.session_state.error_status = False
        return

    # Step 9: Render the main full entry view
    table_codes[collection]["full_entry"](entry, 0, status)

    # Step 10: Render related products in sidebar (if supported)
    finder = table_codes[collection].get("find_products")

    if finder is not None:
        products = finder(open_code) or []

        # Step 11: Render each related product as a navigation button
        pointer = 0  # Tracks the overall index of each product
        counter = 0  # Counts items per row (max 5 per row)
        table = []  # Temporary storage for current row of buttons

        # Loop through all products
        for product in products:

            counter += 1

            # Add product to current row (up to 5 items)
            if counter <= 5:
                table.append({
                    'Name': product["CodeID"],
                    'Pointer': pointer
                })

            # Once we reach 5 items → render the row
            if counter == 5:
                cols = st.columns(len(table))

                # Create one button per column
                for i, val in enumerate(table):
                    with cols[i]:
                        st.button(
                            val['Name'],
                            use_container_width=True,
                            on_click=open_new_code,
                            args=[val['Name']],
                            key=f"open_{val['Name']}_{val['Pointer']}"
                        )

                # Reset for next row
                counter = 0
                table = []

            pointer += 1

        # Handle remaining items (if total not divisible by 5)
        if len(table) >= 1:
            cols = st.columns(len(table))

            for i, val in enumerate(table):
                with cols[i]:
                    st.button(
                        val['Name'],
                        use_container_width=True,
                        on_click=open_new_code,
                        args=[val['Name']],
                        key=f"open_{val['Name']}_{val['Pointer']}"
                    )
