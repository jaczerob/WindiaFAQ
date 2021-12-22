import asyncio

import hikari
import lightbulb
from lightbulb import commands


plugin = lightbulb.Plugin('FAQ', 'FAQ commands and handlers')
plugin.add_checks(lightbulb.checks.has_role_permissions(hikari.Permissions.MANAGE_MESSAGES))


def check(bot_channel: hikari.GuildTextChannel, message_channel: hikari.GuildTextChannel, member: hikari.Member):
   return True if member.get_top_role().permissions.MANAGE_MESSAGES or bot_channel.id == message_channel.id or member.user == plugin.bot.application.owner else False


@plugin.listener(hikari.MessageCreateEvent)
async def faq_handler(message: hikari.MessageCreateEvent):
    if message.is_bot or not plugin.bot.d.db.is_connected() or not message.channel_id:
        return

    bot_channel_id = plugin.bot.d.config['bot'][ 'channel']
    guild_id = plugin.bot.d.config['bot']['guild']

    bot_channel: hikari.GuildTextChannel = await plugin.bot.rest.fetch_channel(bot_channel_id)
    message_channel: hikari.GuildTextChannel = await plugin.bot.rest.fetch_channel(message.channel_id)
    guild: hikari.Guild = await message_channel.fetch_guild()
    if not guild.id == guild_id:
        return
        
    member = guild.get_member(message.author_id)
    if not check(bot_channel, message_channel, member):
        event = await message_channel.send(f'Please use the bot channel, {member.mention}.')
        await asyncio.sleep(5)
        return await event.message.delete()

    content = message.content
    prefix = plugin.bot.d.config['bot']['prefix']
    command = content[len(prefix):].split(' ')[0]

    if not content.startswith(prefix) or plugin.bot.get_prefix_command(command):
        return
        
    if not (resp := await plugin.bot.d.db.request(command)):
        return

    if isinstance(resp, str):
        return await message_channel.send(resp)
    elif isinstance(resp, list):
        return await message_channel.send(f'Did you mean... {", ".join(resp)}')


@plugin.command()
@lightbulb.option('description', 'The description of the command', modifier=commands.OptionModifier.CONSUME_REST)
@lightbulb.option('command', 'The command to add')
@lightbulb.command('add', 'Adds a FAQ command')
@lightbulb.implements(commands.PrefixCommand)
async def add(ctx: lightbulb.context.Context) -> None:
    """usage: `command` `description`"""
    command, description = ctx.options.command, ctx.options.description
    await plugin.bot.d.db.create(command, description)
    return await ctx.respond(f'{command} added.')


@plugin.command()
@lightbulb.option('description', 'The description of the command', modifier=commands.OptionModifier.CONSUME_REST)
@lightbulb.option('command', 'The command to update')
@lightbulb.command('update', 'Updates a FAQ command')
@lightbulb.implements(commands.PrefixCommand)
async def update(ctx: lightbulb.context.Context) -> None:
    """usage: `command` `description`"""
    command, description = ctx.options.command, ctx.options.description
    await plugin.bot.d.db.update(command, description)
    return await ctx.respond(f'{command} updated.')


@plugin.command()
@lightbulb.option('command', 'The command to add')
@lightbulb.command('delete', 'Deletes a FAQ command')
@lightbulb.implements(commands.PrefixCommand)
async def add(ctx: lightbulb.context.Context) -> None:
    """usage: `command`"""
    command = ctx.options.command
    await plugin.bot.d.db.delete(command)
    return await ctx.respond(f'{command} deleted.')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)
    