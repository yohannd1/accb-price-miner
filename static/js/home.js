import Cookies from "./cookie.min.mjs";
import { showMessage } from "./misc.mjs";

let ESTAB_DATA = undefined;
let PRODUCT_DATA = undefined;
let CANCEL_CAPTCHA = false;
let EDIT_FORM_DATA = undefined;

const updateProgressBar = (newValue) => {
    const pb = document.querySelector("#progress_bar");
    if (pb == null) {
        console.log("#progress_bar não encontrada");
        return;
    }

    const encoded = newValue.toFixed(0).toString() + "%";
    pb.textContent = encoded;
    pb.style.width = encoded;
};

/**
 * Filtra a aba de pesquisa de acordo com o mês passado
 * @param  {string} month
 */
function filter_search(month) {
    // var search_id = $("#search-select").val();

    // if (search_id == "null") {
    //     alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
    //     return;
    // }

    $.get("/select_search_info", { month: month }, (response) => {
        if (response.status !== "success") {
            showMessage(response.message, { notification: false });
            return false;
        }

        const data = response.data;

        if (data.length == 0) {
            showMessage("Nenhuma pesquisa cadastrada para esse mês.", { notification: false });
            return false;
        }

        $("#search-loader").fadeIn(500);
        $(".tr-item").remove();

        $("#search-select option").remove();
        data.map((value) => {
            $("#search-select").append(`<option city=${value[2]} value=${value[1]}>${value[2]} ${value[3]}</option>`);
        });

        $("#search-select").parent().find(".styledSelect").remove();
        $("#search-select").parent().find("ul.options").remove();
        list_search(data[0][0]);
        custom_select_search();

        return true;
    });
}
/**
 * Função de ajuda para a similarity, retorna a distancia entre as palavras.
 * @param  {string} s1
 * @param  {string} s2
 */
function distance(s1, s2) {
    s1 = s1.toLowerCase();
    s2 = s2.toLowerCase();

    var costs = new Array();
    for (var i = 0; i <= s1.length; i++) {
        var lastValue = i;
        for (var j = 0; j <= s2.length; j++) {
            if (i == 0)
                costs[j] = j;
            else {
                if (j > 0) {
                    var newValue = costs[j - 1];
                    if (s1.charAt(i - 1) != s2.charAt(j - 1))
                        newValue = Math.min(Math.min(newValue, lastValue),
                            costs[j]) + 1;
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                }
            }
        }
        if (i > 0)
            costs[s2.length] = lastValue;
    }
    return costs[s2.length];
}
/**
 * Cria um input customizado select na página de configuração.
 */
const custom_select = () => {

    $('.config-menu select').each(function () {

        // Cache the number of options
        var $this = $(this),
            numberOfOptions = $(this).children('option').length;

        // Hides the select element
        $this.addClass('s-hidden');

        // Wrap the select element in a div
        $this.wrap('<div class="select"></div>');

        // Insert a styled div to sit over the top of the hidden select element
        $this.after('<div class="styledSelect z-depth-2"></div>');

        // Cache the styled div
        var $styledSelect = $this.next('div.styledSelect');

        // Show the first select option in the styled div
        $styledSelect.text($this.children('option').eq(0).text());

        // Insert an unordered list after the styled div and also cache the list
        var $list = $('<ul />', {
            'class': 'options'
        }).insertAfter($styledSelect);

        // Insert a list item into the unordered list for each select option
        for (var i = 0; i < numberOfOptions; i++) {
            $('<li />', {
                text: $this.children('option').eq(i).text(),
                rel: $this.children('option').eq(i).val()
            }).appendTo($list);
        }

        // Cache the list items
        var $listItems = $list.children('li');

        // Show the unordered list when the styled div is clicked (also hides it if the div is clicked again)
        $styledSelect.click(function (e) {
            e.stopPropagation();
            $("#search-select").parent().parent().find("div.styledSelect.active").each(function () {
                $(this).removeClass('active').next('ul.options').hide();
            });
            $(this).toggleClass('active').next('ul.options').toggle();
        });

        // Hides the unordered list when a list item is clicked and updates the styled div to show the selected list item
        // Updates the select element to have the value of the equivalent option
        $listItems.click(function (e) {
            e.stopPropagation();
            $styledSelect.text($(this).text()).removeClass('active');
            $this.val($(this).attr('rel'));
            $list.hide();
            list_estab($this.val());
            $('#city_name-save').val($this.val()).change();
            $('#city-edit-select').val($this.val()).change();
            $('#city-delete-select').val($this.val()).change();
            $('#city-delete-select').formSelect();
            $('#city-edit-select').formSelect();
            $('#city_name-save').formSelect();
        });

        // Hides the unordered list when clicking outside of it
        $(document).click(function () {
            $styledSelect.removeClass('active');
            $list.hide();
        });

    });

}
/**
 * Cria um input customizado select na página de pesquisa para os meses.
 */
const custom_select_date = () => {
    $('#month-picker').each(function () {
        // Cache the number of options
        var $this = $(this),
            numberOfOptions = $(this).children('option').length;

        // Hides the select element
        $this.addClass('s-hidden');

        // Wrap the select element in a div
        $this.wrap('<div class="select" style="margin: 0 10px;"></div>');

        // Insert a styled div to sit over the top of the hidden select element
        $this.after('<div class="styledSelect z-depth-2"></div>');

        // Cache the styled div
        var $styledSelect = $this.next('div.styledSelect');

        // Show the first select option in the styled div
        $styledSelect.text($this.children('option:selected').text());

        // Insert an unordered list after the styled div and also cache the list
        var $list = $('<ul />', {
            'class': 'options'
        }).insertAfter($styledSelect);

        // Insert a list item into the unordered list for each select option
        for (var i = 0; i < numberOfOptions; i++) {
            $('<li />', {
                text: $this.children('option').eq(i).text(),
                rel: $this.children('option').eq(i).val()
            }).appendTo($list);
        }

        // Cache the list items
        var $listItems = $list.children('li');

        // Show the unordered list when the styled div is clicked (also hides it if the div is clicked again)
        $styledSelect.click(function (e) {
            e.stopPropagation();
            $("#month-picker").parent().parent().find("div.styledSelect.active").each(function () {
                $(this).removeClass('active').next('ul.options').hide();
            });
            $(this).toggleClass('active').next('ul.options').toggle();
        });

        // Hides the unordered list when a list item is clicked and updates the styled div to show the selected list item
        // Updates the select element to have the value of the equivalent option
        $listItems.click(function (e) {
            e.stopPropagation();
            if ($(this).attr('rel') != $this.val()) {
                var filter = filter_search(parseInt($(this).attr('rel')) + 1);
                if (filter) {
                    $styledSelect.text($(this).text()).removeClass('active');
                    $this.val($(this).attr('rel'));
                    $list.hide();
                } else {
                    $list.hide();
                }
            } else {
                $list.hide();
            }
        });

        // Hides the unordered list when clicking outside of it
        $(document).click(function () {
            $styledSelect.removeClass('active');
            $list.hide();
        });
    });
}

