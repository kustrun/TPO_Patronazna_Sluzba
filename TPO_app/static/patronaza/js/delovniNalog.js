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

        } else if (!isNaN(datumPrvega) && stObiskov && !isNaN(datumZadnjega)) {

            var stDni = 0;
            var datum = datumPrvega;
            while(datum.toDateString() != datumZadnjega.toDateString()) {
                stDni++;
                datum.setDate(datum.getDate() + 1);

                if(datum.getDay() == 6) {
                    datum.setDate(datum.getDate() + 2);
                } else if(datum.getDay() == 0) {
                    datum.setDate(datum.getDate() + 1);
                }
            }

            casovniInterval = Math.round(stDni/stObiskov);

            $("#id_cas_med_dvema").val(casovniInterval);
        } else if (!isNaN(datumPrvega) && casovniInterval && !isNaN(datumZadnjega)) {

            var stDni = 2;
            var datum = datumPrvega;
            while(datum.toDateString() != datumZadnjega.toDateString()) {
                stDni++;
                datum.setDate(datum.getDate() + 1);

                if(datum.getDay() == 6) {
                    datum.setDate(datum.getDate() + 2);
                } else if(datum.getDay() == 0) {
                    datum.setDate(datum.getDate() + 1);
                }
            }

            stObiskov = Math.ceil(stDni/casovniInterval);

            for ( var i = 1; i < stObiskov; i++ ) {
                    datumZadnjega.setDate(datumZadnjega.getDate() - casovniInterval);

                    if(datumZadnjega.getDay() == 6) {
                        datumZadnjega.setDate(datumZadnjega.getDate() - 1);
                    } else if(datumZadnjega.getDay() == 0) {
                        datumZadnjega.setDate(datumZadnjega.getDate() - 2);
                    }

                }

            $("#id_datum_prvega_obiska").val(datumZadnjega.getDate() + "." + (datumZadnjega.getMonth()+1) + "." + datumZadnjega.getFullYear());
            $("#id_st_obiskov").val(stObiskov);
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

    //TIP OBISKA ADDITONAL OPTIONS
    if(typeof $('input[name=tip]:checked').val() != 'undefined' && $('input[name=tip]:checked').val().search("kurativni") >= 0 && window.location.href.indexOf("delovniNalogPodrobno") < 0) {
        $('input[name=vrstaObiska]').each(function(i,item) {
            if($(this).val().search("kurativni") < 0 && window.location.href.indexOf("delovniNalogPodrobno") < 0) {
                $(this).parent().closest('div').css("display", "none");
            } else {
                $(this).parent().closest('div').css("display", "");
            }
       });

    } else if(typeof $('input[name=tip]:checked').val() != 'undefined' && window.location.href.indexOf("delovniNalogPodrobno") < 0) {
        $('input[name=vrstaObiska]').each(function(i,item) {
            if($(this).val().search("preventivni") < 0) {
                $(this).parent().closest('div').css("display", "none");
            } else {
                $(this).parent().closest('div').css("display", "");
            }
        });
    }

    $('input[name=tip]').on('change', function() {
        if($('input[name=tip]:checked').val().search("kurativni") >= 0 && window.location.href.indexOf("delovniNalogPodrobno") < 0) {
            $('input[name=vrstaObiska]').each(function(i,item) {
                if($(this).val().search("kurativni") < 0) {
                    $(this).parent().closest('div').css("display", "none");
                } else {
                    $(this).parent().closest('div').css("display", "");
                }
            });

        } else if(window.location.href.indexOf("delovniNalogPodrobno") < 0) {
            $('input[name=vrstaObiska]').each(function(i,item) {
                if($(this).val().search("preventivni") < 0) {
                    $(this).parent().closest('div').css("display", "none");
                } else {
                    $(this).parent().closest('div').css("display", "");
                }
            });
        }
    });



    //VRSTA OBISKA ADDITIONAL OPTIONS
    $('.dynamic-izberiPacienta-add .add-row').css("display", "none");
    $('.dynamic-izberiPacienta .delete-row').css("display", "none");

    if(typeof $('input[name=vrstaObiska]:checked').val() != 'undefined' && $('input[name=vrstaObiska]:checked').val().search("aplikacija injekcij") >= 0) {
        $('#aplikacijaInjekcij').css("display", "");
        $('#odvzemKrvi').css("display", "none");

   } else if(typeof $('input[name=vrstaObiska]:checked').val() != 'undefined' && $('input[name=vrstaObiska]:checked').val().search("odvzem krvi") >= 0) {
        $('#aplikacijaInjekcij').css("display", "none");
        $('#odvzemKrvi').css("display", "");

   } else {
       $('#aplikacijaInjekcij').css("display", "none");
       $('#odvzemKrvi').css("display", "none");
   }

    $('input[name=vrstaObiska]').on('change', function() {
       if($('input[name=vrstaObiska]:checked').val().search("obisk otročnice in novorojenčka") >= 0) {
           $('.dynamic-izberiPacienta-add .add-row').click();

           $('.dynamic-izberiPacienta-add .add-row').css("display", "");
           $('.dynamic-izberiPacienta .delete-row').css("display", "");

           //Change children
           var split = $('#id_izberiPacienta-0-ime').val().split("&");

           $('#id_izberiPacienta-1-ime').val('');

           $('#id_izberiPacienta-1-ime > option').each(function() {
               var splitChild = this.value.split("&");

               if(!(this.value.search("False") >= 0 && splitChild[1] == split[1])) {
                   $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "none");
               } else if (this.value.search("False") >= 0 && splitChild[1] == split[1]) {
                   $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "");
               }
           });

       } else if ($('#izberiPacientaFormSet .dynamic-izberiPacienta').length == 2) {
           $('.dynamic-izberiPacienta .delete-row')[1].click();

           $('.dynamic-izberiPacienta-add .add-row').css("display", "none");
           $('.dynamic-izberiPacienta .delete-row').css("display", "none");
       }

       if($('input[name=vrstaObiska]:checked').val().search("aplikacija injekcij") >= 0) {
           $('#aplikacijaInjekcij').css("display", "");
            $('#odvzemKrvi').css("display", "none");

       } else if($('input[name=vrstaObiska]:checked').val().search("odvzem krvi") >= 0) {
           $('#aplikacijaInjekcij').css("display", "none");
           $('#odvzemKrvi').css("display", "");

       } else {
           $('#aplikacijaInjekcij').css("display", "none");
           $('#odvzemKrvi').css("display", "none");
       }
    });

    $('.dynamic-izberiPacienta-add .add-row').on('click', function() {
        //Change children
           var split = $('#id_izberiPacienta-0-ime').val().split("&");

           $("[id*=id_izberiPacienta]:last").val('');

           $('[id*=id_izberiPacienta]:last > option').each(function() {
               var splitChild = this.value.split("&");

               if(!(this.value.search("False") >= 0 && splitChild[1] == split[1])) {
                   $('[id*=id_izberiPacienta]:last option[value="' + this.value + '"]').css("display", "none");
               } else if (this.value.search("False") >= 0 && splitChild[1] == split[1]) {
                   $('[id*=id_izberiPacienta]:last option[value="' + this.value + '"]').css("display", "");
               }
           });
    });

    //PACIENT
    var split;
    if( typeof $('#id_izberiPacienta-0-ime').val() != 'undefined') {
        split = $('#id_izberiPacienta-0-ime').val().split("&");
    }

    $('#id_izberiPacienta-1-ime > option').each(function() {
        var splitChild = this.value.split("&");

        if(!(this.value.search("False") >= 0 && splitChild[1] == split[1])) {
            $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "none");
        } else if (this.value.search("False") >= 0 && splitChild[1] == split[1]) {
            $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "");
        }
    });

    $('#id_izberiPacienta-0-ime').on('change', function() {
        var split = $('#id_izberiPacienta-0-ime').val().split("&");

        $('#id_izberiPacienta-1-ime').val('');

        $('#id_izberiPacienta-1-ime > option').each(function() {
            var splitChild = this.value.split("&");

            if(!(this.value.search("False") >= 0 && splitChild[1] == split[1])) {
                $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "none");
            } else if (this.value.search("False") >= 0 && splitChild[1] == split[1]) {
                $('#id_izberiPacienta-1-ime option[value="' + this.value + '"]').css("display", "");
            }
        });
    });



    //DISABLE EDITING ON PAGE delovniNalogPodrobno
    if(window.location.href.indexOf("delovniNalogPodrobno") > 0) {
        $('#id_izberiPacienta-0-ime > option').each(function() {
            if(this.value.search("False") >= 0) {
                $('#id_izberiPacienta-0-ime option[value="' + this.value + '"]').remove();
            }
        });

        $('.add-row').css("display", "none");
        $('.delete-row').css("display", "none");
        $("input").prop('disabled', true);
        $("select").attr('disabled', true);

        var split = $('#id_datum_prvega_obiska').val().split("-")
        $('#id_datum_prvega_obiska').val(split[2] + "." + split[1] + "." + split[0])

        var split2 = $('#id_casovno_obdobje').val().split("-")
        $('#id_casovno_obdobje').val(split2[2] + "." + split2[1] + "." + split2[0])

    }
});
