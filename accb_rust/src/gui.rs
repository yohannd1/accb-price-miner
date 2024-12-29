use eframe::{
    egui::{self, Align, ComboBox, Context, Direction, Layout, Ui},
    run_native, App, CreationContext, Frame, NativeOptions,
};

const TAB_NAMES: &[&str] = &[
    "Pesquisa",
    "Estabelecimentos",
    "Produtos",
    "Histórico",
    "Configurações",
    "Sobre",
];
const MONTHS_PT_BR: &[&str] = &[
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
];

struct Options {
    output_path: String,
    show_driver_window: bool,
    show_extra_search_details: bool,
}

impl Default for Options {
    fn default() -> Self {
        Self {
            output_path: String::from("/path/to/output/dir"),
            show_driver_window: false,
            show_extra_search_details: true,
        }
    }
}

struct HistoryState {
    current_month: u8,
}

struct PriceMiner {
    first_frame: bool,
    tab_idx: u8,
    options: Options,
    history_state: HistoryState,
}

impl PriceMiner {
    pub fn new(_: &CreationContext<'_>) -> Self {
        Self {
            first_frame: true,
            tab_idx: 0,
            options: Options::default(),
            history_state: HistoryState { current_month: 0 },
        }
    }

    pub fn first_frame(&mut self, ctx: &Context, _: &mut Frame) {
        ctx.set_zoom_factor(1.5);
    }

    pub fn draw_tab_bar(&mut self, _: &Context, _: &mut Frame, ui: &mut Ui) {
        let layout = Layout {
            main_dir: Direction::LeftToRight,
            main_wrap: false,
            main_align: Align::Center,
            main_justify: true,
            cross_align: Align::Min,
            cross_justify: false,
        };

        ui.columns(TAB_NAMES.len(), |cols| {
            for (i, &n) in TAB_NAMES.iter().enumerate() {
                cols[i].with_layout(layout, |ui| {
                    if ui.selectable_label(i == self.tab_idx as usize, n).clicked() {
                        self.tab_idx = i as u8;
                    }
                });
            }
        });
    }

    pub fn draw_central_panel(&mut self, ctx: &Context, frame: &mut Frame, ui: &mut Ui) {
        self.draw_tab_bar(ctx, frame, ui);

        match self.tab_idx {
            0 => self.draw_search_tab(ctx, frame, ui),
            1 => self.draw_estabs_tab(ctx, frame, ui),
            2 => self.draw_products_tab(ctx, frame, ui),
            3 => self.draw_history_tab(ctx, frame, ui),
            4 => self.draw_config_tab(ctx, frame, ui),
            5 => self.draw_about_tab(ctx, frame, ui),
            _ => self.draw_placeholder(ctx, frame, ui),
        }
    }

    pub fn draw_search_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("TODO");
    }

    pub fn draw_estabs_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("TODO");
    }

    pub fn draw_products_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("TODO");
    }

    pub fn draw_history_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        let mut x = 0;

        let current_month = match MONTHS_PT_BR.get(self.history_state.current_month as usize) {
            Some(&s) => s,
            None => "???",
        };

        ui.horizontal(|ui| {
            ComboBox::from_label("Ano")
                .selected_text(current_month)
                .show_ui(ui, |ui| {
                    // TODO: popular isso com base nos anos disponíveis
                    ui.selectable_value(&mut x, 0, "2020");
                    ui.selectable_value(&mut x, 0, "2021");
                    ui.selectable_value(&mut x, 0, "2022");
                    ui.selectable_value(&mut x, 0, "2023");
                    ui.selectable_value(&mut x, 0, "2024");
                });

            ComboBox::from_label("Mês")
                .selected_text(current_month)
                .show_ui(ui, |ui| {
                    for (i, &month) in MONTHS_PT_BR.iter().enumerate() {
                        ui.selectable_value(&mut self.history_state.current_month, i as u8, month);
                    }
                });

            ComboBox::from_label("Pesquisas")
                .selected_text(current_month)
                .show_ui(ui, |ui| {
                    // TODO: popular isso com base nas pesquisas disponíveis
                    ui.selectable_value(&mut x, 0, "pesq1 itabuna");
                    ui.selectable_value(&mut x, 0, "pesq2 ilhéus");
                    ui.selectable_value(&mut x, 0, "sla");
                });
        });
    }

    pub fn draw_config_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("Configurações");

        ui.horizontal(|ui| {
            ui.label("Caminho de saída: ");
            ui.label(&self.options.output_path);
            _ = ui.button("Alterar"); // TODO
        });
        ui.label("Se refere ao caminho para onde os arquivos de pesquisa serão exportados.");
        ui.separator();

        ui.checkbox(
            &mut self.options.show_driver_window,
            "Mostrar janela do navegador automatizado durante a pesquisa:",
        );
        ui.label("Útil para entender como a pesquisa está sendo feita em tempo real.");
        ui.separator();

        ui.checkbox(
            &mut self.options.show_extra_search_details,
            "Mostrar detalhes extra na pesquisa:",
        );
        ui.label("Mostra alguns detalhes extra na pesquisa, como quanto tempo está sendo aguardado para a próxima ação.");
        ui.separator();

        // TODO: popup for this!
        ui.label("Dados do programa");
        ui.label("(É mais recomendado salvar o arquivo accb.sqlite gerado pelo programa)");
    }

    pub fn draw_about_tab(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("Esta aplicação objetivou modernizar o processo de coleta de preços dos produtos que compõem a cesta básica do projeto de extensão Acompanhamento do Custo da Cesta Básica (ACCB).");
        ui.label("Para isso, uma das ferramentas desenvolvidas foi esta aplicação desktop, que busca automatizar a pesquisa na plataforma Preço da Hora – Bahia, que disponibiliza os preços de produtos em diversos estabelecimentos da Bahia.");
        ui.label("Para realizar a pesquisa, este aplicativo coleta os dados no processo de scraping no referido site, armazenando-os em um banco de dados e devolvendo-os em uma coleção de arquivos em excel, contendo informações de preços de produtos de interesse. Essa ferramenta pode ser utilizada por outras instituições da Bahia, bastando apenas alterar algumas configurações do programa.");
    }

    pub fn draw_placeholder(&mut self, _ctx: &Context, _frame: &mut Frame, ui: &mut Ui) {
        ui.label("Aba desconhecida...");
    }
}

impl App for PriceMiner {
    fn update(&mut self, ctx: &Context, frame: &mut Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            if self.first_frame {
                self.first_frame(ctx, frame);
                self.first_frame = false;
            }

            self.draw_central_panel(ctx, frame, ui);
        });
    }
}

pub fn run() {
    let options = NativeOptions::default();
    _ = run_native(
        "MyApp",
        options,
        Box::new(|cc| Ok(Box::new(PriceMiner::new(cc)))),
    );
}
