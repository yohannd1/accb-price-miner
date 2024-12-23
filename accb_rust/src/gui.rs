use eframe::{
    egui::{self, Context, Ui},
    run_native, App, CreationContext, Frame, NativeOptions,
};

struct PriceMiner {
    first_frame: bool,
    x: i32,
}

impl PriceMiner {
    pub fn new(_: &CreationContext<'_>) -> Self {
        Self {
            first_frame: true,
            x: 0,
        }
    }

    pub fn first_frame(&mut self, ctx: &Context, _: &mut Frame) {
        ctx.set_zoom_factor(1.25);
    }

    pub fn draw_central_panel(&mut self, _: &Context, _: &mut Frame, ui: &mut Ui) {
        ui.label(format!("Hello, world! {}", self.x));
        if ui.button("Click me").clicked() {
            self.x += 1;
        }
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
