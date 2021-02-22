var BILLINGID;
var DELIVERYID;
const htmlBtnReset = `<button type="button" class="btn btn-danger btn-sm btn_reset">Reset</button>`;
const htmlBtnDeliver = `<button type="button" class="btn btn-success btn-sm btn_deliver">Deliver</button>`;
const htmlBtnDetails = `<button type="button" class="btn btn-primary btn-sm btn_details" data-toggle="modal" data-target="#details_modal" data-placement="bottom">Details</button>`;
const divMunicipalityButtons = $("#divMunicipalityButtons");
const divAreaButtons = $("#divAreaButtons");
const divSubAreaButtons = $("#divSubAreaButtons");
var btnMunicipalityLabel = $("#btnMunicipalityLabel");
var btnAreaLabel = $("#btnAreaLabel");
var btnSubAreaLabel = $("#btnSubAreaLabel");
var dtbl_subscribers;
//call onLoad func...


function onLoad() {
    var sessMunicipality = localStorage.getItem('sessMunicipality');
    var sessArea = localStorage.getItem('sessArea');
    var sessSubArea = localStorage.getItem('sessSubArea');
    var sessSubAreaID = localStorage.getItem('sessSubAreaID');
    BILLINGID = localStorage.getItem('billingID');
    
    $("#btnSubAreaLabel").val(sessSubAreaID);

    if (!(sessSubAreaID)) {
        $("#btnSubAreaLabel").val(0);
    }

    if (BILLINGID) {
        $("#div_subscribers_card").show();
        $("#div_no_selected_billing_card").hide();

        initializeTable();

        getBillingInfo(BILLINGID);

        getMunicipalities();

        btnMunicipalityLabel.html("Choose Municipality...");
        btnAreaLabel.html("Choose Area...");
        btnSubAreaLabel.html("Choose SubArea...");

        if (sessMunicipality) {

            btnMunicipalityLabel.html(sessMunicipality.toUpperCase());
            getMunicipalityAreas(sessMunicipality);

            if (sessArea) {
                btnAreaLabel.html(sessArea.toUpperCase());
                getAreaSubAreas(sessArea);
            }

            if (sessSubArea) {
                btnSubAreaLabel.html(sessSubArea.toUpperCase());
            }

        }

    } else {
        $("#div_subscribers_card").hide();
        $("#div_no_selected_billing_card").show();
    }
}


function initializeTable(){
    dtbl_subscribers = $('#tbl_subscribers').DataTable({
        sDom: 'lrtip',
        pageLength: 25,
        "processing": true,
        serverSide: true,
        ordering: false,
        columnDefs: [
            {
                "targets": 0,
                "visible": false,
            },
            {
                "targets": 4,
                "render": function (data, type, row) {
                    if (data == "NOT YET DELIVERED") {
                        return `<div class="badge badge-info">NOT YET DELIVERED</div>`;
                    } else if (data == "IN-PROGRESS") {
                        return `<div class="badge badge-danger">IN-PROGRESS</div>`;
                    } else if (data == "DELIVERED") {
                        return `<div class="badge badge-success">DELIVERED</div>`;
                    } else if (data == "PENDING") {
                        return `<div class="badge badge-warning">PENDING</div>`;
                    }
                },
            },
            {
                "targets": 5,
                "render": function (data, type, row) {
                    if (row[4] == "NOT YET DELIVERED") {
                        return htmlBtnDeliver;
                    } else if (row[4] == "IN-PROGRESS") {
                        return htmlBtnReset;
                    } else if (row[4] == "DELIVERED") {
                        return htmlBtnReset + htmlBtnDetails;
                    } else if (row[4] == "PENDING") {
                        return htmlBtnReset + htmlBtnDetails;
                    }
                }
            }
        ],
        ajax: {
            url: "/bds/api/sub-areas/" + $("#btnSubAreaLabel").val() + "/subscribers",
            data: function (d) {
                d.billing_id = BILLINGID;
            }
        }
    });
}


function getBillingInfo(billing_id){
    const url = "/bds/api/billings/" + billing_id;

    $.ajax({
        url: url,
        type: "GET",
        success: function(data){
            if(data){
                $("#billing_no").val(data.number);
                $("#name").val(data.name);
                $("#date_from").val(data.date_from);
                $("#date_to").val(data.date_to);
            }
        }
    })
}

