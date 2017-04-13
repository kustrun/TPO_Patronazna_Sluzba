$(document).ready(function(){

    //FORMSET
    $('#zdravilaFormSet tbody tr').formset({
        prefix: 'zdravila',
        formCssClass: 'dynamic-zdravila'
    });
    $('#barvaEpruvetFormSet tbody tr').formset({
        prefix: 'barva',
        formCssClass: 'dynamic-barva'
    });
    $('#izberiPacientaFormSet tbody tr').formset({
        prefix: 'izberiPacienta',
        formCssClass: 'dynamic-izberiPacienta'
    });


    //DATE CALTULATION
    function calculateDate(last) {
        var datumPrvega = $("#id_datum_prvega_obiska").val();
        var dsplit = datumPrvega.split(".");
        datumPrvega=new Date(dsplit[2],dsplit[1]-1,dsplit[0]);

        var stObiskov = parseInt($("#id_st_obiskov").val());
        var casovniInterval =  parseInt($("#id_cas_med_dvema").val()) + 1;

        var datumZadnjega = $("#id_casovno_obdobje").val();
        dsplit = datumZadnjega.split(".");
        datumZadnjega=new Date(dsplit[2],dsplit[1]-1,dsplit[0]);

        if(stObiskov && casovniInterval) {

            if(!isNaN(datumPrvega) && !last) {

                if(datumPrvega.getDay() == 6) {
                    datumPrvega.setDate(datumPrvega.getDate() + 2);
                } else if(datumPrvega.getDay() == 0) {
                    datumPrvega.setDate(datumPrvega.getDate() + 1);
                }

                for ( var i = 1; i < stObiskov; i++ ) {
                    datumPrvega.setDate(datumPrvega.getDate() + casovniInterval);

                    if(datumPrvega.getDay() == 6) {
                        datumPrvega.setDate(datumPrvega.getDate() + 2);
                    } else if(datumPrvega.getDay() == 0) {
                        datumPrvega.setDate(datumPrvega.getDate() + 1);
                    }

                }

                $("#id_casovno_obdobje").val(datumPrvega.getDate() + "." + (datumPrvega.getMonth()+1) + "." + datumPrvega.getFullYear());
            } else if(!isNaN(datumZadnjega) && last) {

                if(datumZadnjega.getDay() == 6) {
                    datumZadnjega.setDate(datumZadnjega.getDate() - 1);
                } else if(datumZadnjega.getDay() == 0) {
                    datumZadnjega.setDate(datumZadnjega.getDate() - 2);
                }

                for ( var i = 1; i < stObiskov; i++ ) {
                    datumZadnjega.setDate(datumZadnjega.getDate() - casovniInterval);

                    if(datumZadnjega.getDay() == 6) {
                        datumZadnjega.setDate(datumZadnjega.getDate() - 1);
                    } else if(datumZadnjega.getDay() == 0) {
                        datumZadnjega.setDate(datumZadnjega.getDate() - 2);
                    }

                }

                $("#id_datum_prvega_obiska").val(datumZadnjega.getDate() + "." + (datumZadnjega.getMonth()+1) + "." + datumZadnjega.getFullYear());

            }

        }
    }

    $('#id_datum_prvega_obiska').blur(function () {

        calculateDate(false);

    });

    $('#id_st_obiskov').blur(function () {

        calculateDate(false);

    });

    $('#id_cas_med_dvema').blur(function () {

        calculateDate(false);

    });

    $('#id_casovno_obdobje').blur(function () {

        calculateDate(true);

    });

    $('.dynamic-izberiPacienta-add .add-row').css("display", "none");
    $('.dynamic-izberiPacienta .delete-row').css("display", "none");


    if($('input[name=vrstaObiska]:checked').val() == "aplikacija injekcij") {
       $('#aplikacijaInjekcij').css("display", "");
        $('#odvzemKrvi').css("display", "none");

   } else if($('input[name=vrstaObiska]:checked').val() == "odvzem krvi") {
       $('#aplikacijaInjekcij').css("display", "none");
       $('#odvzemKrvi').css("display", "");

   } else {
       $('#aplikacijaInjekcij').css("display", "none");
       $('#odvzemKrvi').css("display", "none");
   }

    $('input[name=vrstaObiska]').on('change', function() {
       if($('input[name=vrstaObiska]:checked').val() == "obisk otročnice in novorojenčka") {
           $('.dynamic-izberiPacienta-add .add-row').click();

           $('.dynamic-izberiPacienta-add .add-row').css("display", "none");
           $('.dynamic-izberiPacienta .delete-row').css("display", "none");

       } else if ($('#izberiPacientaFormSet .dynamic-izberiPacienta').length == 2) {
           $('.dynamic-izberiPacienta .delete-row')[1].click();

           $('.dynamic-izberiPacienta-add .add-row').css("display", "none");
           $('.dynamic-izberiPacienta .delete-row').css("display", "none");
       }

       if($('input[name=vrstaObiska]:checked').val() == "aplikacija injekcij") {
           $('#aplikacijaInjekcij').css("display", "");
            $('#odvzemKrvi').css("display", "none");

       } else if($('input[name=vrstaObiska]:checked').val() == "odvzem krvi") {
           $('#aplikacijaInjekcij').css("display", "none");
           $('#odvzemKrvi').css("display", "");

       } else {
           $('#aplikacijaInjekcij').css("display", "none");
           $('#odvzemKrvi').css("display", "none");
       }
    });

});