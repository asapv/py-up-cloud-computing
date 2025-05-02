import sys
import os
print(f"Usando Python en: {sys.executable}\n")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import argparse
from src.pipeline import ejecutar_pipeline_completo

def main():
    parser = argparse.ArgumentParser(description="YouTube Scraper Pipeline")
    parser.add_argument("--channel", required=True, help="YouTube channel URL")
    parser.add_argument("--n-videos", type=int, default=5, help="Number of videos to process")
    parser.add_argument("--output-file", required=True, help="Path to output Excel file")
    args = parser.parse_args()

    df = ejecutar_pipeline_completo(
        canal=args.channel,
        n_videos=args.n_videos,
        comentarios=True,
        analizar_momentos=True,
        threshold=75.0
    )
    
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    df.to_excel(args.output_file, index=False)
    print(f"DataFrame guardado en {args.output_file}")

if __name__ == "__main__":
    main()