function getMunicipalities() {
    const url = "/bds/api/municipalities";

    $.ajax({
        url: url,
        type: "GET",
        success: function (data) {

            if (data) {
                for (i = 0; i < data.length; ++i) {
                    divMunicipalityButtons.append(`<button type="button" tabindex="0" class="dropdown-item btn-municipality">${data[i].name}</button>`)
                }
            } else {
                divMunicipalityButtons.append(`
                    <h6 tabindex="-1" class="dropdown-header">No municipalities yet</h6>`
                );
            }

        }
    });
}


function getMunicipalityAreas(municipality_name) {

    const url = "/bds/api/get-municipality-areas?municipality_name=" + municipality_name.trim();

    $.ajax({
        url: url,
        type: "GET",
        success: function (data) {
            divAreaButtons.empty();
            divSubAreaButtons.empty();

            if (data.result.length > 0) {
                for (i = 0; i < data.result.length; ++i) {
                    divAreaButtons.append(`<button type="button" tabindex="0" class="dropdown-item btn-area">${data.result[i].name}</button>`)
                }

            } else {
                divAreaButtons.append(`
                <h6 tabindex="-1" class="dropdown-header">No areas yet</h6>`
                );
            }
        }
    });
}


function getAreaSubAreas(area_name) {

    const url = "/bds/api/get-area-sub-areas?area_name=" + area_name.trim();

    $.ajax({
        url: url,
        type: "GET",
        success: function (data) {

            divSubAreaButtons.empty();

            if (data.result.length > 0) {
                for (i = 0; i < data.result.length; ++i) {
                    divSubAreaButtons.append(`<button value="${data.result[i].id}" type="button" tabindex="0" class="dropdown-item btn-sub-area">${data.result[i].name}</button>`);
                }
            } else {
                divSubAreaButtons.append(`
                <h6 tabindex="-1" class="dropdown-header">No sub areas yet</h6>`
                );
            }

        }
    })
}


function show_toast(type) {
    if (type == "success") {
        $(".toast-success").show();
    } else if (type == "error") {
        $(".toast-error").show();
    }
}


function hide_toast(type) {
    if (type == "success") {
        $(".toast-success").hide();
    } else if (type == "error") {
        $(".toast-error").hide();
    }
}


