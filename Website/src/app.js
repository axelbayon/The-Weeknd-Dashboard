// Navigation entre les pages
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('[data-page]');
    const pages = document.querySelectorAll('[data-page-content]');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.dataset.page;

            // Mettre à jour les liens actifs
            navLinks.forEach(l => l.classList.remove('topbar__link--active'));
            link.classList.add('topbar__link--active');

            // Afficher la page correspondante
            pages.forEach(page => {
                if (page.dataset.pageContent === targetPage) {
                    page.style.display = 'flex';
                } else {
                    page.style.display = 'none';
                }
            });
        });
    });
});