/**
 * Cria um input customizado select na página de pesquisa para as pesquisas.
 */
const custom_select_search = () => {
    $('#pesquisa #search-select').each(function () {
        // Cache the number of options
        var $this = $(this),
            numberOfOptions = $(this).children('option').length;

        // Hides the select element
        $this.addClass('s-hidden');

        // Wrap the select element in a div
        $this.wrap('<div class="select"></div>');

        // Insert a styled div to sit over the top of the hidden select element
        $this.after('<div class="styledSelect z-depth-2"></div>');

        // Cache the styled div
        var $styledSelect = $this.next('div.styledSelect');

        // Show the first select option in the styled div
        $styledSelect.text($this.children('option').eq(0).text());

        // Insert an unordered list after the styled div and also cache the list
        var $list = $('<ul />', {
            'class': 'options'
        }).insertAfter($styledSelect);

        // Insert a list item into the unordered list for each select option
        for (var i = 0; i < numberOfOptions; i++) {
            $('<li />', {
                text: $this.children('option').eq(i).text(),
                rel: $this.children('option').eq(i).val()
            }).appendTo($list);
        }

        // Cache the list items
        var $listItems = $list.children('li');

        // Show the unordered list when the styled div is clicked (also hides it if the div is clicked again)
        $styledSelect.click(function (e) {
            e.stopPropagation();
            $("#city-select").parent().parent().find("div.styledSelect.active").each(function () {
                $(this).removeClass('active').next('ul.options').hide();
            });
            $(this).toggleClass('active').next('ul.options').toggle();
        });

        // Hides the unordered list when a list item is clicked and updates the styled div to show the selected list item
        // Updates the select element to have the value of the equivalent option
        $listItems.click(function (e) {
            e.stopPropagation();
            $styledSelect.text($(this).text()).removeClass('active');
            $this.val($(this).attr('rel'));
            $list.hide();
            list_search($this.val());
        });

        // Hides the unordered list when clicking outside of it
        $(document).click(function () {
            $styledSelect.removeClass('active');
            $list.hide();
        });
    });
}

// Listagem de cidades
/**
 * Lista todos os estabelecimentos para uma cidade de id CITY, na pagina de configuração.
 * @param  {integer} city=undefined
 */
const list_estab = (city = undefined) => {

    if (city == undefined)
        city = $("city").attr('value');
    else {
        $(".estab-config").remove();
        $("#no-result").hide();
    }

    $.get("/select_estab", { city: city }, (response) => {

        response = JSON.parse(response);
        ESTAB_DATA = response;
        if (response.length == 0) {

            $("#no-result").fadeIn(500);

        } else {
            response.map((value, index) => {
                $(`
                    <div class="z-depth-3 estab-config edit" id="ed-${value[1]}" value="${value[1]}">
                        <p>${value[1]}</p>
                        <div class="right">
                            <a  id="e-${value[1]}" value="${value[1]}" class="btn-floating btn-large   primary_color edit "  ><i class="fa fa-edit"></i></a>
                            <a  value="${value[1]}" class="remove-estab btn-floating btn-large  red " data-position="left" ><i class="fa fa-minus"></i></a>
                        </div>
                    </div>
                `).appendTo("#list-config").hide().slideDown("slow");
            });
        }

    });


}

// Lista Pesquisas
/**
 * Lista todos os dados de pesquisas para uma pesquisa de id search_id, na pagina de pesquisas.
 * @param  {integer} search_id=undefined
 */
const list_search = (search_id = undefined) => {

    $("#search-loader").show();

    if (search_id == undefined) {

        search_id = $("#search-select").val();

    }
    else if (search_id == null) {
        $(".no-result").fadeIn(500);
        $("#search-loader").fadeOut(500);
        return;
    } else {
        $(".no-result").hide();
        // $("#search-tbody tr").remove();
    }

    $(".tr-item").remove();
    // console.log(search_id);

    $.get("/select_search_data", { search_id: search_id }, (response) => {

        response = JSON.parse(response);
        // console.table(response);
        $("#search-loader").fadeOut(500);
        if (response.length == 0) {

            $(".no-result").show();

        } else {

            var duration = $(".duration").html();
            duration = duration.split(":")[0];
            var time = 0;


            // 4 = city , 5 = product , 6 = local, 7 = adress, 8 = price, 9 = keyword
            // console.table(response);
            response.map((value, index) => {
                time = value[4];
                $(`
                    <tr class="tr-item flow-text">
                        <td title="${value[7]}" style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[7]}</td>
                        <td title="${value[8]}" style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[8]}</td>
                        <td title="${value[10]}" style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:50px;">${value[10]}</td>
                        <td title="${value[6]}" style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[6]}</td>
                        <td title="${value[9]}">${value[9]}</td>
                    </tr>
                `).appendTo("#search-tbody");
            });

            $(".duration").fadeOut(200);
            if (time == 1)
                $(".duration").html(`${duration} : ${time} minuto`).fadeIn(100);
            else
                $(".duration").html(`${duration} : ${time} minutos`).fadeIn(100);
        }

    });


}

// Listagem de produtos
/**
 * Lista todos os produtos na página de produtos.
 */
const list_product = () => {

    $.get("/select_product", (response) => {

        response = JSON.parse(response);
        PRODUCT_DATA = response;
        if (response.length == 0) {

            $("#no-result-product").fadeIn(500);

        } else {

            response.map((value, index) => {
                $(`
                    <div class="z-depth-3 product-config edit-product" id="ed-${value[0]}" value="${value[0]}">
                        <p>${value[0]}</p>
                        <div class="right">
                            <a style="margin-right: 10px;" id="e-${value[0]}" value="${value[0]}" class="btn-floating btn-large   primary_color edit-product " data-position="top"><i class="fa fa-edit"></i></a>
                            <a  value="${value[0]}" class="remove-product btn-floating btn-large red " ><i class="fa fa-minus"></i></a>
                        </div>
                    </div>
                `).appendTo("#list-product").hide().slideDown("slow");
            });
        }

    });


}

// Conteudo do modal dinamico
/**
 * Modal dinâmico que retorna o conteúdo do estabelecimento estab_name para uma cidade cities filtrada.
 * @param  {string} estab_name
 * @param  {Array(string)} cities
 */
