from Mongo_Connection import MealCombination
from Request import create_request
from User import validate_user
from Ingredient import validate_ingredient, validate_ingredient_deep
from Meal import validate_meal
from MongoDB_General_Functions import generate_code, get_now, get_products, role_table
from Record import create_record
from typing import Optional

# Item Description Labels for Item as Foreign Key
meal_combination_codeID_label = "Meal Combination CodeID: "
meal_combination_createdAt_label = "Creation Date: "
meal_combination_quantity_label = "Quantity: "

# Collection Tag
collection_name = "MealCombination"


def return_all_meal_combinations(query: Optional[dict] = None):
    # 1) Default query handling
    # If no query is provided, return all entries in collection
    if query is None:
        query = {}

    # 2) Database fetch
    # Retrieve all user documents matching the query
    return list(MealCombination.find(query))


def validate_meal_combination(codeID: str):
    # 1) Input presence validation
    # Ensure an ID was provided
    if codeID is None:
        return f"[{collection_name}] Invalid Input: No Item Inserted", None, False

    # 2) Database lookup
    # Fetch entries matching the CodeID
    item = return_all_meal_combinations({'CodeID': codeID})

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


def make_meal_combination(codeID: str, createdAt: str, userID: str, ingredientID: str, mealID: str, quantity: float = 0):
    # 1) Document construction
    # Build and return the user document for database insertion or update
    return {
        'CodeID': codeID,
        'CreatedAt': createdAt,
        'UserID': userID,
        'IngredientID': ingredientID,
        'MealID': mealID,
        'Quantity': quantity
    }


