$("#id_datum_rojstva").focusout(function(){
    var regEx = /^\d{2}.\d{2}.\d{4}$/;
    if($("#id_datum_rojstva").val().match(regEx)){
        $("#nepravilni_datum").html("Nepravilni format datuma. Pavilni %d.%m.%Y.")
    }
});