import redis.asyncio as redis
import json
async def CreateEmptyPlaylist(redis_client, playlist,user):
    try:
        playlist_name = playlist.get("name")
        playlist_image = playlist.get("image")
        playlist_desc= playlist.get("desc")
        playlist_songs= playlist.get("songs")
        playlist_id= playlist.get("id")
        playlist_time= playlist.get("time")
        playlist_isPlaying= playlist.get("isPlaying")
        key = f"user:{user}:playlist:{playlist_name}"
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
            await redis_client.sadd(f"user:{user}:playlists:set", playlist_name)
        
        # Save updated playlist back to Redis
        await redis_client.set(key, json.dumps(playlist))
        
    except Exception as e:
        print(f"Error storing data: {e}")

async def EditPlaylist(redis_client, playlist, user):
    try:
        playlist_name = playlist.get("name")
        playlist_image = playlist.get("image")
        playlist_desc  = playlist.get("desc")
        playlist_songs = playlist.get("songs")
        playlist_id    = playlist.get("id")
        playlist_time = playlist.get("Time")  
        playlist_isPlaying = playlist.get("isPlaying")

        key = f"user:{user}:playlist:{playlist_name}"
        existing = await redis_client.get(key)

        if not existing:
            # No playlist found with this name
            return "not_found"

        # Overwrite with new details
        updated_playlist = {
            "id": playlist_id,
            "image": playlist_image,
            "name": playlist_name,
            "desc": playlist_desc,
            "songs": playlist_songs,
            "Time": playlist_time,
            "isPlaying": playlist_isPlaying
        }

        await redis_client.set(key, json.dumps(updated_playlist))
        return "updated"

    except Exception as e:
        print(f"Error editing data: {e}")
        return {"type": "error", "message": str(e)}

async def storeData(redis_client,playlist_name,new_song,user):
    try:
        key = f"user:{user}:playlist:{playlist_name}"
        existing = await redis_client.get(key)
        if existing:
            playlist = json.loads(existing)
            print("playlist value: ",playlist)
            playlist["songs"].append(new_song)
        else:
            playlist = {
                "Time": None,
                "desc": "",
                "id": None,
                "image": None,
                "isPlaying": False,
                "name": playlist_name,
                "songs": [new_song]
            }
            await redis_client.sadd("playlists:set", playlist_name)
        
        await redis_client.set(key, json.dumps(playlist))
        return {"type":"success"}
        
    except Exception as e:
        print(e)
        return {"type": "error", "message": str(e)}
    
async def persistMusics(redis_client,searchedMusics,user):
    try:
        key = f"user:{user}:searched"
        print(searchedMusics)
        await redis_client.set(key, json.dumps(searchedMusics))
    except Exception as e:
        print(e)
import json

async def getpersistMusics(redis_client, user):
    try:
        key = f"user:{user}:searched"

        existing = await redis_client.get(key)
        if existing is not None:
            searched = existing.decode("utf-8")  # decode bytes to str
            print(searched)
            return searched
        else:
            return "[]"  # or return an empty list as JSON string
    except Exception as e:
        print("Error:", e)
        return "[]"
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
async def get_all_playlists_as_array(redis_client,user):
    try:
        print(user)
        playlist_names = await redis_client.smembers(f"user:{user}:playlists:set")
        print(playlist_names)
        playlists = []
        
        for name_bytes in playlist_names:
            playlist_name = name_bytes.decode() if isinstance(name_bytes, bytes) else name_bytes
            key = f"user:{user}:playlist:{playlist_name}"
            data = await redis_client.get(key)
            
            if data:
                playlist_data = json.loads(data)
            else:
                playlist_data = []
            
            playlists.append({"name":playlist_name,"value": playlist_data})
        print(playlists)
    except Exception as e:
        print("error",e)
    return playlists




