from AdministrativeFunctions import open_new_code
from Mongo_Connection import Schedule
from Request import create_request
from User import validate_user, user_information
from Day import validate_day, get_date, day_information
from Meal import validate_meal, meal_information
from MealType import validate_meal_type, meal_type_information
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional
from datetime import date
import streamlit as st

# Item Description Labels
schedule_codeID_label = "Schedule CodeID: "
schedule_createdAt_label = "Creation Date: "
schedule_outcome_label = "Outcome: "
schedule_notes_label = "Notes: "

# Valid Outcome Values tagged with the meaning of each value
outcome_table_with_tags = {
    "Upcoming": ["Upcoming"],
    "Current": ["Pending"],
    "Locked": ["Completed Correctly", "Completed Incorrectly", "Skipped"]
}

# Valid Outcome Values
outcome_table = [item for sublist in outcome_table_with_tags.values() for item in sublist]

# Collection Tag
collection_name = "Schedule"


def return_all_schedules(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all Schedule entries.
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all Schedule documents matching the query.
    return list(Schedule.find(query))


def validate_schedule(codeID: str):
    # 1) Input presence validation
    # Ensure a Schedule CodeID was provided.
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch Schedule entries matching the CodeID.
    item = return_all_schedules({'CodeID': codeID})

    # 3) Result validation
    # No match found.
    if len(item) == 0:
        return f"[{collection_name}] Invalid Input: No Item Found", None, False

    # Single valid match found.
    elif len(item) == 1:
        return f"[{collection_name}] Valid Input: Item Found", item, True

    # More than one match found (data integrity issue).
    else:
        message, entry, status = create_request(f"[{collection_name}]Multiple Items Found", codeID, get_now())
        return f"[{collection_name}] Invalid Input: Multiple Items Found" + message, item, False


def make_schedule(codeID: str, createdAt: str, userID: str, mealTypeID: str, mealID: str, dayID: str, outcome: str,
                  notes: str = None):
    # 1) Document construction
    # Build and return the Schedule document for database insertion or update.
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'MealTypeID': mealTypeID,
        'MealID': mealID,
        'DayID': dayID,
        'Outcome': outcome,
        'Notes': notes
    }


