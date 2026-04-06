import pandas as pd
import streamlit as st
import plotly.express as px
from AdministrativeFunctions import open_new_code
from Day import return_all_days
from General_Functions import search_by_button
from Meal import validate_meal
from MealType import validate_meal_type
from Menu import menu
from Page_14 import alter_schedule_officially
from Schedule import return_all_schedules, outcome_table, outcome_table_with_tags, schedule_outcome_label, \
    schedule_notes_label
from User import validate_user
from datetime import datetime, timedelta
from functools import cmp_to_key

# Step 1: Initialize session state variables (first run only)
# Step 1a: Track the current page number
if "page" not in st.session_state:
    st.session_state.page = 1

# Step 1b: Track whether an error message should be shown
if "error_status" not in st.session_state:
    st.session_state.error_status = None

# Step 1c: Store the current signed-in user's CodeID
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Step 1d: Store the current error message (global handler reads this)
if "error" not in st.session_state:
    st.session_state.error = "You are doing great! Keep going."

# Step 1e: Store the CodeID to open in "full view"
if "open_code" not in st.session_state:
    st.session_state.open_code = None


def page_6_layout():
    # Step 1: Validate the currently signed-in user
    # We use the CodeID stored in session state to confirm the user exists
    # and has permission to access this page.
    message, entry, status = validate_user(st.session_state.current_user)

    # Step 2: If validation succeeds, build and show the page.
    if status:
        # Step 2a: Render the standard menu for the validated user.
        menu(entry)

        # Step 2b: Show the page title.
        st.title("Accountability Page")

        # Step 3: Ask the user for the date range and build the date table.
        st.header("Date Selection")
        date_table = get_table()

        # Step 4: Build and display the statistics section.
        # This returns:
        # - stats_table: one row per date plus a final total row
        # - all_schedule_data: all matching schedule entries for the selected dates
        if len(date_table) >= 1:

            stats_table, all_schedule_data = make_stats(date_table)

            show_rest = False
            for key, value in stats_table[-1].items():
                if key not in ['Date', 'Weekday']:
                    if value >= 1:
                        show_rest = True

            if show_rest:

                st.header("Statistics")

                present_stats(stats_table)

                # Step 5: Build the final enriched table.
                # We take each raw schedule entry and add extra information
                # such as MealType, Meal, Priority, and Disabled status.
                final_table = []
                for entry in all_schedule_data:
                    final_table.append(build_schedule_row(entry))

                # Step 6: Let the user choose how to arrange the final table.
                # The user can decide:
                # - whether to arrange by Date or Category/MealType in code
                # - whether the order should be Ascending or Descending
                st.header("Update Progress")
                add_group_column, alter_ascending_column = st.columns(2, vertical_alignment="center")
                with add_group_column:
                    group_element = search_by_button(
                        "Select Grouping Element",
                        ["Date", "Category"],
                        "None",
                        "None",
                        "Group"
                    )
                with alter_ascending_column:
                    ascending_depending = search_by_button(
                        "Select Sorting Method",
                        ['Ascending', 'Descending'],
                        "None",
                        "None",
                        "Sort"
                    )

                # Step 7: Start with the raw final table.
                # If the user selected a valid sorting option, apply it.
                arranged_table = final_table
                if group_element in sort_table and ascending_depending in sort_table[group_element]:
                    arranged_table = sort_table[group_element][ascending_depending](final_table)

                # Step 8: Display each row of the arranged table.
                for entry in arranged_table:
                    display_schedule_row(entry)

            else:

                st.write('You have no data planed for this duration of time')

    else:
        # Step 9: If validation failed, store the error for the global handler.
        st.session_state.error = message
        st.session_state.error_status = status


def generate_date_table(start_date_str, end_date_str):
    # Step 1: Try to convert both input strings into datetime objects.
    # Expected format is YYYY-MM-DD.
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        # Step 1a: If conversion fails, return an empty table and an error.
        return [], "Invalid Input: Can't convert input values", False

    # Step 2: Make sure the date range is valid.
    # The end date must not be before the start date.
    if start_date > end_date:
        return [], "Invalid Input: End Date is not Valid", False

    # Step 3: Build the table of dates.
    # Each entry is stored as a string in YYYY-MM-DD format.
    table = []
    current = start_date

    # Step 4: Add each day from start_date to end_date, inclusive.
    while current <= end_date:
        table.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    # Step 5: Return the completed table with a success message.
    return table, "Valid Input: Table Generated", True


