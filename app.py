import discord
import json
from discord.ext import commands
from data import *

import sys

# import time
token = sys.argv[1]
intents=discord.Intents(messages=True, guilds=True, reactions = True, members=True,dm_messages=True,guild_reactions=True)
client = commands.Bot(command_prefix='.Check ',intents=intents)

appelList = {}


def got_the_role(role, author:list):
    if isinstance(role, list):
        for i in role:
            if i in [y.id for y in author]:
                return True
    elif isinstance(role, int):
        return role in [y.id for y in author]


def returnPresent(idmessage: str, guildID: int,rolelist :list):
    """
    Retourne la liste des élèves ayant notifié leur présence sur un message.
    """
    liste = appelList[idmessage]['listStudents']
    messages=returnLanguage(readGuild(guildID)["language"], "endcall")
    if liste == []:
        return returnLanguage(readGuild(guildID)["language"], "NoStudents")
    else:
        message = messages[0]
        eleve = []
        for member in liste:
            if not member.id in eleve:
                message += "• *{}* <@{}>\n".format(member.name, member.id)  # [user.display_name,user.id]
                eleve.append(member.id)
                if rolelist is not None :rolelist.remove(member)
        if rolelist !=[]:
            message+="\n"+messages[1]
            for member in rolelist:
                message += "• *{}* <@{}>\n".format(member.name,member.id)
        else:
            message+=messages[2]
        return message


def convert(role: str):
    try:
        return int(role.replace(" ", "").lstrip("<@&").rstrip(">"))
    except Exception as e:
        print(e)
        return None


@client.event
async def on_guild_join(guild):  # readGuild(message.guild.id)
    rolebot = discord.utils.get(guild.roles, name="CheckStudents").id
    createGuild(guild.id, rolebot)


@client.event
async def on_guild_remove(guild):
    removeGuild(guild.id)

@client.command()
async def send(message, channel):
    await channel.send(message)

@client.command()
async def add_reaction(emoji, message):
    await message.add_reaction(emoji)

@client.command()
async def remove_reaction(emoji, message, user):
    await message.remove_reaction(emoji, user)


@client.command()
async def clear_reaction(emoji, message):
    await message.clear_reaction(emoji)


@client.event
async def on_reaction_add(reaction, user):
    global appelList
    idMessage = str(reaction.message.id)
    idGuild = str(reaction.message.guild.id)
    entry = idGuild + "-" + idMessage

    if entry in appelList:  # si c'est un message d'appel lancé par un professeur
        reactionContent = str(reaction).strip(" ")

        if reactionContent == "✅":  # si l'utilisateur a coché présent
            if got_the_role(appelList[entry]['ClasseRoleID'],
                            user.roles):  # si user a le role de la classe correspondante
                appelList[entry]['listStudents'].append(user)  # on le rajoute à la liste d'appel
            elif not got_the_role(readGuild(idGuild)['botID'], user.roles):
                await remove_reaction("✅", reaction.message, user)
                await send("<@{}> : {}".format(user.id, returnLanguage(readGuild(idGuild)["language"], "cantNotify")),
                           reaction.message.channel)


        elif reactionContent == "🆗":  # si l'utilisateur a coché OK
            if got_the_role(readGuild(idGuild)["admin"], user.roles):  # est prof
                await send(
                    "<@{}> :{} <@&{}>".format(user.id, returnLanguage(readGuild(idGuild)["language"], "FinishCall"),
                                              appelList[entry]['ClasseRoleID']), reaction.message.channel)
                await clear_reaction("✅", reaction.message)
                await clear_reaction("🆗", reaction.message)
                presents=returnPresent(entry, idGuild,reaction.message.guild.get_role(appelList[entry]['ClasseRoleID']).members)
                
                await send(presents, reaction.message.channel)
                del appelList[entry]

            elif not got_the_role(readGuild(idGuild)['botID'], user.roles):  # pas le bot
                await remove_reaction("🆗", reaction.message, user)
                await send("<@{}> : {}".format(user.id, returnLanguage(readGuild(idGuild)["language"], "NoRightEnd")),
                           reaction.message.channel)

        elif reactionContent=="🛑":
            if got_the_role(readGuild(idGuild)["admin"], user.roles):
                await clear_reaction("✅", reaction.message)
                await clear_reaction("🆗", reaction.message)
                await clear_reaction("🛑", reaction.message)
                del appelList[entry]
                await send(returnLanguage(readGuild(idGuild)["language"], "cancelCall"),
                       reaction.message.channel)

            elif not got_the_role(readGuild(idGuild)['botID'], user.roles):  # pas le bot
                await remove_reaction("🛑", reaction.message, user)
                await send("<@{}> : {}".format(user.id, returnLanguage(readGuild(idGuild)["language"], "NoRightEnd")),
                           reaction.message.channel)
        else:  #autre emoji
            await remove_reaction(reactionContent, reaction.message, user)
            await send("<@{}> : {}".format(user.id, returnLanguage(readGuild(idGuild)["language"], "unknowEmoji")),
                       reaction.message.channel)


