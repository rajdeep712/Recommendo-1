const trailerBtn = document.querySelector('.trailer-btn');
const favBtn = document.querySelector('.favorite-btn');
const watchBtn = document.querySelector('.watch-now-btn');
const closeBtn = document.querySelector('.close-btn');
const commentBtn = document.querySelector('.comment-btn');
const loginOverlay = document.querySelector('.overlay');
// const iframe = document.querySelector('.video-frame');




trailerBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'block';
    document.body.style.overflow = 'hidden';

    closeBtn.addEventListener('click', () => {
        loginOverlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    })
})


favBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'block';
    document.body.style.overflow = 'hidden';

    closeBtn.addEventListener('click', () => {
        loginOverlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    })
})


watchBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'block';
    document.body.style.overflow = 'hidden';

    closeBtn.addEventListener('click', () => {
        loginOverlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    })
})


commentBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'block';
    document.body.style.overflow = 'hidden';

    closeBtn.addEventListener('click', () => {
        loginOverlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    })
})