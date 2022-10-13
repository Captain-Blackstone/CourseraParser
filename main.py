from bs4 import BeautifulSoup
from selenium import webdriver
import time
import math
import pyautogui
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import sys


def generate_checkboxes_coordinates() -> list:
    """
    Helper function, generates the coordinates of checkboxes of categories
    """
    x, y = 504, 496  # coordinates of the top-left box
    down = 60  # distance between rows
    right = 400  # distance between columns
    all_categories = []
    for row in range(4):
        for column in range(3):
            if not (column == 3 and row == 2):
                all_categories.append([x + column * right, y + row * down])
    return all_categories


CHECKBOX_CATEGORIES_COORDINATES = generate_checkboxes_coordinates()
CATEGORIES = ['Arts and Humanities', 'Business', 'Computer Science', 'Data Science',
              'Health', 'Information Technology', 'Language Learning', 'Math and Logic',
              'Personal Development', 'Physical Science and Engineering', 'Social Sciences']


def collect_courses_urls_form_single_category(category_number: int) -> list:
    """
    :param category_number:
    :return:
    """
    # Create new driver
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path="./chromedriver", options=options)

    # Go on the page #1
    driver.get("https://www.coursera.org/"
               "search?index=prod_all_products_term_optimization_mzhang_coldstart_test&entityTypeDescription=Courses")
    time.sleep(2)

    # Show categories list
    driver.find_element(by='xpath',
                        value='//*[@id="rendered-content"]/div/div/div[1]/main/div[2]/'
                              'div/div/div/div/div[1]/div/div[1]/div[2]/button/span').click()

    time.sleep(3)

    # Check category checkbox
    x, y = CHECKBOX_CATEGORIES_COORDINATES[category_number]
    pyautogui.click(x=x, y=y)

    # Click apply button
    pyautogui.click(x=392, y=787)
    time.sleep(3)
    i = 0
    final_page = None

    # Go through all the pages and collect the urls of the courses from them
    url_list = []
    while True:
        i += 1
        if final_page and i > final_page:  # If we run out of pages, end loop
            break
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "lxml")
        urls = [a["href"] for a in soup.find_all("a", {"data-click-key": "search.search.click.search_card"})]

        # Figure out the number of the last page. You actually only need to do it the first time, but whatever.
        final_page = min(
            math.ceil(int(soup.find_all("div", {"data-e2e": "NumberOfResultsSection"})[0].text.split()[0]) / 12), 84)
        url_list += urls

        # Click 'next page' button
        driver.find_element(by="xpath",
                            value="/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/"
                                  "div/div/div[2]/div[3]/div/button[7]").click()
    driver.quit()
    return url_list


def collect_business_courses_urls() -> list:
    """
    Business category needs to be taken care of separately because it has more than 84*12 courses (this is the maximum
    number coursera will render)
    :return: list of business courses urls
    """

    xpaths = {
        "beginner": "/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[1]/div/"
                    "div[3]/div/div/div[1]/div/label/span/span/input",
        "intermediate": "/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[1]/"
                        "div/div[3]/div/div/div[2]/div/label/span/span/input",
        "advanced": "/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[1]/div/"
                    "div[3]/div/div/div[3]/div/label/span/span/input",
        "mixed": "/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[1]/div/"
                 "div[3]/div/div/div[4]/div/label/span/span/input"
    }

    all_urls = []
    for category, xpath in xpaths.items():
        # Create new driver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(executable_path="./chromedriver", options=options)

        # Go on the page #1
        driver.get(
            "https://www.coursera.org/search?index=prod_all_products_term_optimization_mzhang_coldstart_test&"
            "entityTypeDescription=Courses")
        time.sleep(2)

        # show more categories
        show_more = driver.find_element(by='xpath',
                                        value='//*[@id="rendered-content"]/div/div/div[1]/main/'
                                              'div[2]/div/div/div/div/div[1]/div/div[1]/div[2]/button/span')
        show_more.click()
        time.sleep(3)

        # choose category
        x, y = CHECKBOX_CATEGORIES_COORDINATES[1]  # business
        pyautogui.click(x=x, y=y)

        # apply
        pyautogui.click(x=392, y=787)
        time.sleep(3)

        # Choose courses only of current level
        beginner = driver.find_element(by="xpath", value=xpath)
        beginner.click()

        # Choose courses only
        val = '/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[1]/div/div[5]/div/div/div[2]/div/' \
              'label/span/span/input'
        courses = driver.find_element(by="xpath", value=val)
        courses.click()

        i = 0
        final_page = None
        while True:
            i += 1
            if final_page and i > final_page:
                break
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "lxml")
            links = [a["href"] for a in soup.find_all("a", {"data-click-key": "search.search.click.search_card"})]
            final_page = min(
                math.ceil(int(soup.find_all("div", {"data-e2e": "NumberOfResultsSection"})[0].text.split()[0]) / 12),
                84)
            all_urls += links
            val = "/html/body/div[3]/div/div/div[1]/main/div[2]/div/div/div/div/div[2]/div[3]/div/button[7]"
            next_page_button = driver.find_element(by="xpath", value=val)
            next_page_button.click()
        driver.quit()
    return all_urls


