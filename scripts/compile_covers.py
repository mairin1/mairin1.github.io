import requests

# TODO: add attribution to OpenLibrary for the covers

import pandas as pd
import json
import os
HEADERS = {
        "User-Agent": "Personal project (mairinoshaughnessy@gmail.com)"
    }

def spreadsheet_to_json(path):
    data = pd.read_excel(path)
    json_data = data.to_json()
    return json_data

def update_books_list(updated_json_data):
    updated_books = json.loads(updated_json_data)
    with open('files/books.json', 'r') as f:
        existing_books = json.load(f)
    updated_titles = [(key, title) for key, title in updated_books['Title'].items()]
    existing_titles = [book['title'] for book in existing_books['books']]
    new_titles = [(key, title) for key, title in updated_titles if title not in existing_titles]
    ind = max(len(existing_titles), 1)
    for row, title in new_titles:
        isbn_url = f"https://openlibrary.org/search.json?title={title}&fields=isbn&lang=eng"
        isbn_response = requests.get(isbn_url, headers=HEADERS)
        isbn = None
        if isbn_response.status_code == 200:
            isbn_bytes = isbn_response.content
            data = json.loads(isbn_bytes.decode('utf-8'))
            if len(data['docs']) > 0:
                isbn = data['docs'][0]['isbn'][0]
        else:
            print(f"Failed to get isbn for {title}")
        entry_to_add = {'id': ind,
                 'title': title,
                 'author': updated_books['Author'][row],
                 'isbn': isbn,
                 'rating': updated_books['Rating'][row],
                 'brief_review': updated_books['Review'][row]
                 }
        ind += 1
        existing_books['books'].append(entry_to_add)
    json_str = json.dumps(existing_books, indent=4)
    with open("files/books.json", "w") as f:
        f.write(json_str)

def get_cover(isbn, title):
    if f'{isbn}.jpg' not in os.listdir("files/covers"):
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        cover_response = requests.get(cover_url, headers=HEADERS)
        if cover_response.status_code == 200:
            with open(f'files/covers/{isbn}.jpg', 'wb') as file:
                file.write(cover_response.content)
        else:
            print(f"Failed to save cover for {title}")

# Seeding intial books.json
# json_data = spreadsheet_to_json("files/books-08-07.xlsx")
# update_books_list(json_data)

with open('files/books.json', 'r') as f:
    books = json.load(f) 
data = [(book['isbn'], book['title']) for book in books['books']]
for isbn, title in data:
    get_cover(isbn, title)
