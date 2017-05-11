
$(document).ready(function () {
    $(".alert-dismissible").fadeTo(7000, 500).slideUp(500, function () {
        $(".alert-dismissible").alert('close');
    });
    $("input[type='checkbox']").bootstrapToggle({
        size:"small"
    });
});