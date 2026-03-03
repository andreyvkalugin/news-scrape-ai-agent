def normalize(url: str):
    if url.endswith(".html"):
        return url
    return f"{url}/"