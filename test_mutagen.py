import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

const PlaylistSlice = createSlice({
    name: "playlist",
    initialState: {
        data: [],
        id: -1,
        playlistNo: -1,
        loading: false,
        error: null
    },
    reducers: {
        addPlaylist(state, action) {
            state.data = [...state.data, action.payload.playlist];
        },
        addMusicinPlaylist(state, action) {
            let bool = true;
            if (state.data[action.payload.id].songs.length === 0) {
                console.warn(action.payload.music.image)
                state.data[action.payload.id].image = action.payload.music.image
            }
            state.data[action.payload.id].songs.forEach(element => {
                if (element.id === action.payload.music.id) {
                    bool = false
                }
            });
            if (bool) {
                state.data[action.payload.id].songs = [...state.data[action.payload.id].songs, action.payload.music]
            }
            state.data[action.payload.id].Time += action.payload.music.duration
            console.log("Time", state.data[action.payload.id].Time)
        },
        setPlaylistplaying(state, action) {
            if (typeof action.payload.action === "boolean") {
                state.data[action.payload.id].isPlaying = action.payload.action;
            } else if (action.payload.action === "toggle") {
                state.data[action.payload.id].isPlaying = !state.data[action.payload.id].isPlaying
            }
        },
        changePlaylist(state, action) {
            state.playlistNo = action.payload;
        },
        clearError(state) {
            state.error = null;
        }
    },
    extraReducers: (builder) => {
        builder
            .addCase(migrate.fulfilled, (state, action) => {
                const response = action.payload;
                if (response && Array.isArray(response) && response.length > 0) {
                    const id = state.id + 1;
                    const playlist = {
                        id: id,
                        image: response[0].cover_url || null,
                        name: response[0].album_name,
                        desc: "imported from spotify",
                        songs: [],
                        Time: 0,
                        isPlaying: false
                    }
                    state.data = [...state.data, playlist];
                    const song = [];

                    response.forEach((item) => {
                        song.push({
                            id: item.song_id,
                            title: item.name || null,
                            uploader: item.artist || null,
                            image: item.cover_url || null,
                            url: item.url || null,
                            duration: item.duration || 0,
                        });
                        state.data[id].Time += item.duration;
                    });

                    state.data[id].songs = song;
                    state.id = id;
                }
                state.loading = false;
                state.error = null;
            })
            .addCase(migrate.pending, (state, action) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(migrate.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Migration failed';
                console.error("Migration failed:", action.error);
            })
            .addCase(AddNewPlaylist.fulfilled, (state, action) => {
                const response = action.payload;
                console.warn("New playlist added");
                state.loading = false;
                state.error = null;
            })
            .addCase(AddNewPlaylist.pending, (state, action) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(AddNewPlaylist.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to add playlist';
                console.error("Add playlist failed:", action.error);
            })
            .addCase(pullPlaylists.fulfilled, (state, action) => {
                const response = action.payload;
                // Add safety check for response data
                if (response && Array.isArray(response)) {
                    response.forEach((item) => {
                        if (item && item.value) {
                            const data = item.value;
                            state.data = [...state.data, data];
                        }
                    });
                    console.warn("Playlists loaded:", response.length);
                } else {
                    console.warn("No playlists data received or invalid format");
                }
                state.loading = false;
                state.error = null;
            })
            .addCase(pullPlaylists.pending, (state, action) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(pullPlaylists.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to load playlists';
                console.error("Pull playlists failed:", action.error);
            })
            .addCase(AddNewPlaylistwithmusic.fulfilled, (state, action) => {
                console.log("Playlists added");
                state.loading = false;
                state.error = null;
            })
            .addCase(AddNewPlaylistwithmusic.pending, (state, action) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(AddNewPlaylistwithmusic.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to add playlist with music';
                console.error("Add playlist with music failed:", action.error);
            })
    }
})

export const { addPlaylist, addMusicinPlaylist, setPlaylistplaying, changePlaylist, clearError } = PlaylistSlice.actions;
export default PlaylistSlice.reducer;

export const migrate = createAsyncThunk('/migratedata', async ({ Url: data }, { rejectWithValue }) => {
    try {
        console.warn(data)
        const response = await axios.post("http://192.168.1.44/api/migrate", { playlist: data })
        console.warn("reached back")
        return response.data
    }
    catch (e) {
        console.error("error migrating!!", e)
        return rejectWithValue(e.message || 'Migration failed')
    }
})

export const AddNewPlaylist = createAsyncThunk('/newplaylist', async ({ data: playlist, userid: userid }, { rejectWithValue }) => {
    try {
        console.warn("adding new playlist");
        const response = await axios.post("http://192.168.1.44/api/NewPlaylists", { playlist: playlist, user: userid })
        return response.data
    }
    catch (e) {
        console.error("Add playlist error:", e)
        return rejectWithValue(e.message || 'Failed to add playlist')
    }
})

export const AddNewPlaylistwithmusic = createAsyncThunk('/newplaylistwithmusic', async ({ data: value, song: song }, { rejectWithValue }) => {
    try {
        console.warn("adding new playlist");
        const response = await axios.post("http://192.168.1.44/api/NewPlaylistswithmusic", { playlist: value, song: song })
        return response.data
    }
    catch (e) {
        console.error("Add playlist with music error:", e)
        return rejectWithValue(e.message || 'Failed to add playlist with music')
    }
})

export const pullPlaylists = createAsyncThunk('/pullPlaylists', async ({ user: user }, { rejectWithValue }) => {
    try {
        console.warn("pulling playlist");
        console.warn("user reached pull: ", user)
        const response = await axios.post("http://192.168.1.44/api/Playlist", { data: user })
        
        // Check if response has data
        if (!response.data) {
            throw new Error('No data received from server');
        }
        
        return response.data
    }
    catch (e) {
        console.error("Pull playlists error:", e)
        return rejectWithValue(e.message || 'Failed to load playlists')
    }
})