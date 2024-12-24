use crate::{model::OngoingSearch, Result};
use thirtyfour::prelude::*;

const DEFAULT_URL: &'static str = "https://precodahora.ba.gov.br/produtos";

pub struct Scraper<'a> {
    url: &'a str,
    ongoing: &'a mut OngoingSearch,
    driver: &'a mut WebDriver,
}

impl<'a> Scraper<'a> {
    pub fn new(ongoing: &'a mut OngoingSearch, driver: &'a mut WebDriver) -> Self {
        Self {
            url: DEFAULT_URL,
            ongoing,
            driver,
        }
    }

    pub fn begin_search(&mut self) -> Result<()> {
        Ok(())

    // // Navigate to https://wikipedia.org.
    // driver.goto("https://wikipedia.org").await?;
    // let elem_form = driver.find(By::Id("search-form")).await?;

    // // Find element from element.
    // let elem_text = elem_form.find(By::Id("searchInput")).await?;

    // // Type in the search terms.
    // elem_text.send_keys("selenium").await?;

    // // Click the search button.
    // let elem_button = elem_form.find(By::Css("button[type='submit']")).await?;
    // elem_button.click().await?;

    // // Look for header to implicitly wait for the page to load.
    // driver.find(By::ClassName("firstHeading")).await?;
    // assert_eq!(driver.title().await?, "Selenium - Wikipedia");

    // // Always explicitly close the browser.
    // driver.quit().await?;

    // Ok(())
    }
}
