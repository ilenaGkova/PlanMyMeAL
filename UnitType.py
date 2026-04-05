from AdministrativeFunctions import open_new_code
from Mongo_Connection import UnitType
from User import validate_user, user_information
from Request import create_request
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st

# Item Description Labels
unit_type_codeID_label = "Unit Type CodeID: "
unit_type_createdAt_label = "Creation Date: "
unit_type_name_label = "Unit Type Name: "

# Collection Tag
collection_name = "UnitType"

# Store the current signed-in user's CodeID
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def return_all_unit_types(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(UnitType.find(query))


def validate_unit_type(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_unit_types({'CodeID': codeID})

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


def make_unit_type(codeID: str, createdAt: str, userID: str, name: str):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'Name': name
    }


def create_unit_type(name: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate input fields
    # Name must be a non-empty string
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    # 3) Uniqueness check
    # Unit type name must be unique across the collection
    if len(return_all_unit_types({'Name': name, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 4) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(UnitType, collection_name)

    if codeID_status:
        # 5) Build new document
        new_entry = make_unit_type(codeID, get_now(), userID, name)

        # 6) Insert into database
        UnitType.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 7) Create record log
        record_message, record, record_status = create_record(UnitType, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 8) Rollback on record failure
        UnitType.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 9) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_unit_type_products(codeID: str):
    # 1) Input guard
    # If no unit type ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this unit type
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'UnitTypeID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_unit_type(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the unit type is not referenced by any other entries
    entry = find_unit_type_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target unit type
    # Ensure the unit type to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_unit_type(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this unit type
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    UnitType.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(UnitType, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted unit type entry
    new_entry = make_unit_type(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Name']
    )
    UnitType.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_unit_type(codeID: str, name: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate target unit type
    # Ensure the unit type to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_unit_type(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 3) Ownership check
    # Ensure the requesting user is the creator of this unit type
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 4) Input validation (explicit None guard)
    # Ensure name is not None and not empty
    if name is None or not name.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", entry, False

    # 5) Uniqueness check
    # Unit type name must be unique (unless unchanged for this entry)
    key_entry = return_all_unit_types({'Name': name, 'UserID': entry[0]['UserID']})
    if len(key_entry) >= 1 and name != entry[0]['Name']:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 6) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_unit_type(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], name)

    # 7) Update database entry
    UnitType.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 8) Create record log
    record_message, record, record_status = create_record(UnitType, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 9) Rollback on record failure
    # Restore the previous unit type entry values
    new_entry = make_unit_type(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Name']
    )
    UnitType.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def convert_ID_to_content():
    # Step 1: Fetch all unit type entries from the database
    table = None
    if st.session_state.current_user is not None:
        item_message, entry, item_status = validate_user(st.session_state.current_user)
        if item_status and entry[0]['Role'] == role_table["Plain User"]:
            table = return_all_unit_types({'UserID': st.session_state.current_user})
    if table is None:
        table = return_all_unit_types()

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


def unit_type_id_to_index(unit_type_id, lookup, options):
    # Step 1: If no Unit Type is associated, default to the None option
    if unit_type_id is None:
        return 0

    # Step 2: Find the display label that corresponds to the stored CodeID
    for label, code_id in lookup.items():
        if code_id == unit_type_id:
            # Step 3: Return the index of that label in the options list
            #         (used by Streamlit selectbox)
            try:
                return options.index(label)
            except ValueError:
                # Step 4: Fallback in case the label is missing from options
                return 0

    # Step 5: If no matching CodeID was found, fall back to None
    return 0


def unit_type_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Section header + basic Unit Type reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['UnitTypeID']
    else:
        codeID = None

    st.write(f"{unit_type_codeID_label}{codeID}")

    # Step 2: Validate / fetch Unit Type document
    unit_type_message, unit_type_entry, unit_type_status = validate_unit_type(codeID)

    # Step 3: If Unit Type exists, display Unit Type details
    if unit_type_status:
        # Step 3a: Display Unit Type creation date
        st.write(f"{unit_type_createdAt_label}{unit_type_entry[0]['CreatedAt']}")

        # Step 3b: Display Unit Type frequency / quantity formatting
        st.write(f"{unit_type_name_label}{unit_type_entry[0]['Name']}")

        if status:
            # Step 3c: Action button to open full Unit Type view (and show product count)
            st.button(
                f"This Item has {len(find_unit_type_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        st.write(unit_type_message)


def full_entry_unit_type(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display unit type-related information
    #         - Item details (unit type-specific fields)
    #         - Creator/user information
    #         - Rule information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render unit type/item information in the first column
    with item_column:
        with st.container(border=True):
            unit_type_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")


def select_unitTypeID(entry, pointer: int):
    # Step 1: Display the unit type label (used as section context / caption)
    st.write(unit_type_name_label)

    # Step 2: Fetch unit type lookup table and plain options list
    #         - frequency_table: label -> CodeID
    #         - frequency_list:  [None, "X per Y", ...]
    unit_type_table, unit_type_list = convert_ID_to_content()

    # Step 3: Render selectbox for unit type selection
    #         - Pre-selects the current unit type if entry exists
    #         - Falls back to None if no unit type is attached
    unit_type = st.selectbox(
        unit_type_name_label,
        unit_type_list,
        index=unit_type_id_to_index(
            entry.get("UnitTypeID") if entry else None,
            unit_type_table,
            unit_type_list
        ),
        label_visibility="collapsed",
        key=f"unit_typeID_button_{pointer}",
    )

    # Step 4: Translate selected display label back into the stored CodeID
    unitTypeID = unit_type_table.get(unit_type)

    # Step 5: Return the resolved unit type CodeID (or None)
    return unitTypeID
