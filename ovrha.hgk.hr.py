# -*- coding: cp1250 -*-
import csv
import traceback
from time import sleep

import json
import os

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from xlsxwriter.workbook import Workbook
from datetime import datetime, time

t = 1
timeout = 10

debug = False

headless = False
images = False
max = False
incognito = True
testing = False
headers = ['Sud', 'Broj predmeta', 'Država KO', 'Katastarska općina', 'ZK uložak', 'Katastarska čestica',
           'Vrsta predmeta', 'Površina', 'Vrijednost', 'Država naselja', 'Naselje', 'Općina', 'Županija', 'Adresa',
           'U naravi predstavlja', 'Datum dražbe', 'Adresa dražbe', 'Uvjet prodaje', 'Razgledavanje', 'Jamčevina',
           'Datum odluke o prodaji', 'Nadležni katastar', 'Napomena']

site = "http://ovrha.hgk.hr/ocevidnik-web/#!pretrazivanje_nekretnina"
encoding = 'utf8'
outfile = 'out-ovrha.hgk.hr.csv'
logfile = "log-ovrha.hgk.hr.csv"
logxl = 'log-ovrha.hgk.hr.xlsx'
errorfile = 'error-ovrha.hgk.hr.txt'

licitacija = 'https://licitacija.hr/upload.php'


def main():
    os.system('color 0a')
    logo()
    try:
        print('Press Ctrl+C to skip waiting...')
        wait_start('18:00')
    except KeyboardInterrupt:
        print('Waiting skipped...')
    if not os.path.isfile(outfile):
        with open(outfile, 'w', newline='', encoding=encoding) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
    with open(logfile, 'w', newline='', encoding=encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
    driver = getChromeDriver()
    if not debug:
        driver.get("http://ovrha.hgk.hr/ocevidnik-web/#!pretrazivanje_nekretnina")
        click(driver, '//div[@id="pretraziButton"]')
    scraped = os.listdir('./json')
    while True:
        try:
            for i in range(1, 11):
                broj = getElement(driver, f'//tr[contains(@class,"v-table-row")][{i}]')
                btext = broj.text.strip().replace("/", "-").replace(":", "-").replace("\n", "_") + ".json"
                if btext not in scraped:
                    print("Working on", btext)
                    click(broj, './td')
                    while "Povratak na listu predmeta" not in driver.page_source:
                        sleep(1)
                    data = {}
                    for tr in getElements(driver,
                                          '//tr[@class="v-formlayout-row" or @class="v-formlayout-row v-formlayout-lastrow"]'):
                        td = getElements(tr, './td')
                        data[td[0].text] = td[2].text
                    print(json.dumps(data, indent=4))
                    with open(f'./json/{btext}', 'w') as jfile:
                        json.dump(data, jfile, indent=4)
                    append(data)
                    click(driver, '//span[text()="Povratak na listu predmeta"]')
                else:
                    print("Already scraped", btext)
            print("Moving to next page...")
            click(driver, '//span[text()="Sljedeća"]')
            sleep(2)
            # break
        except:
            traceback.print_exc()
            break
    print("Converting to XLSX...")
    cvrt()
    print("Uploading logs...")
    print(requests.post(licitacija, files={'file': open(logxl, 'rb')}))
    print("All done!")


def cvrt():
    workbook = Workbook(logxl)
    worksheet = workbook.add_worksheet()
    with open(outfile, 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                worksheet.write(r, c, col)
    workbook.close()


def append(row):
    with open(outfile, 'a', newline='', encoding=encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writerow(row)
    with open(logfile, 'a', newline='', encoding=encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
        writer.writerow(row)


def wait_start(runTime):
    startTime = time(*(map(int, runTime.split(':'))))
    while startTime > datetime.today().time():
        sleep(1)
        print(f"Waiting for {runTime}")


def click(driver, xpath, js=False):
    if js:
        driver.execute_script("arguments[0].click();", getElement(driver, xpath))
    else:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def getElement(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


def getElements(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))


def sendkeys(driver, xpath, keys, js=False):
    if js:
        driver.execute_script(f"arguments[0].value='{keys}';", getElement(driver, xpath))
    else:
        getElement(driver, xpath).send_keys(keys)


def getChromeDriver(proxy=None):
    options = webdriver.ChromeOptions()
    if debug:
        # print("Connecting existing Chrome for debugging...")
        options.debugger_address = "127.0.0.1:9222"
    else:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
    if not images:
        # print("Turning off images to save bandwidth")
        options.add_argument("--blink-settings=imagesEnabled=false")
    if headless:
        # print("Going headless")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    if max:
        # print("Maximizing Chrome ")
        options.add_argument("--start-maximized")
    if proxy:
        # print(f"Adding proxy: {proxy}")
        options.add_argument(f"--proxy-server={proxy}")
    if incognito:
        # print("Going incognito")
        options.add_argument("--incognito")
    return webdriver.Chrome(options=options)


def getFirefoxDriver():
    options = webdriver.FirefoxOptions()
    if not images:
        # print("Turning off images to save bandwidth")
        options.set_preference("permissions.default.image", 2)
    if incognito:
        # print("Enabling incognito mode")
        options.set_preference("browser.privatebrowsing.autostart", True)
    if headless:
        # print("Hiding Firefox")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(options)


def logo():
    print(f"""
                        .__                .__             __        .__           
      _______  _________|  |__ _____       |  |__    ____ |  | __    |  |_________ 
     /  _ \  \/ /\_  __ \  |  \\\\__  \      |  |  \  / ___\|  |/ /    |  |  \_  __ \\
    (  <_> )   /  |  | \/   Y  \/ __ \_    |   Y  \/ /_/  >    <     |   Y  \  | \/
     \____/ \_/   |__|  |___|  (____  / /\ |___|  /\___  /|__|_ \ /\ |___|  /__|   
                             \/     \/  \/      \//_____/      \/ \/      \/       
============================================================================================
         www.ovrha.hgk.hr scraper by: fiverr.com/muhammadhassan7
============================================================================================
[+] Resumeble
[+] Upload new logs to licitacija.hr
""")


if __name__ == "__main__":
    main()
