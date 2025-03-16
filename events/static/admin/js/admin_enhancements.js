(function($) {
    $(document).ready(function() {
        // Dodanie przycisku "Dodaj nowe miejsce" obok pola venue
        var venueField = $('.field-venue .related-widget-wrapper');
        if (venueField.length) {
            var addButton = $('<a class="add-another" href="/admin/events/venue/add/" target="_blank">Dodaj nowe miejsce</a>');
            addButton.css('margin-left', '10px');
            venueField.append(addButton);
        }
    });
})(django.jQuery);