def get_table():
    # Step 1: Create a bordered container for the date selection UI.
    with st.container(border=True):
        # Step 2: Split the area into two columns:
        # one for the start date and one for the end date.
        column_from, column_to = st.columns(2, vertical_alignment="center")

        # Step 3: Ask the user for the start date.
        with column_from:
            from_date = st.date_input("Start Date")

        # Step 4: Ask the user for the end date.
        with column_to:
            to_date = st.date_input("End Date", min_value=from_date+timedelta(days=1))

        # Step 5: Only build the table if the user explicitly asks to show it.
        show_result = st.checkbox("Show Result")

        if show_result:
            # Step 6: Convert the selected date objects to strings
            # and generate the date table.
            date_table, message, status = generate_date_table(str(from_date), str(to_date))

            # Step 7: If generation failed, store the error and return an empty table.
            if not status:
                st.session_state.error = message
                st.session_state.error_status = status
                return []

        else:
            # Step 8: If the user has not requested the result yet,
            # return an empty table.
            return []

    # Step 9: Return the generated date table.
    return date_table


def get_stats(date):
    # Step 1: Find the day record that matches the given date.
    # This should return exactly one entry from the Day collection.
    date_entry = return_all_days({'Date': date})

    # Step 2: If we do not find exactly one matching day,
    # return empty results.
    if len(date_entry) != 1:
        return [], []

    # Step 3: Prepare a simple list to hold only the status values.
    table = []

    # Step 4: Fetch all schedule entries linked to that day.
    schedule_data = return_all_schedules({'DayID': date_entry[0]['CodeID']})

    # Step 5: Attach the date string to each schedule entry.
    # This makes later processing easier because each schedule entry
    # now carries its own date.
    for entry in schedule_data:
        entry['Date'] = date

    # Step 6: Extract just the Status value from each schedule entry.
    for entry in schedule_data:
        table.append(entry['Outcome'])

    # Step 7: Return both:
    # - the list of statuses
    # - the full schedule data
    return table, schedule_data


def add_status_information(row, data):
    # Step 1: Go through each status value in the provided data.
    for entry in data:
        # Step 2: If the status is recognised, increment that status column.
        if entry in outcome_table:
            row[entry] += 1
        else:
            # Step 3: Otherwise count it as Unidentified.
            row['Unidentified'] += 1

        # Step 4: Every status also increases the total count.
        row['Total'] += 1

    # Step 5: Return the updated row.
    return row


def make_stats(date_table):
    # Step 1: Prepare the output tables.
    # stats_table will hold one row per date plus a final total row.
    # all_schedule_data will hold all raw schedule entries from all selected dates.
    stats_table = []
    all_schedule_data = []

    # Step 2: Build the final total row.
    final_row = {
        'Date': 'Total',
        'Weekday': "",
        'Total': 0,
        'Unidentified': 0
    }

    # Step 3: Add one column for every known outcome status.
    for status in outcome_table:
        final_row[status] = 0

    # Step 4: Process each date in the selected date table.
    for entry in date_table:
        # Step 4a: Get both the status list and the full schedule entries for this date.
        status_data, schedule_data = get_stats(entry)

        # Step 4b: Add all schedule entries into the combined full table.
        all_schedule_data.extend(schedule_data)

        # Step 4c: Create the per-day stats row.
        new_row = {
            'Date': entry,
            'Weekday': datetime.strptime(entry, "%Y-%m-%d").strftime("%A"),
            'Total': 0,
            'Unidentified': 0
        }

        # Step 4d: Add zero values for all known outcome statuses.
        for status in outcome_table:
            new_row[status] = 0

        # Step 4e: Fill the per-day row with status counts.
        stats_table.append(add_status_information(new_row, status_data))

        # Step 4f: Also add the same data into the final total row.
        add_status_information(final_row, status_data)

    # Step 5: Add the total row at the bottom of the stats table.
    stats_table.append(final_row)

    # Step 6: Return both the stats table and the raw schedule data.
    return stats_table, all_schedule_data


def present_stats(stats_table):
    # Step 1: Only continue if the stats table has data.
    if len(stats_table) >= 2:
        # Step 2: Split the section into two parts:
        # - left side for the shape/chart and optional full table
        # - right side for summary numbers
        shape, information = st.columns([8, 2])

        with shape:
            # Step 3: Show the pie chart summary.
            st.subheader("Overall Progress")
            make_shape(stats_table)

            # Step 4: Let the user choose whether to see the day-by-day breakdown.
            show_full = st.checkbox("Show Day by Day distribution")

        with information:
            # Step 6: Show the number of actual day rows included.
            st.write(f"The following data correspond to {len(stats_table) - 1} days")

            # Step 7: Show the values from the final total row,
            # excluding Date and Weekday.
            for key, value in stats_table[-1].items():
                if key not in ['Date', 'Weekday']:
                    st.write(f"{key}: {value}")

        if show_full:
            # Step 5: Show the table header and the rows for each day.
            # We exclude the final total row here.
            st.subheader("Individual Progress")
            header_columns()
            bottom_columns(stats_table[:-1])


