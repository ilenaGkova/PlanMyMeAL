from AdministrativeFunctions import open_new_code
from Mongo_Connection import User
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st
from Request import create_request

# Sign Up Form questions
sign_up_username_question = "Enter a unique Username here"

# Sign In Form questions
sign_in_username_question = "Enter your Username here"
sign_in_passcode_question = "Enter your CodeID here"

# Change Username Form questions
old_username_question = "Enter your old Username here"
new_username_question = "Enter your new Username here"

# Item Description Labels
user_codeID_label = "User CodeID: "
user_createdAt_label = "Creation Date: "
user_username_label = "Username: "
user_status_label = "Account Status: "
user_role_label = "Role: "

# User Statuses based on True or False
user_status = {
    True: "Active",
    False: "Inactive"
}

# Collection Tag
user_collection_name = "User"


def return_all_users(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(User.find(query))


def validate_user(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{user_collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_users({'CodeID': codeID})

    # 3) Result validation
    # No match found
    if len(item) == 0:
        return f"[{user_collection_name}] Invalid Input: No Item Found", None, False

    # Single valid match found
    elif len(item) == 1:
        return f"[{user_collection_name}] Valid Input: Item Found", item, True

    # More than one match found (data integrity issue)
    else:
        message, entry, status = create_request(f"[{user_collection_name}]Multiple Items Found", codeID, get_now())
        return f"[{user_collection_name}] Invalid Input: Multiple Items Found" + message, item, False


def make_user(codeID: str, createdAt: str, userID: str, username: str, status: bool = True,
              role: str = role_table["Plain User"]):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'Username': username,
        'Status': status,
        'Role': role
    }


def create_admin(username: str):
    # 1) Validate input fields
    # Username must be a non-empty string
    if username is None or not username.strip():
        return f"[{user_collection_name}] Invalid Input: No String Detected", None, False

    # 2) Uniqueness check
    # Username must be unique across the collection
    if len(return_all_users({'Username': username})) >= 1:
        return f"[{user_collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 3) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(User, user_collection_name)

    if codeID_status:
        # 4) Since userID is None, this is a self-created / initial user.
        userID = codeID

        # 5) Build new document
        new_entry = make_user(codeID, get_now(), userID, username, True, role_table["Administrator"])

        # 6) Insert into database
        User.insert_one(new_entry)
        message = f"[{user_collection_name}] Valid Output: Entry Generated"

        # 7) Create record log
        record_message, record, record_status = create_record(User, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 8) Rollback on record failure
        User.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 9) Code generation failure
    return f"[{user_collection_name}] " + codeID_message, None, False


def create_user(username: str, userID: str = None, role: str = role_table["Plain User"]):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, entry, user_status_create = validate_user(userID)
    if userID is not None and not user_status_create:
        return user_message, entry, user_status_create

    # 1b) Check Role input
    # Only and Admin can assign admin role to a user
    if role == role_table["Administrator"] and entry[0]['Role'] != role_table["Administrator"]:
        return f"[{user_collection_name}] Invalid Input: User Can't Assign Admin Status", entry, False

    # 2) Validate input fields
    # Username must be a non-empty string
    if username is None or not username.strip():
        return f"[{user_collection_name}] Invalid Input: No String Detected", None, False

    if role != role_table["Administrator"] and role != role_table["Plain User"]:
        return f"[{user_collection_name}] Invalid Input: Role Value not Valid", entry, False

    # 3) Uniqueness check
    # Username must be unique across the collection
    if len(return_all_users({'Username': username})) >= 1:
        return f"[{user_collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 4) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(User, user_collection_name)

    if codeID_status:
        # If userID is None, this is a self-created / initial user.
        if userID is None:
            userID = codeID

        # 5) Build new document
        new_entry = make_user(codeID, get_now(), userID, username, True, role)

        # 6) Insert into database
        User.insert_one(new_entry)
        message = f"[{user_collection_name}] Valid Output: Entry Generated"

        # 7) Create record log
        record_message, record, record_status = create_record(User, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 8) Rollback on record failure
        User.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 9) Code generation failure
    return f"[{user_collection_name}] " + codeID_message, None, False


