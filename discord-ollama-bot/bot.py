import logging
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, OLLAMA_MODEL, AGENT_ID
from db import (
    init_db_pool, 
    close_db_pool, 
    get_agent_knowledge, 
    get_chat_history, 
    add_chat_message,
    get_pool,
    save_memory,
    load_memories
)
from ollama_client import OllamaClient


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("discord_bot")

class GritTinBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ollama = OllamaClient()

    async def setup_hook(self):
        # Initialize DB pool during setup
        await init_db_pool()
        logger.info("Database pool initialized in setup_hook.")

    async def close(self):
        # Close DB pool during shutdown
        await close_db_pool()
        await super().close()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = GritTinBot(command_prefix="!", intents=intents)

def split_message(text: str, limit: int = 1900) -> list[str]:
    """Splits a message into chunks within Discord's 2000 character limit."""
    if len(text) <= limit:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # Find a suitable splitting point like newline or space
        split_idx = text.rfind("\n", 0, limit)
        if split_idx == -1:
            split_idx = text.rfind(" ", 0, limit)
        if split_idx == -1:
            split_idx = limit
            
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
    return chunks

@bot.event
async def on_ready():
    logger.info(f"Bot connected as {bot.user.name} ({bot.user.id})")
    # Change status
    await bot.change_presence(activity=discord.Game(name=f"Role: {AGENT_ID}"))

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot itself or other bots
    if message.author.bot:
        return

    # Check if this is a DM or the bot is mentioned
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    
    # Process standard commands prefix first if applicable
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # If it's a DM or the bot is mentioned, treat it as a conversation
    if is_dm or is_mentioned:
        # Clean the content to remove the bot mention tag
        clean_content = message.content
        if is_mentioned and bot.user:
            clean_content = clean_content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not clean_content:
            await message.reply("สวัสดีครับ! มีอะไรให้ผมช่วยเหลือพิมพ์คุยมาได้เลยครับ")
            return

        session_id = str(message.channel.id)

        async with message.channel.typing():
            try:
                # 1. Fetch persona/knowledge for configured AGENT_ID
                agent = await get_agent_knowledge(AGENT_ID)
                
                # 1.5. Fetch long-term memories for this session
                memories = await load_memories(session_id)
                memory_text = ""
                if memories:
                    memory_text = "\n### Long-Term Memories (Persisted summaries from previous conversations):\n"
                    for m in memories:
                        memory_text += f"- [{m['context_category']}]: {m['key_summary']}\n"

                if agent:
                    system_instruction = (
                        f"You are {agent.get('agent_name', 'GritTin')}.\n"
                        f"Your skills and responsibilities: {agent.get('skill_set', '')}\n"
                        f"Operating Context: {agent.get('context_data', '')}\n"
                        f"Learned Logic / Rules: {agent.get('learned_logic', '')}\n"
                        f"{memory_text}\n"
                        f"Please follow these instructions strictly and answer in the user's language.\n"
                        f"Memory Rule: If the user confirms a decision, project scope, setting, or requirements that you should remember long-term, "
                        f"you MUST append this tag at the very end of your response: "
                        f"[SAVE_MEMORY: category=CategoryName; summary=Detailed summary here]. "
                        f"Categories: 'Requirement', 'WBS', 'User_Preference', 'Project_State'. Keep summaries clear and concise."
                    )
                else:
                    system_instruction = "You are GritTin, a helpful workspace assistant."

                # 2. Get past chat history
                history = await get_chat_history(session_id, limit=15)

                # 3. Call local Ollama / OpenRouter
                reply = await bot.ollama.get_chat_response(
                    system_instruction=system_instruction,
                    history=history,
                    user_message=clean_content
                )

                # 4. Check for and extract SAVE_MEMORY tags
                import re
                memory_pattern = r"\[SAVE_MEMORY:\s*category=([^;]+);\s*summary=([^\]]+)\]"
                matches = re.findall(memory_pattern, reply)
                for cat, summ in matches:
                    await save_memory(session_id, cat.strip(), summ.strip())
                
                # Strip memory tags from the reply
                clean_reply = re.sub(memory_pattern, "", reply).strip()
                if not clean_reply:
                    clean_reply = reply

                # 5. Save history to DB (User and Assistant)
                await add_chat_message(session_id, 'user', clean_content)
                await add_chat_message(session_id, 'assistant', clean_reply)

                # 6. Send chunks to Discord
                reply_chunks = split_message(clean_reply)
                for chunk in reply_chunks:
                    await message.channel.send(chunk)

            except Exception as e:
                logger.error(f"Error handling message conversation: {e}")
                await message.reply(f"เกิดข้อผิดพลาดในการประมวลผลคำตอบครับ: {str(e)}")