@client.command(aliases= ['call'])
async def appel(context, args):
    global appelList
    classe = convert(args)
    data = readGuild(context.guild.id)
    if classe is None:
        await send(returnLanguage(data["language"], "rolenotValid"), context.channel)
    else:
        if got_the_role(data["admin"], context.author.roles):
            appelList["{}-{}".format(context.guild.id, context.message.id)] = {'ClasseRoleID': classe, 'listStudents': []}
            await send(returnLanguage(data["language"], "startCall"), context.channel)
            await add_reaction("✅", context.message)  # on rajoute les réactions ✅ & 🆗
            await add_reaction("🆗", context.message)
            await add_reaction("🆗", context.message)
            await add_reaction("🛑", context.message)
        else:
            await send("<@{}> : {}".format(context.author.id, returnLanguage(data["language"], "notTeacher")),
                    context.channel)


@client.command(aliases= ['listroles','roles','Roles','list'])
async def ListRoles(context,args):
    message="**Admins :**"
    quiet= args=='-q'
    for i in readGuild(context.guild.id)["admin"]:
        if quiet:
            message+="\n{}".format(discord.utils.get(context.guild.roles, id=i))
        else:
            message+="\n<@&{}> : {}".format(i, discord.utils.get(context.guild.roles, id=i))
    await send(message, context.channel)


@client.command(aliases= ['add'])
async def addRole(context, *args):
    guild = str(context.guild.id)
    data = readGuild(guild)
    if len(data["admin"]) > 0 and not got_the_role(data["admin"], context.author.roles):
        await send("<@{}> : {}".format(context.author.id, returnLanguage(data["language"], "NoPrivileges")),
                   context.channel)
    else:
        message=str()
        for i in args:
            role = convert(i)
            if role is not None:
                if not role in data["admin"]:
                    data["admin"].append(role)
                    message+='\n'+returnLanguage(data["language"], "newAdmin")+i
                else:
                    message+="\n **{}** role already added".format(i)
            else :
                message+="\n**{}** not valid role".format(i)
        editGuild(guild, data)
        await context.channel.send(message)


@client.command(aliases= ['rm','del','remove'])
async def rmRole(context, *args):
    guild = str(context.guild.id)
    data = readGuild(guild)
    if len(data["admin"]) > 0:
        if got_the_role(data["admin"], context.author.roles):
            message=str()
            for i in args:
                role = convert(i)
                if role in data["admin"]:
                    data["admin"].remove(role)
                    message+='\n*{}:* <@&{}>'.format(returnLanguage(data["language"], "removeAdmin"),role)
                else:
                    message+="\n*<@&{}> {}*".format(role, returnLanguage(data["language"], "notAdmin"))
            editGuild(guild, data)
            await send(message,context.channel)
        else:
            await send("<@{}> : {}".format(context.author.id, returnLanguage(data["language"], "NoPrivileges")),
                       context.channel)
    else:
        await send(returnLanguage(data["language"], "zeroPrivileges"), context.channel)


@client.command()
async def language(context, langue):
    if langue in ["fr", "en", "de"]:
        data = readGuild(context.guild.id)
        if got_the_role(data["admin"], context.author.roles):
            data["language"] = langue
            await send(returnLanguage(langue, "changeLanguage"), context.channel)
            editGuild(context.guild.id, data)
        else:
            await send("<@{}> : {}".format(context.author.id, returnLanguage(data["language"], "NoPrivileges")),
                       context.channel)
    else:
        await send("Unknow language:\n**Languages :**\n• English: en\n• French: fr\n• German: de", context.channel)


@client.event
async def on_command_error(context, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await send(returnLanguage(readGuild(context.guild.id)["language"], "unknowCommand"), context.message.channel)
        await help(context)
    raise error

client.remove_command('help')
@client.command()
async def help(ctx):
    
    message=returnLanguage(readGuild(ctx.guild.id)["language"], "commands")
    
    embed=discord.Embed(color=discord.Colour.green(),title="Help Commands")
    embed.set_author(name="CheckStudents",url="https://github.com/Renaud-Dov/CheckStudents",icon_url="https://raw.githubusercontent.com/Renaud-Dov/CheckStudents/master/img/logo.png")
    embed.add_field(name=".Check call",value=message[1])
    embed.add_field(name=".Check addRole",value=message[2])
    embed.add_field(name=".Check rmRole",value=message[3])
    embed.add_field(name=".Check language",value=message[4])
    embed.add_field(name=".Check ListRoles",value=message[5])

    await ctx.message.author.send(message[0],embed=embed)
    # await ctx.message.author.send()



client.run(token)
client.add_command(appel)
client.add_command(help)
client.add_command(addRole)
client.add_command(rmRole)
client.add_command(ListRoles)
client.add_command(language)