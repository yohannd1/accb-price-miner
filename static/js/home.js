let ESTAB_DATA = undefined;
let PRODUCT_DATA = undefined;
let CANCEL_CAPTCHA = false;
let EDIT_FORM_DATA = undefined;

var i = 0;
var width = 0;
function move(val = 100 / 12) {
	i = 1;
	var elem = document.getElementById("progress_bar");
	if (width >= 100) {
		i = 0;
	} else {
		width += val;
		var floor = Math.floor(width);
		console.log(floor);
		elem.style.width = floor.toString() + "%";
		elem.innerHTML = floor.toString() + "%";
	}
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
			$('div.styledSelect.active').each(function () {
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
	else
		$(".estab-config").remove();

	$.get("/select_estab", { city: city }, (response) => {

		response = JSON.parse(response);
		ESTAB_DATA = response;
		if (response.length == 0) {

			$(`<div class="z-depth-3 estab-config" id="no-result" style="justify-content: center;"><a style="color: white; width: 100%;"  href="#add-modal" rel="modal:open">
			<p>Nenhum estabelecimento cadastrado, pressione para adicionar.</p>
			</a></div>`).appendTo("#list-config").hide().slideDown();

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

// Listagem de produtos

const list_product = () => {

	$.get("/select_product", (response) => {

		response = JSON.parse(response);
		PRODUCT_DATA = response;
		if (response.length == 0) {

			$(`<div class="z-depth-3 product-config" id="no-result-product" style="justify-content: center;"><a style="color: white; width: 100%;"  href="#add-modal-product" rel="modal:open">
			<p>Nenhum produto cadastrado, pressione para adicionar.</p>
			</a></div>`).appendTo("#list-product").hide().slideDown();

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
			<div class="row">
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

	console.log({ filtered_product, keywords });

	let modal = `
		<div class="modal-content">
			<primary_key_product style="display: none;" value="${filtered_product[0]}" />
			<h5 class="modal-title">${filtered_product[0]}</h5>
			<div class="row">
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
				<div class="modal-menu">
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

	$("#no-result").fadeOut("500").remove();

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
	$("#no-result-product").fadeOut("500").remove();

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

$(document).ready(function () {

	if (Notification.permission === "granted") {
		// alert("we have permission");
		// new Notification("Teste message", {
		// 	body: "Teste body",
		// });

	} else if (Notification.permission !== "denied") {
		Notification.requestPermission().then(permission => {
			console.log(permission);
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
			$("#progress h5").html(`Pesquisando produto ${msg['product']}`);
			move(100 / 12);
			if (msg['done'] == 1) {
				$("#progress_bar").css("width", "0%");
				$("#progress_bar").html("0%");
			}
		} else if (msg['type'] == 'captcha') {
			Materialize.toast(msg['message'], 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: msg['message'],
			});
		}
	});

	socket.on('search', (msg) => {

		if (msg['type'] == 'error') {
			Materialize.toast("Um erro inexperado aconteceu durante a pesquisa, consulte o arquivo err.log para mais detalhes.", 8000, 'rounded');
			new Notification("ACCB - Pesquisa Automática", {
				body: "Um erro inexperado aconteceu durante a pesquisa, consulte o arquivo err.log para mais detalhes.",
			});
		}

	});

	var city = undefined;
	$("select").formSelect();
	$('.tooltipped').tooltip();
	list_estab();
	list_product();
	custom_select();

	$("#pause").click(function (e) {

		e.preventDefault();
		move(100 / 13);
		$(this).html("PAUSANDO PESQUISA");
		$(this).addClass('disable');

	});

	// Mascara para keywords
	// ACUCAR CRISTAL, ACUCAR CRISTAL 1KG, A

	$('body').on('keyup', '#keywords', function (e) {

		var pattern = new RegExp(',+(?=[/\s])', 'i');
		var keywords = $('#keywords').val().toUpperCase();
		var result = keywords.replace(pattern, "");
		console.log({ keywords, result });
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

		$('.city').removeClass("select-item-active")
		city = undefined;

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
		$('.estab').removeClass("select-item-active");

		if (city === undefined) {
			city = id;
			$(`#${id}`).addClass('select-item-active');
		} else {

			if (city === id) {
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
			Materialize.toast('Pesquisa iniciada ...', 3000, 'rounded');
			var estabs = $(".select-item-active");
			var names = [];
			var city = $(".select-item-active").attr("city");

			estabs.each(function (estab) {

				names.push($(this).attr("value"));

			});

			console.log(city);
			socket.emit('search', { names: JSON.stringify(names), city: city, backup: 0 });
			$('ul.tabs').tabs('select', 'progress');
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

	// Voltar da seleção

	$("#back").click(() => {
		$('ul.tabs').tabs('select', 'pesquisar');

		$("#config-product").addClass('enable');
		$("#search").addClass('enable');
		$("#config").addClass('enable');

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
					$(this).parent().parent().fadeOut(250, () => {
						$(this).remove();
					});
					Materialize.toast(response.message, 2000, 'rounded');
					console.log(response);
					// window.location = window.location.origin + "#configurar";
					// window.location.reload(true);

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
					console.log(response);
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
					$(this).parent().parent().fadeOut(250, () => {
						$(this).remove();
					});
					Materialize.toast(response.message, 2000, 'rounded');
					console.log(response);
					// window.location = window.location.origin + "#produtos";
					// window.location.reload(true);

				} else {
					Materialize.toast(response.message, 2000, 'rounded');
					console.log(response);
				}


			});
		}


	});


});
