from AdministrativeFunctions import open_new_code
from Ingredient import validate_ingredient
from Mongo_Connection import Meal, MealCombination
from Request import create_request
from UnitType import validate_unit_type
from User import validate_user, user_information
from Category import validate_category, category_information
from Rule import validate_rule, rule_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st

# Item Description Labels for Item as Foreign Key
meal_codeID_label = "Meal CodeID: "
meal_createdAt_label = "Creation Date: "
meal_name_label = "Meal Name: "
meal_notes_label = "Notes: "

# Collection Tag
collection_name = "Meal"


def return_all_meals(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Meal.find(query))


def validate_meal(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_meals({'CodeID': codeID})

    # 3) Result validation
    # No match found
    if len(item) == 0:
        return f"[{collection_name}] Invalid Input: No Item Found", None, False

    # Single valid match found
    elif len(item) == 1:
        return f"[{collection_name}] Valid Input: Item Found", item, True

    # More than one match found (data integrity issue)
    else:
        message, entry, status = create_request(f"[{collection_name}]Multiple Items Found", codeID, get_now())
        return f"[{collection_name}] Invalid Input: Multiple Items Found" + message, item, False


def make_meal(codeID: str, createdAt: str, userID: str, categoryID: str, name: str, notes: str, ruleID: str = None):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'CategoryID': categoryID,
        'RuleID': ruleID,
        'Name': name,
        'Notes': notes
    }


