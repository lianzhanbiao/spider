import os
import json
import subprocess
from datetime import datetime, timezone

input_location = "上海"
start_time = "2023-01-01"
end_time = "2023-11-02"
start_time = datetime.strptime(start_time, '%Y-%m-%d')
end_time = datetime.strptime(end_time, '%Y-%m-%d')


columns = ['mid', 'publish_time', 'content', 'location', 'iplocation', 'longitude', 'latitude', 'user_id', 'user_name', 'user_link', 'weibo_link', 'pics']
csvfile = f'{input_location}_weibo.csv'
result_dir = f'{input_location}_weibo'
if not os.path.exists(result_dir):
    os.mkdir(result_dir)
with open(csvfile, 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()[1:]
    for line in lines:
        data = line.split(',')
        weibo_data = {
                    'mid': data[0],
                    'publish_time': data[1],
                    'content': data[2],
                    'location': data[3],
                    'iplocation': data[4],
                    'longitude': data[5],
                    'latitude': data[6],
                    'user_id': data[7],
                    'user_name': data[8],
                    'user_link': data[9],
                    'weibo_link': data[10],
                    'pics': data[11]
                }
        if datetime.strptime(weibo_data['publish_time'], '%Y-%m-%d %H:%M:%S') < start_time or datetime.strptime(weibo_data['publish_time'], '%Y-%m-%d %H:%M:%S') > end_time:
            continue
        temp_result_dir = f'{result_dir}/{weibo_data["mid"]}'
        if not os.path.exists(temp_result_dir):
            os.mkdir(temp_result_dir)
        else:
            continue
        temp_result_file = f'{temp_result_dir}/{weibo_data["mid"]}.json'
        with open(temp_result_file, 'w', encoding='utf-8', newline='') as f:
            json.dump(weibo_data, f, ensure_ascii=False, indent=4)
            pics = weibo_data['pics'].split('-')

            if len(pics) > 0:
                for url in pics:
                        savepath = f'{temp_result_dir}/{url.split("/")[-1]}'
                        subprocess.run(['wget', url, '-O', savepath])