def create_schedule(userID: str, mealTypeID: str, mealID: str, dayID: str, outcome: str = "Upcoming",
                    notes: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Ensure the referenced MealType, Day, and Meal exist.
    meal_type_message, entry, meal_type_status = validate_meal_type(mealTypeID)
    if not meal_type_status:
        return meal_type_message, entry, meal_type_status

    day_message, entry, day_status = validate_day(dayID)
    if not day_status:
        return day_message, entry, day_status

    meal_message, entry, meal_status = validate_meal(mealID)
    if not meal_status:
        return meal_message, entry, meal_status

    # 2b) Access / ownership check for Meal
    # Prevent users from creating Schedule entries for Meals they do not own.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[Meal] Invalid Input: User can't Access this Meal", entry, False

    # 3) Validate input fields
    # Outcome is required and must be one of the allowed status values.
    if outcome is None or outcome not in outcome_table:
        return f"[{collection_name}] Invalid Input: Invalid Outcome Value", None, False

    # 4) Uniqueness check
    # Prevent duplicate Schedule entries for the same user, meal type, and day.
    # (A user can only have one scheduled meal per MealType per Day.)
    if len(return_all_schedules({'UserID': userID, 'MealTypeID': mealTypeID, 'DayID': dayID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(Schedule, collection_name)

    if codeID_status:
        # 6) Build new document
        new_entry = make_schedule(codeID, get_now(), userID, mealTypeID, mealID, dayID, outcome, notes)

        # 7) Insert into database
        Schedule.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 8) Create record log
        # Log the created Schedule entry using the inserted document snapshot.
        record_message, record, record_status = create_record(
            Schedule, "Create", codeID, new_entry, userID
        )
        if record_status:
            return message + " " + record_message, new_entry, True

        # 9) Rollback on record failure
        # If record creation fails, remove the inserted Schedule entry
        # to keep database state and audit log consistent.
        Schedule.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 10) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_schedule_products(codeID: str):
    # 1) Input guard
    # If no Schedule CodeID is provided, there can be no dependent entries.
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all collections that may reference a Schedule entry
    # (as defined by get_products(collection_name)) for documents
    # that store this Schedule's CodeID as a foreign key.
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'ScheduleID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    # Used to block deletion of Schedule entries that are still referenced elsewhere.
    return products


def delete_schedule(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the Schedule entry is not referenced by any other collections.
    # This is a safety check to prevent deleting entries that are still in use
    # and to future-proof against new references being added later.
    entry = find_schedule_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target Schedule
    # Ensure the Schedule entry to be deleted exists and is uniquely identified.
    item_message, entry, item_status = validate_schedule(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator/owner of this Schedule entry.
    # Users may only delete Schedule entries they created.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    # Remove the Schedule document identified by CodeID.
    Schedule.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    # Log the deletion using the pre-delete snapshot of the Schedule entry.
    record_message, record, record_status = create_record(
        Schedule, "Delete", codeID, entry[0], userID
    )
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # If record creation fails, restore the deleted Schedule entry
    # to keep database state and audit log consistent.
    new_entry = make_schedule(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['MealTypeID'],
        entry[0]['MealID'],
        entry[0]['DayID'],
        entry[0]['Outcome'],
        entry[0]['Notes']
    )
    Schedule.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_schedule(codeID: str, userID: str, mealTypeID: str, mealID: str, dayID: str, outcome: str,
                    notes: str = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Ensure the referenced MealType, Day, and Meal exist.
    meal_type_message, meal_type_entry, meal_type_status = validate_meal_type(mealTypeID)
    if not meal_type_status:
        return meal_type_message, meal_type_entry, meal_type_status

    day_message, day_entry, day_status = validate_day(dayID)
    if not day_status:
        return day_message, day_entry, day_status

    meal_message, meal_entry, meal_status = validate_meal(mealID)
    if not meal_status:
        return meal_message, meal_entry, meal_status

    # 2b) Access / ownership check for Meal
    # Prevent users from updating Schedule entries linked to Meals they do not own.
    if meal_entry[0]['UserID'] != userID:
        return f"[Meal] Invalid Input: User can't Access this Meal", meal_entry, False

    # 3) Validate target Schedule
    # Ensure the Schedule entry to be updated exists and is uniquely identified.
    item_message, entry, item_status = validate_schedule(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) If trying to change the meal, block it if the Day is in the past
    if mealTypeID != entry[0]["MealTypeID"] or dayID != entry[0]["DayID"] or mealID != entry[0]["MealID"]:
        conversion_message, day_date, conversion_outcome = get_date(dayID)
        today = date.today()
        if day_date < today:
            return f"[{collection_name}] Invalid Input: Cannot change Meal for a past day", meal_entry, False

    # 4b) Ownership check
    # Ensure the requesting user is the creator/owner of this Schedule entry.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Validate input fields
    # Outcome is required and must be one of the allowed status values.
    # Note: This module defines 'status', so ensure the validation uses the same set.
    if outcome is None or outcome not in outcome_table:
        return f"[{collection_name}] Invalid Input: Invalid Outcome Value", None, False

    # 6) Uniqueness check
    # Prevent duplicate Schedule entries for the same user, meal type, and day.
    # (A user can only have one scheduled item per MealType per Day.)
    key_entry = return_all_schedules(
        {'UserID': userID, 'MealTypeID': mealTypeID, 'DayID': dayID, 'CodeID': {'$ne': codeID}})
    if len(key_entry) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 7) Build updated document
    # Preserve CreatedAt and apply the new field values.
    new_entry = make_schedule(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], mealTypeID, mealID, dayID, outcome,
                              notes)

    # 8) Update database entry
    # Apply the updated values to the existing Schedule document.
    Schedule.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 9) Create record log
    # Log the updated state of the Schedule entry.
    record_message, record, record_status = create_record(Schedule, "Update", codeID, new_entry, userID)
    if record_status:
        return message + " " + record_message, new_entry, True

    # 10) Rollback on record failure
    # If record creation fails, restore the previous Schedule values
    # to keep database state and audit log consistent.
    new_entry = make_schedule(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['MealTypeID'],
        entry[0]['MealID'],
        entry[0]['DayID'],
        entry[0]['Outcome'],
        entry[0]['Notes']
    )
    Schedule.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def schedule_information(outcome, pointer: int, status: bool, use: str = "Primary"):
    # Step 1: Section header + basic schedule reference
    st.subheader(f"{collection_name} Information")

    # Step 1a: Find attribute to find entry
    if use == "Primary":
        codeID = outcome[pointer]['CodeID']
    elif use == "Secondary":
        codeID = outcome[pointer]['MealTypeID']
    else:
        codeID = None

    st.write(f"{schedule_codeID_label}{codeID}")

    # Step 2: Validate / fetch schedule document
    schedule_message, schedule_entry, schedule_status = validate_schedule(codeID)

    # Step 3: If schedule exists, display schedule details
    if schedule_status:
        # Step 3a: Display schedule creation date
        st.write(f"{schedule_createdAt_label}{schedule_entry[0]['CreatedAt']}")

        # Step 3b: Display schedule outcome
        st.write(f"{schedule_outcome_label}{schedule_entry[0]['Outcome']}")

        # Step 3c: Display schedule notes
        st.write(f"{schedule_notes_label}{schedule_entry[0]['Notes']}")

        if status:
            # Step 3d: Action button to open full schedule view (and show product count)
            st.button(
                f"This Item has {len(find_schedule_products(codeID))} Product(s)",
                use_container_width=True,
                on_click=open_new_code,
                args=[codeID],
                key=f"open_{collection_name}_{pointer}"
            )

    else:
        # Step 4: Validation failed; display message
        st.write(schedule_message)


def full_entry_schedule(outcome, pointer: int, status: bool = False):
    # Step 1: Create a three-column layout to display schedule-related information
    #         - Item details (day-specific fields)
    #         - Creator/user information
    #         - Meal Type information
    #         - Meal information
    #         - Day information
    item_column, creator_column = st.columns(2, vertical_alignment="center")

    # Step 2: Render schedule/item information in the first column
    with item_column:
        with st.container(border=True):
            schedule_information(outcome, pointer, status, "Primary")

    # Step 3: Render creator / user metadata in the second column
    with creator_column:
        with st.container(border=True):
            user_information(outcome, pointer, status, "Secondary")

    # Step 4: Render Meal metadata in the second column
    with st.container(border=True):
        meal_information(outcome, pointer, status, "Secondary")

    meal_type_column, day_column = st.columns(2, vertical_alignment="center")

    # Step 5: Render Meal Type metadata in the first column
    with meal_type_column:
        with st.container(border=True):
            meal_type_information(outcome, pointer, status, "Secondary")

    # Step 6: Render day metadata in the third column
    with day_column:
        with st.container(border=True):
            day_information(outcome, pointer, status, "Secondary")
