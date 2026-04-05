import random
from datetime import datetime
from Mongo_Connection import User, Record, UnitType, Rule, Ingredient, Category, MealType, Day, Meal, MealCombination, \
    Schedule
import pytz

# Roles a User can be assigned
role_table = {
    "Plain User": "User",
    "Administrator": "Admin"
}


# Code Letters and the assigned collection
table_codes = {
    "User": "US",
    "UnitType": "UT",
    "Ingredient": "IN",
    "Record": "RE",
    "Category": "CA",
    "Day": "DA",
    "MealCombination": "MC",
    "Rule": "RU",
    "Meal": "ME",
    "Schedule": "SC",
    "MealType": "MT",
    "Request": "RQ"
}


def generate_code(collection, collection_string: str):
    # 1) Validate collection identifier
    # Ensure the provided collection name is registered for code generation
    if collection_string not in table_codes:
        return "Invalid Input: Collection Not Found", None, False

    # 2) Initialize attempt counter
    # Limit retries to avoid infinite loops in case of collisions
    attempt_count = 0

    # 3) Attempt code generation
    # Generate random codes until a unique one is found or limit is reached
    while attempt_count < 100:
        # Build candidate CodeID using the collection prefix
        new_code = f"{table_codes[collection_string]}{random.randrange(100_000_000):08d}"

        # Check for uniqueness in the target collection
        if not collection.find_one({"CodeID": new_code}) and not Record.find_one({'ItemID': new_code}):
            return "Valid Output: Code ID Created", new_code, True

        # Collision detected, try again
        attempt_count += 1

    # 4) Exhaustion failure
    # No unique CodeID could be generated within the attempt limit
    return "Invalid Output: Code ID Not Created", None, False


# List of collection with foreign keys
product_table = {
    "User": [User, UnitType, Rule, Ingredient, Category, MealType, Day, Meal, MealCombination, Schedule],
    "UnitType": [Ingredient],
    "Ingredient": [MealCombination],
    "Record": [],
    "Category": [Meal],
    "Day": [Schedule],
    "MealCombination": [],
    "Rule": [Ingredient, Meal, Category, MealType],
    "Meal": [Schedule, MealCombination],
    "Schedule": [],
    "MealType": [Schedule],
    "Request": []
}


def get_products(collection_string: str):
    # 1) Validate collection key
    # Ensure the collection is registered as having dependent product collections
    if collection_string not in product_table:
        return []

    # 2) Return dependent collections
    # Used for dependency checks before delete operations
    return product_table[collection_string]


def get_now():
    # 1) Define timezone
    # All timestamps are stored in Greece (Europe/Athens) time
    greece_tz = pytz.timezone('Europe/Athens')

    # 2) Get current localized time
    # Ensures consistent timestamps across the system
    now = datetime.now(greece_tz)

    # 3) Format timestamp
    # Stored as a human-readable string
    return now.strftime("%Y-%m-%d %H:%M:%S")
