let ESTAB_DATA = undefined;
let PRODUCT_DATA = undefined;
let CANCEL_CAPTCHA = false;
let EDIT_FORM_DATA = undefined;
let WIDTH = 0;

var i = 0;
function move(val) {

	if (val == undefined)
		val = 0.0
	val.toFixed(2);
	var elem = document.getElementById("progress_bar");
	WIDTH = parseFloat($("#progress_bar").html().replace("%", ""));
	WIDTH += val;
	try {
		WIDTH = WIDTH.toFixed(2);
	}
	catch (e) {
		// Error
	}
	var floor = Math.floor(WIDTH);
	elem.style.width = floor.toString() + "%";
	elem.innerHTML = floor.toString() + "%";
}

function similarity(s1, s2) {
	var longer = s1;
	var shorter = s2;
	if (s1.length < s2.length) {
		longer = s2;
		shorter = s1;
	}
	var longerLength = longer.length;
	if (longerLength == 0) {
		return 1.0;
	}
	return (longerLength - distance(longer, shorter)) / parseFloat(longerLength);
}

function filter_search(month) {
	var search_id = $("#search-select").val();

	if (search_id == "null") {
		alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
		return;
	}


	$.get("/select_search_info", { month: month }, (response) => {

		if (response.success) {

			var data = JSON.parse(response.data);
			console.log(month);
			if (data.length != 0) {

				$("#search-loader").fadeIn(500);
				$(".tr-item").remove();

				$("#search-select option").remove();
				data.map((value) => {

					console.log(value);
					$("#search-select").append(`<option city=${value[2]} value=${value[1]}>${value[2]} ${value[3]}</option>`);

				});

				;
				$("#search-select").parent().find(".styledSelect").remove();
				$("#search-select").parent().find("ul.options").remove();
				list_search();
				custom_select_search();
				return true;

			} else {
				Materialize.toast("Nenhuma pesquisa cadastrada para esse mês.", 2000, 'rounded');
				return false;
			}

		} else {
			return false;
			Materialize.toast(response.message, 2000, 'rounded');
		}

	});
}

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
			// Materialize.toast($this.val());
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
			// Materialize.toast($this.val());
		});

		// Hides the unordered list when clicking outside of it
		$(document).click(function () {
			$styledSelect.removeClass('active');
			$list.hide();
		});

	});

}
const custom_select_search = () => {

	$('#pesquisa select').each(function () {

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
			// Materialize.toast($this.val());
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
						<td style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[7]}</td>
						<td style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[8]}</td>
						<td style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:50px;">${value[10]}</td>
						<td style="white-space: nowrap; text-overflow:ellipsis; overflow: hidden; max-width:250px;">${value[6]}</td>
						<td>${value[9]}</td>
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

// Cria novo produto adidiconado e o coloca no front end

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

// Valida formulários para campos vázios

const validate_form = (info, edit = false) => {

	if (!edit) {
		var validated = info.map((value, index) => {
			if (value == " " || value == "") {
				return false;
			} else {
				return true;
			}
		});

		if (validated.some(elem => elem == false)) {
			Materialize.toast("Preencha todos os campos para realizar esta ação.", 2000, 'rounded');
			return false

		} else
			return true
	} else {

	}

}

// DOCUMENT.READY

$(document).ready(function () {

	if (Notification.permission === "granted") {
		//  alert("we have permission");
		// new Notification("Teste message", {
		// 	body: "Teste body",
		// });

	} else if (Notification.permission !== "denied") {
		Notification.requestPermission().then(permission => {
			// console.log(permission);
		});
	}

	var socket = io().connect("http://127.0.0.1:5000/");
	socket.on('captcha', (msg) => {
		if (msg['type'] == 'notification') {

			Materialize.toast(msg['message'], 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: msg['message'],
			});

		} else if (msg['type'] == 'progress') {

			$("#progress h5").html(`Pesquisando produto <strong>${msg['product']}</strong>`).hide().fadeIn(500);
			if (msg['value'] != '')
				move(msg['value']);
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

			Materialize.toast(msg['message'], 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: msg['message'],
			});

		} else if (msg['type'] == 'log') {

			var log_data = JSON.parse(msg['data'])
			console.table(log_data);
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
		}
	});

	socket.on('search', (msg) => {

		if (msg['type'] == 'error') {

			Materialize.toast("Um erro inexperado aconteceu durante a pesquisa, consulte o arquivo err.log para mais detalhes.", 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: "Um erro inexperado aconteceu durante a pesquisa, consulte o arquivo err.log para mais detalhes.",
			});

		} else if (msg['type'] == 'notification') {

			Materialize.toast(msg['message'], 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: msg['message'],
			});

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
			if (msg['value'] != '')
				move(msg['value']);
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

	// $('.datepicker').datepicker({
	// 	i18n: {
	// 		months: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
	// 		monthsShort: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
	// 		weekdays: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sabádo'],
	// 		weekdaysShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'],
	// 		weekdaysAbbrev: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'],
	// 		today: 'Hoje',
	// 		clear: 'Limpar',
	// 		cancel: 'Sair',
	// 		done: 'Confirmar',
	// 		labelMonthNext: 'Próximo mês',
	// 		labelMonthPrev: 'Mês anterior',
	// 		labelMonthSelect: 'Selecione um mês',
	// 		labelYearSelect: 'Selecione um ano',
	// 		selectMonths: true,
	// 		selectYears: 1,
	// 	},
	// 	format: 'dd mmmm, yyyy',
	// 	maxDate: new Date(),
	// 	container: 'body',
	// });

	// M.AutoInit();
	// $("#sec-navigation").find("a.active").parent().css("width", "100%");


	$("#sec-navigation").tabs({
		onShow: () => {

			// console.log("kaka");
			// $("#sec-navigation").find("a").each(function (e) {

			// 	$(this).parent().css("width", "10px");

			// });
			// $("#sec-navigation").find("a.active").parent().css("width", "100%");
			// $("#sec-navigation").find("a.active").parent().css("width", "100%");

		},
	})

	$("#pause").click(function (e) {

		e.preventDefault();
		// $(this).html("PAUSANDO PESQUISA");
		// $(this).addClass('disable');
		if (window.confirm(`Realmente deseja PAUSAR a pesquisa ? Todos o progresso será salvo.`)) {
			socket.emit('pause');
			$("#progress h5").html(`Pausando Pesquisa`);
			$(".pause-overlay").fadeIn(500);
			$("#pause-loader").fadeIn(500);
			$(window).off();

		}


	});

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
		if (validate_form([old_name, new_name]) && (new_name !== old_name))

			if (window.confirm(`Realmente deseja alterar o nome  da cidade ${old_name} para ${new_name} ?`)) {

				$.get("/update_city", { city_name: new_name, primary_key: old_name }, (response) => {

					if (response.success) {

						alert(response.message);
						var modal = $("#edit-city").modal();
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

	// Salvar edição de produto

	$('body').on('click', '#save-edit-product', function (e) {

		e.preventDefault();

		var product_name = $("#product_name_edit").val().toUpperCase();
		var primary_key = $("primary_key_product").attr('value').toUpperCase();
		var keywords = $("#keywords_edit").val().toUpperCase();

		if (validate_form([product_name, keywords]))

			if (window.confirm(`Realmente deseja alterar os valores inseridos ?`)) {

				$.get("/update_product", { product_name: product_name, keywords: keywords, primary_key: primary_key }, (response) => {

					if (response.success) {

						alert(response.message);
						var modal = $("#edit-modal-product").modal();
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
		if (validate_form([new_city]))

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

		if (validate_form([city_name, estab_name, web_name, adress]))

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

		if (validate_form([product_name, keywords]))

			$.get("/insert_product", { product_name: product_name, keywords: keywords }, (response) => {

				if (response.success) {

					Materialize.toast(response.message, 2000, 'rounded');
					var modal = $("#add-modal-product").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					// $(".estab-config").remove();
					// list_estab();
					PRODUCT_DATA.push([product_name, keywords]);
					create_product_element(product_name);

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
				}

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

		if (validate_form([city_name, estab_name, web_name, adress]))

			$.get("/update_estab", { primary_key: primary_key, city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

				if (response.success) {

					Materialize.toast(response.message, 2000, 'rounded');
					var modal = $("#edit-modal").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					$(".estab-config").remove();
					list_estab();

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
				}

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
		if (window.confirm(`Realmente deseja deletar o estabelecimento ${estab_name} permanentemente ?`)) {
			$.get("/remove_estab", { estab_name: estab_name }, (response) => {

				if (response.success) {
					$(this).parent().parent().remove();
					Materialize.toast(response.message, 2000, 'rounded');
					// console.log(response);
					if ($(".estab-config .edit").length == 0) {
						$("#no-result").fadeIn(500);
					}
					// window.location = window.location.origin + "#configurar";
					// window.location.reload(true);

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
					// console.log(response);
				}


			});
		}


	});

	// Remover product

	$('body').on('click', 'a.remove-product', function (e) {

		e.stopPropagation();
		e.preventDefault();
		let product_name = $(this).attr('value').toUpperCase();
		if (window.confirm(`Realmente deseja deletar o produto ${product_name} permanentemente ?`)) {
			$.get("/remove_product", { product_name: product_name }, (response) => {

				if (response.success) {
					$(this).parent().parent().remove();
					Materialize.toast(response.message, 2000, 'rounded');
					// console.log(response);
					if ($(".product-config .edit-product").length == 0) {
						$("#no-result-product").fadeIn(500);
					}
					// window.location = window.location.origin + "#produtos";
					// window.location.reload(true);

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
					// console.log(response);
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
			return

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

	$("#search_check").one("click", (e) => {
		e.preventDefault();
		if ($("#search-select").val() == "null")
			alert("Realize uma pesquisa para utilizar essa função.");
	});

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

	$("#generate-file").on('click', () => {

		var city_name = $("#search-select option:selected").attr("city");

		if (!$('.estab').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000, 'rounded');
		} else {

			var estabs = $(".select-item-active");
			var names = [];

			estabs.each(function (estab) {

				names.push($(this).attr("value"));

			});

			var search_id = $("#search-select").val();
			// console.table(form_data);
			// socket.emit('search', form_data);
			$.get("/generate_file", { names: JSON.stringify(names), city_name: city_name, search_id: search_id }, (response) => {

				if (response["status"] == "success") {
					// console.log(response);
					$('.estab').removeClass("select-item-active");
					Materialize.toast(`Arquivos gerados com sucesso no diretório ${response.dic}.`, 15000, 'rounded');
					// new Notification("ACCB - Pesquisa Automática", {
					// 	body: `Arquivos gerados com sucesso no diretório ${response.dic}.`,
					// });
				} else {
					// console.log(response);
				}

			});

		}

	});

	$("#remove-search").on("click", () => {

		var search_id = $("#search-select").val();
		var search_info = $("#search-select  option:selected").html();

		if (search_id == "null") {
			alert("Nenhuma pesquisa encontrada, realize uma pesquisa para utilizar essa função.");
			return;
		}

		if (window.confirm(`Realmente deseja remover a pesquisa ${search_info}`)) {

			$.get("/delete_search", { search_id: search_id }, (response) => {

				if (response["status"] == "success") {

					alert(response["message"]);
					Materialize.toast(response["message"], 2000, 'rounded');
					window.location = window.location.origin + "#pesquisa";
					window.location.reload(true);

				} else {
					Materialize.toast(response["message"], 2000, 'rounded');
				}

			});
		}

	});

	$("#export").on("click", (e) => {
		e.preventDefault();

		if (window.confirm(`Realmente deseja exportar todos os dados atuais ?`)) {

			$.get("/export_database", (response) => {

				if (response["status"] == "success") {

					Materialize.toast(response["message"], 8000, 'rounded');

				} else {
					Materialize.toast(response["message"], 8000, 'rounded');
				}

			});
		}

	});

	$("#import").on("click", (e) => {

		$("#import_file").click();

	});

	$("#import_file").on("change", function (e) {

		e.preventDefault();
		e.stopPropagation();

		var form_data = new FormData();
		var files = $('#import_file')[0].files;

		// Check file selected or not  fd.append('file',files[0]);
		form_data.append('file', files[0]);
		$.ajax({
			url: '/import_database',
			type: 'post',
			data: form_data,
			contentType: false,
			processData: false,
			cache: false,
			success: function (response) {
				if (response.status == "success") {
					alert(response["message"]);
					window.location = window.location.origin + "#co$figurar";
					window.location.reload(true);
				} else {
					Materialize.toast(response["message"], 8000, 'rounded');
				}
			},
		});

		// console.log({ file, file_name });

	});

});

