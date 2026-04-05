import streamlit as st
from MongoDB_General_Functions import role_table
from AdministrativeFunctions import change_page


def menu(entry):
    # Step 1: Initialize sidebar navigation
    # This menu is rendered for every authenticated user
    st.sidebar.title("Navigation")

    # Step 2: Standard user navigation
    # These pages are available to all users regardless of role
    st.sidebar.header("For Users")

    st.sidebar.subheader("Home Page")

    st.sidebar.button(
        'Home Page',
        icon=":material/home_work:",
        use_container_width=True,
        on_click=change_page,
        args=[3],
        key="home_page"
    )

    st.sidebar.subheader("My Nutrition Plan")

    st.sidebar.button(
        'My Grocery List',
        icon=":material/grocery:",
        use_container_width=True,
        on_click=change_page,
        args=[4],
        key="grocery_page"
    )

    st.sidebar.button(
        'My Meal Plan',
        icon=":material/calendar_meal:",
        use_container_width=True,
        on_click=change_page,
        args=[5],
        key="plan_page"
    )

    st.sidebar.button(
        'Accountability Corner',
        icon=":material/calendar_check:",
        use_container_width=True,
        on_click=change_page,
        args=[6],
        key="accountability_page"
    )

    st.sidebar.subheader("My Information")

    st.sidebar.button(
        'Profile',
        icon=":material/account_circle:",
        use_container_width=True,
        on_click=change_page,
        args=[7],
        key="profile_page"
    )

    st.sidebar.subheader("Tutorial")

    st.sidebar.button(
        'Tutorial',
        icon=":material/help:",
        use_container_width=True,
        on_click=change_page,
        args=[19],
        key="user_tutorial_page"
    )

    # Step 3: Administrator-only navigation
    # These options are only visible to users with the Administrator role
    if entry[0]['Role'] == role_table["Administrator"]:
        st.sidebar.header("For Administrators")

        # Step 3a: Full collection management
        # Includes create, search, update, and delete operations
        st.sidebar.subheader("Search / Add / Alter / Delete Collection")

        st.sidebar.button('Category', icon=":material/category:", use_container_width=True,
                          on_click=change_page, args=[8], key="category_page")
        st.sidebar.button('Day', icon=":material/calendar_clock:", use_container_width=True,
                          on_click=change_page, args=[9], key="day_page")
        st.sidebar.button('Ingredient', icon=":material/cooking:", use_container_width=True,
                          on_click=change_page, args=[10], key="ingredient_page")
        st.sidebar.button('Meal', icon=":material/menu_book:", use_container_width=True,
                          on_click=change_page, args=[11], key="meal_page")
        st.sidebar.button('MealType', icon=":material/calendar_meal_2:", use_container_width=True,
                          on_click=change_page, args=[12], key="meal_type_page")
        st.sidebar.button('Rule', icon=":material/rule:", use_container_width=True,
                          on_click=change_page, args=[13], key="rule_page")
        st.sidebar.button('Schedule', icon=":material/schedule:", use_container_width=True,
                          on_click=change_page, args=[14], key="schedule_page")
        st.sidebar.button('UnitType', icon=":material/brick:", use_container_width=True,
                          on_click=change_page, args=[15], key="unit_type_page")
        st.sidebar.button('User', icon=":material/manage_accounts:", use_container_width=True,
                          on_click=change_page, args=[16], key="user_page")

        # Step 3b: Limited collection management
        # Restricted to search and modification (no creation or deletion)
        st.sidebar.subheader("Search / Alter Collection")

        st.sidebar.button('Request', icon=":material/request_page:", use_container_width=True,
                          on_click=change_page, args=[17], key="request_page")

        # Step 3c: Read-only database access
        st.sidebar.subheader("Search Database")

        st.sidebar.button('Record', icon=":material/database:", use_container_width=True,
                          on_click=change_page, args=[18], key="search_page")

    # Step 4: Sign-out action
    # Ends the current session and returns the user to the entry page
    st.sidebar.header("Sign Out")
    st.sidebar.button(
        'Sign out',
        icon=":material/logout:",
        use_container_width=True,
        on_click=change_page,
        args=[1],
        key="log_out"
    )
