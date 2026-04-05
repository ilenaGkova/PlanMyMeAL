import random
from datetime import datetime
from typing import List, Dict, Any
from User import return_all_users
import streamlit as st

# Do not include statement
do_not_include = "Do Not Include"


def generate_animal_username(max_attempts=100):
    # Step 1: Initialize attempt counter
    attempt_count = 0

    # Step 2: Define word pools used to construct the username
    animals = [
        'Lion', 'Tiger', 'Elephant', 'Giraffe', 'Zebra',
        'Panda', 'Koala', 'Kangaroo', 'Cheetah', 'Penguin'
    ]
    adjectives = [
        'Fluffy', 'Mighty', 'Sneaky', 'Grumpy', 'Mysterious',
        'Sleepy', 'Bold', 'Spiky', 'Shiny', 'Wild'
    ]

    # Step 3: Attempt username generation up to the maximum allowed attempts
    while attempt_count < max_attempts:

        # Step 3a: Generate a candidate username
        username = (
            f"{random.choice(adjectives)}"
            f"{random.choice(animals)}"
            f"#{random.randint(1000, 9999)}"
        )

        # Step 3b: Check if the username already exists in the User collection
        if len(return_all_users({"Username": username})) == 0:
            # Step 3c: Return the username if it is unique
            return username

        # Step 3d: Increment attempt counter and retry
        attempt_count += 1

    # Step 4: Fail gracefully if no unique username is found
    return "Please reload the page"


def return_table(attribute: str, entries: List[Dict[str, Any]], first_options=None, is_date: bool = False):
    # Step 1: Apply default "first options" if none are provided
    if first_options is None:
        first_options = [do_not_include, None]

    # Step 2: Collect unique non-empty values for the selected attribute
    values = {
        entry.get(attribute)
        for entry in entries
        if entry.get(attribute)
    }

    # Step 3: Sort values
    # - If date-based, sort chronologically
    # - Otherwise, sort alphabetically as strings
    if is_date:
        sorted_values = sorted(values, key=lambda x: datetime.fromisoformat(x))
    else:
        sorted_values = sorted(values, key=lambda x: str(x))

    # Step 4: Return options list (first options first, then sorted values)
    return first_options + sorted_values


def search_by_button(title: str, entries, collection: str, attribute: str, action: str):
    st.write(title)

    item = st.selectbox(
        title,
        entries,
        index=0,
        label_visibility="collapsed",
        key=f"{action}_{collection}_{attribute}",
    )

    return item


def build_query(selections: dict):
    # Step 1: Initialize empty Mongo query
    query = {}

    # Step 2: Iterate over selected fields and values
    for field, value in selections.items():

        # Step 2a: Skip placeholder option ("Do Not Include")
        if value == do_not_include:
            continue

        # Step 2b: Include the selection as a query filter (including None)
        query[field] = value

    # Step 3: Return finalized query dict
    return query


def create_entry_user(title: str, collection: str, current_user: str):
    # Step 1: Render a read-only text input for the user field
    # This displays the currently authenticated user so it can be
    # attached to the new entry without allowing edits.
    item = st.text_input(
        title,  # Step 1a: Field label shown in the UI
        value=current_user,  # Step 1b: Pre-fill with current user ID
        key=f"add_{collection}_userID",  # Step 1c: Unique session key per collection
        disabled=True  # Step 1d: Prevent user modification
    )

    # Step 2: Return the user identifier
    # Used by the calling function when constructing the final entry payload
    return item
