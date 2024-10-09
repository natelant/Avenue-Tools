# Written in Python 3.12.
# Requires the requests library
from datetime import datetime, timedelta, UTC
import json
import time
import os
import requests

url = 'https://api.iteris-clearguide.com/v1/data_downloader/data_downloader/?customer_key=ut'


def create_data_download(jwt_token):
    yesterday = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    name = yesterday.strftime('UT Download %Y-%m-%d')
    data = {
        'name': name,
        # Start and end timestamp is the same
        's_timestamp': yesterday.timestamp(),
        'e_timestamp': yesterday.timestamp(),
        'granularity': '5min',
        'time_periods': ['00:00-23:59'],
        'dows': ["mon", "tue", "wed", "thu", "fri", "sat", "sun", ],
        'geography_codes': ['state:ut'],
        'columns': [
            'local_timestamp',
            'network_id',
            'source_id',
            'length',
            'closed',
            'primary_source',
            'source_reference',
            'min_speed',
            'avg_speed',
            'max_speed',
            'freeflow',
        ],
        'timezone': 'America/Denver',
    }

    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {jwt_token}'
    }

    # Creates the download
    post_res = requests.post(url, data=json.dumps(data), headers=headers)

    if post_res.status_code != 201:
        print(f'Data download creation failed: {post_res.content}')
        return
    else:
        print(f'Data download creation successful. Generation in progress')

    # Get all the downloads created so far
    get_res = requests.get(url, headers=headers)
    if get_res.status_code != 200:
        print(f'Data download info fetch failed: {get_res.content}')
        return

    get_data = get_res.json()
    my_id = -1
    for download in get_data:
        if download['name'] == name:
            my_id = download['id']
            break
    print(f'Download ID: {my_id}')

    return my_id, name


def download_data(jwt_token, download_id, download_name, download_folder):
    # Get the download status. Note that it could take an hour or more for the download to complete
    # This API call will give a warning if the download is still in progress.
    # Once complete the user who submitted the download (whoever used their JWT) will get an email,
    # which will also have a link to download the data.
    # Result will be a redirect followed by the download. Requests handles it all.
    # When downloading, this might take a few minutes
    download_url = f'https://api.iteris-clearguide.com/v1/data_downloader/data_downloader_download/{download_id}/?customer_key=ut&jwt={jwt_token}'
    while True:
        download_res = requests.get(download_url)
        if download_res.status_code == 400:
            data = download_res.json()
            if 'msg' in data and 'Please check again soon.' in data['msg']:
                print('Data download is still generating. Sleeping for ten seconds.')
            else:
                print(f'Data download file download failed: {download_res.content}')
        elif download_res.status_code != 200:
            print(f'Data download file download failed: {download_res.content}')
        elif download_res.status_code == 200 and download_res.history:
            print('Download finished! Saving to disk.')
            break
        time.sleep(10)
    full_folder = os.path.join(download_folder, f'{download_name}.csv.gz')
    with open(full_folder, 'wb') as f:
        f.write(download_res.content)
    print('Download saved to disk!')


token = 'ADD YOUR TOKEN HERE'
folder = '/path/to/download'
download_id, download_name = create_data_download(token)
download_data(token, download_id, download_name, folder)