def collect_all_course_urls(category_num: int) -> None:
    """
    Collects the urls to all the courses on Coursera and saves them into file.
    :return:
    """
    if category_num != 1:
        all_urls = collect_courses_urls_form_single_category(category_num)
    else:
        all_urls = collect_business_courses_urls()
    with open(f"{CATEGORIES[category_num].replace(' ', '_')}.txt", "w") as fl:
        for url in set(list(filter(lambda el: el.startswith("/learn"), all_urls))):
            fl.write(f"{url}\n")


def read_urls_from_file(file_path: str) -> list:
    with open(file_path, "r") as fl:
        urls = [el.strip() for el in fl.readlines()]
    return urls


def get_data_dict_from_url(url: str) -> dict:
    """
    :param url: course page url
    :return: dict, a row in the resulting dataframe. Contains all the necessary info - category, course name, etc.
    """
    url = "https://www.coursera.org" + url
    soup = BeautifulSoup(requests.get(url).text, "lxml")

    # Number of enrolled students - if it's zero, parsing will fail
    enrolled_div = soup.find_all("div", {"class": "_1fpiay2"})
    if enrolled_div:
        n_students = enrolled_div[0].find_all("span")[1].text
    else:
        n_students = "0"

    # Number of ratings - same story
    ratings_div = soup.find_all("span", {"data-test": "ratings-count-without-asterisks"})
    if ratings_div:
        n_ratings = ratings_div[0].find_all("span")[0].text.split()[0]
    else:
        n_ratings = "0"

    # For some reason some urls are broken and redirect to wrong pages. I will return an empy dict for them.
    category_name_div = soup.find_all("div", {"class": "_1ruggxy"})
    if len(category_name_div) < 2:
        print(url)
        return dict()

    record_dict = {
        "Category Name": [category_name_div[1].text],
        "Course Name": [soup.find_all("h1")[0].text.strip()],
        "First Instructor Name": [soup.find_all("h3")[0].text],
        "Course Description": [soup.find_all("div", {"class": "m-t-1 description"})[0].text.strip()],
        "# of Students Enrolled": [n_students],
        "# of Ratings": [n_ratings]
    }
    return record_dict


def form_final_dataframe(file_path: str, category_num: int) -> None:
    """
    Forms the dataframe containing the info about all the Coursera courses
    :return:
    """
    urls = read_urls_from_file(file_path)
    datas = []
    chunk_size = 50
    with ThreadPoolExecutor(chunk_size) as pool:
        for start in range(0, len(urls), chunk_size):
            datas += list(pool.map(get_data_dict_from_url, urls[start:start+chunk_size]))
    coursera_courses_table = pd.DataFrame(columns=["Category Name", "Course Name",
                                                   "First Instructor Name", "Course Description",
                                                   "# of Students Enrolled", "# of Ratings"])
    for data in datas:
        coursera_courses_table = pd.concat([coursera_courses_table, pd.DataFrame.from_dict(data)], ignore_index=True)
    coursera_courses_table.to_csv(f"{CATEGORIES[category_num].repalce(' ', '_')}_courses_info.tsv",
                                  sep="\t", index=False)


if __name__ == "__main__":
    # Intarface as requested

    category = sys.argv[1]
    if category in CATEGORIES:
        category_num = CATEGORIES.index(category)

        # Two stage process.

        # Get the urls of all the courses and save it to 'all_urls.txt'
        collect_all_course_urls(category_num)

        # Form the dataframe using these urls and save it to 'coursera_courses_info.tsv'
        form_final_dataframe(f"{category.replace(' ', '_')}.txt", category_num)
    else:
        print(f"No such category, try one of {', '.join(CATEGORIES)}; if your category name "
              f"consists of multiple words, use quotation marks.")