# Command: Status Check
@bot.command(name="status")
async def status_check(ctx):
    """Checks the bot status and connections."""
    status_msg = f"**{AGENT_ID} Status Check**\n"
    
    # Check Database connection
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1")
            if val == 1:
                status_msg += "✅ PostgreSQL: Connected\n"
    except Exception as e:
        status_msg += f"❌ PostgreSQL: Disconnected ({str(e)})\n"

    # Check AI Model connection
    if bot.ollama.use_openrouter:
        try:
            headers = {"Authorization": f"Bearer {bot.ollama.openrouter_api_key}"}
            async with httpx.AsyncClient() as client:
                res = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
                if res.status_code == 200:
                    status_msg += f"✅ OpenRouter: Connected (Model: `{bot.ollama.openrouter_model}`)\n"
                else:
                    status_msg += f"❌ OpenRouter: Connected but returned status {res.status_code}\n"
        except Exception as e:
            status_msg += f"❌ OpenRouter: Offline/Error ({str(e)})\n"
    else:
        try:
            tags_url = bot.ollama.ollama_url.replace("/api/chat", "/api/tags")
            async with httpx.AsyncClient() as client:
                res = await client.get(tags_url)
                if res.status_code == 200:
                    models = [m["name"] for m in res.json().get("models", [])]
                    status_msg += f"✅ Ollama: Connected (Model: `{bot.ollama.ollama_model}`, Available: {', '.join(models)})\n"
                else:
                    status_msg += f"❌ Ollama: Connected but returned status {res.status_code}\n"
        except Exception as e:
            status_msg += f"❌ Ollama: Offline ({str(e)})\n"

    await ctx.reply(status_msg)


# Command: Clear Chat History
@bot.command(name="clear")
async def clear_history(ctx):
    """Clears the chat history for the current session/channel."""
    session_id = str(ctx.channel.id)
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM chat_history WHERE session_id = $1", session_id)
        await ctx.reply("🧹 ล้างประวัติการคุยในห้องนี้เรียบร้อยแล้วครับ!")
    except Exception as e:
        await ctx.reply(f"ไม่สามารถล้างประวัติได้เนื่องจากเกิดข้อผิดพลาด: {str(e)}")

# Command: Update Agent Logic
@bot.command(name="learn")
async def learn_logic(ctx, *, new_logic: str):
    """Appends dynamic instructions/learned logic to configured AGENT_ID."""
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT learned_logic FROM agent_knowledge WHERE agent_id = $1", AGENT_ID)
            current_logic = row["learned_logic"] if row and row["learned_logic"] else ""
            updated_logic = (current_logic + "\n" + new_logic).strip()
            
            await conn.execute(
                "UPDATE agent_knowledge SET learned_logic = $1 WHERE agent_id = $2",
                updated_logic, AGENT_ID
            )
        await ctx.reply(f"💡 เรียนรู้กฎและตรรกะใหม่สำหรับ `{AGENT_ID}` เรียบร้อยแล้ว:\n```\n{new_logic}\n```")
    except Exception as e:
        await ctx.reply(f"ไม่สามารถบันทึกตรรกะได้: {str(e)}")

# Command: Dynamic Feedback Loop
@bot.command(name="feedback")
async def feedback_loop(ctx, feedback_type: str, *, feedback_text: str):
    """
    Logs feedback on bot behavior (good or bad) and updates learned_logic.
    Usage: !feedback good <things did well> or !feedback bad <things to avoid>
    """
    f_type = feedback_type.lower()
    if f_type not in ["good", "bad"]:
        await ctx.reply("รูปแบบไม่ถูกต้อง กรุณาใช้: `!feedback good <รายละเอียด>` หรือ `!feedback bad <รายละเอียด>`")
        return
        
    tag = "[FEEDBACK - PREFER]" if f_type == "good" else "[FEEDBACK - AVOID]"
    feedback_rule = f"{tag}: {feedback_text}"
    
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT learned_logic FROM agent_knowledge WHERE agent_id = $1", AGENT_ID)
            current_logic = row["learned_logic"] if row and row["learned_logic"] else ""
            updated_logic = (current_logic + "\n" + feedback_rule).strip()
            
            await conn.execute(
                "UPDATE agent_knowledge SET learned_logic = $1 WHERE agent_id = $2",
                updated_logic, AGENT_ID
            )
        await ctx.reply(f"📌 บันทึกคำแนะนำของ `{AGENT_ID}` เรียบร้อยแล้ว:\n`{feedback_rule}`")
    except Exception as e:
        await ctx.reply(f"ไม่สามารถบันทึกฟีดแบคได้: {str(e)}")



if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "PLACEHOLDER_TOKEN":
         logger.warning("Using default or placeholder Discord Token. Ensure your bot token is updated in .env if connection fails.")
    
    bot.run(DISCORD_TOKEN)
