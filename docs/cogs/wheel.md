# Wheel Cog Documentation

## Overview

`/wheel` helps a channel decide. The pick is made at random up front, then the message is edited a few times (about 0.8 seconds apart) so the pointer looks like it spins before it stops on the result. One wheel spins per channel at a time.

## `/wheel spin options`

`options` are separated by commas (`,` `，` `、` `;` `|`): `火鍋, 拉麵, 咖哩`. Duplicates are dropped; 2–20 options of up to 80 characters each. Nothing in the options can ping anyone.

## `/wheel food [keyword]`

The options are nearby restaurants from the same search as `/search type:eat`: the keyword you give, or one the recommender suggests from what the server liked before. Up to six of the best-ranked restaurants go on the wheel, and it stops on that restaurant's card with the usual buttons (map, menu, reviews, like/dislike, back to browsing). A restaurant search calls a paid API, so `/wheel food` counts as one use of your chat quota (the `chat` rate limit).

The AI's `spin_wheel` tool calls `spin_in_channel`, which posts the spin as a new message in the channel (one spin per channel at a time, like the command).
