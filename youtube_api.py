import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Replace with your own API key
YT_API_KEY = "AIzaSyBGPSxEyEk6GDv2M_aaPihseB24Lj22Kug"

# Build the YouTube service
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

def youtube_search(query):
    # Call the search.list method to retrieve results matching the specified query term
    request = youtube.search().list(
        part="snippet",
        maxResults=10,  # Number of results to return
        q=query,        # The search query term
        type="video",   # We only want videos
        videoCategoryId="10"  # Music category
    )

    response = request.execute()

    # Extract the search results
    for item in response['items']:
        print(f"Title: {item['snippet']['title']}")
        print(f"Video ID: {item['id']['videoId']}")
        print(f"Channel: {item['snippet']['channelTitle']}")
        print(f"Published at: {item['snippet']['publishedAt']}")
        print('-' * 40)

# Replace with your search query
query = "Phantom of the Opera - Ghost"
youtube_search(query)