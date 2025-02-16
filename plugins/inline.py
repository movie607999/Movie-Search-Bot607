import logging
import requests
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    
    string = query.query.strip()
    results = []
    
    if not string:
        await query.answer(results=[],
                           cache_time=0,
                           switch_pm_text='Type a movie name...',
                           switch_pm_parameter="start")
        return

    url = "https://imdb8.p.rapidapi.com/title/find"
    headers = {
        "X-RapidAPI-Key": "ca6dbf9407msh61bd2e5c7e991dap1de329jsn47ad675ee76d",
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com"
    }
    params = {"q": string}
    
    response = requests.get(url, headers=headers, params=params)
    
    movie_poster = "https://via.placeholder.com/300x450?text=No+Image"  # ডিফল্ট ইমেজ
    movie_title = string
    movie_year = "Unknown Year"
    movie_rating = "No Rating"

    if response.status_code == 200:
        data = response.json()
        # print("IMDb API Response:", data)  # ডিবাগ করার জন্য (প্রয়োজনে চালু করো)
        
        try:
            movie_info = data.get('results', [])[0]  # Taking first search result
            if movie_info:
                movie_title = movie_info.get('title', 'Unknown Title')
                movie_poster = movie_info.get('image', {}).get('url', movie_poster)  # Default if not found
                movie_year = movie_info.get('year', 'Unknown Year')
                movie_rating = movie_info.get('ratings', {}).get('rating', 'No Rating')

        except (IndexError, KeyError):
            pass

    # Adding movie image result
    results.append(
        InlineQueryResultPhoto(
            photo_url=movie_poster,
            thumb_url=movie_poster,  # Thumbnail সেট করা
            title=f"{movie_title} ({movie_year})",
            description=f"IMDb Rating: {movie_rating}",
            caption=f"🎬 <b>{movie_title}</b> ({movie_year})\n⭐ <b>IMDb Rating:</b> {movie_rating}",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('🔄 Search again', switch_inline_query_current_chat=string)]
            ])
        )
    )

    await query.answer(results=results, cache_time=cache_time)
