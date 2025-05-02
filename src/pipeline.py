from .video_metadata import obtener_metadata_videos, extraer_comentarios_para_dataframe
from .svg_extraction import Extractor
from .moments_analyzer import MomentosAnalyzer

def ejecutar_pipeline_metadata(channel_url, num_videos=5, extraer_comentarios=True):
    """
    Executes the metadata extraction pipeline.

    :param channel_url: YouTube channel URL.
    :type channel_url: str
    :param num_videos: Number of videos to process.
    :type num_videos: int
    :param extraer_comentarios: Whether to extract comments.
    :type extraer_comentarios: bool
    :return: DataFrame with video metadata or None on failure.
    :rtype: pandas.DataFrame or None
    """
    print(f"Iniciando pipeline para canal {channel_url}, extrayendo {num_videos} videos...")
    
    print("\n== FASE 1: Extrayendo metadata básica ==")
    df_videos = obtener_metadata_videos(channel_url, num_videos)
    
    if df_videos.empty:
        print("No se pudo obtener información de videos. Abortando pipeline.")
        return None
    
    print(f"Metadata básica extraída para {len(df_videos)} videos.")
    
    if extraer_comentarios:
        print("\n== FASE 2: Extrayendo comentarios ==")
        df_videos = extraer_comentarios_para_dataframe(df_videos)
    
    return df_videos

def ejecutar_pipeline_completo(canal, n_videos, comentarios=True, analizar_momentos=True, threshold=80.0):
    """
    Executes the complete pipeline including metadata, SVG extraction, and moments analysis.

    :param canal: YouTube channel URL.
    :type canal: str
    :param n_videos: Number of videos to analyze.
    :type n_videos: int
    :param comentarios: Whether to extract comments.
    :type comentarios: bool
    :param analizar_momentos: Whether to analyze popular moments.
    :type analizar_momentos: bool
    :param threshold: Popularity threshold for moments (0-100).
    :type threshold: float
    :return: DataFrame with all information.
    :rtype: pandas.DataFrame
    """
    df_videos = ejecutar_pipeline_metadata(channel_url=canal, num_videos=n_videos, extraer_comentarios=comentarios)
    
    extractor = Extractor(list(df_videos["URL"]))
    svg_dict = extractor.get_svg_dict()
    svg_list = list(svg_dict.values())
    df_videos["HEATMAP_SVG"] = svg_list
    
    if analizar_momentos:
        print("\n== FASE 3: Analizando momentos populares ==")
        momentos_list = []
        segmentos_list = []
        
        for i, row in df_videos.iterrows():
            video_id = row['ID_VIDEO']
            svg = row['HEATMAP_SVG']
            duration = row['LENGTH']
            
            print(f"Analizando momentos para video: {row['TITLE']}")
            
            analyzer = MomentosAnalyzer(svg, duration)
            momentos, segmentos = analyzer.get_popular_moments(threshold)
            
            momentos_list.append(momentos)
            segmentos_list.append(segmentos)
            
            print(f"  - Encontrados {len(momentos)} momentos populares y {len(segmentos)} segmentos")
        
        df_videos["POPULAR_MOMENTS"] = momentos_list
        df_videos["POPULAR_SEGMENTS"] = segmentos_list
    
    return df_videos