$(document).ready(function () {

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    onLoad();

    $('.search-input').on('keyup', function () {
        dtbl_subscribers.search(this.value).draw();
    });


    $("#divMunicipalityButtons").on('click', '.btn-municipality', function () {
        var _municipality_name = $(this).html();

        if (!(localStorage.getItem('sessMunicipality') == _municipality_name)) {
            btnAreaLabel.html("Choose Area...");
            btnSubAreaLabel.html("Choose Sub Area...");
            btnMunicipalityLabel.html(_municipality_name.toUpperCase());

            localStorage.setItem('sessMunicipality', _municipality_name);
            getMunicipalityAreas(localStorage.getItem('sessMunicipality'));

            localStorage.removeItem('sessArea');
            localStorage.removeItem('sessSubArea');
        }

    });


    $("#divAreaButtons").on('click', '.btn-area', function () {
        var _area_name = $(this).html();

        console.log(localStorage.getItem('sessArea'), _area_name);
        // if(!(localStorage.getItem('sessArea') == _area_name)){
        $("#btnSubAreaLabel").html("Choose Sub Area...");
        $("#btnAreaLabel").html(_area_name.toUpperCase());

        localStorage.setItem('sessArea', _area_name);
        getAreaSubAreas(localStorage.getItem('sessArea'));
        localStorage.removeItem('sessSubArea');

        // }

    });


    $("#divSubAreaButtons").on('click', '.btn-sub-area', function () {
        var _sub_area_name = $(this).html();

        // if(!(localStorage.getItem('sessSubArea') == _sub_area_name)){
        $("#btnSubAreaLabel").html(_sub_area_name.toUpperCase());
        $("#btnSubAreaLabel").val($(this).val());

        localStorage.setItem('sessSubAreaID', $(this).val());
        localStorage.setItem('sessSubArea', _sub_area_name);

        dtbl_subscribers.ajax.url(`/bds/api/sub-areas/${$(this).val()}/subscribers`).load();
        // }

    });


    $("#btn_deliver_all").click(function () {
        var sessSubArea = localStorage.getItem('sessSubArea');
        
        $.ajax({
            url: "/bds/api/deliveries/deliver-all",
            type: "POST",
            dataType: "json",
            data: JSON.stringify({ 'sub_area_name': sessSubArea, 'billing_id': BILLINGID}),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    show_toast('success');
                } else {
                    show_toast('error');
                }
                dtbl_subscribers.ajax.reload();
            }
        });
    });


    $("#btn_reset_all").click(function () {
        var subAreaName = $("#btnSubAreaLabel").html().trim();

        $.ajax({
            url: "/bds/api/deliveries/reset-all",
            type: "POST",
            dataType: "json",
            data: JSON.stringify({ 'sub_area_name': subAreaName }),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    show_toast('success');
                } else {
                    show_toast('error');
                }
                dtbl_subscribers.ajax.reload();
            }
        });
    });


    $("#tbl_subscribers tbody").on('click', '.btn_deliver', function () {
        var $row = $(this).closest('tr');

        // Get row data
        var data = dtbl_subscribers.row($row).data();

        // Get row ID
        var rowId = data[0];

        const url = "/bds/api/subscribers/" + rowId + "/deliveries/deliver";

        $.ajax({
            url: url,
            type: "POST",
            dataType: "json",
            data: JSON.stringify({
                'billing_id': BILLINGID,
            }),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    dtbl_subscribers.ajax.reload();
                    show_toast('success');
                } else {
                    show_toast('error');
                }
            }
        });

    });


    $("#tbl_subscribers").on('click', '.btn_reset', function () {
        var subscriberContractNo = $(this).closest("tr").children('td:first').text();
        var area_name = $("#btnAreaLabel").html();
        var sub_area_name = $("#btnSubAreaLabel").html().trim();

        $.ajax({
            url: "/bds/api/subscriber/delivery/reset",
            type: "POST",
            dataType: "json",
            data: JSON.stringify({
                'subscriber_contract_no': subscriberContractNo,
                'sub_area_name': sub_area_name,
                'area_name': area_name
            }),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    dtbl_subscribers.ajax.reload();
                    show_toast('success');
                } else {
                    show_toast('error');
                }
            }
        });

    });


    $("#tbl_subscribers").on('click', '.btn_details', function () {
        var $row = $(this).closest('tr');

        // Get row data
        var data = dtbl_subscribers.row($row).data();

        // Get row ID
        var rowId = data[0];

        const url = "/bds/subscribers/" + rowId + "/delivery" + `?billing_id=` + BILLINGID;

        $.ajax({
            url: url,
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.id) {
                    DELIVERYID = data.id;

                    //body
                    $("#div_details_content").empty();
                    $("#div_details_content").append(
                        `
                        <img src="${data.image_path}" class="img-fluid" alt="Responsive image">
                        `
                    );

                    //details
                    $("#li_subscriber").empty();
                    $("#li_subscriber").append(`<i class="pe-7s-user"> </i>` + "<strong> " + data.subscriber_fname + " " + data.subscriber_lname + "</strong>");
                    $("#li_address").empty();
                    $("#li_address").append(`<i class="pe-7s-map-marker"> </i>` + "<strong> " + data.subscriber_address + "</strong>");
                    $("#li_location").empty();
                    $("#li_location").append(
                        `<i class="pe-7s-map-2"> </i>
                        ` + "<strong>LAT: " + data.latitude + " | LONG: " + data.longitude
                        + " | ACC: " + data.accuracy + "</strong>"
                    );
                    $("#li_mobile_date").empty();
                    $("#li_mobile_date").append(`<i class="pe-7s-id"> </i>` + "<strong> " + data.messenger_fname + " " + data.messenger_lname + "</strong>" + "    " + `<i class="pe-7s-date"> </i>` + "<strong> " + data.date_mobile_delivery + "</strong>");

                    if (data.status == "PENDING") {
                        //footer
                        $("#div_modal_footer").empty();
                        $("#div_modal_footer").append(
                            `
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                            <button id="btn_confirm" type="button" class="btn btn-success">Confirm</button>
                            `
                        );

                        //title
                        $("#card_title").empty();
                        $("#card_title").append(
                            `<div class="badge badge-warning">PENDING</div>`
                        );
                    } else if (data.status == "DELIVERED") {
                        //title
                        $("#card_title").empty();
                        $("#card_title").append(
                            `<div class="badge badge-success">DELIVERED</div>`
                        );
                    }
                }

            }
        });

    });

    $("#div_modal_footer").on('click', '#btn_confirm', function () {
        const url = "/bds/api/delivery/" + DELIVERYID + "/confirm";

        $.ajax({
            url: url,
            type: "POST",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    show_toast('success');
                    $("#btn_confirm").remove();
                    dtbl_subscribers.ajax.reload();
                } else {
                    show_toast('error');
                }

            }
        });
    });

    $(".toast-error").on('click', function () {
        hide_toast('error');
    });

    $(".toast-success").on('click', function () {
        hide_toast('success');
    });

});