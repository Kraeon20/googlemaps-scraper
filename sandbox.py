from playwright.async_api import async_playwright, TimeoutError, Page, Locator
from dataclasses import dataclass, asdict, field
import pandas as pd
import logging
import asyncio
import re
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Business:
    name: str = ""
    address: str = ""
    website: str = ""
    phone_number: str = ""
    email: str = ""
    facebook: str = ""
    instagram: str = ""
    twitter: str = ""
    linkedin: str = ""

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )



async def extract_emails_from_page(page: Page):
    """
    Extract email from a webpage using a regex pattern and validate it.
    """
    content = await page.content()
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, content)
    return emails[0] if emails else "None"

async def extract_social_media_links(page: Page):
    """
    Extracts social media links from a webpage.
    """
    social_media_links = {
        "Facebook": None,
        "Instagram": None,
        "Twitter": None,
        "LinkedIn": None
    }
    
    content = await page.content()
    
    # Search for social media links
    for platform in social_media_links.keys():
        pattern = rf"https?:\/\/(www\.)?{platform.lower()}\.com\/(\w+)\/?"
        match = re.search(pattern, content)
        if match:
            social_media_links[platform] = match.group(0)
        else:
            social_media_links[platform] = "None"

    # Specific patterns for LinkedIn
    linkedin_pattern_company = r"https?://(www\.)?linkedin\.com/company/([\w-]+)/?"
    linkedin_pattern_personal = r"https?://(www\.)?linkedin\.com/in/([\w-]+)/?"

    match_company = re.search(linkedin_pattern_company, content)
    match_personal = re.search(linkedin_pattern_personal, content)

    if match_company:
        social_media_links["LinkedIn"] = match_company.group(0)
    elif match_personal:
        social_media_links["LinkedIn"] = match_personal.group(0)

    return social_media_links

async def main(search_list, quantities):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Launch in headless mode for production
        page = await browser.new_page()

        try:
            await accept_cookies(page)
            business_list = BusinessList()

            for search_for, total in zip(search_list, quantities):
                logging.info(f"Searching for {search_for} with quantity: {total}")
                listings = await scrape_listings(page, search_for, total)
                businesses = await scrape_business_details(page, listings)
                business_list.business_list.extend(businesses.business_list)

            return business_list
        except Exception as e:
            logging.error(f"An error occurred in the main process: {e}")
            return None
        finally:
            await browser.close()

async def accept_cookies(page):
    try:
        await page.goto("https://www.google.com/maps", timeout=30000)
        await page.wait_for_selector("form[action='https://consent.google.com/save'] button", timeout=5000)

        cookies_button = page.locator("form[action='https://consent.google.com/save'] button")
        if await cookies_button.count() > 0:
            await cookies_button.first.click()
            logging.info("Accepted cookies")
    except TimeoutError:
        logging.warning("Timeout while trying to accept cookies")

async def scrape_listings(page, search_for, total):
    try:
        await page.locator('//input[@id="searchboxinput"]').fill(search_for)
        await page.keyboard.press("Enter")
        await page.wait_for_selector('a[href*="https://www.google.com/maps/place"]', timeout=10000)
        await page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        previously_counted = 0
        while True:
            await page.mouse.wheel(0, 10000)
            await page.wait_for_timeout(2000)

            current_count = await page.locator('a[href*="https://www.google.com/maps/place"]').count()
            if current_count >= total:
                listings = await page.locator('a[href*="https://www.google.com/maps/place"]').all()  # Await the result
                listings = listings[:total]  # Now you can slice the list
                logging.info(f"Total Scraped: {len(listings)}")
                return listings
            elif current_count == previously_counted:
                listings = await page.locator('a[href*="https://www.google.com/maps/place"]').all()  # Await the result
                logging.info(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                return listings
            else:
                previously_counted = current_count
                logging.info(f"Currently Scraped: {previously_counted}")
    except Exception as e:
        logging.error(f"Error scraping listings: {e}")
        return []

async def scrape_business_details(page, listings):
    business_list = BusinessList()
    
    for listing in listings:
        try:
            await listing.click()
            await page.wait_for_timeout(2000)  # Wait for page to load completely
            business = await extract_business_info(page, listing)
            if business:
                business_list.business_list.append(business)
        except Exception as e:
            logging.error(f'Error occurred while scraping business details: {e}')
    
    return business_list

async def extract_business_info(page: Page, listing: Locator):
    """
    Extract business information from a listing and detailed page.
    """
    name_attribute = 'aria-label'
    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
    website_url_xpath = '//a[@data-item-id="authority"]'

    business = Business()

    try:
        business.name = await listing.get_attribute(name_attribute) or ""
        if len(business.name) < 1:
            business.name = ""

        address_locator = page.locator(address_xpath)
        website_locator = page.locator(website_xpath)
        phone_number_locator = page.locator(phone_number_xpath)
        website_url_locator = page.locator(website_url_xpath)

        business.address = await address_locator.inner_text() if await address_locator.count() > 0 else ""
        business.website = await website_locator.inner_text() if await website_locator.count() > 0 else ""
        business.phone_number = await phone_number_locator.inner_text() if await phone_number_locator.count() > 0 else ""

        if await website_url_locator.count() > 0:
            try:
                async with page.context.expect_page() as new_page_info:
                    await website_url_locator.first.click()
                new_page = await new_page_info.value
                await new_page.wait_for_load_state("networkidle")

                business.email = await extract_emails_from_page(new_page)

                social_media_links = await extract_social_media_links(new_page)
                business.facebook = social_media_links.get("Facebook", "None")
                business.instagram = social_media_links.get("Instagram", "None")
                business.twitter = social_media_links.get("Twitter", "None")
                business.linkedin = social_media_links.get("LinkedIn", "None")

                await new_page.close()
            except Exception as e:
                logging.error(f"Error retrieving social media links: {e}")
                business.facebook = business.instagram = business.twitter = business.linkedin = "None"
        else:
            business.website = None

    except Exception as e:
        logging.error(f"Error retrieving data: {e}")

    return business




def business_to_table_row(business):
    row = [
        business.name,
        business.address,
        business.email,
        business.website,
        business.phone_number,
        business.linkedin,
        business.twitter,
        business.facebook,
        business.instagram,
    ]
    return row


if __name__ == "__main__":
    search_list = ["lawyers in New York"]
    quantities = [40]
    
    result = asyncio.run(main(search_list, quantities))  # Running async function in main thread
    if result:
        df = result.dataframe()
        df.to_csv("business_data.csv", index=False)
        logging.info("Data saved to business_data.csv")