def find_user_products(codeID: str):
    # 1) Input guard
    # If no user ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this User
    products = []
    for collection in get_products(user_collection_name):
        data = list(collection.find({'UserID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_user(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, entry, user_status_create = validate_user(userID)
    if not user_status_create:
        return user_message, entry, user_status_create

    # 2) Dependency check
    # Ensure the user is not referenced by any other entries
    entry = find_user_products(codeID)
    if len(entry) >= 1:
        return f"[{user_collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target user
    # Ensure the user to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_user(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this user entry
    if entry[0]['UserID'] != userID and entry[0]['Role'] == role_table["Plain User"]:
        return f"[{user_collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    User.delete_one({'CodeID': codeID})
    message = f"[{user_collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(User, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted user entry
    new_entry = make_user(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Username'],
        entry[0]['Status'],
        entry[0]['Role']
    )
    User.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_user(codeID: str, username: str, userID: str, status: bool, role: str = role_table["Plain User"]):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, entry, user_status_create = validate_user(userID)
    if not user_status_create:
        return user_message, entry, user_status_create

    # 1b) Check Role input
    # Only and Admin can assign admin role to a user
    if role == role_table["Administrator"] and entry[0]['Role'] != role_table["Administrator"]:
        return f"[{user_collection_name}] Invalid Input: User Can't Assign Admin Status", entry, False

    # 2) Validate target user
    # Ensure the user to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_user(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 3) Ownership check
    # Ensure the requesting user is the creator of this user entry
    if entry[0]['UserID'] != userID and entry[0]['Role'] == role_table["Plain User"]:
        return f"[{user_collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 4) Validate input fields
    # Username must be a non-empty string
    if username is None or not username.strip():
        return f"[{user_collection_name}] Invalid Input: No String Detected", entry, False

    if role != role_table["Administrator"] and role != role_table["Plain User"]:
        return f"[{user_collection_name}] Invalid Input: Role Value not Valid", entry, False

    if isinstance(status, bool):
        return f"[{user_collection_name}] Invalid Input: Status Value not Valid", entry, False

    # 5) Uniqueness check
    # Username must be unique (unless unchanged for this entry)
    key_entry = return_all_users({'Username': username})
    if len(key_entry) >= 1 and username != entry[0]['Username']:
        return f"[{user_collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 6) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_user(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], username, status, role)

    # 7) Update database entry
    User.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{user_collection_name}] Valid Output: Entry Updated"

    # 8) Create record log
    record_message, record, record_status = create_record(User, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 9) Rollback on record failure
    # Restore the previous user entry values
    new_entry = make_user(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Username'],
        entry[0]['Status'],
        entry[0]['Role']
    )
    User.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def user_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Title + basic user reference
    st.subheader(f"{user_collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['UserID']
    else:
        codeID = None

    st.write(f"{user_codeID_label}{codeID}")

    # Step 2: Validate / fetch creator user document
    creator_message, creator_entry, creator_status = validate_user(codeID)

    # Step 3: If user exists, display creator details
    if creator_status:

        # Step 3a: Display user creation date
        st.write(f"{user_createdAt_label}{creator_entry[0]['CreatedAt']}")

        # Step 3b: Display username
        st.write(f"{user_username_label}{creator_entry[0]['Username']}")

        # Step 3c: Display account status (mapped label)
        st.write(f"{user_status_label}{user_status[creator_entry[0]['Status']]}")

        # Step 3d: Display role (mapped label)
        st.write(f"{user_role_label}{creator_entry[0]['Role']}")

        if status:
            # Step 3e: Action button to open full user view (and show product count)
            st.button(
                f"This Item has {len(find_user_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{user_collection_name}_{pointer}_{use}"
            )

    else:

        # Step 5: Validation failed; display message
        st.write(creator_message)


def full_entry_user(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display user-related information
    #         - Item details (user-specific fields)
    #         - Creator/user information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render user/item information in the first column
    with item_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")
