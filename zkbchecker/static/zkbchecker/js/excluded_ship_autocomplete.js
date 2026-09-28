(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const nameInput = document.getElementById('id_name');
        const shipTypeIdInput = document.getElementById('id_ship_type_id');

        if (!nameInput || !shipTypeIdInput) {
            return;
        }

        // Show a small "selected ship" indicator next to the hidden field
        const indicator = document.createElement('div');
        indicator.className = 'zkb-selected-ship';
        indicator.style.cssText = 'margin-top: 5px; font-size: 0.9em; color: #6c757d;';
        shipTypeIdInput.parentNode.appendChild(indicator);

        function updateIndicator() {
            if (shipTypeIdInput.value) {
                indicator.textContent = `Selected ship type ID: ${shipTypeIdInput.value}`;
            } else {
                indicator.textContent = 'No ship selected yet.';
            }
        }
        updateIndicator();

        let ships = [];
        let suggestionsBox = null;

        fetch('/zkbchecker/ship-list/')
            .then((r) => r.json())
            .then((data) => {
                ships = data.ships || [];
            });

        function hideSuggestions() {
            if (suggestionsBox) {
                suggestionsBox.remove();
                suggestionsBox = null;
            }
        }

        function showSuggestions(matches) {
            hideSuggestions();

            if (matches.length === 0) {
                return;
            }

            const rect = nameInput.getBoundingClientRect();

            suggestionsBox = document.createElement('ul');
            suggestionsBox.className = 'zkb-ship-suggestions';
            suggestionsBox.style.cssText = `
                position: fixed;
                z-index: 1000;
                list-style: none;
                margin: 0;
                padding: 4px 0;
                background: #212529;
                border: 1px solid #495057;
                border-radius: 4px;
                max-height: 220px;
                overflow-y: auto;
                width: ${rect.width}px;
                top: ${rect.bottom + 2}px;
                left: ${rect.left}px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
            `;

            matches.slice(0, 10).forEach((ship) => {
                const li = document.createElement('li');
                li.textContent = `${ship.name} (${ship.id})`;
                li.style.cssText = 'padding: 6px 12px; cursor: pointer; color: #f8f9fa;';
                li.addEventListener('mouseenter', function () {
                    li.style.background = '#343a40';
                });
                li.addEventListener('mouseleave', function () {
                    li.style.background = 'transparent';
                });
                li.addEventListener('mousedown', function (event) {
                    event.preventDefault();
                    nameInput.value = ship.name;
                    shipTypeIdInput.value = ship.id;
                    updateIndicator();
                    hideSuggestions();
                });
                suggestionsBox.appendChild(li);
            });

            document.body.appendChild(suggestionsBox);
        }

        nameInput.addEventListener('input', function () {
            const query = nameInput.value.trim().toLowerCase();
            if (query.length < 2) {
                hideSuggestions();
                return;
            }

            const matches = ships.filter((s) => s.name.toLowerCase().includes(query));
            showSuggestions(matches);
        });

        nameInput.addEventListener('blur', function () {
            setTimeout(hideSuggestions, 150);
        });
    });
})();