const get_modal_content = (estab_name, cities) => {
    $('#edit-modal .modal-content').remove();
    var filtered_estab = ESTAB_DATA.filter((item, index) => {
        if (item[1] === estab_name)
            return item;
    });

    filtered_estab = filtered_estab[0];

    cities = cities.filter((item, index) => {
        if (item[0] !== filtered_estab[0])
            return item;
    });

    let modal = `
        <div class="modal-content">
            <primary_key style="display: none;" value="${filtered_estab[1]}" />
            <h5 class="modal-title">${filtered_estab[1]}</h5>
            <div>
                <div style="margin: 20px 0;">
                    <div class="input-field col s6">
                        <select id="city_name" style="color: black !important;">
                            <option value = "${filtered_estab[0]}" > ${filtered_estab[0]}</option>
                            ${cities.map((city_name, index) => { return `<option value="${city_name[0]}">${city_name[0]}</option>` })}
                        </select>
                        <label>Cidade</label>
                    </div>
                    <div class="input-field col s6">
                        <input value="${filtered_estab[1]}" placeholder="Estabelecimento" id="estab_name" type="text" class="validate">
                        <label class="active" for="estab_name">Estabelecimento</label>
                    </div>
                    <div class="input-field col s6">
                        <input value="${filtered_estab[3]}" placeholder="Nome na Plataforma" id="web_name" type="text" class="validate">
                        <label class="active" for="web_name">Nome na Plataforma</label>
                    </div>
                    <div class="input-field col s6">
                        <input value="${filtered_estab[2]}" placeholder="Endereço" id="adress" type="text" class="validate">
                        <label class="active" for="adress">Endereço</label>
                    </div>
                </div>
                </div>
                <div class="modal-menu">
                    <button id="cancel" class="primary_color btn-large" href="#" rel="modal:close">Cancelar</button>
                    <button id="save-edit" class="primary_color   btn-large">Salvar Alterações</button>
                </div>
        </div>
    `

    $(modal).appendTo('#edit-modal');

    $("#edit-modal").modal({
        // fadeDuration: 200,
    });
    $('select').formSelect();
}

// Conteudo do modal dinamico - Produto

/**
 * Modal dinâmico que retorna o conteúdo do produto product_name.
 * @param  {string} product_name
 */
const get_modal_content_product = (product_name) => {
    $('#edit-modal-product .modal-content').remove();
    var filtered_product = PRODUCT_DATA.filter((item, index) => {
        if (item[0] === product_name)
            return item;
    });

    filtered_product = filtered_product[0];
    keywords = filtered_product[1].split(',');

    // console.log({ filtered_product, keywords });

    let modal = `
        <div class="modal-content"">
            <primary_key_product style="display: none;" value="${filtered_product[0]}" />
            <h5 class="modal-title">${filtered_product[0]}</h5>
            <div>
                <div style="margin: 20px 0;">
                    <div class="input-field col s12">
                        <input value="${filtered_product[0]}" placeholder="Produto" id="product_name_edit" type="text" class="validate">
                        <label class="active" for="product_name_edit">Produto</label>
                    </div>
                    <div class="input-field col s12">
                        <input value="${filtered_product[1]}" placeholder="Palavras Chave" id="keywords_edit" type="text" class="validate">
                        <label class="active" for="keywords_edit">Palavras Chave</label>
                    </div>
                </div>
                </div>
                <div class="modal-menu" style="position: relative;">
                    <button id="cancel" class="primary_color btn-large" href="#" rel="modal:close">Cancelar</button>
                    <button id="save-edit-product" class="primary_color   btn-large">Salvar Alterações</button>
                </div>
        </div>
    `

    $(modal).appendTo('#edit-modal-product');

    $("#edit-modal-product").modal({
        // fadeDuration: 200,
    });
    $('select').formSelect();

}

// Cria novo estab adidiconado e o coloca no front end
/**
 * Adiciona um novo elemento .estab para a listagem de estabs com o nome novo dele. Chamado pel modal de criação de estabelecimento.
 * @param  {string} new_estab
 */
const create_estab_element = (new_estab) => {

    var element =
        `
        <div class="z-depth-3 estab-config edit" id="ed-${new_estab}" value="${new_estab}">
            <p>${new_estab}</p>
            <div class="right">
                <a  id="e-${new_estab}" value="${new_estab}" class="btn-floating btn-large   primary_color edit" ><i class="fa fa-edit"></i></a>
                <a  value="${new_estab}" class="remove-estab btn-floating btn-large   red"><i class="fa fa-minus"></i></a>
            </div>
        </div>
        `

    $("#list-config").prepend(element).hide().fadeIn(1000);

    $("#no-result").fadeOut("500");

}

/**
 * Tenta abrir uma pasta no computador.
 *
 * @param {string} path
 */
const openFolder = (path) => {
    $.get("/open_folder", { path: path }, (res) => {
        if (res.status !== "success")
            showMessage("Não foi possível abrir a pasta", { notification: true });
    });
};

// Cria novo produto adidiconado e o coloca no front end
/**
 * Adiciona um novo elemento .product para a listagem de produtos com o nome novo dele. Chamado pel modal de criação de produtos.
 * @param  {string} new_product
 */
const create_product_element = (new_product) => {

    var element =
        `
        <div class="z-depth-3 product-config edit-product" id="ed-${new_product}" value="${new_product}">
            <p>${new_product}</p>
            <div class="right">
                <a style="margin-right: 10px;" id="e-${new_product}" value="${new_product}" class="btn-floating btn-large   primary_color edit-product" ><i class="fa fa-edit"></i></a>
                <a  value="${new_product}" class="remove-product btn-floating btn-large   red"><i class="fa fa-minus"></i></a>
            </div>
        </div>
        `

    $("#list-product").prepend(element).hide().fadeIn(1000);
    $("#no-result-product").fadeOut("500");

}

/**
 * Confirma se todos os dados foram preenchidos em um dado array info.
 * @param  {Array} info
 * @param  {boolean} edit=false
 */
const validateForm = (info, edit = false) => {
    if (edit)
        return null;

    const isEmpty = (x) => (x.trim().length == 0);
    if (info.map(isEmpty).some(x => x)) {
        showMessage("Preencha todos os campos para realizar esta ação.", {
            notification: false,
        });
        return false;
    }

    return true;
}

const requestNotificationPermission = () => {
    if (Notification.permission === "granted" || Notification.permission === "denied")
        return;

    Notification.requestPermission().then(_ => {});
};

const copyToClipboard = (value) => {
    navigator.clipboard.writeText(value);
    showMessage("Texto copiado para área de transferências.", { notification: false });
};

