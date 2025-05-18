import redis.asyncio as redis
import json
async def CreateEmptyPlaylist(redis_client, playlist):
    try:
        playlist_name = playlist.get("name")
        playlist_image = playlist.get("image")
        playlist_desc= playlist.get("desc")
        playlist_songs= playlist.get("songs")
        playlist_id= playlist.get("id")
        playlist_time= playlist.get("time")
        playlist_isPlaying= playlist.get("isPlaying")
        key = f"playlist:{playlist_name}"
        existing = await redis_client.get(key)
        if existing:
            # Playlist exists, load it
            playlist = json.loads(existing)
        else:
            # Playlist doesn't exist, create new list and add playlist name to index
            playlist = {"id": playlist_id,
                "image": playlist_image,
                "name": playlist_name,
                "desc": playlist_desc,
                "songs": playlist_songs,
                "Time": playlist_time,
                "isPlaying": playlist_isPlaying}
            await redis_client.sadd("playlists:set", playlist_name)
        
        # Save updated playlist back to Redis
        await redis_client.set(key, json.dumps(playlist))
        
    except Exception as e:
        print(f"Error storing data: {e}")
async def storeData(redis_client,playlist_name,new_song):
    try:
        key = f"playlist:{playlist_name}"
        existing = await redis_client.get(key)
        if existing:
            playlist = json.loads(existing)
            song_id = str(len(playlist) + 1)
            playlist[song_id] = new_song
        else:
            playlist=[]
            await redis_client.sadd("playlists:set", playlist_name)
        
        await redis_client.set(key, json.dumps(playlist))
        
    except Exception as e:
        print(e)
    
# async def CreateEmptyPlaylist(redis_client,playlist):
#     try:
#         playlist_name = playlist.get("name")
#         key = f"playlist:{playlist_name}"
#         existing = await redis_client.get(key)
#         if existing:
#             return "playlist exists"
#         else:
#             playlist=[]
#             await redis_client.sadd("playlists:set", playlist_name)
        
#         await redis_client.set(key, json.dumps(playlist))
        
#     except Exception as e:
#         print(e)
async def get_all_playlists_as_array(redis_client):
    playlist_names = await redis_client.smembers("playlists:set")
    playlists = []
    
    for name_bytes in playlist_names:
        playlist_name = name_bytes.decode() if isinstance(name_bytes, bytes) else name_bytes
        key = f"playlist:{playlist_name}"
        data = await redis_client.get(key)
        
        if data:
            playlist_data = json.loads(data)
        else:
            playlist_data = []
        
        playlists.append({"name":playlist_name,"value": playlist_data})
    
    return playlists




