from aiohttp import web

async def handle_uptime(request):
    return web.Response(text="✅ Uptime OK")

app = web.Application()
app.router.add_get("/", handle_uptime)
app.router.add_get("/uptime", handle_uptime)

if __name__ == "__main__":
    web.run_app(app, port=8081)
