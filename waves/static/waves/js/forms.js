/**
 * Created by marc on 07/07/16.
 * WAVES form javascript library used in base templates
 */

$(document).ready(function () {
    $(".has_dependent").change(function(elem){
        /*
          * for each inputs with related_inputs, hide all except the one corresponding
          * to input value
         */
        var dependents = $("[dependent-on='" + $(this).attr("name") + "']")
        var has_dep = $(this).val();
        console.log('Type obj:', $(this).attr('type'));
        if ($(this).attr('type') == 'checkbox' || $(this).attr('type') == 'radio') {
            if ($(this).prop('checked') == true)
                has_dep = 'True';
            else
                has_dep = 'False';
            console.log('In Array ', $(this).attr('type'), $(this).val());
        }
        console.log('Event fired ! ' + has_dep);
        dependents.each(function() {
            console.log($(this), $(this).attr('dependent-4-value'), has_dep);
            if ($(this).attr('dependent-4-value') == has_dep) {
                $('#div_id_' + $(this).attr('name')).removeClass('hid_dep_parameter');
                $('#tab_pane_' + $(this).attr('name')).removeClass('hid_dep_parameter');
                $(this).removeAttr('disabled');
            } else {
                $('#div_id_' + $(this).attr('name')).addClass('hid_dep_parameter');
                $('#tab_pane_' + $(this).attr('name')).addClass('hid_dep_parameter');
                $(this).attr('disabled', '');
            }
        });
    });


    // TODO add function to disable/enable associated file fields when selecting a sample
});


