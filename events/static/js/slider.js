const sliderBox = document.querySelector('.slider__box')
const leftBtn = document.querySelector('.btn--left')
const rightBtn = document.querySelector('.btn--right')
const carouselImages = document.querySelectorAll('.slider__img')

const carouselSpeed = 3000

// Funkcja określająca szerokość karuzeli na podstawie aktualnej szerokości ekranu
function getCarouselWidth() {
    const slider = document.querySelector('.slider');
    return slider.offsetWidth;
}
// Inicjalizacja szerokości karuzeli od razu po załadowaniu DOM
let carouselWidth = getCarouselWidth();

// Dodaj wywołanie funkcji po pełnym załadowaniu strony
window.addEventListener('load', () => {
    carouselWidth = getCarouselWidth();
    changeImage();
});

// Nasłuchiwanie na zmianę rozmiaru okna
window.addEventListener('resize', () => {
    carouselWidth = getCarouselWidth();
    changeImage(); // Aktualizacja pozycji przy zmianie rozmiaru
});


let index = 0

const handleCarousel = () => {
    index++
    changeImage()
}

let startCarousel = setInterval(handleCarousel, carouselSpeed)

const changeImage = () => {
    if (index > carouselImages.length - 1) {
        index = 0
    } else if (index < 0) {
        index = carouselImages.length - 1
    }

    sliderBox.style.transform = `translateX(${-index * carouselWidth}px)`
}

const handleRightArrow = () => {
    index++
    resetInterval()
}

const handleLeftArrow = () => {
    index--
    resetInterval()
}

const resetInterval = () => {
    changeImage()
    clearInterval(startCarousel)
    startCarousel = setInterval(handleCarousel, carouselSpeed)
}



rightBtn.addEventListener('click', handleRightArrow)

leftBtn.addEventListener('click', handleLeftArrow)
