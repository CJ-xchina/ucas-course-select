import json
import threading
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from matplotlib import pyplot as plt
import ddddocr
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime

from utils import driverOption, click, dataCollection, loop, ocrCal

def select_course(config):
    try:
        options = webdriver.EdgeOptions()
        driver = webdriver.Edge()

        driver.get('https://sep.ucas.ac.cn/')

        while True:
            username_input = driver.find_element(By.ID, 'userName1')
            password_input = driver.find_element(By.ID, 'pwd1')
            username_input.send_keys(config['username'])
            password_input.send_keys(config['password'])
            if config.get('noCaptcha', False):
                pass
            else:
                captcha_image = driver.find_element(By.ID, 'certCode1')
                captcha_image.screenshot('captcha.png')

                image = Image.open('captcha.png')
                image = image.crop((100, 0, 250, 45))
                image.save('captcha.png')

                ocr = ddddocr.DdddOcr(beta=True)
                with open('captcha.png', 'rb') as f:
                    image = f.read()

                res = ocr.classification(image)
                print(res)

                captcha_image.send_keys(res)

            login_button = driver.find_element(By.ID, 'sb1')
            login_button.click()

            wait = WebDriverWait(driver, 3)

            try:
                wait.until(EC.url_to_be('https://sep.ucas.ac.cn/appStore'))
                break
            except:
                print("验证码输入错误，正在刷新页面...")
                driver.refresh()

        sleep(1)

        click(driver, By.LINK_TEXT, '选课系统')
        click(driver, By.LINK_TEXT, '选修课程', loop=False)

        sleep(2)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        click(driver, By.XPATH, '//button[contains(text(), "保存联系方式")]')

        sleep(2)
        click(driver, By.XPATH, '//button[contains(text(), "新增加本学期研究生课程")]')

        sleep(2)
        while True:
            driver.refresh()
            frame = driver.find_element(By.ID, config['subjectID'])
            print(frame.is_selected())
            frame.click()
            print(frame.is_selected())

            sleep(1)

            loop(driver, By.XPATH, config['courseID'])

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            ocrImage = driver.find_element(By.ID, 'adminValidateImg')
            ocrImage.screenshot('ocrCal.png')

            image = Image.open('ocrCal.png')
            res = ocrCal('ocrCal.png', import_onnx_path='models/ocr_1.0_299_3000_2023-06-07-12-34-41.onnx', \
                        charsets_path='models/charsets.json')

            vcode = driver.find_element(By.ID, 'vcode')
            vcode.send_keys(res)

            submit_button = driver.find_element(By.XPATH, "//button[@name='sb' and @value='y']")
            submit_button.click()

            sleep(2)

            current_url = driver.current_url

            confirm_button = driver.find_element(By.XPATH, "//button[text()='确定']")
            confirm_button.click()

            print(f'[{datetime.datetime.now()}]选课完成！')
            sleep(1)

            if driver.find_element(By.XPATH, \
                        "//a[text()='"+config['courseID']+"']/ancestor::tr//button").is_enabled():
                print(f'[{datetime.datetime.now()}]选课完成！')
                driver.quit()
                return True
    except Exception as e:
        print(f'Error occurred: {e}')
        driver.quit()
        return False

def start_thread(config):
    while True:
        success = select_course(config)
        if success:
            print(f"Thread for {config['courseID']} finished successfully.")
            break
        else:
            print(f"Thread for {config['courseID']} failed, restarting...")

if __name__ == "__main__":
    with open('config.json', 'r') as f:
        configs = json.load(f)

    threads = []
    for config in configs:
        t = threading.Thread(target=start_thread, args=(config,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