$(document).ready(() => {
    requestNotificationPermission();

    const hjs_data = document.querySelector("#home-js-data");
    const active = hjs_data.getAttribute("data-active");
    const progress_value = hjs_data.getAttribute("data-progress-value");
    const search = hjs_data.getAttribute("data-search") === "True";
    const is_chrome_installed = hjs_data.getAttribute("data-is-chrome-installed") === "True";

    const socket = io();

    socket.on("connect", () => {
        console.log(`Conectado - id do socket: ${socket.id}`);
    });

    const searchLoaded = () => {
        if (search || !is_chrome_installed)
            return;

        if (confirm("Uma pesquisa foi encontrada em progresso, deseja retomá-la?")) {
            $("#backup-button").addClass("disable");
            $("#config_path").addClass("disable");
            $("#progress h5").html(`Retomando Pesquisa`).hide().fadeIn(500);
            socket.emit("search", { names: "", city: "", backup: 1});

            var width = active.split(".")[0];
            var elem = document.getElementById("progress_bar");
            width = width * progress_value;
            width = width.toFixed(2);
            elem.style.width = width.toString() + "%";
            elem.innerHTML = width.toString() + "%";

            $("#main-navigation").tabs("select", "progress");
            $("#main-navigation  a").addClass("disabled");
        }
    }

    socket.on("search.updateProgressBar", (msg) => {
        console.log(`Progresso da pesquisa: ${msg.value}%`);
        updateProgressBar(parseFloat(msg.value));
    });

    /**
     * Função responsável por tratar todas as emisões do tipo catpcha vinda do servidor.
     * @param  {route} 'captcha'
     * @param  {json} msg
     */
    socket.on('captcha', (msg) => {
        if (msg['type'] == 'notification') {
            showMessage(msg.message);
        } else if (msg['type'] == 'progress') {
            $("#progress h5").html(`Pesquisando produto <strong>${msg['product']}</strong>`).hide().fadeIn(500);

            if (msg.value !== undefined)
                updateProgressBar(parseFloat(msg.value));

            if (msg['done'] == 1) {
                // console.log("DONE");
                $("#progress_bar").css("width", "0%");
                $("#progress_bar").html("0%");
                $('ul.tabs').tabs('select', 'pesquisar');
                $("#progress h5").html(`Iniciando Pesquisa`);
                $(".log_item").remove();
                $("#progress_log").css("height", "100%");
                $(".estab").remove();
                $('#main-navigation li a').removeClass("disabled");
                $(window).off();

                $(".log_item").remove();
                window.location.reload(true);
            }

        } else if (msg['type'] == 'captcha') {
            showMessage(msg.message);
        } else if (msg['type'] == 'log') {

            var log_data = JSON.parse(msg['data'])
            // console.table(log_data);
            $("#progress_log").css("height", "fit-content");
            log_data.map((data) => {
                $("#progress_log").append($(`<p class="log_item">${data}</p>`).hide().fadeIn(300));
            });

            $("#progress_scroll").animate({ scrollTop: $('#progress_scroll').prop("scrollHeight") }, 1000);

        } else if (msg['type'] == 'cancel') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".tabs a").addClass('enable');
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            socket.emit('cancel');
            new Notification("ACCB - Pesquisa Automática", {
                body: msg['message'],
            });
            $(".pause-overlay").fadeOut(500);
            $("#pause-loader").fadeOut(500);
            socket.emit('reload');
            window.location.reload(true);

        } else if (msg['type'] == 'pause') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".tabs a").addClass('enable');
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            new Notification("ACCB - Pesquisa Automática", {
                body: msg['message'],
            });
            $("#pause-loader").fadeOut(500);
            $(".pause-overlay").fadeOut(500);
        } else if (msg['type'] == 'error') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".tabs a").addClass('enable');
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            new Notification("ACCB - Pesquisa Automática", {
                body: msg['message'],
            });
            alert(msg['message'])
        }
    });

    /**
     * Função responsável por tratar todas as emisões do tipo catpcha vinda do servidor.
     * @param  {route} 'search'
     * @param  {json} msg
     */
    socket.on('search', (msg) => {
        if (msg['type'] == 'error') {
            showMessage("Um erro inexperado aconteceu durante a pesquisa, consulte o arquivo err.log para mais detalhes.");
        } else if (msg['type'] == 'notification') {
            showMessage(msg.message);
        } else if (msg['type'] == 'chrome') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            $('#main-navigation li a').removeClass("disabled");
            $(window).off();
            alert("Instale uma versão do Google Chrome para prosseguir com a pesquisa.");
            window.location.reload(true);
        } else if (msg['type'] == 'done') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            $('#main-navigation li a').removeClass("disabled");
            $(window).off();
            window.location.reload(true);
        } else if (msg['type'] == 'cancel') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".tabs a").addClass('enable');
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            socket.emit('cancel');
            new Notification("ACCB - Pesquisa Automática", {
                body: msg['message'],
            });
            $(".pause-overlay").fadeOut(500);
            $("#pause-loader").fadeOut(500);
            socket.emit('reload');
            window.location.reload(true);
        } else if (msg['type'] == 'pause') {
            $("#progress_bar").css("width", "0%");
            $("#progress_bar").html("0%");
            $('ul.tabs').tabs('select', 'pesquisar');
            $("#progress h5").html(`Iniciando Pesquisa`);
            $(".tabs a").addClass('enable');
            $(".log_item").remove();
            $("#progress_log").css("height", "100%");
            new Notification("ACCB - Pesquisa Automática", {
                body: msg['message'],
            });
            $("#pause-loader").fadeOut(500);
            $(".pause-overlay").fadeOut(500);
            socket.emit('reload');
            window.location.reload(true);
        } else if (msg['type'] == 'log') {
            var log_data = JSON.parse(msg['data'])
            // console.table(log_data);
            $("#progress_log").css("height", "fit-content");
            log_data.map((data) => {
                $("#progress_log").append($(`<p class="log_item">${data}</p>`).hide().fadeIn(300));
            });
            $("#progress_scroll").animate({ scrollTop: $('#progress_scroll').prop("scrollHeight") }, 1000);
        } else if (msg['type'] == 'progress') {
            $("#progress h5").html(`Pesquisando produto <strong>${msg['product']}</strong>`).hide().fadeIn(500);

            if (msg.value !== undefined)
                updateProgressBar(parseFloat(msg.value));

            if (msg['done'] == 1) {
                $("#progress_bar").css("width", "0%");
                $("#progress_bar").html("0%");
                $('ul.tabs').tabs('select', 'pesquisar');
                $("#progress h5").html(`Iniciando Pesquisa`);
                $(".tabs a").addClass('enable');
                $(".log_item").remove();
                $("#progress_log").css("height", "100%");
                $(".estab").remove();
                $(".log_item").remove();
                window.location.reload(true);
            }
        }
    });

    // Inicia todos os elementos js da aplicação.
    $('.modal').modal();

    var city = undefined;
    $("select").formSelect();
    $('.tooltipped').tooltip();
    list_estab();
    list_product();
    list_search();
    custom_select();
    custom_select_date();
    custom_select_search();


    $("#sec-navigation").tabs({
        onShow: () => { },
    })
    /**
     * Listener responsável por parar a pesquisa.
     * @param  {id} "#pause"
     */
    $("#pause").click(function (e) {

        e.preventDefault();
        if (window.confirm(`Realmente deseja PARAR a pesquisa ? Todo o progresso será salvo.`)) {
            socket.emit('pause');
            $("#progress h5").html(`Parando Pesquisa`);
            $(".pause-overlay").fadeIn(500);
            $("#pause-loader").fadeIn(500);
            $(window).off();
        }


    });
    /**
     * Listener responsável por cancelar a pesquisa.
     * @param  {id} "#cancel"
     */
    $("#cancel").click(function (e) {

        e.preventDefault();
        // $(this).html("PAUSANDO PESQUISA");
        // $(this).addClass('disable');
        if (window.confirm(`Realmente deseja CANCELAR a pesquisa ? Todos os dados serão EXCLUIDOS.`)) {
            socket.emit('pause', { data: true });
            $("#progress h5").html(`Cancelando Pesquisa`);
            $(".pause-overlay").fadeIn(500);
            $("#pause-loader").fadeIn(500);
            $(window).off();
        }

    });

    // Mascara para keywords
    // ACUCAR CRISTAL, ACUCAR CRISTAL 1KG, A

    $('body').on('keyup', '#keywords', function (e) {

        var pattern = new RegExp(',+(?=[/\s])', 'i');
        var keywords = $('#keywords').val().toUpperCase();
        var result = keywords.replace(pattern, "");
        // console.log({ keywords, result });
        $("#keywords").val(result);

    });

    // Salvar deleção de cidade

    $('#save-delete-city').click(function (e) {

        e.preventDefault();
        var city_name = $("#city-delete-select").val();

        if (window.confirm(`Realmente deseja deletar a cidade ${city_name} e todos os estabelecimentos pertencentes permanentemente ?`)) {
            $.get("/delete_city", { city_name: city_name }, (response) => {
                if (response.success) {
                    alert(response.message);
                    var modal = $("#delete-city").modal();
                    modal.closeModal();
                    $(".jquery-modal").fadeOut(500);
                    window.location = window.location.origin + "#configurar";
                    window.location.reload(true);

                } else {
                    Materialize.toast(response.message, 2000, 'rounded');
                }
            });
        }
    });

    // Salvar edição de cidade

    $('#save-edit-city').click(function (e) {

        e.preventDefault();
        var old_name = $("#city-edit-select").val();
        var new_name = $("#city-edit").val();
        if (validateForm([old_name, new_name]) && (new_name !== old_name))

            if (window.confirm(`Realmente deseja alterar o nome  da cidade ${old_name} para ${new_name} ?`)) {

                $.get("/update_city", { city_name: new_name, primary_key: old_name }, (response) => {
                    if (response.status !== "success") {
                        showMessage(`Falha ao mudar o nome da cidade.`, { notification: false });
                        return;
                    }

                    alert(response.message);
                    var modal = $("#edit-city").modal();
                    modal.closeModal();
                    $(".jquery-modal").fadeOut(500);
                    window.location = window.location.origin + "#configurar";
                    window.location.reload(true);
                });
            }

    });

    // Salvar edição de produto
    $('body').on('click', '#save-edit-product', function (e) {
        e.preventDefault();

        var product_name = $("#product_name_edit").val().toUpperCase();
        var primary_key = $("primary_key_product").attr('value').toUpperCase();
        var keywords = $("#keywords_edit").val().toUpperCase();

        if (validateForm([product_name, keywords]))
            if (window.confirm(`Realmente deseja alterar os valores inseridos?`)) {
                $.get("/update_product", { product_name: product_name, keywords: keywords, primary_key: primary_key }, (response) => {
                    if (response.status !== "success") {
                        showMessage(`O produto ${product_name} não pôde ser atualizado.`, { notification: false });
                    }

                    showMessage(response.message, { notification: false });
                    $("#edit-modal-product").modal().closeModal();
                    $(".jquery-modal").fadeOut(500);
                    window.location = window.location.origin + "#produtos";
                    window.location.reload(true);
                    // TODO: não reiniciar a janela. é muito desorientador
                });
            }

    });

    // Macro para fechar modal
    $(".cancel").click(function (e) {
        e.preventDefault();
        let id = $(this).attr('href');
        var modal = $(id).modal();
        modal.closeModal();
        $(".jquery-modal").fadeOut(500);

    });

    // Adicionar cidade

    $("#add-city").click(function (e) {
        e.preventDefault();

        var new_city = $("#save-city").val();
        if (validateForm([new_city]))
            $.get("/insert_city", { city_name: new_city }, (response) => {
                if (response.success) {
                    alert(response.message);
                    var modal = $("#add-city-modal").modal();
                    modal.closeModal();
                    $(".jquery-modal").fadeOut(500);
                    var element = `<option value="${new_city}">${new_city}</option>`
                    $("#city-select").append(element);
                    window.location = window.location.origin + "#configurar";
                    window.location.reload(true);
                } else {
                    Materialize.toast(response.message, 2000, 'rounded');
                }

            });


    });

    // Adicionar estab

    $("#save-add").click(function (e) {

        var city_name = $("#city_name-save").val();
        var estab_name = $("#estab_name-save").val();
        var web_name = $("#web_name-save").val().toUpperCase();
        var adress = $("#adress-save").val().toUpperCase();

        if (validateForm([city_name, estab_name, web_name, adress]))

            $.get("/insert_estab", { city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

                if (response.success) {

                    Materialize.toast(response.message, 2000, 'rounded');
                    var modal = $("#add-modal").modal();
                    modal.closeModal();
                    $(".jquery-modal").fadeOut(500);

                    ESTAB_DATA.push([city_name, estab_name, adress, web_name]);
                    create_estab_element(estab_name);

                } else {
                    Materialize.toast(response.message, 2000, 'rounded');
                }

            });

    });

    // Adicionar produto

    $("#save-add-product").click(function (e) {
        var product_name = $("#product_name").val().toUpperCase();
        var keywords = $("#keywords").val().toUpperCase();

        if (!validateForm([product_name, keywords]))
            return;

        $.get("/insert_product", { product_name: product_name, keywords: keywords }, (response) => {
            if (response.status !== "success") {
                showMessage(`O produto ${product_name} não pôde ser inserido`, { notification: false });
                return;
            }

            showMessage(response.message, { notification: false })
            var modal = $("#add-modal-product").modal();
            modal.closeModal();
            $(".jquery-modal").fadeOut(500);
            PRODUCT_DATA.push([product_name, keywords]);
            create_product_element(product_name);
        });

    });

    // Abrir modal dinamico de estab

    $('body').on('click', '.edit', (event) => {
        event.preventDefault();

        if ($("#edit-modal").find('.modal-content').length !== 0) {
            $('#edit-modal .modal-content').remove();
            $('#edit-modal .modal-title').remove();
        }

        $.get("/select_city", (response) => {
            let estab_name = $(event.currentTarget).attr('value');
            get_modal_content(estab_name, JSON.parse(response));
        });

    });

    // Abrir modal dinamico de product

    $('body').on('click', '.edit-product', (event) => {
        event.preventDefault();

        if ($("#edit-modal-product").find('.modal-content').length !== 0) {
            $('#edit-modal-product .modal-content').remove();
            $('#edit-modal-product .modal-title').remove();
        }

        let product_name = $(event.currentTarget).attr('value').toUpperCase();
        get_modal_content_product(product_name);


    });

    // Cancelar edição de estab

    $('body').on('click', '#cancel', (event) => {
        event.preventDefault();

        var modal = $("#edit-modal").modal();
        modal.closeModal();
        $(".jquery-modal").fadeOut(500);
    });

    // Salvar edição de estab

    $('body').on('click', '#save-edit', (event) => {
        event.stopPropagation();
        event.preventDefault();
        var city_name = $("#city_name").val();
        var estab_name = $("#estab_name").val();
        var primary_key = $("primary_key").attr("value");
        var web_name = $("#web_name").val().toUpperCase();
        var adress = $("#adress").val().toUpperCase();

        if (validateForm([city_name, estab_name, web_name, adress]))
            $.get("/update_estab", { primary_key: primary_key, city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {
                if (response.status !== "success") {
                    showMessage(`O estabelecimento ${estab_name} não pôde ser atualizado com sucesso.`, { notification: false });
                    return;
                }

                showMessage(response.message, { notification: false });

                var modal = $("#edit-modal").modal();
                modal.closeModal();
                $(".jquery-modal").fadeOut(500);
                $(".estab-config").remove();
                list_estab();
            });
    });

    // Botões de seleção de estab

    $('body').on('click', 'a.estab', function (e) {

        let id = $(this).attr('id');

        if ($(`#${id}`).hasClass('select-item-active')) {

            $(`#${id}`).removeClass('select-item-active');

        } else {

            $(`#${id}`).addClass('select-item-active');

        }

    });

    // Botões de seleção de cidade

    $('.city').click(function (e) {

        let id = $(this).attr('id');
        let value = $(this).attr('value');
        $('.estab').removeClass("select-item-active"); ''

        if (city === undefined) {
            city = value;
            $(`#${id}`).addClass('select-item-active');
        } else {

            if (city === value) {
                $(`#${id}`).removeClass('select-item-active');
                city = undefined;
            } else {
                Materialize.toast('Você só pode selecionar um municipio por vez ...', 1000, 'rounded');
            }

        }

    });

    // Botão de iniciar pesquisa

    $("#start").click((e) => {

        e.preventDefault();

        if (!$('.estab').hasClass("select-item-active")) {
            Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000, 'rounded');
        } else {
            // Materialize.toast('Pesquisa iniciada ...', 3000, 'rounded');
            var local_city = $($(".select-item-active")[0]).attr("value");
            $('.city').removeClass("select-item-active")
            city = undefined;

            var estabs = $(".select-item-active");
            var names = [];

            estabs.each(function (estab) {

                names.push($(this).attr("value"));

            });

            var form_data = { names: JSON.stringify(names), city: local_city, backup: 0 };
            // console.table(form_data);


            socket.emit('search', form_data);
            $('ul.tabs').tabs('select', 'progress');
            $("#main-navigation a").addClass("disable");
            $(window).on('unload', function (event) {
                return "Realmente deseja sair ? Existe uma pesquisa em andamento.";
            });
            $("#backup-button").addClass("disable");
            $("#config_path").addClass("disable");

        }

    });

    // Botão de ir para seleção de estabelecimentos

    $("#select").click(() => {

        $("#loader").show();

        if (!$('.city').hasClass("select-item-active")) {
            Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000, 'rounded');
        } else {
            // Materialize.toast('Pesquisa iniciada ...', 1000);
            $('ul.tabs').tabs('select', 'listagem');
        }
        let city_name = $('.select-item-active').html();

        $.get("/select_estab", { city: city_name }, (response) => {

            response = JSON.parse(response);
            if (response.length == 0) {

                $("#listagem h5").html("Nenhum estabelecimento encontrado para essa cidade, se dirija até a aba de configuração para prosseguir.");
                $("#select-all").addClass("disabled");
                $("#start").addClass("disabled");

            } else {

                $("#select-all").removeClass("disabled");
                $("#start").removeClass("disabled");

                $("#listagem h5").html("Selecione pelo menos um estabelecimento para prosseguir");
                $(".tabs a").addClass('disable');
                response.map((value, index) => {
                    var delay = 400 + index * 100;
                    $("#listagem  .select_wrapper").append($(`<a class="z-depth-2 select-item estab" city="${value[0]}" value="${value[1]}" id="E${index}" >${value[1]}</a>`).hide().fadeIn(delay))
                });
                $("#loader").hide();

            }

        });

    });

    // Botão selecionar todos

    $("#select-all").click(() => {

        if (!$('.estab').hasClass("select-item-active")) {
            $(`.estab`).addClass('select-item-active');
        } else {
            $(`.estab`).removeClass('select-item-active');
        }

    });

    $("#select-all-file").click(() => {

        if (!$('.estab').hasClass("select-item-active")) {
            $(`.estab`).addClass('select-item-active');
        } else {
            $(`.estab`).removeClass('select-item-active');
        }

    });

    // Voltar da seleção

    $("#back").click(() => {

        $('.city').removeClass("select-item-active")
        city = undefined;

        $('ul.tabs').tabs('select', 'pesquisar');

        $("#config-product").addClass('enable');
        $("#search").addClass('enable');
        $("#config").addClass('enable');
        $("#sobre").addClass('enable');
        $("#search_check").addClass('enable');

        $(".estab").remove();
    });

    // Remover estabelecimento

    $('body').on('click', 'a.remove-estab', function (e) {
        e.stopPropagation();
        e.preventDefault();
        let estab_name = $(this).attr('value');

        if (window.confirm(`Realmente deseja deletar o estabelecimento ${estab_name} permanentemente?`)) {
            $.get("/remove_estab", { estab_name: estab_name }, (response) => {
                if (response.status !== "success") {
                    showMessage(`O estabelecimento ${estab_name} não pôde ser removido.`, { notification: false });
                    return;
                }

                showMessage(response.message, { notification: false });

                $(this).parent().parent().remove();
                if ($(".estab-config .edit").length == 0) {
                    $("#no-result").fadeIn(500);
                }
            });
        }


    });

    // Remover product
    $('body').on('click', 'a.remove-product', function (e) {
        e.stopPropagation();
        e.preventDefault();
        let product_name = $(this).attr('value').toUpperCase();

        if (window.confirm(`Realmente deseja deletar o produto ${product_name} permanentemente?`)) {
            $.get("/remove_product", { product_name: product_name }, (response) => {
                if (response.success) {
                    $(this).parent().parent().remove();
                    Materialize.toast(response.message, 2000, 'rounded');
                    if ($(".product-config .edit-product").length == 0) {
                        $("#no-result-product").fadeIn(500);
                    }
                } else {
                    Materialize.toast(response.message, 2000, 'rounded');
                }
            });
        }
    });

    // Search bar - Search
    $('#search_bar').on("keyup", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var row_len = $("#list-search table tr").length;
        var value = $('#search_bar').val().toUpperCase();

        if ($("#search-select").val() == "null")
            return;

        if (row_len == 0) {
            return;
        }

        if (e.key === 'Backspace' || e.keyCode === 8) {
            if (value == '') {
                if ($(".tr-item").is(":hidden"))
                    $(".tr-item").fadeIn();
                if ($(".no-result").is(":visible"))
                    $(".no-result").hide();
                $(".tr-item").css("background", "transparent");
                $("table.striped > tbody > tr:nth-child(odd)").css("background", "rgba(242, 242, 242, 0.5)");
                return;
            }
        }

        if (e.key === 'Enter' || e.keyCode === 13) {

            // console.log('enter', row_len, value);
            var hide_len = 0;

            if (value == '') {
                if ($(".tr-item").is(":hidden"))
                    $(".tr-item").fadeIn();
                if ($(".no-result").is(":visible"))
                    $(".no-result").hide();
                $(".tr-item").css("background", "transparent");
                $("table.striped > tbody > tr:nth-child(odd)").css("background", "rgba(242, 242, 242, 0.5)");
                return;
            }

            $(".tr-item").css("background", "transparent");

            var odd = true;
            $(".tr-item").each(function (index) {

                var found = false;

                $(this).find("td").each(function (index) {

                    var id = $(this).text().toUpperCase();

                    if (id.includes(value) || similarity(id, value) >= 0.6) {
                        // console.log(`${index} ${id} == ${value}`);
                        found = true;
                        return false;
                    }
                    else {
                        // console.log(`${index} ${id} == ${value}`);
                        found = false;
                    }

                });

                if (found) {
                    $(this).show();
                    if (odd) {
                        odd = !odd;
                    } else {
                        $(this).css("background", "rgba(242, 242, 242, 0.5)");
                        odd = !odd;
                    }
                }
                else {
                    $(this).hide();
                    hide_len += 1;
                }
            });

            if (hide_len + 1 == row_len - 1) {
                $(".no-result").show();
            } else {
                $(".no-result").hide();
            }

        }
    });

    // Botão ao lado da barra de pesquisa

    $('#do_search').on("click", function (e) {

        var row_len = $("#list-search table tr").length;
        var value = $('#search_bar').val().toUpperCase();
        if ($("#search-select").val() == "null")
            return

        if (row_len == 0)
            return;

        if (value == '') {
            if ($(".tr-item").is(":hidden"))
                $(".tr-item").fadeIn();
            if ($(".no-result").is(":visible"))
                $(".no-result").hide();
            $(".tr-item").css("background", "transparent");
            $("table.striped > tbody > tr:nth-child(odd)").css("background", "rgba(242, 242, 242, 0.5)");
            return;
        }

        var hide_len = 0;

        $("#list-search table tr").css("background", "transparent");

        var odd = true;
        $("#list-search table tr").each(function (index) {
            if (index != 0) {
                var found = false;

                $(this).find("td").each(function (index) {

                    var id = $(this).text().toUpperCase();

                    if (id.includes(value) || similarity(id, value) >= 0.6) {
                        // console.log(`${index} ${id} == ${value}`);
                        found = true;
                        return false;
                    }
                    else {
                        // console.log(`${index} ${id} == ${value}`);
                        found = false;
                    }

                });

                if (found) {
                    $(this).show();
                    if (odd) {
                        odd = !odd;
                        $(this).css("background", "rgba(242, 242, 242, 0.5)");
                    } else {
                        odd = !odd;
                    }
                }
                else {
                    $(this).hide();
                    hide_len += 1;
                }
            }
        });


        if (hide_len + 1 == row_len) {
            $(".no-result").show();
        } else {
            $(".no-result").hide();
        }

    });

    // Botão da tab de navegação que leva para a aba de pesquisa
    $("#search_check").one("click", (e) => {
        e.preventDefault();
        if ($("#search-select").val() == "null")
            showMessage("Nenhuma pesquisa encontrada - realize uma pesquisa para utilizar essa função.", { notification: false });
    });

    // Abre o modal para gerar a coleção de arquivos para uma pesquisa existente (aba de pesquisas).
    $("#open-search-file").on("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        $(".estab").remove();

        var search_value = $("#search-select").val();

        if (search_value == "null") {
            alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
            return;
        }

        var city_name = $("#search-select option:selected").attr("city");
        // console.log();

        $.get("/select_estab", { city: city_name }, (response) => {
            response = JSON.parse(response);
            if (response.length == 0) {

                $("#listagem h5").html("Nenhum estabelecimento encontrado para essa cidade, se dirija até a aba de configuração para prosseguir.");
                alert("Nenhum estabelecimento encontrado para essa cidade, se dirija até a aba de configuração e tente novamente.");

                $("#generate-file").addClass("disabled");
            } else {
                $("#generate-file").addClass("enabled");
                response.map((value, index) => {
                    $("#file-list").append($(`<a class="z-depth-2 select-item estab" city="${value[0]}" value="${value[1]}" id="F${index}" >${value[1]}</a>`).hide().fadeIn(200 * index))
                });

                $("#loader").fadeOut();

                $("#search-file").modal({
                    fadeDuration: 200,
                });
            }
        });
    });

    // Limpa todas as pesquisas da aplicação
    $("#clean-search").on('click', () => {
        var search_id = $("#search-select").val();

        if (search_id == "null") {
            alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
            return;
        }

        if (!window.confirm("Realmente deseja excluir todas as pesquisas salvas?"))
            return

        var generate = window.confirm("Deseja gerar uma coleção de arquivos excel com todas as pesquisas existentes?");

        $.get("/clean_search", { generate: generate.toString() }, (response) => {
            if (response.status !== "success") {
                showMessage("Ocorreu um erro gerando os arquivos, tente novamente.", { notification: false });
                return;
            }

            showMessage(response.message, { notification: true });

            const path = response.path;
            if (path === undefined)
                return;

            if (window.confirm(`Deseja abrir o diretório ${path}?`))
                openFolder(path);

            setInterval(() => window.location.reload(true), 2000);
        });
    });

    // Realiza a geração de coleção de arquivos para uma pesquisa existente no modal de gerar arquivos (aba de pesquisas).
    $("#generate-file").on('click', () => {
        const city_name = $("#search-select option:selected").attr("city");
        const format_type = $("#file_format").val();

        if (!$('.estab').hasClass("select-item-active") && format_type != "all") {
            Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000, 'rounded');
            return;
        }

        const search_id = $("#search-select").val();

        const processResponse = (response) => {
            if (response.status !== "success") {
                showMessage("Ocorreu um erro gerando os arquivos, tente novamente.", { notification: false });
                return;
            }

            const path = response.path;
            showMessage(`Arquivos gerados com sucesso no diretório ${path}.`, { notification: true });

            $('.estab').removeClass("select-item-active");

            if (window.confirm(`Deseja abrir o diretório ${path}?`))
                openFolder(path);
        };

        if (format_type == "all") {
            $.get("/generate_file", { city_name: city_name, search_id: search_id, format: format_type }, processResponse);
            return;
        }

        var estabs = $(".select-item-active");
        var names = [];

        estabs.each(function (estab) {
            names.push($(this).attr("value"));
        });

        $.get("/generate_file", { names: JSON.stringify(names), city_name: city_name, search_id: search_id, format: format_type }, processResponse);
    });

    $("#file_format").on("change", function () {
        if (this.value == "all") {
            $("#select-all-file").addClass("disabled");
            $(".select-item.estab").addClass("disabled");
        } else {
            $("#select-all-file").removeClass("disabled");
            $(".select-item.estab").removeClass("disabled");
        }
    });

    // Remove uma pesquisa.
    $("#remove-search").on("click", () => {
        var search_id = $("#search-select").val();
        var search_info = $("#search-select option:selected").html();

        if (search_id == "null") {
            alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
            return;
        }

        if (window.confirm(`Realmente deseja remover a pesquisa ${search_info}?`)) {
            $.get("/delete_search", { search_id: search_id }, (response) => {
                if (response.status !== "success") {
                    showMessage("Ocorreu um erro durante a deleção da pesquisa, mais detalhes no arquivo err.log.", { notification: false });
                    return;
                }

                alert(response.message);
                window.location = window.location.origin + "#pesquisa";
                window.location.reload(true);
            });
        }
    });

    // Botão responsável por exportar as configurações da aplicação.
    $("#export").on("click", (e) => {
        e.preventDefault();

        if (window.confirm(`Realmente deseja exportar todos os dados atuais?`)) {
            $.get("/export_database", (response) => {
                if (response.status !== "success") {
                    alert("Ocorreu um erro durante a exportação dos dados.");
                    return;
                }

                showMessage(response.message, { notification: false });
            });
        }
    });

    // Botão responsável por abrir o popup de importação de configuração da aplicação.
    $("#import").on("click", (e) => {
        $("#import_file").click();
    });

    // Listener para o input de importação de configuração.
    $("#import_file").on("change", function (e) {
        e.preventDefault();
        e.stopPropagation();

        var form_data = new FormData();
        var files = $('#import_file')[0].files;
        if (!files[0].name.includes(".sql")) {
            showMessage("Insira um arquivo .sql válido.", { notification: false });
            return;
        }

        form_data.append('file', files[0]);
        $.ajax({
            url: '/import_database',
            type: 'post',
            data: form_data,
            contentType: false,
            processData: false,
            cache: false,
            success: (response) => {
                if (response.status !== "success") {
                    alert("Ocorreu um erro durante a importação dos dados.");
                    return;
                }

                alert(response.message);
                window.location = window.location.origin + "#configurar";
                window.location.reload(true);
            },
        });
    });

    if (Cookies.get("warning") === undefined) {
        $("#warning").modal({});
        Cookies.set("warning", "seen", {expires: 1});
    } else {
        searchLoaded();
    }

    const setOutputPath = () => {
        $.get("/set_path", (response) => {
            if (response.status !== "success") {
                alert("Ocorreu um erro durante a configuração do caminho.");
                return;
            }

            Cookies.set("path", response.path, { expires: 10 });
            showMessage(`Caminho alterado para ${response.path}`, { notification: false });
        });
    };

    if (Cookies.get("path") === undefined) {
        alert("Selecione uma pasta para salvar todos os arquivos gerados pelo o programa. Você pode estar alterando este caminho posteriormente no botão de configuração no canto superior direito.");
        setOutputPath();
    } else {
        socket.emit("set_path", { path: Cookies.get("path") });
    }

    if (!is_chrome_installed)
        alert("Instale uma versão do Google Chrome para realizar uma pesquisa.");

    if (search)
        $("body").on("click", "#backup-button", (_) => searchLoaded());

    socket.on("set_path", () => {
        alert("O antigo diretório foi deletado! Selecione uma pasta nova para salvar todos os arquivos gerados pelo o programa. Você pode estar alterando este caminho posteriormente no botão de configuração no canto superior direito.");
        setOutputPath();
    });

    socket.connect("http://127.0.0.1:5000/");

    $("#config_path").on("click", (e) => {
        e.preventDefault();

        alert("Selecione uma pasta para salvar todos os arquivos gerados pelo o programa. Você pode estar alterando este caminho posteriormente no botão de configuração no canto superior direito.");
        setOutputPath();
    });

    $("#close_app").on("click", () => {
        if (!window.confirm("Deseja realmente fechar o programa?"))
            return;

        socket.emit("exit");
        window.close();
    });

    $("#open_folder").on("click", () => {
        const path = Cookies.get("path");
        if (path)
            openFolder(path);
    });
});
