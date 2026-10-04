import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("PROMOTION_LOG_CHANNEL_ID", "0"))

if not TOKEN:
raise RuntimeError("DISCORD_TOKEN is missing from your environment or .env file.")

intents = discord.Intents.default()

class CSRPLABot(commands.Bot):
async def setup_hook(self):
await self.tree.sync()
print("Synced slash commands.")

bot = CSRPLABot(command_prefix="!", intents=intents)

def check_role_permissions(interaction: discord.Interaction, role: discord.Role):
guild = interaction.guild

```
if guild is None:
    return False, "This command can only be used in a server."

if role.is_default() or role.managed:
    return False, "This role cannot be manually assigned or removed."

bot_member = guild.me

if bot_member is None or role >= bot_member.top_role:
    return False, "My highest role must be above the selected role."

moderator = interaction.user

if not isinstance(moderator, discord.Member):
    return False, "Could not verify your server permissions."

if not moderator.guild_permissions.administrator:
    if role >= moderator.top_role:
        return False, "You can only manage roles below your highest role."

return True, None
```

async def send_log(
guild: discord.Guild,
action: str,
member: discord.Member,
role: discord.Role,
moderator: discord.Member,
reason: str
):
if not LOG_CHANNEL_ID:
return

```
channel = guild.get_channel(LOG_CHANNEL_ID)

if not isinstance(channel, discord.TextChannel):
    print("Promotion log channel was not found. Check PROMOTION_LOG_CHANNEL_ID.")
    return

is_promotion = action == "PROMOTION"

embed = discord.Embed(
    title="Staff Promotion" if is_promotion else "Staff Demotion",
    description=(
        f"• **User:** {member.mention}\n"
        f"• **Updated Rank:** {role.mention if is_promotion else role.name}\n"
        f"• **Reason:** {reason or 'No reason provided'}"
    ),
    color=discord.Color.green() if is_promotion else discord.Color.red(),
    timestamp=discord.utils.utcnow()
)

embed.set_author(
    name=f"Signed, {moderator.display_name} | CSRPLA Staff",
    icon_url=moderator.display_avatar.url
)

embed.set_thumbnail(url=member.display_avatar.url)
embed.set_footer(text="CSRPLA | Staff Management")

try:
    await channel.send(
        embed=embed,
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=[role] if is_promotion else []
        )
    )
except discord.Forbidden:
    print("The bot cannot send messages in the promotion log channel.")
except discord.HTTPException as error:
    print(f"Could not send promotion log: {error}")
```

@bot.tree.command(
name="promote",
description="Promote a member by giving them a role."
)
@app_commands.describe(
member="The member to promote",
role="The new role to give",
reason="Reason for the promotion"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def promote(
interaction: discord.Interaction,
member: discord.Member,
role: discord.Role,
reason: str = "No reason provided"
):
allowed, error = check_role_permissions(interaction, role)

```
if not allowed:
    await interaction.response.send_message(error, ephemeral=True)
    return

if role in member.roles:
    await interaction.response.send_message(
        f"{member.mention} already has the {role.mention} role.",
        ephemeral=True
    )
    return

try:
    await member.add_roles(
        role,
        reason=f"Promoted by {interaction.user}: {reason}"
    )
except discord.Forbidden:
    await interaction.response.send_message(
        "I cannot assign that role. Check my Manage Roles permission and role hierarchy.",
        ephemeral=True
    )
    return
except discord.HTTPException:
    await interaction.response.send_message(
        "Discord could not complete the promotion. Please try again.",
        ephemeral=True
    )
    return

await send_log(
    interaction.guild,
    "PROMOTION",
    member,
    role,
    interaction.user,
    reason
)

await interaction.response.send_message(
    f"🎉 Successfully promoted {member.mention} to **{role.name}**!",
    ephemeral=True
)
```

@bot.tree.command(
name="demote",
description="Demote a member by removing a role."
)
@app_commands.describe(
member="The member to demote",
role="The role to remove",
reason="Reason for the demotion"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def demote(
interaction: discord.Interaction,
member: discord.Member,
role: discord.Role,
reason: str = "No reason provided"
):
allowed, error = check_role_permissions(interaction, role)

```
if not allowed:
    await interaction.response.send_message(error, ephemeral=True)
    return

if role not in member.roles:
    await interaction.response.send_message(
        f"{member.mention} does not have the {role.name} role.",
        ephemeral=True
    )
    return

try:
    await member.remove_roles(
        role,
        reason=f"Demoted by {interaction.user}: {reason}"
    )
except discord.Forbidden:
    await interaction.response.send_message(
        "I cannot remove that role. Check my Manage Roles permission and role hierarchy.",
        ephemeral=True
    )
    return
except discord.HTTPException:
    await interaction.response.send_message(
        "Discord could not complete the demotion. Please try again.",
        ephemeral=True
    )
    return

await send_log(
    interaction.guild,
    "DEMOTION",
    member,
    role,
    interaction.user,
    reason
)

await interaction.response.send_message(
    f"📉 Successfully removed **{role.name}** from {member.mention}.",
    ephemeral=True
)
```

@promote.error
@demote.error
async def role_command_error(
interaction: discord.Interaction,
error: app_commands.AppCommandError
):
if isinstance(error, app_commands.MissingPermissions):
message = "❌ You need the Manage Roles permission to use this command."
else:
print(f"Command error: {error}")
message = "❌ An unexpected error occurred."

```
if interaction.response.is_done():
    await interaction.followup.send(message, ephemeral=True)
else:
    await interaction.response.send_message(message, ephemeral=True)
```

@bot.event
async def on_ready():
print(f"CSRPLA Promotions Bot online as {bot.user}")

bot.run(TOKEN)
