
async function loadBooks() {
    const coversData = await fetch('files/covers.json');
    const covers = (await coversData.json()).covers;

    const booksData = await fetch('files/books.json');
    const books = (await booksData.json()).books;

    // TODO: don't allow duplicates
    random_books = [1, 2, 3]
        .map(() => covers[Math.floor(Math.random() * Object.keys(covers).length)]);

    const src = document.getElementById("book-row");
    src.replaceChildren();

    for(let i=0; i<random_books.length; i++){
        const key = random_books[i].books_json_key
        displayBookInfo(random_books[i].file,
                        books[key].title,
                        books[key].author,
                        books[key].rating,
                        books[key].brief_review);
    }
}

function displayBookInfo(filename, title, author, rating, review) {
    const row = document.getElementById("book-row");
    const book = document.createElement('li');
    book.className = 'book-item';
    let stars = "";
    for(let i=0; i<rating; i++){
        stars += "\u{1F31F}";
    }
    book.innerHTML = `
        <img src="${'files/covers/'+filename}" alt="image">
        <div class="title">${title}</div>
        <div class="author">${author}</div>
        <div class="rating">${stars}</div>
        <div class="review">${review}</div>
    `;
    
    row.appendChild(book);
}