def make_shape(stats_table):
    # Step 1: Build a value list in the same order as outcome_table.
    # We use the final total row for the values.
    outcome_table_list = list(outcome_table)
    value = []
    for entry in outcome_table_list :
        value.append(stats_table[-1].get(entry, 0))

    # Step 2: Convert the data into a DataFrame for Plotly.
    df = pd.DataFrame({
        "category": outcome_table_list,
        "value": value
    })

    # Step 3: Build the pie chart.
    fig = px.pie(df, values='value', names='category')

    # Step 4: Display the chart.
    st.plotly_chart(fig, use_container_width=True)


def header_columns():
    # Step 1: Create the header layout for the day-by-day stats table.
    header_date, header_weekday, header_total, header_categories, header_unidentified = st.columns([2, 2, 2, 10, 2])

    # Step 2: Fill each header cell with its label.
    with header_date:
        st.write("Date")

    with header_weekday:
        st.write("Weekday")

    with header_total:
        st.write("Total")

    with header_categories:
        # Step 3: Inside the categories area, create one column per outcome.
        header_cols = st.columns(len(outcome_table))
        for i, entry in enumerate(outcome_table):
            header_cols[i].write(entry)

    with header_unidentified:
        st.write("Unidentified")


def bottom_columns(stats_table):
    # Step 1: Display one row for each entry in the provided stats table.
    for entry in stats_table:
        # Step 2: Create the same column structure used by the header.
        bottom_date, bottom_weekday, bottom_total, bottom_categories, bottom_unidentified = st.columns([2, 2, 2, 10, 2])

        # Step 3: Fill the standard columns.
        with bottom_date:
            st.write(entry['Date'])

        with bottom_weekday:
            st.write(entry['Weekday'])

        with bottom_total:
            st.write(entry['Total'])

        # Step 4: Fill the category columns in the same order as outcome_table.
        with bottom_categories:
            bottom_cols = st.columns(len(outcome_table))
            for i, status_entry in enumerate(outcome_table):
                bottom_cols[i].write(entry.get(status_entry, 0))

        # Step 5: Show the unidentified count.
        with bottom_unidentified:
            st.write(entry['Unidentified'])


def build_schedule_row(schedule_entry):
    # Step 1: Start by copying the original schedule entry.
    # This lets us enrich it without changing the original object directly.
    row = dict(schedule_entry)

    # Step 2: Validate the MealType linked to this schedule entry.
    meal_type_message, meal_type_entry, meal_type_status = validate_meal_type(schedule_entry['MealTypeID'])

    # Step 3: By default, the row is enabled.
    # We will switch it to disabled if validation fails or if the status is not editable.
    row['Disabled'] = False

    # Step 4: If MealType validation succeeds, add its display information.
    if meal_type_status:
        row['MealType'] = meal_type_entry[0]['Name']
        row['Priority'] = meal_type_entry[0]['Priority']
    else:
        # Step 5: If MealType validation fails, store the error text instead
        # and mark the row as disabled.
        row['MealType'] = meal_type_message
        row['Priority'] = -1
        row['Disabled'] = True

    # Step 6: Validate the Meal linked to this schedule entry.
    meal_message, meal_entry, meal_status = validate_meal(schedule_entry['MealID'])

    # Step 7: If Meal validation succeeds, add the meal name.
    if meal_status:
        row['Meal'] = meal_entry[0]['Name']
    else:
        # Step 8: If Meal validation fails, store the error text
        # and disable the row.
        row['Meal'] = meal_message
        row['Disabled'] = True

    # Step 9: Only entries with the "Current" status are editable.
    # If the schedule entry is not current, disable editing.
    if schedule_entry['Outcome'] not in outcome_table_with_tags["Current"]:
        row['Disabled'] = True

    # Step 10: Return the enriched row.
    return row


def compare_by_date(row1, row2, reverse=False):
    # Step 1: Compare the rows by Date first.
    if row1['Date'] < row2['Date']:
        result = -1
    elif row1['Date'] > row2['Date']:
        result = 1
    else:
        # Step 2: If the Date is the same, compare by Priority.
        if row1['Priority'] < row2['Priority']:
            result = -1
        elif row1['Priority'] > row2['Priority']:
            result = 1
        else:
            # Step 3: If Priority is also the same, only use Meal
            # if the rows belong to different Categories.
            if row1['MealType'] != row2['MealType']:
                if row1['Meal'] < row2['Meal']:
                    result = -1
                elif row1['Meal'] > row2['Meal']:
                    result = 1
                else:
                    result = 0
            else:
                # Step 4: If none of the rules separate them, treat them as equal.
                result = 0

    # Step 5: If reverse sorting is requested, flip the result.
    return result if not reverse else -result