def create_meal_combination(userID: str, ingredientID: str, mealID: str, quantity: float = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Ensure the referenced Ingredient and Meal exist.
    # Note: Ingredients may be universal; we do NOT enforce ingredient ownership here.
    ingredient_message, entry, ingredient_status = validate_ingredient(ingredientID)
    if not ingredient_status:
        return ingredient_message, entry, ingredient_status

    meal_message, entry, meal_status = validate_meal(mealID)
    if not meal_status:
        return meal_message, entry, meal_status

    # 2b) Access / ownership check for Meal
    # Prevent users from linking combinations to meals they do not own.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[Meal] Invalid Input: User can't Access this Meal", entry, False

    # 3) Validate input fields
    # Quantity is required and must be a positive integer.
    if not isinstance(quantity, float) or quantity <= 0:
        return f"[{collection_name}] Invalid Input: Quantity must be a positive integer", None, False

    # 4) Uniqueness check
    # Prevent duplicate MealCombination entries for the same (UserID, MealID, IngredientID).
    if len(return_all_meal_combinations({'IngredientID': ingredientID, 'MealID': mealID, 'UserID': userID})) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", None, False

    # 5) Generate unique CodeID
    codeID_message, codeID, codeID_status = generate_code(MealCombination, collection_name)

    if codeID_status:
        # 6) Build new document
        new_entry = make_meal_combination(codeID, get_now(), userID, ingredientID, mealID, quantity)

        # 7) Insert into database
        MealCombination.insert_one(new_entry)
        message = f"[{collection_name}] Valid Output: Entry Generated"

        # 8) Create record log
        record_message, record, record_status = create_record(MealCombination, "Create", codeID, new_entry, userID)
        if record_status:
            return message + " " + record_message, new_entry, True

        # 9) Rollback on record failure
        # If record creation fails, remove the inserted MealCombination entry.
        MealCombination.delete_one({'CodeID': codeID})
        return message + " " + record_message, new_entry, False

    # 10) Code generation failure
    return f"[{collection_name}] " + codeID_message, None, False


def find_meal_combination_products(codeID: str):
    # 1) Input guard
    # If no meal combination ID is provided, there can be no dependent entries
    if codeID is None:
        return []

    # 2) Dependency lookup
    # Search all product collections for entries referencing this meal combination
    products = []
    for collection in get_products(collection_name):
        data = list(collection.find({'MealCombinationID': codeID}))
        for entry in data:
            products.append({'CodeID': entry['CodeID']})

    # 3) Return dependent entry identifiers
    return products


def delete_meal_combination(codeID: str, userID: str):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Dependency check
    # Ensure the MealCombination entry is not referenced by any other collections.
    # This is a safety check to prevent deleting entries that are still in use
    # (and to future-proof against new references being added later).
    entry = find_meal_combination_products(codeID)
    if len(entry) >= 1:
        return f"[{collection_name}] Invalid Input: Entry Listed as Having Dependents", entry, False

    # 3) Validate target MealCombination
    # Ensure the MealCombination to be deleted exists and is uniquely identified.
    item_message, entry, item_status = validate_meal_combination(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator/owner of this MealCombination entry.
    # Users may only delete MealCombination entries they created.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Delete entry from database
    # Remove the MealCombination document identified by CodeID.
    MealCombination.delete_one({'CodeID': codeID})
    message = f"[{collection_name}] Valid Output: Entry Deleted"

    # 6) Create record log
    # Log the deletion using the pre-delete snapshot of the entry.
    record_message, record, record_status = create_record(
        MealCombination, "Delete", codeID, entry[0], userID
    )
    if record_status:
        return message + " " + record_message, entry[0], True

    # 7) Rollback on record failure
    # If record creation fails, restore the deleted MealCombination entry
    # to keep database state and audit log consistent.
    new_entry = make_meal_combination(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['IngredientID'],
        entry[0]['MealID'],
        entry[0]['Quantity']
    )
    MealCombination.insert_one(new_entry)
    return message + " " + record_message, new_entry, record_status


def update_meal_combination(codeID: str, userID: str, ingredientID: str, mealID: str, quantity: float = None):
    # 1) Validate requesting user
    # Ensure the user performing the action exists and is valid.
    user_message, user_entry, user_status = validate_user(userID)
    if not user_status:
        return user_message, user_entry, user_status

    # 2) Validate referenced documents (foreign keys)
    # Ensure the referenced Ingredient and Meal exist.
    # Ingredients may be universal; ownership is enforced only on the Meal.
    ingredient_message, entry, ingredient_status = validate_ingredient(ingredientID)
    if not ingredient_status:
        return ingredient_message, entry, ingredient_status

    meal_message, entry, meal_status = validate_meal(mealID)
    if not meal_status:
        return meal_message, entry, meal_status

    # 2b) Access / ownership check for Meal
    # Prevent users from updating MealCombinations linked to Meals they do not own.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[Meal] Invalid Input: User can't Access this Meal", entry, False

    # 3) Validate target MealCombination
    # Ensure the MealCombination to be updated exists and is uniquely identified.
    item_message, entry, item_status = validate_meal_combination(codeID)
    if not item_status:
        return item_message, entry, item_status

    # 4) Ownership check
    # Ensure the requesting user is the creator/owner of this MealCombination entry.
    if entry[0]['UserID'] != userID and user_entry[0]['Role'] == role_table["Plain User"]:
        return f"[{collection_name}] Invalid Input: UserID is Not the Creator of this Entry", entry, False

    # 5) Validate input fields
    # Quantity is required and must be a positive integer.
    if not isinstance(quantity, float) or quantity is None or quantity <= 0:
        return f"[{collection_name}] Invalid Input: Quantity must be a positive integer", None, False

    # 6) Uniqueness check
    # Prevent creation of a duplicate MealCombination entry with the same
    # (UserID, MealID, IngredientID, Quantity) as an existing entry.
    # The current entry is excluded implicitly by allowing unchanged values.
    key_entry = return_all_meal_combinations({'IngredientID': ingredientID, 'MealID': mealID, 'UserID': userID, 'Quantity': quantity, 'CodeID': {'$ne': codeID}})
    if len(key_entry) >= 1:
        return f"[{collection_name}] Invalid Input: Key Attribute Not Unique", key_entry, False

    # 7) Build updated document
    # Preserve CreatedAt and apply the new field values.
    new_entry = make_meal_combination(codeID, entry[0]['CreatedAt'], entry[0]['UserID'], ingredientID, mealID, quantity)

    # 8) Update database entry
    # Apply the updated values to the existing MealCombination document.
    MealCombination.update_one({"CodeID": codeID}, {"$set": new_entry})
    message = f"[{collection_name}] Valid Output: Entry Updated"

    # 9) Create record log
    # Log the updated state of the MealCombination entry.
    record_message, record, record_status = create_record(
        MealCombination, "Update", codeID, new_entry, userID
    )
    if record_status:
        return message + " " + record_message, new_entry, True

    # 10) Rollback on record failure
    # If record creation fails, restore the previous MealCombination values
    # to keep database state and audit log consistent.
    new_entry = make_meal_combination(
        entry[0]['CodeID'],
        entry[0]['CreatedAt'],
        entry[0]['UserID'],
        entry[0]['IngredientID'],
        entry[0]['MealID'],
        entry[0]['Quantity']
    )
    MealCombination.update_one({"CodeID": codeID}, {"$set": new_entry})
    return message + " " + record_message, new_entry, False


def validate_combination(entry):
    # Step 1: Validate that the combination still exists.
    # This ensures measurement integrity and prevents broken formatting.
    combination_message, combination_entry, combination_status = validate_meal_combination(entry['CodeID'])
    if combination_status:

        return validate_ingredient_deep(entry)

    else:

        # Step 5: Return fail message
        return False, combination_message, None, None
