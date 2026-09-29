def get_mark(prompt):
    # Keep asking until the user enters a valid mark.
    while True:
        # Read the mark and remove spaces from its beginning and end.
        entered_mark = input(prompt).strip()

        # Try to convert the entered text into a number.
        try:
            mark = float(entered_mark)
        except ValueError:
            # Explain the problem if the text was not a number.
            print("Invalid mark. Enter a number between 0 and 100.")
            # Start the loop again and ask for the mark once more.
            continue

        # Check that the mark is within the inclusive range 0 to 100.
        if not 0 <= mark <= 100:
            # Explain that marks outside the allowed range are not accepted.
            print("Invalid mark. Enter a number between 0 and 100.")
            # Start the loop again and ask for the mark once more.
            continue

        # Give the valid number back to the part of the program that asked for it.
        return mark


def get_grade(mark):
    # Give an A when the mark is 90 or higher.
    if mark >= 90:
        return "A"
    # Otherwise, give a B when the mark is 80 or higher.
    elif mark >= 80:
        return "B"
    # Otherwise, give a C when the mark is 70 or higher.
    elif mark >= 70:
        return "C"
    # Otherwise, give a D when the mark is 60 or higher.
    elif mark >= 60:
        return "D"
    # All remaining valid marks are below 60, so give an E.
    return "E"


def main():
    # Create an empty list to hold each student's name, mark, and grade.
    students = []

    # Repeat the student-entry steps five times.
    for student_number in range(1, 6):
        # Ask for the student's name and remove extra spaces around it.
        name = input(f"Enter student {student_number}'s name: ").strip()
        # Keep asking if the name was left blank.
        while not name:
            # Tell the user that a name is required.
            print("Name cannot be empty.")
            # Ask for the student's name again.
            name = input(f"Enter student {student_number}'s name: ").strip()

        # Ask for this student's mark and validate it.
        mark = get_mark(f"Enter {name}'s mark (0-100): ")
        # Save the student's name, mark, and calculated grade in the list.
        students.append((name, mark, get_grade(mark)))

    # Print a title above the results.
    print("\nStudent Grades")
    # Print labels for the three result columns.
    print("Name | Mark | Grade")
    # Go through the saved student records one at a time.
    for name, mark, grade in students:
        # Print this student's name, mark, and grade on one line.
        print(f"{name} | {mark:g} | {grade}")


# Check whether this file was run directly rather than imported by another file.
if __name__ == "__main__":
    # Start the program by calling the main function.
    main()