def create_meal(name: str, userID: str, categoryID: str, notes: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Validate required foreign key (CategoryID) and optional foreign key (RuleID).
    category_message, entry, category_status = validate_category(categoryID)
    if not category_status:
        return category_message, entry, category_status

    # RuleID is optional; only validate it when provided.
    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate input fields
    # Name is required and must be a non-empty string.
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    if notes is None:
        notes = ""

    # 4) Uniqueness check
    # Meal name must be unique per user (same user cannot create two meals with the same name).
    if len(return_all_meals({'Name': name, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Meal, collection_name)

    if codeID_status:
        # 6) Build new document
        new_entry = make_meal(codeID, get_now(), userID, categoryID, name, notes, ruleID)

        # 7) Insert into database
        Meal.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 8) Create record log
        # Log the created Meal entry using the inserted document snapshot.
        record_message, record, record_status = create_record(Meal, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 9) Rollback on record failure
        # If record creation fails, remove the inserted Meal entry to keep database state and audit log consistent.
        Meal.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 10) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_meal_products(codeID: str):
    # 1) Input guard
    # If no Meal CodeID is provided, there can be no dependent entries.
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all collections that may reference a Meal entry
    # (as defined by get_products(collection_name)) for documents
    # that store this Meal's CodeID as a foreign key.
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'MealID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    # Used to block deletion of Meals that are still referenced elsewhere.
    return products


def delete_meal(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the Meal entry is not referenced by any other collections
    # (e.g. MealCombination, Schedule, etc.).
    # This prevents deleting meals that are still in use.
    entry = find_meal_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target Meal
    # Ensure the Meal to be deleted exists and is uniquely identified.
    item_message, entry, item_status = validate_meal(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator/owner of this Meal entry.
    # Users may only delete Meals they created.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    # Remove the Meal document identified by CodeID.
    Meal.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    # Log the deletion using the pre-delete snapshot of the Meal entry.
    record_message, record, record_status = create_record(
        Meal, "Delete", codeID, entry[0], userID
    )
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # If record creation fails, restore the deleted Meal entry
    # to keep database state and audit log consistent.
    new_entry = make_meal(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['CategoryID'],
        entry[0]['Name'],
        entry[0]['Notes'],
        entry[0]['RuleID']
    )
    Meal.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_meal(codeID: str, userID: str, name: str, categoryID: str, notes: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Validate required foreign key (CategoryID) and optional foreign key (RuleID).
    category_message, entry, category_status = validate_category(categoryID)
    if not category_status:
        return category_message, entry, category_status

    # RuleID is optional; only validate it when provided.
    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate target Meal
    # Ensure the Meal to be updated exists and is uniquely identified.
    item_message, entry, item_status = validate_meal(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator/owner of this Meal entry.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Validate input fields
    # Name is required and must be a non-empty string.
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", entry, False

    if notes is None:
        notes = ""
    # 6) Uniqueness check
    # Meal name must be unique per user (unless unchanged for this entry).
    key_entry = return_all_meals({'Name': name, 'UserID': entry[0]['UserID']})
    if len(key_entry) >= 1 and name != entry[0]['Name']:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 7) Build updated document
    # Preserve CreatedAt and apply the new field values.
    new_entry = make_meal(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], categoryID, name, notes, ruleID)

    # 8) Update database entry
    # Apply the updated values to the existing Meal document.
    Meal.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 9) Create record log
    # Log the updated state of the Meal entry.
    record_message, record, record_status = create_record(Meal, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 10) Rollback on record failure
    # If record creation fails, restore the previous Meal values
    # to keep database state and audit log consistent.
    new_entry = make_meal(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['CategoryID'],
        entry[0]['Name'],
        entry[0]['Notes'],
        entry[0]['RuleID']
    )
    Meal.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def convert_ID_to_content():
    # Step 1: Fetch all meal entries from the database
    table = return_all_meals()

    # Step 2: Initialize lookup table and selectbox options
    #         - lookup maps display label -> CodeID
    #         - options is a plain list for UI components
    lookup = {}
    options = []

    # Step 3: Build label-to-ID mapping and UI options list
    for entry in table:
        label = entry['Name']
        lookup[label] = entry['CodeID']
        options.append(label)

    # Step 4: Return both structures so UI and logic stay in sync
    return lookup, options


def meal_id_to_index(meal_id, lookup, options):
    # Step 1: If no meal is associated, default to the None option
    if meal_id is None:
        return 0

    # Step 2: Find the display label that corresponds to the stored CodeID
    for label, code_id in lookup.items():
        if code_id == meal_id:
            # Step 3: Return the index of that label in the options list
            #         (used by Streamlit selectbox)
            try:
                return options.index(label)
            except ValueError:
                # Step 4: Fallback in case the label is missing from options
                return 0

    # Step 5: If no matching CodeID was found, fall back to None
    return 0


def meal_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['MealID']
    else:
        codeID = None

    meal_column, ingredient_column = st.columns(2, vertical_alignment="center")

    with meal_column:

        # Step 1a: Section header + basic meal reference
        st.subheader(f"{collection_name} Information")

        st.write(f"{meal_codeID_label}{codeID}")

        # Step 2: Validate / fetch meal document
        meal_message, meal_entry, meal_status = validate_meal(codeID)

        # Step 3: If meal exists, display meal details
        if meal_status:
            # Step 3a: Display meal creation date
            st.write(f"{meal_createdAt_label}{meal_entry[0]['CreatedAt']}")

            # Step 3b: Display meal name
            st.write(f"{meal_name_label}{meal_entry[0]['Name']}")

            # Step 3c: Display meal notes
            if len(meal_entry[0]['Notes']) != 0:
                st.write(f"{meal_notes_label}{meal_entry[0]['Notes']}")
            else:
                st.write('No Notes')

            if status:
                # Step 3d: Action button to open full meal view (and show product count)
                st.button(
                    f"This Item has {len(find_meal_products(codeID))} Product(s)",
                    use_container_width=True,
                    on_click=open_new_code,
                    args=[codeID],
                    key=f"open_{collection_name}_{pointer}"
                )

        else:
            # Step 4: Validation failed; display message
            st.write(meal_message)

    with ingredient_column:

        with st.container(border=True):

            # Step 3b: Display meal ingredients
            st.subheader(f"Ingredient Information")

            # Fetch all ingredient mappings linked to this specific meal.
            # MealCombination acts as a junction table between Meals and Ingredients.
            ingredients = list(MealCombination.find({'MealID': codeID}))

            if len(ingredients) == 0:
                st.write("No Ingredients found")

            for entry in ingredients:

                # Validate that the ingredient still exists.
                # This protects against orphaned references if an ingredient was deleted.
                ingredient_message, ingredient_entry, ingredient_status = validate_ingredient(entry['IngredientID'])
                if ingredient_status:

                    # Validate the unit type (e.g., grams, cups, pieces).
                    # This ensures measurement integrity and prevents broken formatting.
                    unit_type_message, unit_type_entry, unit_type_status = validate_unit_type(ingredient_entry[0]['UnitTypeID'])

                    if unit_type_entry:
                        # Display formatted ingredient line.
                        st.write(f"{entry['Quantity']} {unit_type_entry[0]['Name']}(s) of {ingredient_entry[0]['Name']}")

                    else:
                        # If unit type validation fails, explicitly show the validation error.
                        # Prevents silent data inconsistencies.
                        st.write(unit_type_message)

                else:
                    # If ingredient validation fails, display the error.
                    # This avoids rendering partial or corrupt meal data.
                    st.write(ingredient_message)


def full_entry_meal(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display meal-related information
    #         - Item details (category-specific fields)
    #         - Creator/user information
    #         - Rule information
    #         - Category information

    # Step 2: Render meal/item information
    with st.container(border=True):
        meal_information(outcome, pointer, status, "Primary")

    creator_column, category_column, rule_column = st.columns(3, vertical_alignment="center")

    # Step 3: Render creator / user metadata in the first column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")

    # Step 4: Render creator / category metadata in the second column
    with category_column:
        with st.container(border=True):
            category_information(outcome, pointer, status, "Secondary")

    # Step 5: Render rule-related information in the third column
    with rule_column:
        with st.container(border=True):
            rule_information(outcome, pointer, status, "Secondary")


def select_mealID(entry, pointer: int):
    # Step 1: Display the Meal Type label (used as section context / caption)
    st.write(meal_name_label)

    # Step 2: Fetch Meal Type lookup table and plain options list
    #         - frequency_table: label -> CodeID
    #         - frequency_list:  [None, "X per Y", ...]
    meal_table, meal_list = convert_ID_to_content()

    # Step 3: Render selectbox for Meal Type selection
    #         - Pre-selects the current Meal Type if entry exists
    #         - Falls back to None if no Meal Type is attached
    meal = st.selectbox(
        meal_name_label,
        meal_list,
        index=meal_id_to_index(
            entry.get("MealID") if entry else None,
            meal_table,
            meal_list
        ),
        label_visibility="collapsed",
        key=f"mealID_button_{pointer}",
    )

    # Step 4: Translate selected display label back into the stored CodeID
    meal_id = meal_table.get(meal)

    # Step 5: Return the resolved Meal Type CodeID (or None)
    return meal_id
