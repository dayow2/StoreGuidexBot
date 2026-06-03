import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Retrieve configurations from Render environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

# --- Bot Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Store Guide! Your shopping and retail companion.\n\n"
        "Available commands:\n"
        "/help - Find out how I can assist you\n"
        "/status - Check my connection status"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "As your Store Guide, I am here to help you navigate products, "
        "find item locations, or check local retail details. What are you looking for today?"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Store Guide is live, healthy, and running smoothly on Render!")

# --- Server Application ---
async def main():
    if not TOKEN:
        print("Error: No TELEGRAM_TOKEN found in environment variables.")
        return

    # Initialize the Telegram Application
    application = Application.builder().token(TOKEN).build()

    # Register our command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))

    await application.initialize()
    await application.start()

    # Base endpoint so Render knows the web service is alive
    async def home_handler(request):
        return web.Response(text="Store Guide Bot is online!")

    # Incoming webhook data processor
    async def webhook_handler(request):
        try:
            data = await request.json()
            update = Update.de_json(data, application.bot)
            await application.process_update(update)
        except Exception as e:
            print(f"Error processing webhook update: {e}")
        return web.Response(status=200)

    # Setup the web server routing
    app = web.Application()
    app.router.add_get("/", home_handler)
    app.router.add_post(f"/{TOKEN}", webhook_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Hook up Telegram API to Render's deployment URL
    if RENDER_URL:
        webhook_target_url = f"{RENDER_URL}/{TOKEN}"
        print(f"Setting Telegram Webhook to: {webhook_target_url}")
        await application.bot.set_webhook(url=webhook_target_url)
    else:
        print("Local Warning: RENDER_EXTERNAL_URL environment variable not found.")

    print(f"Store Guide server successfully started on port {PORT}")

    # Keep the server alive indefinitely
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        # Proper application shutdown cleanup
        await application.stop()
        await application.shutdown()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Server manually stopped.")
