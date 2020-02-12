(function ($) {
    $(document).ready(function () {
        var input_group = $('#inputs-group')
        input_group.find('a.inlinechangelink').each(function () {
            var href = $(this).attr('href')
            if (href.indexOf('?') === -1) {
                href += '?_popup=1';
            } else {
                href += '&_popup=1';
            }
            $(this).attr('href', href);
            $(this).addClass('related-widget-wrapper-link change-related')
        });
        $(document).on('formset:added', function (event, $row, formsetName) {
            if (formsetName === 'inputs') {
                // Do something
                event.preventDefault();
                event.stopPropagation();
                $row.remove()
                $('#add_submission_input_link').trigger('click');
            }
        });

        $(document).on('formset:removed', function (event, $row, formsetName) {
            // Row removed
        });
    })
})(jQuery || django.jQuery);