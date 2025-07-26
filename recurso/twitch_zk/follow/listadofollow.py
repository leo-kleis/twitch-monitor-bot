import os
import requests
import csv
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv

def main():
    if os.environ.get('ENVIRONMENT') != 'production':
        load_dotenv()

    def get_followers(token, user_id, client_id):
        followers = []
        url = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={user_id}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(url, headers=headers)
        print(response)
        response.raise_for_status()
        data = response.json()

        total_followers = data['total']

        with tqdm(total=total_followers) as pbar:
            while url:
                # Guardamos user_id, user_name y followed_at (cambiado el orden)
                new_followers = [(follower['user_id'], follower['user_name'], follower['followed_at']) for follower in data['data']]
                followers.extend(new_followers)
                pbar.update(len(new_followers))
                cursor = data['pagination'].get('cursor')
                if cursor:
                    url = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={user_id}&after={cursor}'
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                else:
                    break

        total_followers = len(followers)
        # Reorganizado: ahora tenemos rank, user_id, username, fecha
        followers = [(total_followers - i, user_id, name, datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%y')) 
                    for i, (user_id, name, date) in enumerate(followers)]

        return followers

    user_id = os.getenv('BROADCASTER_ID')
    client_id = os.getenv('TTG_BOT_CLIENT_ID')
    token = os.getenv('TTG_BOT_TOKEN')

    followers = get_followers(token, user_id, client_id)
    date = datetime.now().strftime('%y-%m-%d')
    year = datetime.now().strftime('%Y')
    folder_path = os.path.join('recurso/twitch_zk/follow/follow', year)
    filename = f'[{date}] Followers.csv'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    counter = 1
    full_path = os.path.join(folder_path, filename)
    while os.path.isfile(full_path):
        filename = f'[{date}] ({counter}) Followers.csv'
        full_path = os.path.join(folder_path, filename)
        counter += 1

    with open(full_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # Modificado el orden de las columnas segun lo solicitado
        writer.writerow(["#", "User ID", "Username", "Followed At"])
        for follower in followers:
            writer.writerow(follower)  # Ya no necesitamos ajustar nada, el orden ya esta correcto

if __name__ == '__main__':
    main()