def compare_by_category_priority(row1, row2, reverse=False):
    # Step 1: Compare by Priority first.
    if row1['Priority'] < row2['Priority']:
        result = -1
    elif row1['Priority'] > row2['Priority']:
        result = 1
    else:
        # Step 2: If Priority is equal and the Categories differ,
        # compare by Meal.
        if row1['MealType'] != row2['MealType']:
            if row1['Meal'] < row2['Meal']:
                result = -1
            elif row1['Meal'] > row2['Meal']:
                result = 1
            else:
                result = 0
        else:
            # Step 3: If Priority is equal and Category/MealType in code is the same,
            # compare by Date.
            if row1['Date'] < row2['Date']:
                result = -1
            elif row1['Date'] > row2['Date']:
                result = 1
            else:
                result = 0

    # Step 4: If reverse sorting is requested, flip the result.
    return result if not reverse else -result


def arrange_table_by_date(mega_table, reverse=False):
    # Step 1: Sort the table using the custom date-based comparator.
    return sorted(
        mega_table,
        key=cmp_to_key(lambda a, b: compare_by_date(a, b, reverse))
    )


def arrange_table_by_category(mega_table, reverse=False):
    # Step 1: Sort the table using the custom priority/category comparator.
    return sorted(
        mega_table,
        key=cmp_to_key(lambda a, b: compare_by_category_priority(a, b, reverse))
    )


# Step 1: Build the lookup table for all supported sorting combinations.
# The first key is the arrangement mode.
# The second key is the direction.
# The stored value is the function that performs that arrangement.
sort_table = {
    "Date": {
        "Ascending": lambda table: arrange_table_by_date(table, reverse=False),
        "Descending": lambda table: arrange_table_by_date(table, reverse=True)
    },
    "Category": {
        "Ascending": lambda table: arrange_table_by_category(table, reverse=False),
        "Descending": lambda table: arrange_table_by_category(table, reverse=True)
    }
}


def display_schedule_row(entry):
    # Step 1: Wrap the row in a bordered container for visual separation.
    with st.container(border=True):
        # Step 2: Create the six display columns for this schedule row.
        date_category_meal, select_notes, button = st.columns(3, vertical_alignment="center")

        with date_category_meal:
            # Step 3: Show the date and provide a button to open the related day.
            st.button(
                f"{entry['Date']}",
                use_container_width=True,
                on_click=open_new_code,
                args=[entry['DayID']],
                key=f"open_day_{entry['CodeID']}"
            )

            # Step 4: Show the meal type and provide a button to open it.
            st.button(
                f"{entry['MealType']}",
                use_container_width=True,
                on_click=open_new_code,
                args=[entry['MealTypeID']],
                key=f"open_meal_type_{entry['CodeID']}"
            )

            # Step 5: Show the meal and provide a button to open it.
            st.button(
                f"{entry['Meal']}",
                use_container_width=True,
                on_click=open_new_code,
                args=[entry['MealID']],
                key=f"open_meal_{entry['CodeID']}"
            )

        with select_notes:

            # Step 6: If the row is disabled, just display the current status.
            # Otherwise, allow the user to choose a new outcome.
            if entry['Disabled']:
                st.write(entry['Outcome'])
                outcome = entry['Outcome']
            else:
                outcome = st.selectbox(
                    schedule_outcome_label,
                    outcome_table_with_tags['Locked'],
                    index=0,
                    key=f"add_schedule_outcome_{entry['CodeID']}"
                )

            # Step 7: If the row is disabled, just display the notes.
            # Otherwise, allow the user to edit them.
            if entry['Disabled']:
                notes = entry['Notes']
            else:
                notes = st.text_input(
                    schedule_notes_label,
                    value=entry['Notes'],
                    key=f"add_schedule_notes_{entry['CodeID']}"
                )

        with button:
            # Step 8: Show the submit button that saves the selected outcome and notes.
            if not entry['Disabled']:
                st.button(
                    f"Mark as {outcome}",
                    use_container_width=True,
                    on_click=alter_schedule_officially,
                    args=[
                        entry['CodeID'],
                        st.session_state.current_user,
                        entry['MealTypeID'],
                        entry['MealID'],
                        entry['DayID'],
                        outcome,
                        notes
                    ],
                    key=f"submit_{entry['CodeID']}"
                )
            else:
                st.write(entry['Notes'])