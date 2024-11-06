import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="#", intents=intents)

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name="Still on Dev"))
    await client.tree.sync()

    print("#############################")
    print("#                           #")
    print("#  ticket alma BOT By: Mirki#")
    print("#                           #")
    print("#############################")

ticket_counter = 1
general_channels = ["🎫support-ticket🎫"]
ticket_creators = {}

@client.tree.command(name="create_ticket", description="Csatornák létrehozása a szerveren.")
async def create_logs(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        guild = interaction.guild
        for channel_name in general_channels:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not channel:
                await guild.create_text_channel(channel_name)
        await interaction.response.send_message("Csatornák sikeresen létrehozva.", ephemeral=True)
    else:
        await interaction.response.send_message("Nincs jogosultságod ehhez a parancshoz!", ephemeral=True)

@client.tree.command(name="create_ticket_message", description="Ticket-nyitó üzenet létrehozása.")
async def create_ticket_message(interaction: discord.Interaction):
    support_channel = discord.utils.get(interaction.guild.text_channels, name="🎫support-ticket🎫")
    if not support_channel:
        await interaction.response.send_message("A support-ticket csatorna nem található.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Support Ticket",
        description="Segítségre van szükséged? Reagálj a boríték 📩 emojival, és létrehozunk neked egy ticketet.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_footer(text="Developer = @Mirki_240 © Copyright 2024", icon_url="https://i.imgur.com/GZz7V0Y.png")

    ticket_message = await support_channel.send(embed=embed)
    await ticket_message.add_reaction("📩")
    await interaction.response.send_message("Ticket üzenet létrehozva a support csatornában.", ephemeral=True)

@client.event
async def on_raw_reaction_add(payload):

    if payload.user_id == client.user.id:
        return


    global ticket_counter
    guild = client.get_guild(payload.guild_id)
    if guild is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return

    # Ticket nyitása
    if payload.emoji.name == "📩":
        # Remove the user's reaction
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            return

        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction("📩", member)

        ticket_channel_name = f"ticket-{ticket_counter:04}"
        ticket_counter += 1

        support_role = discord.utils.get(guild.roles, name="Szerver Support ❤")
        if not support_role:
            support_role = await guild.create_role(name="Szerver Support ❤")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(ticket_channel_name, overwrites=overwrites)

        # Store the ticket creator for permission removal later
        ticket_creators[ticket_channel.id] = member.id

        embed = discord.Embed(
            title="Új Ticket",
            description=f"{member.mention}, miben tudunk segíteni?\n @ping(DEV) csapatunk segít neked.", # {support_role.mention}
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Developer = @Mirki_240 © Copyright 2024", icon_url="https://i.imgur.com/GZz7V0Y.png")

        ticket_message = await ticket_channel.send(embed=embed)
        await ticket_message.add_reaction("🔒")

    # Ticket lezárása
    elif payload.emoji.name == "🔒":
        # Fetch the channel and message where the reaction was added
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            return


        # Check that the reacting user is not a bot
        if not member.bot:
            # Fetch the support role
            support_role = discord.utils.get(guild.roles, name="Szerver Support ❤")

            # Ensure the user has the support role before proceeding with ticket closure
            if support_role in member.roles:
                # Revoke the ticket creator's read permission on the ticket channel
                try:
                    ticket_creator_id = ticket_creators.get(member.id)
                    if ticket_creator_id:
                        ticket_creator = guild.get_member(ticket_creator_id)
                        if ticket_creator:
                            await channel.set_permissions(ticket_creator, read_messages=False)
                except:
                    embed = discord.Embed(title="Hiba", description="JOGELVÉTELI HIBA")

                # Create and send a closing embed message
                embed = discord.Embed(
                    title="Ticket lezárva",
                    description=f"{member.mention}, a ticket lezárva.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Developer = @Mirki_240 © Copyright 2024", icon_url="https://i.imgur.com/GZz7V0Y.png")
                closed_message = await channel.send(embed=embed)
                await closed_message.add_reaction("✅")  # Add a checkmark reaction to the closed message

    # A ticket elfogadása (pipa reakció)
    elif payload.emoji.name == "✅":
        if member.bot:
            return

        # Fetch the channel based on payload data
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            return  # Return if the channel doesn't exist

        # Ask for the reason in the channel
        await channel.send(f"{member.mention}, kérlek, írd meg a ticket elfogadásának okát. "
                        f"Van 60 másodperced, hogy válaszolj! <t:{int((datetime.now().timestamp() + 60))}:R>")

        def check(m):
            return m.author == member and m.channel == channel

        try:
            # Wait for the user's response in the channel
            msg = await client.wait_for('message', check=check, timeout=60)  # 60 seconds timeout
            reason = msg.content  # User's reason for accepting the ticket

            # Send a confirmation message with details in the user's DM
            embed = discord.Embed(
                title="Ticket: [HeckerMC]",
                description=f"{member.mention}",
                colour=discord.Color.green()
            )
            embed.add_field(name="A ticket státusza:", value="Ticketed el lett fogadva :white_check_mark:", inline=False)
            embed.add_field(name="Által:", value=f"{member.mention}", inline=False)
            embed.add_field(name="Indok:", value=reason, inline=False)

            now = datetime.now()
            embed.timestamp = now
            embed.set_footer(text="Developer = @Mirki_240 © Copyright 2024", icon_url="https://i.imgur.com/GZz7V0Y.png")

            # Send the DM
            await member.send(embed=embed)

        except asyncio.TimeoutError:
            # Notify in the channel if the user didn't respond in time
            await channel.send(f"{member.mention}, a válaszidő lejárt! Kérlek, próbáld újra később.")
        except Exception as e:
                    error_embed = discord.Embed(
                        title="Hiba történt",
                        description=f"Hiba történt a parancs végrehajtása során:\n```{str(e)}```",
                        color=discord.Color.red()
                    )
                    now = datetime.now()
                    error_embed.timestamp = now
                    error_embed.set_footer(text=f"OG heckerMC Developer = @Mirki_240 © Copyright 2024",
                                        icon_url="https://i.imgur.com/GZz7V0Y.png")
                    await ctx.send(embed=error_embed)
                    print(f"Hiba: {str(e)}")

client.run("aaa")
