import requests, os, bs4
from datetime import datetime, timedelta
import sys
from typing import List, Union
import yagmail
from PIL import Image
import pytesseract
import glob

env_file = os.getenv('GITHUB_ENV')

EMAIL1 = os.environ['EMAIL1']
EMAIL2 = os.environ['EMAIL2']
PASSWORD = os.environ['PASSWORD']

# from pydrive.auth import GoogleAuth
# from pydrive.drive import GoogleDrive

# gauth = GoogleAuth(settings_file='settings.yaml')
# gauth.LocalWebserverAuth()

# drive = GoogleDrive(gauth)

# Downloads the URL.
url = 'https://www.weathersa.co.za/home/synopticcharts'
res = requests.get(url)
res.raise_for_status()

# Create the folder in path.
os.makedirs('data', exist_ok = True)

def get_date():
    return datetime.utcnow().strftime('%Y-%m-%d')

def get_time():
    utc_hour = datetime.utcnow().hour
    time = ''
    if utc_hour >= 6 and utc_hour < 12:
        time = '0600'
    elif utc_hour >= 12 and utc_hour < 18:
        time = '1200'
    elif utc_hour >= 18 and utc_hour < 24:
        time = '1800'
    elif utc_hour >= 0 and utc_hour < 6:
        time = '0000'
    return time

def process_page(content):
    # Find the images.
    all_post = content.select('img[src]')
    data = ''

    for post in all_post:
        src = post.get('src')
        if not src:
            print('Could not find image.')
        # Download the images.
        elif src == '/images/data/specialised/ma_sy.gif':
            res = requests.get('https://www.weathersa.co.za'+src)
            res.raise_for_status()
            data = res
        else:
            pass
    return data
            
    #print('Done.')

def pull_data(url):
    resp = requests.get(url)
    resp.raise_for_status()

    content = bs4.BeautifulSoup(res.text, 'html.parser')
    return process_page(content)

def get_latest_file():
    files = glob.glob('data/*.jpg')
    name = max(files, key=os.path.getctime)
    name = name.replace('.jpg', '')
    return name[-4:]

def crop_and_get_text(im, crop_rectangle):
    cropped_im = im.crop(crop_rectangle)
    return pytesseract.image_to_string(cropped_im, config='--psm 7')

def clean_text(text):
    return text.replace('Valid', '').replace('UTC', '').replace(':', '').replace(' ', '')

# a function that will take a path open and crop the image and return the text then compare if that text is similiar to another string
def compare_text(path, text):
    im = Image.open(path)
    crop_rectangle = (655, 125, 830, 175)
    text_from_image = crop_and_get_text(im, crop_rectangle)
    text_from_image = clean_text(text_from_image)
    if text_from_image == text:
        return True
    else:
        return False


def main():
    # The program takes 1 optional argument: an output filename. If not present,
    # we will write the output a default filename, which is:
    
    date = get_date()
    time = get_time()
    print(time)

    filename = f"{date}-{time}.jpg"
    full_path = os.path.join('data', filename)
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print(f"Will write data to {filename}")

    print(f"Pulling data from {url}...")
    data = pull_data(url)
    print(f"Done pulling data.")

    print("Writing data locally...")
    with open(full_path, 'wb') as imageFile:
            for chunk in data.iter_content(100000):
                imageFile.write(chunk)
            imageFile.close()
    print("Done writing data.")

    print('Checking if image has been updated...')
    latest_time = get_latest_file()
    if compare_text(full_path, latest_time) == True:
        print('Image has been updated.')
        with open(env_file, "a") as myfile:
            myfile.write("UPDATED=TRUE")
        print('Sending email...')
        yag = yagmail.SMTP(EMAIL1, PASSWORD)
        yag.send(to=EMAIL2, subject='Test', contents='Hi Chris', attachments=[full_path])
    else:
        print('Image has not been updated.')
        with open(env_file, "a") as myfile:
            myfile.write("UPDATED=FALSE")
        exit()


    # print("Uploading image to Google Drive...")
    # gfile = drive.CreateFile({'parents': [{'id': '1zpmHVwyT_SWaB14JeT2DS1qjfDG_cUzS'}]})
    # # Read file and set it as the content of this instance.
    # gfile['title'] = filename
    # gfile.SetContentFile(full_path)
    # gfile.Upload() # Upload the file.
    # print('Done uploading image.')

    # yagmail.register(EMAIL1, PASSWORD)
    #yag = yagmail.SMTP(EMAIL1, PASSWORD)
    #yag.send(to=EMAIL2, subject='Test', contents='Hi Chris', attachments=[full_path])

if __name__ == "__main__":
    main()