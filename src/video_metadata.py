import isodate
import pandas as pd
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from concurrent.futures import ThreadPoolExecutor, as_completed
from .api_utils import get_youtube_service, retry_request, obtener_nombre_categoria, obtener_dislikes, obtener_comentarios_video, obtener_channel_id

def extraer_id_video(url):
    """
    Extracts the video ID from a YouTube URL.

    :param url: YouTube video URL.
    :type url: str
    :return: Video ID or None if not found.
    :rtype: str or None
    """
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

def obtener_info_detallada_video(video_id):
    """
    Retrieves detailed information for a YouTube video.

    :param video_id: YouTube video ID.
    :type video_id: str
    :return: Dictionary with video details.
    :rtype: dict
    """
    def api_call():
        youtube = get_youtube_service()
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        return request.execute()

    response = retry_request(api_call)
    
    info = {
        "duration_seconds": "Not Available",
        "fecha_publicacion": "Not Available",
        "descripcion": "Not Available",
        "channel_name": "Not Available",
        "tags": [],
        "category_id": "Not Available",
        "view_count": "Not Available",
        "like_count": "Not Available"
    }
    
    if response and 'items' in response and len(response['items']) > 0:
        item = response['items'][0]
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        statistics = item.get('statistics', {})
        
        if 'duration' in content_details:
            duration_iso = content_details['duration']
            info["duration_seconds"] = int(isodate.parse_duration(duration_iso).total_seconds())
            
        info["fecha_publicacion"] = snippet.get('publishedAt', "Not Available")
        if info["fecha_publicacion"] != "Not Available":
            info["fecha_publicacion"] = datetime.strptime(info["fecha_publicacion"], '%Y-%m-%dT%H:%M:%SZ')
        
        info["descripcion"] = snippet.get('description', "Not Available")
        info["channel_name"] = snippet.get('channelTitle', "Not Available")
        info["tags"] = snippet.get('tags', [])
        info["category_id"] = snippet.get('categoryId', "Not Available")
        info["view_count"] = statistics.get('viewCount', "Not Available")
        info["like_count"] = statistics.get('likeCount', "Not Available")
    
    if info["category_id"] != "Not Available":
        info["category_name"] = obtener_nombre_categoria(info["category_id"])
    else:
        info["category_name"] = "Not Available"
        
    return info

def obtener_transcripcion(video_id, lang=['en']):
    """
    Retrieves the transcription for a YouTube video.

    :param video_id: YouTube video ID.
    :type video_id: str
    :param lang: List of preferred languages for transcription.
    :type lang: list
    :return: Tuple of (transcription text, transcription with timestamps).
    :rtype: tuple
    """
    try:
        transcripcion = YouTubeTranscriptApi.get_transcript(video_id, languages=lang)
        texto = ' '.join([entrada['text'] for entrada in transcripcion])
        transcripcion_con_tiempos = normalizar_transcripcion(transcripcion)
        return texto, transcripcion_con_tiempos
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Not Available", []
    except Exception as e:
        print(f"Error al obtener transcripción para {video_id}: {e}")
        return "Error al obtener transcripción", []

def normalizar_transcripcion(transcripcion):
    """
    Normalizes transcription by adding timestamp ranges.

    :param transcripcion: List of transcription entries.
    :type transcripcion: list
    :return: List of normalized transcription segments with timestamps.
    :rtype: list
    """
    if not transcripcion:
        return []

    segmentos = []
    for i, entrada in enumerate(transcripcion):
        start = entrada['start']
        end = start + entrada['duration']

        if i + 1 < len(transcripcion):
            next_start = transcripcion[i + 1]['start']
            end = next_start

        segmentos.append(f"[{start:.2f}s - {end:.2f}s] {entrada['text']}")
    return segmentos

def obtener_info_basica_videos(channel_url, n=10):
    """
    Retrieves basic information for the latest videos from a channel.

    :param channel_url: YouTube channel URL.
    :type channel_url: str
    :param n: Number of videos to retrieve.
    :type n: int
    :return: List of video information dictionaries.
    :rtype: list
    """
    channel_id = obtener_channel_id(channel_url)
    if not channel_id:
        print(f"No se pudo obtener ID de canal para {channel_url}")
        return []

    def api_call():
        youtube = get_youtube_service()
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=n
        )
        return request.execute()
    
    response = retry_request(api_call)
    videos = []
    
    if response and 'items' in response:
        for item in response['items']:
            if item['id']['kind'] == 'youtube#video':
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title']
                })
    
    return videos

