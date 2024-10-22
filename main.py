import sqlite3
import datetime
import csv

conn = sqlite3.connect('books.db')
 
c = conn.cursor()

# Create tables if they don't exist
c.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        bid TEXT,
        quantity INTEGER
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS borrowers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact_info TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS checkouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        borrower_id INTEGER,
        checkout_date DATE,
        due_date DATE,
        FOREIGN KEY (book_id) REFERENCES books(id),
        FOREIGN KEY (borrower_id) REFERENCES borrowers(id)
    )
""")

# Load book data from CSV file
books_data = []
with open('books.csv', 'r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header row
    for row in reader:
        books_data.append((row[0], row[1], row[2], int(row[3])))  # Append book data
# Insert books into the books table
c.executemany("INSERT INTO books (title, author, bid, quantity) VALUES (?, ?, ?, ?)", books_data)

FINE_PER_DAY = 1.00

# Insert books into the books table
c.executemany("INSERT INTO books (title, author, bid, quantity) VALUES (?, ?, ?, ?)", books_data)

def add_borrower():
    #Adds a new borrower to the database, auto-generating the ID
    name = input("Enter the name of the borrower: ")
    contact_info = input("Enter the borrower's contact information: ")
    
    # Auto-generate borrower ID
    c.execute("SELECT MAX(id) FROM borrowers")
    max_id = c.fetchone()[0]
    borrower_id = 1 if max_id is None else max_id + 1
    
    c.execute("INSERT INTO borrowers (id, name, contact_info) VALUES (?, ?, ?)", 
              (borrower_id, name, contact_info))
    
    print(f"Borrower {name} added successfully with ID: {borrower_id}")
    
def checkout_book():
    #Checks out a book for a registered borrower
    #Uses a loop to ensure the book ID is valid
    while True:
        borrower_id = int(input("Enter the borrower ID: "))
        # Check if borrower ID exists
        c.execute("SELECT id FROM borrowers WHERE id = ?", (borrower_id,))
        borrower_data = c.fetchone()
        if borrower_data is None:
            print("Borrower ID not found. Please register first.")
            continue
        # If borrower ID is found, proceed with checkout
        book_checked_out = False  # Flag to track if a book was checked out
        while not book_checked_out:  # Loop until a book is checked out
            book_title = input("Enter the title of the book you want to check out: ")
            c.execute("SELECT author FROM books WHERE title = ?", (book_title,))
            author_data = c.fetchone()
            if author_data is None:
                print("Book not found.")
                continue
            author = author_data[0] #Get the author
            print(f"Author: {author}") #Display the author
            while True:
                confirmation = input(f"Is this the correct author ({author})? (y/n): ").lower()
                if confirmation == 'y':
                    #Proceed with checkout for the original author
                    c.execute("SELECT id, bid, quantity FROM books WHERE title = ? AND author = ?", (book_title, author))
                    book_data = c.fetchone()  # Get the first matching book
                    if book_data is None:
                        print("Book not found.")
                        continue
                    book_id, _, quantity = book_data  # Get the book_id and quantity
                    if quantity == 0:
                        print("Sorry, this book is currently unavailable.")
                        continue
                    # Calculate due date
                    due_date = (datetime.date.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')
                    # Update book quantity and record checkout
                    c.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
                    c.execute("INSERT INTO checkouts (book_id, borrower_id, checkout_date, due_date) VALUES (?, ?, DATE('now'), ?)", (book_id, borrower_id, due_date))
                    print("Book checked out successfully!")
                    print(f"Your due date is: {due_date}")  # Inform the user of the due date
                    book_checked_out = True  # Set the flag to break the loop
                    break  # Exit the inner loop
                elif confirmation == 'n':
                    # Find other books with the same title
                    c.execute("SELECT author FROM books WHERE title = ? AND author != ?", (book_title, author))
                    other_authors = c.fetchall()
                    if other_authors:
                        print("Other books with the same title:")
                        for i, other_author in enumerate(other_authors):
                            print(f"{i+1}. {other_author[0]}")
                        while True:
                            try:
                                choice = int(input("Enter the number of the correct author: "))
                                if 1 <= choice <= len(other_authors):
                                    new_author = other_authors[choice - 1][0]
                                    break
                                else:
                                    print("Invalid choice. Please enter a valid number.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")
                        # Ask for confirmation on the new author
                        while True:
                            confirmation = input(f"Is {new_author} the correct author? (y/n): ").lower()
                            if confirmation == 'y':
                                # Proceed with checkout for the new author
                                c.execute("SELECT id, bid, quantity FROM books WHERE title = ? AND author = ?", (book_title, new_author))
                                book_data = c.fetchone()  # Get the first matching book
                                if book_data is None:
                                    print("Book not found.")
                                    continue
                                book_id, _, quantity = book_data  # Get the book_id and quantity
                                if quantity == 0:
                                    print("Sorry, this book is currently unavailable.")
                                    continue
                                # Calculate due date
                                due_date = (datetime.date.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')
                                # Update book quantity and record checkout
                                c.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
                                c.execute("INSERT INTO checkouts (book_id, borrower_id, checkout_date, due_date) VALUES (?, ?, DATE('now'), ?)", (book_id, borrower_id, due_date))
                                print("Book checked out successfully!")
                                print(f"Your due date is: {due_date}")  # Inform the user of the due date
                                book_checked_out = True  # Set the flag to break the loop
                                break  # Exit the inner loop
                            elif confirmation == 'n':
                                print("Please try again.")
                                break
                            else:
                                print("Invalid input. Please enter 'y' or 'n'.")
                    else:
                        print("No other books with that title and a different author found.")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        break  # Exit the outer loop after successful checkout

def return_book():
    #Returns a book for the given borrower
    #Uses a loop to ensure the borrower ID is valid
    while True:
        borrower_id = int(input("Enter the borrower ID: "))
        # Check if borrower ID exists
        c.execute("SELECT id FROM borrowers WHERE id = ?", (borrower_id,))
        borrower_data = c.fetchone()
        if borrower_data is None:
            print("Borrower ID not found. Please register first.")
            continue
        # If borrower ID is found, proceed with returning the book
        book_returned = False  # Flag to track if a book was returned
        while not book_returned:  # Loop until a book is returned
            book_title = input("Enter the title of the book you want to return: ")
            c.execute("SELECT author FROM books WHERE title = ?", (book_title,))
            author_data = c.fetchone()
            if author_data is None:
                print("Book not found.")
                continue
            author = author_data[0] #Get the author
            print(f"Author: {author}") #Display the author
            while True:
                confirmation = input(f"Is this the correct author ({author})? (y/n): ").lower()
                if confirmation == 'y':
                    # Proceed with returning the book for the original author
                    c.execute("SELECT id, bid FROM books WHERE title = ? AND author = ?", (book_title, author))
                    book_data = c.fetchone()  # Get the first matching book
                    if book_data is None:
                        print("Book not found.")
                        continue
                    book_id = book_data[0]  # Get the book_id
                    # Find the checkout record
                    c.execute("SELECT id FROM checkouts WHERE book_id = ? AND borrower_id = ?", (book_id, borrower_id))
                    checkout_id = c.fetchone()
                    if checkout_id is None:
                        print("This book is not currently checked out by you.")
                        continue
                    checkout_id = checkout_id[0]  # Get the checkout ID from the tuple
                    # Update book quantity and remove checkout record
                    c.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
                    c.execute("DELETE FROM checkouts WHERE id = ?", (checkout_id,))
                    print("Book returned successfully!")
                    book_returned = True  # Set the flag to break the loop
                    break  # Exit the inner loop
                elif confirmation == 'n':
                    # Find other books with the same title
                    c.execute("SELECT author FROM books WHERE title = ? AND author != ?", (book_title, author))
                    other_authors = c.fetchall()
                    if other_authors:
                        print("Other books with the same title:")
                        for i, other_author in enumerate(other_authors):
                            print(f"{i+1}. {other_author[0]}")
                        while True:
                            try:
                                choice = int(input("Enter the number of the correct author: "))
                                if 1 <= choice <= len(other_authors):
                                    new_author = other_authors[choice - 1][0]
                                    break
                                else:
                                    print("Invalid choice. Please enter a valid number.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")
                        # Ask for confirmation on the new author
                        while True:
                            confirmation = input(f"Is {new_author} the correct author? (y/n): ").lower()
                            if confirmation == 'y':
                                # Proceed with returning the book for the new author
                                c.execute("SELECT id, bid FROM books WHERE title = ? AND author = ?", (book_title, new_author))
                                book_data = c.fetchone()  # Get the first matching book
                                if book_data is None:
                                    print("Book not found.")
                                    continue
                                book_id = book_data[0]  # Get the book_id
                                # Find the checkout record
                                c.execute("SELECT id FROM checkouts WHERE book_id = ? AND borrower_id = ?", (book_id, borrower_id))
                                checkout_id = c.fetchone()
                                if checkout_id is None:
                                    print("This book is not currently checked out by you.")
                                    continue
                                checkout_id = checkout_id[0]  # Get the checkout ID from the tuple
                                # Update book quantity and remove checkout record
                                c.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
                                c.execute("DELETE FROM checkouts WHERE id = ?", (checkout_id,))
                                print("Book returned successfully!")
                                book_returned = True  # Set the flag to break the loop
                                break  # Exit the inner loop
                            elif confirmation == 'n':
                                print("Please try again.")
                                break
                            else:
                                print("Invalid input. Please enter 'y' or 'n'")
                    else:
                        print("No other books with that title and a different author found.")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        # Exit the outer loop after a book is returned
        break  # Exit the outer loop after successful return

while True:
  print("\nLibrary Management System")
  print("1. Add Borrower")
  print("2. Checkout Book")
  print("3. Return Book")
  print("4. Exit")
  choice = input("Enter your choice: ")
  if choice == '1':
      add_borrower()
  elif choice == '2':
      checkout_book()
  elif choice == '3':
      return_book()
  elif choice == '4':
      break
  else:
      print("Invalid choice.")

conn.commit()

conn.close()