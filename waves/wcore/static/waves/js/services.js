/**
 * Created by Marc Chakiachvili on 22/11/16.
 * This is a first version, should be made available through a proper JS library.
 *
 */
(function ($) {

    function toggleDependents(elem) {
        let dependents = $("[dependent-on='" + elem.attr("name") + "']");
        let has_dep = elem.val();
        console.log('Type obj:', elem, has_dep, elem.is(':visible'));
        if (elem.attr('type') === 'checkbox' || elem.attr('type') === 'radio') {
            if (elem.prop('checked') === true)
                has_dep = 'True';
            else
                has_dep = 'False';
        }
        if (elem.attr('type') === 'file'){
            has_dep = elem.is(':visible') ? 'True': 'False';
        }
        console.log('Event fired ! ' + has_dep);
        dependents.each(function () {
            console.log('dependent:', $(this), $(this).attr('dependent-4-value'), has_dep);
            if ($(this).attr('dependent-4-value') === has_dep) {
                $('#tab_pane_' + $(this).attr('name')).toggle(true);
                $('#div_id_' + $(this).attr('name')).toggle(true)
                $(this).trigger('show');
                $(this).removeAttr('disabled');
            } else {
                $('#tab_pane_' + $(this).attr('name')).toggle(false);
                $('#div_id_' + $(this).attr('name')).toggle(false)
                $(this).trigger('hide');
                $(this).attr('disabled', '');
            }
        });
    }

    $(document).ready(function () {
        $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
            var input = $(this).parents('.input-group').find(':text'),
                log = numFiles > 1 ? numFiles + ' files selected' : label;
            if (input.length) {
                input.val(log);
            } else {
                if (log) alert(log);
            }

        });
        $(document).on('change', '.btn-file :file', function () {
            var input = $(this),
                numFiles = input.get(0).files ? input.get(0).files.length : 1,
                label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
            input.trigger('fileselect', [numFiles, label]);
        });
        $('.has_dependent').on('show hide change', function (e) {
            console.log('Type event:', $(this), e);
            toggleDependents($(this))
        });


        document.submit_waves_api_form = function (form, token) {
            /***
             * Provide simple WAVES-core api form submission using ajax JQuery, based on a classic token base authentication scheme
             *
             * @type {FormData}
             */
            var form_data = new FormData(form);
            //return new Promise(function (resolve, reject) {
            if (token != null) {
                return $.ajax({
                    type: 'POST',
                    url: form.action,
                    processData: false,
                    contentType: false,
                    data: form_data,
                    beforeSend: function (xhr) {
                        // Add auth token to XHR request
                        xhr.setRequestHeader("Authorization", "Token " + token);
                    }
                })
            } else {
                console.error("Token not provided, it's required for WAVES-core token based submission process");
            }
            //})
        }
        $(document).on('submit', "form.submit-ajax", function (event) {
            /**
             * Avoid default behavior on all form.submit-ajax submit event, may force ajax submission
             */
            event.preventDefault();
        })
    })
})(jQuery || django.jQuery);

