from AdministrativeFunctions import open_new_code
from General_Functions import return_table
from Mongo_Connection import Ingredient
from Request import create_request
from User import validate_user, user_information
from UnitType import validate_unit_type, unit_type_information
from Rule import validate_rule, rule_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st

# Item Description Labels
ingredient_codeID_label = "Ingredient CodeID: "
ingredient_createdAt_label = "Creation Date: "
ingredient_name_label = "Ingredient Name: "

# Collection Tag
collection_name = "Ingredient"

if "current_user" not in st.session_state:
    st.session_state.current_user = None


def return_all_ingredients(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Ingredient.find(query))


def validate_ingredient(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_ingredients({'CodeID': codeID})

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


def make_ingredient(codeID: str, createdAt: str, userID: str, unitTypeID: str, name: str, ruleID: str = None):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'UnitTypeID': unitTypeID,
        'RuleID': ruleID,
        'Name': name
    }


def create_ingredient(name: str, userID: str, unitTypeID: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate foreign keys
    # Validate required foreign keys (UnitTypeID) and optional foreign keys (RuleID)
    unitType_message, entry, unitType_status = validate_unit_type(unitTypeID)
    if not unitType_status:
        return unitType_message, entry, unitType_status

    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate input fields
    # Name must be a non-empty string
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    # 4) Uniqueness check
    # Ingredient name must be unique across the collection
    if len(return_all_ingredients({'Name': name, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Ingredient, collection_name)

    if codeID_status:
        # 6) Build new document
        new_entry = make_ingredient(codeID, get_now(), userID, unitTypeID, name, ruleID)

        # 7) Insert into database
        Ingredient.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 8) Create record log
        record_message, record, record_status = create_record(Ingredient, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 9) Rollback on record failure
        Ingredient.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 10) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_ingredient_products(codeID: str):
    # 1) Input guard
    # If no ingredient ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this ingredient
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'IngredientID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_ingredient(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the ingredient is not referenced by any other entries
    entry = find_ingredient_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target ingredient
    # Ensure the ingredient to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_ingredient(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this ingredient
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    Ingredient.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(Ingredient, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted ingredient entry
    new_entry = make_ingredient(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['UnitTypeID'],
        entry[0]['Name'],
        entry[0]['RuleID']
    )
    Ingredient.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_ingredient(codeID: str, userID: str, name: str, unitTypeID: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate foreign keys
    # Validate required foreign keys (UnitTypeID) and optional foreign keys (RuleID)
    unitType_message, entry, unitType_status = validate_unit_type(unitTypeID)
    if not unitType_status:
        return unitType_message, entry, unitType_status

    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate target ingredient
    # Ensure the ingredient to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_ingredient(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this ingredient
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Validate input fields
    # Name must be a non-empty string
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", entry, False

    # 6) Uniqueness check
    # Ingredient name must be unique (unless unchanged for this entry)
    key_entry = return_all_ingredients({'Name': name, 'UserID': entry[0]['UserID']})
    if len(key_entry) >= 1 and name != entry[0]['Name']:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 7) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_ingredient(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], unitTypeID, name, ruleID)

    # 8) Update database entry
    Ingredient.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 9) Create record log
    record_message, record, record_status = create_record(Ingredient, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 10) Rollback on record failure
    # Restore the previous ingredient entry values
    new_entry = make_ingredient(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['UnitTypeID'],
        entry[0]['Name'],
        entry[0]['RuleID']
    )
    Ingredient.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def ingredient_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Section header + basic ingredient reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['IngredientID']
    else:
        codeID = None

    st.write(f"{ingredient_codeID_label}{codeID}")

    # Step 2: Validate / fetch ingredient document
    ingredient_message, ingredient_entry, ingredient_status = validate_ingredient(codeID)

    # Step 3: If rule exists, display ingredient details
    if ingredient_status:
        # Step 3a: Display ingredient creation date
        st.write(f"{ingredient_createdAt_label}{ingredient_entry[0]['CreatedAt']}")

        # Step 3b: Display ingredient frequency / quantity formatting
        st.write(f"{ingredient_name_label}{ingredient_entry[0]['Name']}")

        if status:
            # Step 3c: Action button to open full ingredient view (and show product count)
            st.button(
                f"This Item has {len(find_ingredient_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(ingredient_message)


def full_entry_ingredient(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display ingredient-related information
    #         - Item details (category-specific fields)
    #         - Creator/user information
    #         - Unit Type information
    #         - Rule information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    unit_type_column, rule_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render category/item information in the first column
    with item_column:
        with st.container(border=True):
            ingredient_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")

    # Step 4: Render UnitType-related information in the third column
    with unit_type_column:
        with st.container(border=True):
            unit_type_information(outcome, pointer, status, "Secondary")

    # Step 5: Render rule-related information in the third column
    with rule_column:
        with st.container(border=True):
            rule_information(outcome, pointer, status, "Secondary")


def validate_ingredient_deep(entry):
    # Step 1: Validate that the ingredient still exists.
    # This protects against orphaned references if an ingredient was deleted.
    try:
        ingredient_message, ingredient_entry, ingredient_status = validate_ingredient(entry['IngredientID'])
    except Exception as e:
        ingredient_message, ingredient_entry, ingredient_status = validate_ingredient(entry['CodeID'])

    if ingredient_status:

        # Step 2: Validate the unit type (e.g., grams, cups, pieces).
        # This ensures measurement integrity and prevents broken formatting.
        unit_type_message, unit_type_entry, unit_type_status = validate_unit_type(ingredient_entry[0]['UnitTypeID'])
        if unit_type_status:

            # Step 3: Return relevant information
            return True, f"[{collection_name}] Valid Output: Entry Found", unit_type_entry[0]['Name'], ingredient_entry[
                0]

        else:

            # Step 4: Return fail message
            return False, unit_type_message, None, None

    else:

        # Step 4: Return fail message
        return False, ingredient_message, None, None


def get_ingredients_not_in_meal(entries):
    # Step 1: Turn entries into a unique list of IngredientIDs (strings)
    existing_ingredients = return_table("IngredientID", entries, [], False)

    if not existing_ingredients:
        existing_ingredients = []

    # Step 2: query full ingredient docs NOT in that list
    table = None
    if st.session_state.current_user is not None:
        item_message, entry, item_status = validate_user(st.session_state.current_user)
        if item_status and entry[0]['Role'] == role_table["Plain User"]:
            table = return_all_ingredients({"CodeID": {"$nin": existing_ingredients}, 'UserID': st.session_state.current_user})
    if table is None:
        table = return_all_ingredients({"CodeID": {"$nin": existing_ingredients}})
    return table
