from functools import cache

from aiogram import Router

from . import actions, audio, start, text


@cache
def build_router() -> Router:
    root = Router(name="root")
    # Tartib muhim: buyruqlar → audio → tugmalar → matn (oxirida, hammasini ushlaydi)
    root.include_routers(start.router, audio.router, actions.router, text.router)
    return root
