from googleapiclient.discovery import build

# Replace with your own API key
YT_API_KEY = "AIzaSyBGPSxEyEk6GDv2M_aaPihseB24Lj22Kug"

# Build the YouTube service
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

def youtube_search(query):
    # Call the search.list method to retrieve results matching the specified query term
    request = youtube.search().list(
        part="snippet",
        maxResults=1,  # We only need the first result
        q=query,        # The search query term
        type="video",   # We only want videos
        videoCategoryId="10"  # Music category
    )

    response = request.execute()

    # Extract the first search result
    if response['items']:
        first_item = response['items'][0]
        video_id = first_item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"Title: {first_item['snippet']['title']}")
        print(f"Video ID: {video_id}")
        print(f"Channel: {first_item['snippet']['channelTitle']}")
        print(f"Published at: {first_item['snippet']['publishedAt']}")
        print(f"Video URL: {video_url}")
        print('-' * 40)
        return video_url
    else:
        print("No results found.")
        return None

# Replace with your search query
query = "Phantom of the Opera - Ghost"
youtube_search(query)
