const navMobile = document.querySelector('.nav__items-mobile');
const navBTN = document.querySelector('.hamburger');
const allNavItems = document.querySelectorAll('.nav__item--mobile');
const footerYear = document.querySelector('.footer__year')
const header = document.querySelector('.header');

// Funkcja zmieniająca kolor hamburger menu w zależności od tła
const updateHamburgerColor = () => {
    // Jeśli menu jest aktywne, nie zmieniaj kolorów na podstawie przewijania
    if (navBTN.classList.contains('is-active')) {
        return;
    }
    // Pobieramy pozycję przewijania i pozycję headera
    const scrollY = window.scrollY;
    const headerBottom = header.offsetTop + header.offsetHeight;
    // Jeśli jesteśmy w obszarze headera, hamburger jest na ciemnym tle

    if(scrollY < headerBottom) {
        navBTN.classList.add('on-dark-bg');
    } else {
        navBTN.classList.remove('on-dark-bg');
    }
}

const handleNavMobile = () => {
    navBTN.classList.toggle('is-active');
    navMobile.classList.toggle('nav__items-mobile--active');

    // Aktualizacja stanu aria-expanded
    const isExpanded = navBTN.getAttribute('aria-expanded') === 'true';
    navBTN.setAttribute('aria-expanded', !isExpanded);

    // Aktualizacja tekstu aria-label w zależności od stanu
    navBTN.setAttribute('aria-label', isExpanded ? 'Otwórz menu' : 'Zamknij menu');

    // Gdy menu jest otwarte, zawsze używamy tego samego stylu niezależnie od pozycji przewijania
    if (navBTN.classList.contains('is-active')) {
        // Usuwamy klasę on-dark-bg, gdy menu jest aktywne
        // dzięki temu style dla .is-active będą miały priorytet
        navBTN.classList.remove('on-dark-bg');
    } else {
        // Gdy menu jest zamykane, sprawdzamy ponownie pozycję i aktualizujemy kolor
        updateHamburgerColor();
    }

    handleNavAnimation()
}

const handleNavAnimation = () => {
    let delayTime = 0;

    allNavItems.forEach((item) => {
        item.classList.toggle('nav-items-animation')
        item.style.animationDelay = '.' + delayTime + 's';
        delayTime++;
    })

}
const handleCurrentYear = () => {
    footerYear.innerText = (new Date()).getFullYear();
}

allNavItems.forEach(item => {
    item.addEventListener('click', handleNavMobile);
})

navBTN.addEventListener('click', handleNavMobile);



// Dodajemy nowy event listener do śledzenia przewijania
window.addEventListener('scroll', updateHamburgerColor);

handleCurrentYear();
updateHamburgerColor(); // Wywołujemy od razu, aby ustawić właściwy kolor na start

