import random

from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class GradCrackerLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).filter(has_not_text="2024/25").inner_text()
        company = await page.locator("xpath=/html/body/div[4]/div/div[3]/ul/li[2]/a").inner_text()
        company = company[:-4]
        description = await page.locator(".job-description").inner_text()
        sidebar = page.locator("xpath=/html/body/div[4]/div/div[5]/div[2]/div[1]/div[1]/ul")
        location = ""
        for li in await sidebar.get_by_role("listitem").all():
            text = await li.inner_text()
            if "Location" in text:
                location = text.replace("Location\n", "")
        return {"title": title, "description": description, "company": company, "location": location}


class GradCracker(JobBoardScraper):
    site_url = "https://www.gradcracker.com"
    site_name = "Gradcracker"
    run_flag = False

    async def get_recommendations(self, a, b, c, d=0):
        return

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set, lock):
        links = await page.get_by_title("Apply For").all()
        for head in links:
            text = await head.text_content()
            if Job.test_blacklist(text):
                async with lock:
                    link_set.add(GradCrackerLink(await head.get_attribute("href"), self.site_name))

    def get_next_button(self, page):
        return page.locator("css=a[rel='next']")

    async def get_search_results(self, link_set, lock, sem, search_term, no_pages=0):
        # Gradcracker works a little differently, so instead of searching for a term, you'd search by discipline.
        # Doing this means we're actually going to discard the search term and check against the flag for whether
        # we've done a search or not.
        async with sem:
            async with lock:
                if not GradCracker.run_flag:
                    context, page = await self.get_context()
                    await page.goto("https://www.gradcracker.com/search/computing-technology/graduate-jobs")
                    GradCracker.run_flag = True
                else:
                    return

            # We're going to check everything and throw out the no_pages variable too, what a shame!
            while True:
                await self.process_search_result_page(page, link_set, lock)
                if not await self.next_page(page):
                    break
            await page.close()
            await context.close()
            return
