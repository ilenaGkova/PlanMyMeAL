from AdministrativeFunctions import open_new_code
from Mongo_Connection import Rule
from Request import create_request
from User import validate_user, user_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
import streamlit as st

# Appropriate values for Per
per_table = {"Day", "Week", "Month", "Year"}

# Item Description Labels for Item as Foreign Key
rule_codeID_label = "Rule CodeID: "
rule_createdAt_label = "Creation Date: "
rule_frequency_label = "Frequency: "

# Collection Tag
collection_name = "Rule"

# Store the current signed-in user's CodeID
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def return_all_rules(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(Rule.find(query))


def validate_rule(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_rules({'CodeID': codeID})

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


def make_rule(codeID: str, createdAt: str, userID: str, quantity: int, per: str):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'Quantity': quantity,
        'Per': per
    }


def create_rule(quantity: int, per: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate input fields
    # Quantity must be a positive integer
    if not isinstance(quantity, int) or quantity is None or quantity <= 0:
        return f"[{collection_name}] Invalid Input: No Quantity Detected", None, False

    # Per must be a valid value from the allowed table
    if per is None or per not in per_table:
        return f"[{collection_name}] Invalid Input: No Valid Type Detected", None, False

    # 3) Uniqueness check
    # Rule combination (Quantity + Per) must be unique
    if len(return_all_rules({'Quantity': quantity, 'Per': per, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 4) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Rule, collection_name)

    if codeID_status:
        # 5) Build new document
        new_entry = make_rule(codeID, get_now(), userID, quantity, per)

        # 6) Insert into database
        Rule.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 7) Create record log
        record_message, record, record_status = create_record(Rule, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 8) Rollback on record failure
        Rule.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 9) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_rule_products(codeID: str):
    # 1) Input guard
    # If no rule ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this rule
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'RuleID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_rule(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the rule is not referenced by any other entries
    entry = find_rule_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target rule
    # Ensure the rule to be deleted exists and is uniquely identified
    item_message, entry, item_status = validate_rule(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator of this rule
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    Rule.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    record_message, record, record_status = create_record(Rule, "Delete", codeID, entry[0], userID)
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # Restore the deleted rule entry
    new_entry = make_rule(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Quantity'],
        entry[0]['Per']
    )
    Rule.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_rule(codeID: str, quantity: int, per: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate target rule
    # Ensure the rule to be updated exists and is uniquely identified
    item_message, entry, item_status = validate_rule(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 3) Ownership check
    # Ensure the requesting user is the creator of this rule
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 4) Validate input fields
    # Quantity must be a positive integer
    if not isinstance(quantity, int) or quantity is None or quantity <= 0:
        return f"[{collection_name}] Invalid Input: No Quantity Detected", entry, False

    # 'per' must be a valid value from the allowed table
    if per is None or per not in per_table:
        return f"[{collection_name}] Invalid Input: No Valid Type Detected", entry, False

    # 5) Uniqueness check
    # Rule combination (Quantity + Per) must be unique (unless unchanged for this entry)
    key_entry = return_all_rules({'Quantity': quantity, 'Per': per, 'UserID': entry[0]['UserID']})
    if len(key_entry) >= 1 and (per != entry[0]['Per'] or quantity != entry[0]['Quantity']):
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 6) Build updated document
    # Preserve CreatedAt and apply new values
    new_entry = make_rule(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], quantity, per)

    # 7) Update database entry
    Rule.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 8) Create record log
    record_message, record, record_status = create_record(Rule, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 9) Rollback on record failure
    # Restore the previous rule entry values
    new_entry = make_rule(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['Quantity'],
        entry[0]['Per']
    )
    Rule.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def convert_ID_to_content():
    # Step 1: Fetch all rule entries from the database
    table = None
    if st.session_state.current_user is not None:
        item_message, entry, item_status = validate_user(st.session_state.current_user)
        if item_status and entry[0]['Role'] == role_table["Plain User"]:
            table = return_all_rules({'UserID': st.session_state.current_user})
    if table is None:
        table = return_all_rules()

    # Step 2: Initialize lookup table and selectbox options
    #         - lookup maps display label -> CodeID
    #         - options is a plain list for UI components
    #         Both include a None option as the default
    lookup = {None: None}
    options = [None]

    # Step 3: Build label-to-ID mapping and UI options list
    for entry in table:
        label = f"{entry['Quantity']} per {entry['Per']}"
        lookup[label] = entry['CodeID']
        options.append(label)

    # Step 4: Return both structures so UI and logic stay in sync
    return lookup, options


def rule_id_to_index(rule_id, lookup, options):
    # Step 1: If no rule is associated, default to the None option
    if rule_id is None:
        return 0

    # Step 2: Find the display label that corresponds to the stored CodeID
    for label, code_id in lookup.items():
        if code_id == rule_id:
            # Step 3: Return the index of that label in the options list
            #         (used by Streamlit selectbox)
            try:
                return options.index(label)
            except ValueError:
                # Step 4: Fallback in case the label is missing from options
                return 0

    # Step 5: If no matching CodeID was found, fall back to None
    return 0


def rule_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Section header + basic rule reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['RuleID']
    else:
        codeID = None

    st.write(f"{rule_codeID_label}{codeID}")

    # Step 2: Validate / fetch rule document
    rule_message, rule_entry, rule_status = validate_rule(codeID)

    # Step 3: If rule exists, display rule details
    if rule_status:
        # Step 3a: Display rule creation date
        st.write(f"{rule_createdAt_label}{rule_entry[0]['CreatedAt']}")

        # Step 3b: Display rule frequency / quantity formatting
        st.write(f"{rule_frequency_label}{rule_entry[0]['Quantity']} per {rule_entry[0]['Per']}")

        if status:
            # Step 3c: Action button to open full rule view (and show product count)
            st.button(
                f"This Item has {len(find_rule_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(rule_message)


def full_entry_rule(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display rule-related information
    #         - Item details (rule-specific fields)
    #         - Creator/user information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render rule/item information in the first column
    with item_column:
        with st.container(border=True):
            rule_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")


def select_ruleID(entry, pointer: int):
    # Step 1: Display the rule label (used as section context / caption)
    st.write(rule_frequency_label)

    # Step 2: Fetch rule lookup table and plain options list
    #         - frequency_table: label -> CodeID
    #         - frequency_list:  [None, "X per Y", ...]
    frequency_table, frequency_list = convert_ID_to_content()

    # Step 3: Render selectbox for rule selection
    #         - Pre-selects the current rule if entry exists
    #         - Falls back to None if no rule is attached
    frequency = st.selectbox(
        rule_frequency_label,
        frequency_list,
        index=rule_id_to_index(
            entry.get("RuleID") if entry else None,
            frequency_table,
            frequency_list
        ),
        label_visibility="collapsed",
        key=f"ruleID_button_{pointer}",
    )

    # Step 4: Translate selected display label back into the stored CodeID
    ruleID = frequency_table.get(frequency)

    # Step 5: Return the resolved rule CodeID (or None)
    return ruleID
