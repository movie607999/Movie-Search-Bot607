# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging
import requests
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InlineQueryResultCachedDocument, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

async def inline_users(query: InlineQuery):
    if AUTH_USERS:
        if query.from_user and query.from_user.id in AUTH_USERS:
            return True
        else:
            return False
    if query.from_user and query.from_user.id not in temp.BANNED_USERS:
        return True
    return False

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    chat_id = await active_connection(str(query.from_user.id))
    
    if not await inline_users(query):
        await query.answer(results=[],
                           cache_time=0,
                           switch_pm_text='okDa',
                           switch_pm_parameter="hehe")
        return

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(results=[],
                           cache_time=0,
                           switch_pm_text='You have to subscribe my channel to use the bot',
                           switch_pm_parameter="subscribe")
        return

    results = []
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    # Fetch movie details from IMDb API (RapidAPI)
    url = "https://imdb8.p.rapidapi.com/title/find"
    headers = {
        "X-RapidAPI-Key": "ca6dbf9407msh61bd2e5c7e991dap1de329jsn47ad675ee76d",  # তোমার API Key
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com"
    }
    params = {"q": string}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        try:
            movie_info = data['results'][0]  # Taking first search result
            movie_title = movie_info.get('title', 'Unknown Title')
            movie_poster = movie_info.get('image', {}).get('url')  
            movie_year = movie_info.get('year', 'Unknown Year')
            movie_rating = movie_info.get('ratings', {}).get('rating', 'No Rating')

            # Default Image if IMDb API does not return an image
            if not movie_poster:
                movie_poster = "https://via.placeholder.com/300x450?text=No+Image"

        except (IndexError, KeyError):
            movie_title = string
            movie_poster = "https://via.placeholder.com/300x450?text=No+Image"
            movie_year = "Unknown Year"
            movie_rating = "No Rating"
    else:
        movie_title = string
        movie_poster = "https://via.placeholder.com/300x450?text=No+Image"
        movie_year = "Unknown Year"
        movie_rating = "No Rating"

    # Adding movie image result
    results.append(
        InlineQueryResultPhoto(
            photo_url=movie_poster,
            title=f"{movie_title} ({movie_year})",
            description=f"IMDb Rating: {movie_rating}",
            caption=f"🎬 <b>{movie_title}</b> ({movie_year})\n⭐ <b>IMDb Rating:</b> {movie_rating}",
            parse_mode="html",
            reply_markup=reply_markup
        )
    )

    # Fetch movie quality and other files
    files, next_offset, total = await get_search_results(
                                                  chat_id,
                                                  string,
                                                  file_type=file_type,
                                                  max_results=10,
                                                  offset=offset)

    for file in files:
        title=file.file_name
        size=get_size(file.file_size)
        f_caption=file.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"{file.file_name}"
        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {get_size(file.file_size)}\nType: {file.file_type}',
                reply_markup=reply_markup))

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"
        try:
            await query.answer(results=results,
                           is_personal = True,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="start",
                           next_offset=str(next_offset))
        except QueryIdInvalid:
            pass
        except Exception as e:
            logging.exception(str(e))
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'

        await query.answer(results=[],
                           is_personal = True,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="okay")


def get_reply_markup(query):
    buttons = [
        [
            InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)
        ]
    ]
    return InlineKeyboardMarkup(buttons)
