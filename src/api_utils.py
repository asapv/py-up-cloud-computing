import os
import time
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def get_youtube_service():
    """
    Builds and returns a YouTube API service client.

    :return: YouTube API service client.
    :rtype: googleapiclient.discovery.Resource
    """
    api_key = os.getenv("GOOGLE_KEY")
    if not api_key:
        raise ValueError("GOOGLE_KEY environment variable not set.")
    return build('youtube', 'v3', developerKey=api_key)

def retry_request(api_call, max_retries=5, backoff_factor=2):
    """
    Retries an API call with exponential backoff.

    :param api_call: The API call function to execute.
    :type api_call: callable
    :param max_retries: Maximum number of retry attempts.
    :type max_retries: int
    :param backoff_factor: Factor for exponential backoff delay.
    :type backoff_factor: int
    :return: Result of the API call or None if all retries fail.
    :rtype: any
    """
    retries = 0
    while retries < max_retries:
        try:
            return api_call()
        except Exception as e:
            print(f"Error: {e}. Intento {retries + 1} de {max_retries}")
            time.sleep(backoff_factor ** retries)
            retries += 1
    print("Se alcanzó el número máximo de reintentos.")
    return None

def obtener_nombre_categoria(category_id):
    """
    Retrieves the category name for a given category ID.

    :param category_id: YouTube category ID.
    :type category_id: str
    :return: Category name or "Not Available" if not found.
    :rtype: str
    """
    def api_call():
        youtube = get_youtube_service()
        request = youtube.videoCategories().list(part='snippet', id=category_id)
        return request.execute()
        
    response = retry_request(api_call)
    
    if response and 'items' in response and len(response['items']) > 0:
        return response['items'][0]['snippet'].get('title', "Not Available")
    return "Not Available"

def obtener_dislikes(video_id):
    """
    Retrieves the number of dislikes for a video using an external API.

    :param video_id: YouTube video ID.
    :type video_id: str
    :return: Number of dislikes or "Not Available" if not found.
    :rtype: str
    """
    def api_call():
        url = f'https://returnyoutubedislikeapi.com/votes?videoId={video_id}'
        return requests.get(url)

    response = retry_request(api_call)

    if response and response.status_code == 200:
        data = response.json()
        return data.get('dislikes', 'Not Available')
    return 'Not Available'

def obtener_comentarios_video(video_id, max_results=100, max_pages=5):
    """
    Retrieves comments for a YouTube video.

    :param video_id: YouTube video ID.
    :type video_id: str
    :param max_results: Maximum number of comments per page.
    :type max_results: int
    :param max_pages: Maximum number of pages to fetch.
    :type max_pages: int
    :return: List of comment texts.
    :rtype: list
    """
    def api_call(page_token=None):
        youtube = get_youtube_service()
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText",
            pageToken=page_token
        )
        return request.execute()
    
    comentarios = []
    next_page_token = None
    pages_fetched = 0
    
    while pages_fetched < max_pages:
        try:
            response = retry_request(lambda: api_call(next_page_token))
            if not response or "items" not in response:
                break
            for item in response["items"]:
                comentario = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comentarios.append(comentario)

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
            pages_fetched += 1
        except Exception as e:
            print(f"Error al obtener comentarios del video {video_id}: {e}")
            break

    return comentarios

def obtener_channel_id(channel_url):
    """
    Retrieves the channel ID from a YouTube channel URL.

    :param channel_url: YouTube channel URL.
    :type channel_url: str
    :return: Channel ID or None if not found.
    :rtype: str or None
    """
    if "/@" in channel_url:
        username = channel_url.split("/@")[-1].split("/")[0]
    else:
        username = channel_url.rstrip('/').split('/')[-1]

    def api_call():
        youtube = get_youtube_service()
        request = youtube.search().list(
            part="snippet",
            q=username,
            type="channel",
            maxResults=1
        )
        return request.execute()
    
    response = retry_request(api_call)
    if response and response.get('items'):
        return response['items'][0]['snippet']['channelId']
    return None