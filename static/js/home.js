let ESTAB_DATA = undefined;
let PRODUCT_DATA = undefined;
let EDIT_FORM_DATA = undefined;

var i = 0;
function move() {
	if (i == 0) {
		i = 1;
		var elem = document.getElementById("myBar");
		var width = 10;
		var id = setInterval(frame, 10);
		function frame() {
			if (width >= 100) {
				clearInterval(id);
				i = 0;
			} else {
				width++;
				elem.style.width = width + "%";
				elem.innerHTML = width + "%";
			}
		}
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

	});


}

// Listagem de produtos

const list_product = () => {

	$.get("/select_product", (response) => {

		response = JSON.parse(response);
		PRODUCT_DATA = response;
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
			Materialize.toast("Preencha todos os campos para realizar esta ação.");
			return false

		} else
			return true
	} else {

	}

}

$(document).ready(function () {

	var socket = io().connect("http://127.0.0.1:5000/");
	socket.on('progress', function () {
		socket.emit('my event', { data: 'I\'m connected!' });
	});

	var city = undefined;
	$("select").formSelect();
	$('.tooltipped').tooltip();
	list_estab();
	list_product();
	custom_select();

	// Mascara para keywords
	// ACUCAR CRISTAL, ACUCAR CRISTAL 1KG, A

	$('body').on('keyup', '#keywords', (e) => {

		var pattern = new RegExp(',+(?=[/\s])', 'i');
		var keywords = $('#keywords').val();
		var result = keywords.replace(pattern, "");
		console.log({ keywords, result });
		$("#keywords").val(result);

	});

	// Salvar deleção de cidade

	$('#save-delete-city').click((e) => {

		e.preventDefault();
		var city_name = $("#city-delete-select").val();

		if (window.confirm(`Realmente deseja deletar a cidade ${city_name} e todos os estabelecimentos pertencentes permanentemente ?`)) {

			$.get("/delete_city", { city_name: city_name }, (response) => {

				if (response.success) {

					alert(response.message);
					var modal = $("#delete-city").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					window.location.reload(false);

				} else {
					Materialize.toast(response.message, 2000);
				}

			});

		}


	});

	// Salvar edição de cidade

	$('#save-edit-city').click((e) => {

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
						window.location.reload(false);

					} else {
						Materialize.toast(response.message, 2000);
					}

				});
			}

	});

	// Salvar edição de produto

	$('body').on('click', '#save-edit-product', (e) => {

		e.preventDefault();

		var product_name = $("#product_name_edit").val();
		var primary_key = $("primary_key_product").attr('value');
		var keywords = $("#keywords_edit").val();

		if (validate_form([product_name, keywords]))

			if (window.confirm(`Realmente deseja alterar os valores inseridos ?`)) {

				$.get("/update_product", { product_name: product_name, keywords: keywords, primary_key: primary_key }, (response) => {

					if (response.success) {

						alert(response.message);
						var modal = $("#edit-modal-product").modal();
						modal.closeModal();
						$(".jquery-modal").fadeOut(500);
						window.location.reload(false);

					} else {
						Materialize.toast(response.message, 2000);
					}

				});
			}

	});

	// Macro para fechar modal

	$(".cancel").click((e) => {

		e.preventDefault();
		let id = $(e.currentTarget).attr('href');
		var modal = $(id).modal();
		modal.closeModal();
		$(".jquery-modal").fadeOut(500);

	});

	// Adicionar cidade

	$("#add-city").click((e) => {
		e.preventDefault();

		var new_city = $("#save-city").val();
		console.log({ new_city });
		if (validate_form([new_city]))

			$.get("/insert_city", { city_name: new_city }, (response) => {

				if (response.success) {

					alert(response.message);
					var modal = $("#add-city-modal").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					var element = `<option value="${new_city}">${new_city}</option>`
					$("#city-select").append(element);
					window.location.reload(false);

				} else {
					Materialize.toast(response.message, 2000);
				}

			});


	});

	// Adicionar estab

	$("#save-add").click((e) => {

		var city_name = $("#city_name-save").val();
		var estab_name = $("#estab_name-save").val();
		var web_name = $("#web_name-save").val();
		var adress = $("#adress-save").val();

		if (validate_form([city_name, estab_name, web_name, adress]))

			$.get("/insert_estab", { city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

				if (response.success) {

					Materialize.toast(response.message, 2000);
					var modal = $("#add-modal").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);

					ESTAB_DATA.push([city_name, estab_name, adress, web_name]);
					create_estab_element(estab_name);

				} else {
					Materialize.toast(response.message, 2000);
				}

			});

	});

	// Adicionar produto

	$("#save-add-product").click((e) => {

		var product_name = $("#product_name").val();
		var keywords = $("#keywords").val();

		if (validate_form([product_name, keywords]))

			$.get("/insert_product", { product_name: product_name, keywords: keywords }, (response) => {

				if (response.success) {

					Materialize.toast(response.message, 2000);
					var modal = $("#add-modal-product").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					// $(".estab-config").remove();
					// list_estab();
					PRODUCT_DATA.push([product_name, keywords]);
					create_product_element(product_name);

				} else {
					Materialize.toast(response.message, 2000);
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

		let product_name = $(event.currentTarget).attr('value');
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
		var web_name = $("#web_name").val();
		var adress = $("#adress").val();

		if (validate_form([city_name, estab_name, web_name, adress]))

			$.get("/update_estab", { primary_key: primary_key, city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

				if (response.success) {

					Materialize.toast(response.message, 2000);
					var modal = $("#edit-modal").modal();
					modal.closeModal();
					$(".jquery-modal").fadeOut(500);
					$(".estab-config").remove();
					list_estab();

				} else {
					Materialize.toast(response.message, 2000);
				}

			});
	});

	// Botões de seleção de estab

	$('body').on('click', 'a.estab', (e) => {

		$('.city').removeClass("select-item-active")
		city = undefined;

		let id = $(e.currentTarget).attr('id');

		if ($(`#${id}`).hasClass('select-item-active')) {

			$(`#${id}`).removeClass('select-item-active');

		} else {

			$(`#${id}`).addClass('select-item-active');

		}

	});

	// Botões de seleção de cidade

	$('.city').click((e) => {

		let id = $(e.currentTarget).attr('id');
		$('.estab').removeClass("select-item-active");

		if (city === undefined) {
			city = id;
			$(`#${id}`).addClass('select-item-active');
		} else {

			if (city === id) {
				$(`#${id}`).removeClass('select-item-active');
				city = undefined;
			} else {
				Materialize.toast('Você só pode selecionar um municipio por vez ...', 1000);
			}

		}

	});

	// Botão de iniciar pesquisa

	$("#start").click(() => {

		if (!$('.estab').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000);
		} else {
			Materialize.toast('Pesquisa iniciada ...', 3000);
			$('ul.tabs').tabs('select', 'progress');
		}

	});

	// Botão de ir para seleção de estabelecimentos

	$("#select").click(() => {

		$("#loader").show();

		if (!$('.city').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000);
		} else {
			// Materialize.toast('Pesquisa iniciada ...', 1000);
			$('ul.tabs').tabs('select', 'listagem');
			$(".tabs a").addClass('disable');
		}
		let city_name = $('.select-item-active').html();

		$.get("/select_estab", { city: city_name }, (response) => {

			response = JSON.parse(response);
			response.map((value, index) => {
				var delay = 400 + index * 100;
				$("#listagem  .select_wrapper").append($(`<a class="z-depth-2 select-item estab" id="E${index}" >${value[1]}</a>`).hide().fadeIn(delay));
			});
			$("#loader").hide();

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

	$('body').on('click', 'a.remove-estab', (e) => {

		e.stopPropagation();
		e.preventDefault();
		let estab_name = $(e.currentTarget).attr('value');
		if (window.confirm(`Realmente deseja deletar o estabelecimento ${estab_name} permanentemente ?`)) {
			$.get("/remove_estab", { estab_name: estab_name }, (response) => {

				if (response.success) {
					$(e.currentTarget).parent().parent().fadeOut(250, () => {
						$(this).remove();
					});
					Materialize.toast(response.message, 2000);
					console.log(response);
				} else {
					Materialize.toast(response.message, 2000);
					console.log(response);
				}


			});
		}


	});

	// Remover product

	$('body').on('click', 'a.remove-product', (e) => {

		e.stopPropagation();
		e.preventDefault();
		let product_name = $(e.currentTarget).attr('value');
		if (window.confirm(`Realmente deseja deletar o produto ${product_name} permanentemente ?`)) {
			$.get("/remove_product", { product_name: product_name }, (response) => {

				if (response.success) {
					$(e.currentTarget).parent().parent().fadeOut(250, () => {
						$(this).remove();
					});
					Materialize.toast(response.message, 2000);
					console.log(response);
				} else {
					Materialize.toast(response.message, 2000);
					console.log(response);
				}


			});
		}


	});


});
