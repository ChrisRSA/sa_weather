import requests, os, bs4
from datetime import datetime, timedelta
import sys
from typing import List, Union
import yagmail
import keyrings.alt

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

def get_time():
    utc_hour = datetime.utcnow().hour
    time = ''
    if utc_hour >= 9 and utc_hour < 15:
        time = '06h00UTC'
    elif utc_hour >= 15 and utc_hour < 21:
        time = '12h00UTC'
    elif utc_hour >= 21 and utc_hour < 3:
        time = '18h00UTC'
    elif utc_hour >= 3 and utc_hour < 9:
        time = '00h00UTC'
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

def main():
    # The program takes 1 optional argument: an output filename. If not present,
    # we will write the output a default filename, which is:
    
    time = get_time()

    filename = f"{(datetime.utcnow()-timedelta(hours=4)).strftime('%Y-%m-%d')}-{time}.jpg"
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

    # print("Uploading image to Google Drive...")
    # gfile = drive.CreateFile({'parents': [{'id': '1zpmHVwyT_SWaB14JeT2DS1qjfDG_cUzS'}]})
    # # Read file and set it as the content of this instance.
    # gfile['title'] = filename
    # gfile.SetContentFile(full_path)
    # gfile.Upload() # Upload the file.
    # print('Done uploading image.')
    
    yagmail.register(EMAIL1, PASSWORD)
    yag = yagmail.SMTP(EMAIL1)
    yag.send(to=EMAIL2, subject='Test', contents='Hi Chris', attachments=f'data/{filename}.jpg')

if __name__ == "__main__":
    main()