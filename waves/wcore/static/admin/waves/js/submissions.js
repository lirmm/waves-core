(function ($) {
    $(document).ready(function () {
        $('#inputs-group').find('a.inlinechangelink').each(function () {
            var href = $(this).attr('href')
            if (href.indexOf('?') === -1) {
                href += '?_popup=1';
            } else {
                href += '&_popup=1';
            }
            $(this).attr('href', href);
            $(this).addClass('related-widget-wrapper-link change-related')
        });
        $('#inputs-group').find('tr.add-row a').each(function () {
            $(this).off("click");
            $(this).on('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                $('#add_submission_input_link').trigger('click');
            });
        });
    })
})(django.jQuery || jQuery);