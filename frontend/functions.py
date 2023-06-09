import httpx


async def get(*args, **kwargs):
    async with httpx.AsyncClient() as client:
        result = await client.get(*args, **kwargs)
    return result


async def get_data_by_token(token: str):
    result = (await get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"Bearer {token}"})).json()
    return {"id": result.get("user_id", ""), "login": result.get("login", ""), "scopes": result.get("scopes", [])}
