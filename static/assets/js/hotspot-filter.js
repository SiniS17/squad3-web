document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('searchBtn');
    const typeSelect = document.getElementById('typeFilter');
    const zoneSelect = document.getElementById('zoneFilter');
    const cards = document.querySelectorAll('.hotspot-card');

    searchBtn.addEventListener('click', () => {
        const typeValue = typeSelect.value;
        const zoneValue = zoneSelect.value;

        cards.forEach(card => {
            const text = card.innerText;
            const matchesType = typeValue === 'ALL' || text.includes(typeValue);
            const matchesZone = zoneValue === 'ALL' || text.includes(zoneValue);

            card.style.display = (matchesType && matchesZone) ? 'block' : 'none';
        });
    });
});