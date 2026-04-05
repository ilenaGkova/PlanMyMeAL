from AdministrativeFunctions import open_new_code
from Mongo_Connection import Request, User
from MongoDB_General_Functions import generate_code, get_now, role_table, get_products
from Record import create_record
from typing import Optional
import streamlit as st

# Item Description Labels
request_codeID_label = "Request CodeID: "
request_createdAt_label = "Creation Date: "
request_content_label = "Information: "
request_description_label = "Description: "
request_status_label = "Status: "

# Valid Status Values
status_table = {"Pending", "Ongoing", "Closed"}

# Collection Tag
collection_name = "Request"


def return_all_requests(query: Optional[dict] = None):
    # 1) Handle default query
    # If no query is provided, return all entries in the collection
    if query is None:
        query = {}

    # 2) Fetch matching documents from the database
    return list(Request.find(query))


def validate_request(codeID: str):
    # 1) Validate input presence
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Fetch matching entries by CodeID
    item = return_all_requests({'CodeID': codeID})

    # 3) Result validation
    # No match found.
    if len(item) == 0:
        return f"[{collection_name}] Invalid Input: No Item Found", None, False

    # Single valid match focund.
    elif len(item) == 1:
        return f"[{collection_name}] Valid Input: Item Found", item, True

    # More than one match found (data integrity issue).
    else:
        message, entry, status = create_request(f"[{collection_name}]Multiple Items Found", codeID, get_now())
        return f"[{collection_name}] Invalid Input: Multiple Items Found" + message, item, False


def make_request(codeID: str, createdAt: str, description: str, created: str, itemID: str, status: str):
    # 1) Construct the request document
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'When': created,
        'For': itemID,
        'Description': description,
        'Status': status
    }


def create_request(description: str, itemID: str, createdWhen: str):
    # 1) Validate required input fields
    if description is None or not description.strip():
        return f"[{collection_name}] Invalid Input: No String Detected", None, False

    # 2) Prevent duplicate pending requests for the same item + description
    if len(return_all_requests({'For': itemID, 'Description': description, 'Status': "Pending"})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 3) Generate a unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Request, collection_name)

    # 4) Stop if CodeID generation failed
    if not codeID_status:
        return f"[{collection_name}] " + codeID_message, None, False

    # 5) Build the new request document
    new_entry = make_request(codeID, get_now(), description, createdWhen, itemID, "Pending")

    # 6) Insert the new request into the database
    Request.insert_one(new_entry)
    message = f"[{collection_name}] Valid Output: Entry Generated"

    # 7) Create record log
    record_message, record, record_status = create_record(Request, "Create", codeID, new_entry, codeID, False)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 8) Rollback on record failure
    Request.delete_one({'CodeID': codeID})
    return message + " " + record_message, new_entry, False


def find_request_products(codeID: str):
    # 1) Input guard
    # If no request ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this rule
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'RequestID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def update_request(codeID: str, status: str, userID: str):
    # 1) Validate the requesting user
    entry = User.find_one({'CodeID': userID})
    if not entry:
        return f"[{collection_name}] Invalid Input: User Not Found", entry, False

    # 2) Validate admin privileges (as implemented)
    if entry['Role'] != role_table["Administrator"]:
        return f"[{collection_name}] Invalid Input: User has no Admin Privileges", entry, False

    # 3) Validate the target request by CodeID
    item_message, entry, item_status = validate_request(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Validate the requested new status value
    if status not in status_table:
        return f"[{collection_name}] Invalid Input: No Appropriate String Detected", entry, False

    # 5) Prevent updates to closed requests
    if entry[0]['Status'] == "Closed":
        return f"[{collection_name}] Invalid Input: Request Closed", entry, False

    # 6) Build the updated request document
    new_entry = make_request(codeID, entry[0]['CreatedAt'], entry[0]['Description'], entry[0]['When'], entry[0]['For'],
                             status)

    # 7) Update the request in the database
    Request.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 8) Create a record log for the update
    record_message, record, record_status = create_record(Request, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 9) Roll back the update if record creation fails
    old_entry = make_request(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['Description'],
        entry[0]['When'],
        entry[0]['For'],
        entry[0]['Status']
    )
    Request.update_one({"CodeID": codeID}, {"$set": old_entry})
    return message + " " + record_message, old_entry, False


def request_information(outcome, pointer: int, status: bool):
    # Step 1: Section header + basic request reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    codeID = outcome[pointer]['CodeID']

    st.write(f"{request_codeID_label}{codeID}")

    # Step 2: Validate / fetch request document
    request_message, request_entry, request_status = validate_request(codeID)

    # Step 3: If request exists, display request details
    if request_status:
        # Step 3a: Display request creation date
        st.write(f"{request_createdAt_label}{request_entry[0]['CreatedAt']}")

        # Step 3b: Display request content formatting
        st.write(
            f"{request_content_label}Request was made on {request_entry[0]['When']} for item {request_entry[0]['For']}")

        # Step 3c: Display request description formatting
        st.write(f"{request_description_label}{request_entry[0]['Description']}")

        # Step 3d: Display request status formatting
        st.write(f"{request_status_label}{request_entry[0]['Status']}")

        if status:
            # Step 3c: Action button to open full rule view (and show product count)
            st.button(
                f"This Item has {len(find_request_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(request_message)
