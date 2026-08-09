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

def to_snake_case(title):
    title = str(title)
    lowered = str.lower(title)
    underscored = lowered.replace(" ", "_")
    return underscored

def update_books_list(updated_json_data):
    updated_books = json.loads(updated_json_data)
    with open('files/books.json', 'r') as f:
        existing_books = json.load(f)
    updated_titles = [(key, title) for key, title in updated_books['Title'].items()]
    existing_titles = [book['title'] for book in existing_books['books']]
    new_titles = [(key, title) for key, title in updated_titles if title not in existing_titles]
    ind = max(len(existing_titles), 1)
    for row, title in new_titles:
        entry_to_add = {'id': ind,
                 'title': title,
                 'title_id': to_snake_case(title),
                 'author': updated_books['Author'][row],
                 'rating': updated_books['Rating'][row],
                 'brief_review': updated_books['Review'][row]
                 }
        ind += 1
        existing_books['books'].append(entry_to_add)
    json_str = json.dumps(existing_books, indent=4)
    with open("files/books.json", "w") as f:
        f.write(json_str)

# OpenLibrary returns HTTP 200 with a tiny placeholder image
# when no real cover exists for an ISBN.
MIN_COVER_BYTES = 1000

def get_cover_from_title_english(author, title):
    if f'{to_snake_case(title)}.jpg' in os.listdir('files/covers/'):
        print(f'Skipped {title}')
        return
    isbn_url = f"https://openlibrary.org/search.json?title={title}&author={author}&fields=isbn,language,title,key&language=eng"
    isbn_response = requests.get(isbn_url, headers=HEADERS)
    isbn_bytes = isbn_response.content
    data = json.loads(isbn_bytes.decode('utf-8'))
    # Get the work key from English-filtered result
    if data and data.get('docs'):
        work_key = data['docs'][0]['key']
        print(work_key)
        # Fetch all editions for that work
        editions_url = f"https://openlibrary.org{work_key}/editions.json"
        editions_data = requests.get(editions_url, headers=HEADERS).json()

        # Filter for English editiions
        english_edition = None
        for edition in editions_data.get('entries', []):
            if edition.get('languages'):
                is_english = any(lang.get('key') == '/languages/eng' for lang in edition['languages'])
                # Skip if it's not a book format
                # format_type = edition.get('physical_format', '').lower()
                # is_book = True #'cd' not in format_type and 'software' not in format_type

                if is_english: #and is_book:
                    print(edition)
                    english_edition = edition
                    break
        if english_edition:
            if 'isbn_13' in english_edition.keys():
                isbn = english_edition['isbn_13'][0]
            elif 'isbn' in english_edition.keys():
                isbn = english_edition['isbn'][0]
            elif 'isbn_10' in english_edition.keys():
                isbn = english_edition['isbn_10'][0]
            else:
                return
            print(isbn)
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            cover_response = requests.get(cover_url, headers=HEADERS)
            if cover_response.status_code == 200 and len(cover_response.content) > MIN_COVER_BYTES:
                with open(f'files/covers/{to_snake_case(title)}.jpg', 'wb') as file:
                    file.write(cover_response.content)
            else:
                print(f"No real cover found for '{title}' (isbn {isbn}) -- skipping placeholder image")
        else:
            print(f"No English edition found for '{title}'")
    else:
        print(f"No OpenLibrary search results for '{title}' by {author}")

def get_cover_from_key(author, title, key): # key = 'isbn' | 
    if f'{to_snake_case(title)}.jpg' in os.listdir('files/covers/'):
            print(f'Skipped {title}')
            return
    key_url = f"https://openlibrary.org/search.json?title={title}&author={author}&fields={key}&language=eng"
    key_response = requests.get(key_url, headers=HEADERS)
    key_bytes = key_response.content
    data = json.loads(key_bytes.decode('utf-8'))
    if data and 'docs' in list(data.keys()) and len(data['docs']) > 0 and key in list(data['docs'][0].keys()):
        found = data['docs'][0][key][0]
    else:
        print(f"No {key} found for '{title}'")
        return
    cover_url = f"https://covers.openlibrary.org/b/{key}/{found}-M.jpg"
    cover_response = requests.get(cover_url, headers=HEADERS)
    if cover_response.status_code == 200 and len(cover_response.content) > MIN_COVER_BYTES:
        with open(f'files/covers/{to_snake_case(title)}.jpg', 'wb') as file:
            file.write(cover_response.content)
    else:   
        print(f"No real cover found for '{title}' ({key} {found}) -- skipping placeholder image")


def main():
    # Seeding books.json
    json_data = spreadsheet_to_json("files/books-08-07.xlsx")
    update_books_list(json_data)

    # Fetching covers
    with open('files/books.json', 'r') as f:
        books = json.load(f) 
    data = [(book['author'], book['title']) for book in books['books']]
    for author, title in data:
        # Prefer English language title
        get_cover_from_title_english(author, title)
        # The API is a bit weird, so we try a different way of getting covers
        get_cover_from_key(author, title, 'isbn')
        get_cover_from_key(author, title, 'lccn')
        get_cover_from_key(author, title, 'ocid')

main()