def obtener_info_video_basica(video):
    """
    Retrieves basic metadata for a single video.

    :param video: Dictionary with video ID and title.
    :type video: dict
    :return: Dictionary with detailed video metadata.
    :rtype: dict
    """
    video_id = video.get('id')
    titulo = video.get('title', 'Not Available')
    url = f"https://www.youtube.com/watch?v={video_id}"

    info_detallada = obtener_info_detallada_video(video_id)
    dislikes = obtener_dislikes(video_id)
    texto_transcripcion, transcripcion_con_tiempos = obtener_transcripcion(video_id)

    return {
        'ID_VIDEO': video_id,
        'TITLE': titulo,
        'URL': url,
        'CHANNEL_NAME': info_detallada["channel_name"],
        'UPLOAD_DATE': info_detallada["fecha_publicacion"],
        'DESCRIPTION': info_detallada["descripcion"],
        'TAGS': info_detallada["tags"],
        'CATEGORY': info_detallada["category_name"],
        'LENGTH': info_detallada["duration_seconds"],
        'VIEWS': info_detallada["view_count"],
        'LIKES': info_detallada["like_count"],
        'DISLIKES': dislikes,
        'TRANSCRIPTION': texto_transcripcion,
        'TRANSCRIPTION_TIMESTAMPS': transcripcion_con_tiempos,
        'COMMENTS': [],
        'HEATMAP_SVG': 'Not Available'
    }

def obtener_metadata_videos(channel_url, n=10):
    """
    Retrieves metadata for multiple videos from a channel.

    :param channel_url: YouTube channel URL.
    :type channel_url: str
    :param n: Number of videos to process.
    :type n: int
    :return: DataFrame with video metadata.
    :rtype: pandas.DataFrame
    """
    videos = obtener_info_basica_videos(channel_url, n)
    
    if not videos:
        print("No se pudieron obtener videos del canal")
        return pd.DataFrame()
        
    print(f"Se encontraron {len(videos)} videos para procesar")
    
    datos_videos = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(obtener_info_video_basica, video): video for video in videos}

        for future in as_completed(futuros):
            try:
                resultado = future.result()
                if resultado:
                    datos_videos.append(resultado)
                    print(f"Procesada metadata básica del video: {resultado['TITLE']}")
            except Exception as e:
                print(f"Error al procesar un video: {e}")

    return pd.DataFrame(datos_videos)

def extraer_comentarios_para_dataframe(df, max_comments_per_video=100):
    """
    Extracts comments for videos in a DataFrame.

    :param df: DataFrame with video metadata.
    :type df: pandas.DataFrame
    :param max_comments_per_video: Maximum number of comments per video.
    :type max_comments_per_video: int
    :return: Updated DataFrame with comments.
    :rtype: pandas.DataFrame
    """
    print("\n== Extrayendo comentarios para los videos ==")
    
    def procesar_comentarios(row):
        video_id = row['ID_VIDEO']
        print(f"Obteniendo comentarios para: {row['TITLE']}")
        comentarios = obtener_comentarios_video(video_id, max_results=max_comments_per_video)
        return {
            'ID_VIDEO': video_id,
            'COMMENTS': comentarios,
            'COMMENT_COUNT': len(comentarios)
        }
    
    resultados_comentarios = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futuros = {executor.submit(procesar_comentarios, row): i for i, row in df.iterrows()}
        
        for future in as_completed(futuros):
            try:
                resultado = future.result()
                if resultado:
                    resultados_comentarios.append(resultado)
            except Exception as e:
                print(f"Error al obtener comentarios: {e}")
    
    df_comentarios = pd.DataFrame(resultados_comentarios)
    
    if not df_comentarios.empty:
        for i, row in df_comentarios.iterrows():
            video_id = row['ID_VIDEO']
            idx = df.index[df['ID_VIDEO'] == video_id].tolist()
            if idx:
                df.at[idx[0], 'COMMENTS'] = row['COMMENTS']
    
    return df