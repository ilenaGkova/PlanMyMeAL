from AdministrativeFunctions import open_new_code
from Mongo_Connection import Record, User
from MongoDB_General_Functions import generate_code, get_now, get_products
from typing import Optional
import streamlit as st

# Item Description Labels
record_codeID_label = "Record CodeID: "
record_createdAt_label = "Creation Date: "
record_itemID_label = "Item ID: "
record_item_label = "Item Description: "
record_action_label = "Action: "

# Valid Actions
action_table = {"Create", "Update", "Delete"}

# Collection Tag
collection_name = "Record"


def find_all_records(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Record.find(query))


def create_record(collection, action: str, itemID: str, item: dict, userID: str, user: bool = True):
    # 1) Validate input fields
    # itemID and userID must be non-empty strings, and item (old value) must exist
    if itemID is None or not str(itemID).strip():
        return f"[{collection_name}] Invalid Input: No ItemID Detected", None, False

    if userID is None or not str(userID).strip():
        return f"[{collection_name}] Invalid Input: No UserID Detected", None, False

    if item is None:
        return f"[{collection_name}] Invalid Input: No Item Detected", None, False

    # 2) Validate action
    if action is None or action not in action_table:
        return f"[{collection_name}] Invalid Input: Action Not Found", None, False

    # 3) Validate referenced item exists (skip for Delete)
    # For Create/Update, ensure the item exists in the target collection
    if action != "Delete" and not collection.find_one({'CodeID': itemID}) and user:
        return f"[{collection_name}] Invalid Input: Item Not Found", None, False

    # 4) Validate user exists
    # Users are keyed by CodeID in your system
    if not User.find_one({'CodeID': userID}):
        return f"[{collection_name}] Invalid Input: User Not Found", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Record, collection_name)
    if not codeID_status:
        return f"[{collection_name}] " + codeID_message, None, False

    # 6) Build and insert record document
    new_entry = {
        'CodeID': codeID,
        'CreatedAt': get_now(),
        'UserID': userID,
        'ItemID': itemID,
        'Action': action,
        'Item': item
    }
    Record.insert_one(new_entry)
    return f"[{collection_name}] Valid Output: Entry Generated", new_entry, True


def validate_record(codeID: str):
    # 1) Validate input presence
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Fetch matching entries by CodeID
    item = find_all_records({'CodeID': codeID})

    # 3) Result validation
    # No match found.
    if len(item) == 0:
        return f"[{collection_name}] Invalid Input: No Item Found", None, False

    # Single valid match found.
    elif len(item) == 1:
        return f"[{collection_name}] Valid Input: Item Found", item, True

    # More than one match found (data integrity issue).
    else:
        return f"[{collection_name}] Invalid Input: Multiple Items Found", item, False


def find_record_products(codeID: str):
    # 1) Input guard
    # If no record ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this rule
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'RecordID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def record_information(outcome, pointer: int, status: bool):
    # Step 1: Section header + basic record reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    codeID = outcome[pointer]['CodeID']

    st.write(f"{record_codeID_label}{codeID}")

    # Step 2: Validate / fetch record document
    record_entry = find_all_records({"CodeID": codeID})

    # Step 3: If record exists, display record details
    if len(record_entry) == 1:

        # Step 3a: Display record creation date
        st.write(f"{record_createdAt_label}{record_entry[0]['CreatedAt']}")

        # Step 3b: Display record content formatting
        st.write(
            f"{record_itemID_label}{record_entry[0]['ItemID']}")

        # Step 3c: Display record description formatting
        st.write(f"{record_item_label}{record_entry[0]['Item']}")

        # Step 3d: Display record status formatting
        st.write(f"{record_action_label}{record_entry[0]['Action']}")

        if status:
            # Step 3c: Action button to open full rule view (and show product count)
            st.button(
                f"This Item has {len(find_record_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(f"[{collection_name}] Invalid Input: Item Not Found")
