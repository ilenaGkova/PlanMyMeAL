import streamlit as st
from AdministrativeFunctions import open_new_code
from Mongo_Connection import Day
from Request import create_request
from User import validate_user, user_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
from datetime import datetime

# Item Description Labels
day_codeID_label = " Day CodeID: "
day_createdAt_label = "Creation Date: "
day_date_label = "Date: "

# Collection Tag
collection_name = "Day"


def return_all_days(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Day.find(query))


def validate_day(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_days({'CodeID': codeID})

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


def make_day(codeID: str, createdAt: str, userID: str, day: str):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'Date': day
    }


def create_day(day: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate input fields
    # Day must be a non-empty string
    if day is None or not day.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    # 3) Uniqueness check
    # Day must be unique across the collection
    if len(return_all_days({'Date': day})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 4) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Day, collection_name)

    if codeID_status:
        # 5) Build new document
        new_entry = make_day(codeID, get_now(), userID, day)

        # 6) Insert into database
        Day.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 7) Create record log
        record_message, record, record_status = create_record(Day, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 8) Rollback on record failure
        Day.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 9) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_day_products(codeID: str):
    # 1) Input guard
    # If no unit type ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this codeID
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'DayID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_day(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the unit type is not referenced by any other entries
    entry = find_day_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target unit type
    # Ensure the unit type to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_day(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this unit type
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    Day.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(Day, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted unit type entry
    new_entry = make_day(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Date']
    )
    Day.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_day(codeID: str, day: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate target unit type
    # Ensure the unit type to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_day(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 3) Ownership check
    # Ensure the requesting user is the creator of this unit type
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 4) Input validation (explicit None guard)
    # Ensure day is not None and not empty
    if day is None or not day.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", entry, False

    # 5) Uniqueness check
    # Unit type day must be unique (unless unchanged for this entry)
    key_entry = return_all_days({'Date': day})
    if len(key_entry) >= 1 and day != entry[0]['Date']:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 6) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_day(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], day)

    # 7) Update database entry
    Day.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 8) Create record log
    record_message, record, record_status = create_record(Day, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 9) Rollback on record failure
    # Restore the previous unit type entry values
    new_entry = make_day(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Date']
    )
    Day.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def get_date(codeID: str):
    """
    Validate a Day entry and convert its Date field into a date object.
    Returns (message, date | entry, status)
    """
    item_message, entry, item_status = validate_day(codeID)
    if not item_status:
        return item_message, entry, item_status

    date_str = entry[0].get("Date")
    if date_str is None:
        return f"[{collection_name}] Invalid Input: Date Missing", entry, False

    # Try known formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return f"[{collection_name}] Valid Input: Date Parsed", datetime.strptime(date_str, fmt).date(), True
        except ValueError:
            continue

    # Fallback: ISO datetime (e.g. '2026-01-30T14:00')
    try:
        return f"[{collection_name}] Valid Input: Date Parsed", datetime.fromisoformat(date_str).date(), True
    except ValueError:
        return f"[{collection_name}] Invalid Input: Unrecognized Date Format", entry, False


def convert_ID_to_content():
    # Step 1: Fetch all day entries from the database
    table = return_all_days()

    # Step 2: Initialize lookup table and selectbox options
    #         - lookup maps display label -> CodeID
    #         - options is a plain list for UI components
    lookup = {}
    options = []

    # Step 3: Build label-to-ID mapping and UI options list
    for entry in table:
        label = entry['Date']
        lookup[label] = entry['CodeID']
        options.append(label)

    # Step 4: Return both structures so UI and logic stay in sync
    return lookup, options


def day_id_to_index(day_id, lookup, options):
    # Step 1: If no day is associated, default to the None option
    if day_id is None:
        return 0

    # Step 2: Find the display label that corresponds to the stored CodeID
    for label, code_id in lookup.items():
        if code_id == day_id:
            # Step 3: Return the index of that label in the options list
            #         (used by Streamlit selectbox)
            try:
                return options.index(label)
            except ValueError:
                # Step 4: Fallback in case the label is missing from options
                return 0

    # Step 5: If no matching CodeID was found, fall back to None
    return 0


def day_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Title + basic day reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['DayID']
    else:
        codeID = None

    st.write(f"{day_codeID_label}{codeID}")

    # Step 2: Validate / fetch day document
    day_message, day_entry, day_status = validate_day(codeID)

    # Step 3: If day exists, display day details
    if day_status:
        # Step 3a: Display day creation date
        st.write(f"{day_createdAt_label}{day_entry[0]['CreatedAt']}")

        # Step 3b: Display day name
        st.write(f"{day_date_label}{day_entry[0]['Date']}")

        if status:
            # Step 3c: Action button to open full day view (and show product count)
            st.button(
                f"This Item has {len(find_day_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(day_message)


def full_entry_day(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display day-related information
    #         - Item details (day-specific fields)
    #         - Creator/user information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render day/item information in the first column
    with item_column:
        with st.container(border=True):
            day_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")


def select_dayID(entry, pointer: int):
    # Step 1: Display the Meal Type label (used as section context / caption)
    st.write(day_date_label)

    # Step 2: Fetch Meal Type lookup table and plain options list
    #         - frequency_table: label -> CodeID
    #         - frequency_list:  [None, "X per Y", ...]
    day_table, day_list = convert_ID_to_content()

    # Step 3: Render selectbox for Meal Type selection
    #         - Pre-selects the current Meal Type if entry exists
    #         - Falls back to None if no Meal Type is attached
    day = st.selectbox(
        day_date_label,
        day_list,
        index=day_id_to_index(
            entry.get("DayID") if entry else None,
            day_table,
            day_list
        ),
        label_visibility="collapsed",
        key=f"dayID_button_{pointer}",
    )

    # Step 4: Translate selected display label back into the stored CodeID
    day_id = day_table.get(day)

    # Step 5: Return the resolved Meal Type CodeID (or None)
    return day_id
