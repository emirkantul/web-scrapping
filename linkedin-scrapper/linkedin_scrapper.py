import time
import requests
from bs4 import BeautifulSoup
from random import randint
import logging
import json
import os
import dateparser

logging.basicConfig(level=logging.INFO)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


def scrape_linkedin_job(base_url):
    jobs = load_jobs()
    start_page = len(jobs) // 25
    for i in range(start_page, 4000):  # 25 * 4000 = 100,000
        url = f"{base_url}&pageNum={i}"
        response = make_request(url)
        if response is not None:
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")
            for job_card in job_cards:
                job = {}
                title_tag = job_card.find("h3", class_="base-search-card__title")
                company_tag = job_card.find("h4", class_="base-search-card__subtitle")
                location_tag = job_card.find("span", class_="job-search-card__location")
                date_tag = job_card.find(
                    "time", class_="job-search-card__listdate--new"
                )
                salary_tag = job_card.find(
                    "span", class_="job-search-card__salary-info"
                )
                link_tag = job_card.find("a", href=True)
                if title_tag:
                    job["title"] = title_tag.text.strip()
                if company_tag:
                    job["company"] = company_tag.text.strip()
                if location_tag:
                    job["location"] = location_tag.text.strip()
                if date_tag:
                    relative_date = date_tag.text.strip()
                    absolute_date = dateparser.parse(relative_date)
                    job["date"] = absolute_date.strftime("%Y-%m-%d %H:%M:%S")
                if salary_tag:
                    job["salary"] = salary_tag.text.strip()
                if link_tag:
                    job["link"] = link_tag["href"]
                if job:
                    jobs.append(job)

            logging.info(f"Page {i} scraped successfully")
            save_jobs(jobs)
    return jobs


def make_request(url, retries=3):
    for i in range(retries):
        try:
            time.sleep(randint(1, 5))  # Random sleep to avoid getting blocked
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # If the response contains an HTTP error status code, raise an exception
            return response
        except requests.exceptions.HTTPError as errh:
            logging.error("HTTP Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            logging.error("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            logging.error("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            logging.error("Something Else:", err)
    return None


def save_jobs(jobs):
    with open("jobs.json", "w") as f:
        json.dump(jobs, f)


def load_jobs():
    if os.path.exists("jobs.json"):
        with open("jobs.json", "r") as f:
            return json.load(f)
    return []


base_url = "https://www.linkedin.com/jobs/search?keywords=&location=United%20States&geoId=103644278&trk=public_jobs_jobs-search-bar_search-submit&position=1"
jobs = scrape_linkedin_job(base_url)
print(len(jobs))


def scrape_job_details(job_link):
    try:
        response = make_request(job_link)
        if response is not None:
            soup = BeautifulSoup(response.text, "html.parser")

            job_details_div = soup.find(
                "div",
                {
                    "class": "show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden"
                },
            )
            job_details = job_details_div.text if job_details_div else ""

            job_criteria_ul = soup.find(
                "ul", {"class": "description__job-criteria-list"}
            )
            job_criteria_items = (
                job_criteria_ul.find_all(
                    "li", {"class": "description__job-criteria-item"}
                )
                if job_criteria_ul
                else []
            )

            job_criteria = {}
            for item in job_criteria_items:
                key = item.find(
                    "h3", {"class": "description__job-criteria-subheader"}
                ).text
                value = item.find(
                    "span",
                    {
                        "class": "description__job-criteria-text description__job-criteria-text--criteria"
                    },
                ).text
                job_criteria[key.strip()] = value.strip()
            logging.info(f"Job details scraped successfully for {job_link}")
            return job_details, job_criteria
        logging.error(f"Error fetching details for {job_link}")
    except Exception as e:
        logging.error(f"Error fetching details for {job_link}: {e}")
        return None, {}


# In your main function, after you've scraped the job details, add this:
for job in jobs:
    if "details" in job:
        logging.info(f"Skipping {job['link']} as it has already been scraped")
        pass
    job_details, job_criteria = scrape_job_details(job["link"])
    if job_details is not None:
        job["details"] = job_details.strip()
        job.update(job_criteria)
    save_jobs(jobs)
