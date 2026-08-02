const genreButtons = Array.from(document.getElementsByClassName('genre-button'));
const loadingOverlay = document.querySelector('.loading-overlay');
const searchButton = document.querySelector('.search-button');
const searchInput = document.querySelector('.search-input');
const resultDiv = document.querySelector('.result-container');
const beforeResult = document.querySelector('.before-result');
const afterResult = document.querySelector('.after-result');
const loader = document.querySelector('.loader');
let page = 1;
let scrollCategory = "All";
const movieLoader = document.querySelector('.movie-loader');
const movieGrid = document.querySelector('.movie-grid');

function fillSkeletonCards(container, minCount = 12) {
    if (!container) return;
    const minCard = 250;
    const gap = 24;
    const width = container.clientWidth || container.parentElement?.clientWidth || window.innerWidth;
    const cols = Math.max(1, Math.floor(width / (minCard + gap)));
    const count = Math.max(minCount, cols * 2);
    container.innerHTML = Array.from({ length: count }, () =>
        `<article class="movie-card skeleton" aria-hidden="true"></article>`
    ).join('');
}

function movieCardHTML(movie) {
    return `
            <a href="${movie.code}">
            <article class="movie-card">
            <img
            src="${movie.poster}"
            alt="${movie.title}"
            class="movie-image"
            />
            <div class="movie-card-overlay">
                <div class="content-info">
                    ${movie.content_type}
                </div>
                <div class="movie-info">
                <span>${movie.year}</span>
                <div class="rating">
                <svg width="12" height="13" viewBox="0 0 12 13" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11.7214 4.8126C11.7214 4.91082 11.6634 5.01796 11.5474 5.13403L9.1188 7.50457L9.69417 10.8528C9.69863 10.884 9.70086 10.9287 9.70086 10.9867C9.70086 11.0805 9.67745 11.1597 9.63061 11.2244C9.58378 11.2892 9.51576 11.3215 9.42656 11.3215C9.34181 11.3215 9.25261 11.2947 9.15894 11.2412L6.15494 9.66082L3.15093 11.2412C3.05281 11.2947 2.9636 11.3215 2.88332 11.3215C2.78965 11.3215 2.7194 11.2892 2.67257 11.2244C2.62574 11.1597 2.60232 11.0805 2.60232 10.9867C2.60232 10.9599 2.60678 10.9153 2.6157 10.8528L3.19108 7.50457L0.755762 5.13403C0.644255 5.0135 0.588501 4.90635 0.588501 4.8126C0.588501 4.64743 0.713389 4.54475 0.963165 4.50457L4.32176 4.01573L5.82711 0.968855C5.91185 0.785819 6.02113 0.694301 6.15494 0.694301C6.28875 0.694301 6.39802 0.785819 6.48277 0.968855L7.98811 4.01573L11.3467 4.50457C11.5965 4.54475 11.7214 4.64743 11.7214 4.8126Z" fill="#F1F1F1"/>
                </svg>
                <span>${movie.rating}</span>
            </div>
            </div>
            <h3 class="movie-card-title">${movie.title}</h3>
            </div>
            </article>
            </a>
            `;
}

function fetchAndShow(url) {
    fetch(url).then((response) => {
        return response.json();
    }).then((data) => {
        const box = document.querySelector('.movie-grid');
        let movies_html = '';
        data.movies.forEach((movie) => {
            movies_html += movieCardHTML(movie);
        });
        box.innerHTML = movies_html;

        document.body.style.overflow = '';
        loadingOverlay.style.display = 'none';
    });
}


// The above function first clears the innerhtml then adds the new html that is why this is necessary to add to existing html
function fetchAndAdd(url) {
    fetch(url).then((response) => {
        return response.json();
    }).then((data) => {
        if (data.has_next === false) {
            window.removeEventListener('scroll' , handleScroll);
        }
        const box = document.querySelector('.movie-grid');
        data.movies.forEach((movie) => {
            box.innerHTML += movieCardHTML(movie);
        });

        movieLoader.style.display = 'none';
    });
}



genreButtons.forEach((button) => {
    button.addEventListener('click', () => {
        resultDiv.innerHTML = '';
        beforeResult.innerHTML = '';
        afterResult.innerHTML = '';
        if(button.classList.contains('active')) {
            return;
        }

        page = 1;

        genreButtons.forEach((btn) => {
            btn.classList.remove('active');
        })
        button.classList.add('active');

        fillSkeletonCards(movieGrid);

        const category=button.innerText
        scrollCategory = category
        const url = `/home/filter/?category=${encodeURIComponent(category)}&page=${page}`;
        page = page+1;

        fetchAndShow(url);
    });
})


function handleScroll() {
    if(window.scrollY + window.innerHeight >= document.documentElement.scrollHeight) {
        movieLoader.style.display = 'block';
        const url = `/home/filter/?category=${scrollCategory}&page=${page}`;
        
        page = page+1;

        fetchAndAdd(url);
    }
}

function addScrollEvent() {
    window.addEventListener('scroll' , handleScroll);
}

addScrollEvent();


function searchMovie() {
    const mov_name = searchInput.value;
    if(mov_name.trim() === '') {
        searchInput.value = '';
        return;
    }

    searchButton.style.display = 'none';
    loader.style.display = 'block';

    resultDiv.classList.add('result');
    fillSkeletonCards(resultDiv);
    fillSkeletonCards(movieGrid);
    beforeResult.innerHTML = '';
    afterResult.innerHTML = '';

    const url=`/home/search-result/?mov_name=${encodeURIComponent(mov_name)}`;
    fetch(url).then((response) => {
        return response.json();
    }).then((data) => {
        if(data.is_found === 'False') {
            resultDiv.innerHTML = '';
            beforeResult.innerHTML = "No such movie found";
            afterResult.innerHTML = "You may also like";
            page = 1;
            const restoreUrl = `/home/filter/?category=${encodeURIComponent(scrollCategory)}&page=${page}`;
            page = page + 1;
            fetchAndShow(restoreUrl);
        }
        else{
            resultDiv.classList.add('result');
            beforeResult.innerHTML = `Showing results for "<strong>${mov_name}<strong>"`;
            afterResult.innerHTML = "You may also like";
            let results_html = '';
            data.movies.forEach((movie) => {
                results_html += movieCardHTML(movie);
            });
            resultDiv.innerHTML = results_html;

            let related_html = '';
            data.rel_movies.forEach((movie) => {
                related_html += movieCardHTML(movie);
            });
            movieGrid.innerHTML = related_html;
        }
        searchInput.value = '';
        searchButton.style.display = 'block';
        loader.style.display = 'none';
    })
}

searchButton.addEventListener('click',() => {
    searchMovie();
})

searchInput.addEventListener('keydown', (event) => {
    if(event.key === "Enter") {
        searchMovie();
    }
})
