import pymongo
import streamlit as st


@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"][
                                   "uri"])  # Establish Connection with database using the url given by the server in the secrets file


client = init_connection()  # Establish Connection with database using the url given by the server in the secrets file

db = client.PlanMyMeal  # Find and define the database itself

Record = db["Record"]
User = db["User"]
UnitType = db["UnitType"]
Rule = db["Rule"]
Ingredient = db["Ingredient"]
Category = db["Category"]
MealType = db["MealType"]
Day = db["Day"]
Meal = db["Meal"]
MealCombination = db["MealCombination"]
Schedule = db["Schedule"]
Request = db["Request"]






