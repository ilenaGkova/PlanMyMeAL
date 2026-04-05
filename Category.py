from AdministrativeFunctions import open_new_code
from Mongo_Connection import Category
from Request import create_request
from User import validate_user, user_information
from Rule import validate_rule, rule_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st

# Item Description Labels
category_codeID_label = " Category CodeID: "
category_createdAt_label = "Creation Date: "
category_name_label = "Category Name: "

# Collection Tag
collection_name = "Category"

# Store the current signed-in user's CodeID
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def return_all_categories(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all users
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Category.find(query))


def validate_category(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_categories({'CodeID': codeID})

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


def make_category(codeID: str, createdAt: str, userID: str, name: str, ruleID: str = None):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'RuleID': ruleID,
        'Name': name
    }


def create_category(name: str, userID: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate foreign keys
    # Validate optional foreign keys (RuleID)
    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate input fields
    # Name must be a non-empty string
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    # 4) Uniqueness check
    # Category name must be unique across the collection
    if len(return_all_categories({'Name': name, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Category, collection_name)

    if codeID_status:
        # 6) Build new document
        new_entry = make_category(codeID, get_now(), userID, name, ruleID)

        # 7) Insert into database
        Category.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 8) Create record log
        record_message, record, record_status = create_record(Category, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 9) Rollback on record failure
        Category.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 10) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_category_products(codeID: str):
    # 1) Input guard
    # If no category ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this category
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'CategoryID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_category(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the category is not referenced by any other entries
    entry = find_category_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target category
    # Ensure the category to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_category(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this category
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    Category.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(Category, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted category entry
    new_entry = make_category(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Name'],
        entry[0]['RuleID']
    )
    Category.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_category(codeID: str, name: str, userID: str, ruleID: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate foreign keys
    # Validate optional foreign keys (RuleID)
    rule_message, entry, rule_status = validate_rule(ruleID)
    if ruleID is not None and not rule_status:
        return rule_message, entry, rule_status

    # 3) Validate target category
    # Ensure the category to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_category(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this category
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Validate input fields
    # Name must be a non-empty string
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", entry, False

    # 6) Uniqueness check
    # Category name must be unique (unless unchanged for this entry)
    key_entry = return_all_categories({'Name': name, 'UserID': entry[0]['UserID']})
    if len(key_entry) >= 1 and name != entry[0]['Name']:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 7) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_category(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], name, ruleID)

    # 8) Update database entry
    Category.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 9) Create record log
    record_message, record, record_status = create_record(Category, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 10) Rollback on record failure
    # Restore the previous category entry values
    new_entry = make_category(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Name'],
        entry[0]['RuleID']
    )
    Category.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def convert_ID_to_content():
    # Step 1: Fetch all category entries from the database
    table = None
    if st.session_state.current_user is not None:
        item_message, entry, item_status = validate_user(st.session_state.current_user)
        if item_status and entry[0]['Role'] == role_table["Plain User"]:
            table = return_all_categories({'UserID': st.session_state.current_user})
    if table is None:
        table = return_all_categories()

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


def category_id_to_index(category_id, lookup, options):
    # Step 1: If no category is associated, default to the None option
    if category_id is None:
        return 0

    # Step 2: Find the display label that corresponds to the stored CodeID
    for label, code_id in lookup.items():
        if code_id == category_id:
            # Step 3: Return the index of that label in the options list
            #         (used by Streamlit selectbox)
            try:
                return options.index(label)
            except ValueError:
                # Step 4: Fallback in case the label is missing from options
                return 0

    # Step 5: If no matching CodeID was found, fall back to None
    return 0


def category_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Title + basic category reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['CategoryID']
    else:
        codeID = None

    st.write(f"{category_codeID_label}{codeID}")

    # Step 2: Validate / fetch category document
    category_message, category_entry, category_status = validate_category(codeID)

    # Step 3: If category exists, display category details
    if category_status:
        # Step 3a: Display category creation date
        st.write(f"{category_createdAt_label}{category_entry[0]['CreatedAt']}")

        # Step 3b: Display category name
        st.write(f"{category_name_label}{category_entry[0]['Name']}")

        if status:
            # Step 3c: Action button to open full category view (and show product count)
            st.button(
                f"This Item has {len(find_category_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(category_message)


def full_entry_category(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display category-related information
    #         - Item details (category-specific fields)
    #         - Creator/user information
    #         - Rule information
    item_column, creator_column, rule_column = st.columns(3, vertical_alignment="center")

    # Step 2: Render category/item information in the first column
    with item_column:
        with st.container(border=True):
            category_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")

    # Step 4: Render rule-related information in the third column
    with rule_column:
        with st.container(border=True):
            rule_information(outcome, pointer, status, "Secondary")


def select_categoryID(entry, pointer: int):
    # Step 1: Display the category label (used as section context / caption)
    st.write(category_name_label)

    # Step 2: Fetch category lookup table and plain options list
    #         - frequency_table: label -> CodeID
    #         - frequency_list:  [None, "X per Y", ...]
    category_table, category_list = convert_ID_to_content()

    # Step 3: Render selectbox for category selection
    #         - Pre-selects the current category if entry exists
    #         - Falls back to None if no category is attached
    category = st.selectbox(
        category_name_label,
        category_list,
        index=category_id_to_index(
            entry.get("CategoryID") if entry else None,
            category_table,
            category_list
        ),
        label_visibility="collapsed",
        key=f"categoryID_button_{pointer}",
    )

    # Step 4: Translate selected display label back into the stored CodeID
    categoryID = category_table.get(category)

    # Step 5: Return the resolved category CodeID (or None)
    return categoryID
