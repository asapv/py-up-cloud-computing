from bs4 import BeautifulSoup

class MomentosAnalyzer:
    def __init__(self, svg_content, video_duration):
        """
        Initializes the MomentosAnalyzer for SVG heatmap analysis.

        :param svg_content: SVG heatmap content.
        :type svg_content: str
        :param video_duration: Duration of the video in seconds.
        :type video_duration: str or float
        """
        self.svg_content = svg_content
        self.duration = float(video_duration) if video_duration != "Not Available" else 0
    
    def extract_and_scale_points(self):
        """
        Extracts and scales points from the SVG heatmap.

        :return: List of scaled (time, popularity) points.
        :rtype: list
        """
        if self.svg_content in ["Not available", "Failed after max attempts", "Not Available"] or not self.svg_content:
            return []
        
        raw = []
        try:
            soup = BeautifulSoup(self.svg_content, "lxml")
            path = soup.find("path")
            if not path or not path.has_attr("d"):
                return []
                
            d = path["d"]
            coords = d.replace("M ", "").replace("C ", "").split(" ")
            for pair in coords[1:]:
                try:
                    x_raw, y_raw = map(float, pair.split(","))
                    y = max(0.0, 90.0 - y_raw)
                    raw.append((x_raw, y))
                except ValueError:
                    continue
        except Exception as e:
            print(f"Error al procesar SVG: {e}")
            return []

        raw.sort(key=lambda p: p[0])

        if not raw or self.duration == 0:
            return []
            
        max_x = max(p[0] for p in raw)
        scaled = [(x_raw / max_x * self.duration, y) for x_raw, y in raw]
        return scaled
    
    def find_peaks(self, points, threshold=80.0):
        """
        Finds peaks and plateaus in popularity points.

        :param points: List of (time, popularity) points.
        :type points: list
        :param threshold: Popularity threshold for peaks.
        :type threshold: float
        :return: List of peak points.
        :rtype: list
        """
        if not points:
            return []
            
        peaks = []
        in_high_region = False
        high_region_start = None
        current_region = []
        
        for i, (x, y) in enumerate(points):
            if y >= threshold:
                if not in_high_region:
                    in_high_region = True
                    high_region_start = i
                    current_region = [(x, y)]
                else:
                    current_region.append((x, y))
            else:
                if in_high_region:
                    in_high_region = False
                    
                    if len(current_region) >= 3:
                        mid_idx = len(current_region) // 2
                        peaks.append(current_region[mid_idx])
                    elif current_region:
                        max_point = max(current_region, key=lambda p: p[1])
                        peaks.append(max_point)
                    
                    current_region = []
        
        if in_high_region and current_region:
            if len(current_region) >= 3:
                mid_idx = len(current_region) // 2
                peaks.append(current_region[mid_idx])
            else:
                max_point = max(current_region, key=lambda p: p[1])
                peaks.append(max_point)
        
        if not peaks:
            for i in range(1, len(points)-1):
                prev_y = points[i-1][1]
                curr_y = points[i][1]
                next_y = points[i+1][1]
                
                if curr_y >= threshold and curr_y >= prev_y and curr_y >= next_y:
                    peaks.append(points[i])
        
        return peaks
    
    def format_timestamp(self, sec):
        """
        Formats seconds into HH:MM:SS format.

        :param sec: Time in seconds.
        :type sec: float
        :return: Formatted timestamp.
        :rtype: str
        """
        s = int(sec)
        h = s // 3600
        m = (s % 3600) // 60
        s = s % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def find_popular_segments(self, points, threshold=80.0, min_gap=30):
        """
        Finds continuous segments of high popularity.

        :param points: List of (time, popularity) points.
        :type points: list
        :param threshold: Popularity threshold for segments.
        :type threshold: float
        :param min_gap: Minimum gap (seconds) to separate segments.
        :type min_gap: int
        :return: List of popular segment information.
        :rtype: list
        """
        if not points:
            return []
            
        high_points = [(x, y) for x, y in points if y >= threshold]
        
        if not high_points:
            return []
            
        high_points.sort(key=lambda p: p[0])
        
        segments = []
        current_segment = [high_points[0]]
        
        for i in range(1, len(high_points)):
            curr_point = high_points[i]
            last_point = current_segment[-1]
            
            if curr_point[0] - last_point[0] <= min_gap:
                current_segment.append(curr_point)
            else:
                segments.append(current_segment)
                current_segment = [curr_point]
        
        if current_segment:
            segments.append(current_segment)
        
        result = []
        for i, segment in enumerate(segments, 1):
            start_time = segment[0][0]
            end_time = segment[-1][0]
            duration = end_time - start_time
            max_popularity = max(y for _, y in segment)
            
            result.append({
                "segment": i,
                "start_seconds": start_time,
                "end_seconds": end_time,
                "duration": duration,
                "start_formatted": self.format_timestamp(start_time),
                "end_formatted": self.format_timestamp(end_time),
                "max_popularity": max_popularity
            })
            
        return result
    
    def get_popular_moments(self, threshold=80.0):
        """
        Analyzes the SVG and retrieves popular moments and segments.

        :param threshold: Popularity threshold for moments and segments.
        :type threshold: float
        :return: Tuple of (popular moments, popular segments).
        :rtype: tuple
        """
        points = self.extract_and_scale_points()
        
        if not points:
            return [], []
        
        peaks = self.find_peaks(points, threshold)
        
        segments = self.find_popular_segments(points, threshold)
        
        momentos = [
            {
                "time_seconds": x, 
                "time_formatted": self.format_timestamp(x),
                "popularity": y
            }
            for x, y in peaks
        ]
        
        return momentos, segments