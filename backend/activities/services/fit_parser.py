def parse_fit_file(file_path):
    """
    MVP skeleton – zatím jen fake data
    později sem přijde fitparse knihovna
    """

    return {
        "duration_s": 3600,
        "distance_m": 10000,
        "avg_hr": 155,
        "avg_pace_s_per_km": 360,
        "intervals": [
            {"index": 1, "duration_s": 90, "distance_m": 400},
            {"index": 2, "duration_s": 92, "distance_m": 400},
            {"index": 3, "duration_s": 94, "distance_m": 400},
        ],
    }
