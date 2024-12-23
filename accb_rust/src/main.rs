mod gui;

// TODO: thread de banco de dados
// TODO: thread de pesquisa
// TODO: thread de export
// TODO: parar de usar eframe (pesado demais!)

fn main() {
    std::thread::spawn(|| {
        println!("Hello from thread 1!");
    });

    gui::run();
}
