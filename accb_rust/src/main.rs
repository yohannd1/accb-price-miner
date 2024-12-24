// TODO: thread de banco de dados
// TODO: thread de pesquisa
// TODO: thread de export
// TODO: parar de usar eframe (pesado demais!)

use std::error::Error;
use thirtyfour::{DesiredCapabilities, WebDriver};

mod model;
mod scraper;
mod gui;

use model::OngoingSearch;
use scraper::Scraper;

pub type Result<T> = std::result::Result<T, Box<dyn Error + 'static>>;

async fn do_stuff() -> Result<()> {
    let mut ongoing = OngoingSearch {};

    let caps = DesiredCapabilities::chrome();
    let mut driver = WebDriver::new("http://localhost:9515", caps).await?;

    let mut s = Scraper::new(&mut ongoing, &mut driver);
    s.begin_search()?;

    driver.quit().await?;

    Ok(())
}

#[tokio::main]
async fn main() {
    match do_stuff().await {
        Ok(()) => {}
        Err(e) => {
            println!("Error: {:?}", e);
        }
    }

    gui::run();
}
