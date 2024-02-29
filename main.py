from configuration import TOKEN, bot, dbuser, dbserver
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from classes import blacklistPanel
import datetime as dt
import datetime

EmbedColor=discord.Color.from_rgb(0,0,0)


async def status():
  while True:
    await bot.change_presence(activity=discord.Streaming(name="Modération bot", url="https://www.twitch.tv/minoristream"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Streaming(name="Rejoins mes serveurs partenaires!", url="https://www.twitch.tv/minoristream"))
    await asyncio.sleep(10)


class Bot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('+'), intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(blacklistPanel())


    async def on_ready(self):
        print("--------------------------------------------")
        #servDict = getServerInfos()
        print(f"{bot.user.name} est prêt à être utilisé!")
        print("--------------------------------------------")
        
        try:
            
            synced= await bot.tree.sync()

            print(f"Synchronisé {len(synced)} commande(s)")
            print("--------------------------------------------")
            
            logsBotChannel = bot.get_channel(1083804608192839751)
            logsGuild = logsBotChannel.guild
            onlineEmbed = discord.Embed(title=f"Bot en ligne", description= f"**{bot.user.name}** a démarré avec succès!\n**{len(synced)}** commandes ont été **synchronisées**!", timestamp=datetime.datetime.utcnow()+ datetime.timedelta(hours=1))
            onlineEmbed.set_footer(text=logsGuild.name, icon_url = logsGuild.icon)
            onlineEmbed.set_thumbnail(url=bot.user.avatar)
            await logsBotChannel.send(embed= onlineEmbed)

        except Exception as e:
          print(e)

        await bot.loop.create_task(status())
    
bot = Bot()



def getServerInfos(arg= None, serverID = 993849107678515230):
  #arg : rolebienvenue / salonbienvenue / salonlikes / salonselfie / salonsmashs / quoifeur / autorole / blacklist / salonlogbot / salonprofil

  dict= dbserver.server.find_one({"serverID":serverID})

  if arg:

      try:

          return dict[arg]

      except KeyError as e:
          
          print(str(e))

  else:

      return dict
  





@bot.event
async def on_member_join(member: discord.Member):

  guild = member.guild
  ServerDataBase = dbserver.server.find_one({"serverID":guild.id})

  if not dbuser.user.find_one({"userID":member.id}):
    UserDataBase = dbuser.user.update_one({"userID":member.id},{"$set":{"afk":None,
                                                                        "sanctions":[],
                                                                        "moderateur":False,
                                                                        "administrateur": False,
                                                                        "userName": member.name}
                                                                },upsert=True)

  if ServerDataBase["autorole"] == True:

    try:
      roleBvn = guild.get_role(ServerDataBase["rolebienvenue"])
      await member.add_roles(roleBvn)
        
    except discord.errors.Forbidden as e:

      if ServerDataBase["salonlogbot"] != None:
        logchannel = guild.get_channel(ServerDataBase["salonlogbot"])
        await logchannel.send(f"Le rôle auto n'a pas pu être ajouté, merci de placer mon rôle au-dessus de celui des membres! , {str(e)}")

      else:
        print(f"Le rôle auto n'a pas pu être ajouté, merci de placer mon rôle au-dessus de celui des membres!, {str(e)}")

    except AttributeError:

      print("Le rôle membre n'a pas été défini!")
 


@bot.event
async def on_member_remove(member: discord.Member):
    
  guild = member.guild
  serverDataBase = dbserver.server.find_one({"serverID":guild.id})

  if "salonlogbot" in serverDataBase:

    if serverDataBase["salonlogbot"] !=None:

      try:
          
        salonLogs = guild.get_channel(serverDataBase["salonlogbot"])
        await salonLogs.send(f"{member.mention} a quitté le serveur ({member.id}).")

      except Exception as e:

        print("Salon logs invalide")
        print(str(e))




@bot.event
async def on_guild_join(guild: discord.Guild):

#ON PEUT AJOUTER QU'IL INITIALISE LA DB A CHAQUE JOIN DE SERV
  if not dbserver.server.find_one({"serverID":guild.id}):
    UserDataBase = dbserver.server.update_one({"serverID":guild.id},{"$set":{
                                                                      "servername":guild.name,
                                                                      "rolebienvenue":None,
                                                                      "salonbienvenue":None,
                                                                      "autorole":False,
                                                                      "blacklist":[],
                                                                      "salonlogbot":None,
                                                                      "salonchat":None,
                                                                    }},upsert=True)

  print(f"J'ai rejoint le serveur {guild.name}!")



@bot.tree.command(name="massrole", description="Ajoute un rôle à tous les membres/bots")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(cible=[
  app_commands.Choice(name="Membres", value="membres"),
  app_commands.Choice(name="Bots", value="bots")])

async def massrole(i: discord.Interaction, cible: app_commands.Choice[str], role: discord.Role):

  await i.response.send_message("Patientez...", ephemeral=True)

  guild=i.guild
  if cible.value == "bots":
    for user in guild.members:
        if user.bot:
          await user.add_roles(role)
    await i.channel.send(f"Le role {role.name} a été ajouté à tous les bots!")

  elif cible.value == "membres":
    for user in guild.members:
      if not user.bot:
        await user.add_roles(role) 
    await i.channel.send(f"Le role {role.name} a été ajouté à tous les membres!")
  



@bot.tree.command(name="updatedb", description="Met à jour la db en cas de crash du bot")
@app_commands.checks.has_permissions(administrator=True)
async def updatedb(interaction: discord.Interaction):

  guild = interaction.guild
  memberDefaultDict= {}


  for user in guild.members:

    if not user.bot:
      memberDefaultDict = {"afk":None, "sanctions":[], "moderateur":False,"administrateur": False, "userName": user.name}

      userDatas = dbuser.user.find_one({"userID":user.id})

      if userDatas:

        for localKey in memberDefaultDict:

          if localKey in userDatas:

            pass

          else:

            dbuser.user.update_one({"userID":user.id}, {"$set":{localKey:memberDefaultDict.get(localKey)}}, upsert=True)

      else:

        dbuser.user.update_one({"userID":user.id}, {"$set":{"afk":None, "sanctions":[], "moderateur":False,"administrateur": False, "userName": user.name}}, upsert=True)


  for serveur in bot.guilds:

    serverDefaultDict = {
                          "servername":serveur.name,
                          "rolebienvenue":None,
                          "salonbienvenue":None,
                          "autorole":False,
                          "blacklist":[],
                          "salonlogbot":None,
                          "salonchat":None,
                        }
    
    serverDatas = dbserver.server.find_one({"serverID":serveur.id})

    if serverDatas:

      for defaultKey in serverDefaultDict:

        if defaultKey in serverDatas:

          pass
          
        else:

          dbserver.server.update_one({"serverID":serveur.id}, {"$set":{defaultKey:serverDefaultDict.get(defaultKey)}}, upsert=True)

    else:

      dbserver.server.update_one({"serverID":serveur.id}, {"$set":{
                          "servername":serveur.name,
                          "rolebienvenue":None,
                          "salonbienvenue":None,
                          "autorole":False,
                          "blacklist":[],
                          "salonlogbot":None,
                          "salonchat":None,
                        }
        }, upsert=True)

  await interaction.response.send_message("Les différentes db ont été mises à jour", ephemeral=True)




@bot.tree.command(name="unblacklist", description="Unblacklist un utilisateur")
@app_commands.checks.has_permissions(administrator=True)
async def unblacklist(interaction: discord.Interaction, user: discord.User):
  
  serveur= interaction.guild

  description =""
  
  for guild in bot.guilds:

    try:
      await guild.unban(user)
      description = f"{description} `{guild.name}`: débanni\n"

    except:
      description = f"{description} `{guild.name}`: déjà déban\n"


  unblack = False

  blacklistVerif = dbserver.server.find_one({"serverID":serveur.id})

  if blacklistVerif:

    try:
       
      blacklistListe = blacklistVerif["blacklist"]

      for bannedUser in blacklistListe:
          
        utilisateurBlacklist = bannedUser[0]

        if user.id == utilisateurBlacklist:
          
          element = bannedUser
          unblack = True
          dbserver.server.update_one({"serverID":serveur.id}, {"$pull":{"blacklist":element}})
    
    except KeyError:

      pass


  if unblack == True:
  
    await interaction.response.send_message(f'{user} a été unblacklist et débanni(e) des serveurs suivants:\n\n{description}', ephemeral=True)
  
  else:
     
    await interaction.response.send_message(f'{user} n\'était pas blacklist:\n\n{description}', ephemeral=True)



"""@bot.tree.command(name="setsanctionspanel", description="Envoie le panel de sanctions")
@app_commands.checks.has_permissions(administrator=True)
async def setblacklistpanel(interaction: discord.Interaction, channel: discord.TextChannel = None):

    if channel == None:
       channel = interaction.channel

    guild = interaction.guild

    infosEmbed = discord.Embed(title= "Sanctionner un utilisateur",  description="Ce panel sert à faciliter le bannissement / blacklist des utilisateurs \
                               ayant enfreint les règles du serveur")
    
    infosEmbed.set_footer(text=guild.name,icon_url=guild.icon)
    infosEmbed.set_image(url="")

    await channel.send(embed=infosEmbed , view= blacklistPanel())
    await interaction.response.send_message("Le panel de sanctions a bien été défini!",ephemeral=True)

"""


@bot.tree.command(name="purge", description="Supprime un nombre de messages")
@app_commands.checks.has_permissions(administrator=True)
async def purge(interaction: discord.Interaction, nombre: int):
  
  await interaction.response.defer()

  deleted=await interaction.channel.purge(limit=nombre)

  await interaction.followup.send(f'J\'ai supprimé {len(deleted)} message(s)', ephemeral=True)



@bot.tree.command(name="rolebienvenue", description="Active / désactive l'ajout de rôle auto")
@app_commands.checks.has_permissions(administrator=True)
async def rolebienvenue(interaction: discord.Interaction):
    
  guild = interaction.guild

  utilisateur= interaction.user
  serverDict= dbserver.server.find_one({"serverID":guild.id})
  
  if serverDict:

    if "autorole" in serverDict:

      roleAutorisation = serverDict["autorole"]

    else: 
        
      roleAutorisation = True

    dbserver.server.update_one({"serverID": guild.id}, 
    {"$set":{"autorole": not roleAutorisation}})

    if roleAutorisation == False:
      await interaction.response.send_message("Les membres recevront maintenant un rôle automatiquement en rejoignant le serveur",ephemeral=True)
    
    if roleAutorisation == True:
      await interaction.response.send_message("Les membres ne recevront maintenant plus de rôle automatiquement en rejoignant le serveur", ephemeral=True)

  else:
    await interaction.response.send_message("Database Error", ephemeral=True)


@bot.tree.command(name="avatar", description="Affiche ta photo de profil")
async def avatar(i: discord.Interaction, cible: discord.Member = None):
  
  user = i.user


  if cible:
    user = cible
  
  embed = discord.Embed(title= f"Photo de profil de {user}")
  embed.set_image(url = user.avatar.url)

  await i.response.send_message(embed= embed, ephemeral=True)
     

@bot.tree.command(name="boosters", description="Affiche tous les boosters du serveur")
async def booster(i:discord.Interaction):

  guild = i.guild

  boosterStr= ""
  n=0

  for booster in guild.premium_subscribers:
    n+=1
    boosterStr = f"{boosterStr}\n・{booster}"

  if boosterStr != "":
    embed = discord.Embed(title=f"Merci aux {str(n)} boosters du serveur", description= boosterStr)
    await i.response.send_message(embed=embed, ephemeral=True)
  else:
    embed = discord.Embed(title="Aucun booster à afficher ! :(")
    await i.response.send_message(embed=embed, ephemeral=True)




@bot.tree.command(name="setactivity", description="Modifie la bio du bot / son activité")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(activité=[
    app_commands.Choice(name="Streaming", value="streaming"),
    app_commands.Choice(name="Jouer", value="playing"),
    app_commands.Choice(name="Ecoute", value="listening"),
    app_commands.Choice(name="Regarde", value="watching")])
async def editstatus(i:discord.Interaction, activité: app_commands.Choice[str] = None, description:str = None):

    if activité:

        if activité.value == "streaming":
            await bot.change_presence(activity=discord.Streaming(name=description, url="https://www.twitch.tv/minoristream"))

            
        elif activité.value == "watching":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=description))


        elif activité.value == "listening":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=description))


        elif activité.value == "playing":

            await bot.change_presence(activity=discord.Game(name=description), status=discord.Status.do_not_disturb)

    else:

        await bot.change_presence(activity = discord.Streaming(name=description, url="https://www.twitch.tv/minoristream"))
    
    await i.response.send_message(f"Mon activité a bien été changée.", ephemeral=True)


@bot.tree.context_menu(name='Blacklist')
@app_commands.checks.has_permissions(administrator=True)
async def blacklist(interaction: discord.Interaction, user: discord.User):

  guild = interaction.guild
  found = False


  raison = "context_menu"
  description = ""

  for serveur in bot.guilds:
    
    try:
        await serveur.ban(user)
        description = f"{description} `{serveur.name}`: banni\n"

    except:
        description = f"{description} `{serveur.name}`: manque de permissions\n"
        

  blacklistVerif = dbserver.server.find_one({"serverID":guild.id})
  
  try:
    
    blacklistListe = blacklistVerif["blacklist"]
    
    for bannedUser in blacklistListe:
      
      utilisateurBlacklist = bannedUser[0]
      
      if user.id == utilisateurBlacklist:

        found= True

        description = f"{user.name} est déjà dans la blacklist, mais il a quand même été ban:\n\n{description}"
        await interaction.response.send_message(description, ephemeral=True)
        await guild.ban(user, reason=raison)
        break

    if not found:

      dbserver.server.update_one({'serverID': guild.id }, {'$push': {'blacklist': [user.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
      
      description = f"{user.name} a été ajouté à la blacklist:\n\n{description}"
      await interaction.response.send_message(description, ephemeral=True)
    
  except KeyError:
     
    dbserver.server.update_one({'serverID': guild.id }, {'$push': {'blacklist': [user.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
    
    description = f"La blacklist a été créée, {user.name} est maintenant blacklist:\n\n{description}"

    await interaction.response.send_message(description,ephemeral=True)



@bot.tree.command(name="blacklist", description="Blacklist un utilisateur")
@app_commands.checks.has_permissions(administrator=True)
async def blacklist(interaction: discord.Interaction, user: discord.User, raison:str = None):
    
  guild = interaction.guild
    
  description = ""

  found = False

  for serveur in bot.guilds:
      try:
          await serveur.ban(user)
          description = f"{description} `{serveur.name}`: banni\n"

      except:
          description = f"{description} `{serveur.name}`: manque de permission\n"
        
  blacklistVerif = dbserver.server.find_one({"serverID":guild.id})

  try:
    
    blacklistListe = blacklistVerif["blacklist"]
    
    for bannedUser in blacklistListe:
      
      utilisateurBlacklist = bannedUser[0]
      
      if user.id == utilisateurBlacklist:

        found= True
        description = f"{user.name} est déjà dans la blacklist, mais il a quand même été ban:\n\n{description}"
        await interaction.response.send_message(description, ephemeral=True)
        await guild.ban(user, reason=raison)
        break

    if not found:

      dbserver.server.update_one({'serverID': guild.id }, {'$push': {'blacklist': [user.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
      description = f"{user.name} a été ajouté à la blacklist:\n\n{description}"
      await interaction.response.send_message(description, ephemeral=True)
    
  except KeyError:
     
    dbserver.server.update_one({'serverID': guild.id }, {'$push': {'blacklist': [user.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
    description = f"La blacklist a été créée, {user.name} est maintenant blacklist:\n\n{description}"
    await interaction.response.send_message(description,ephemeral=True)



@bot.tree.command(name="setupbienvenue", description="Installe les prérequis du bot")
@app_commands.checks.has_permissions(administrator=True)
async def setupbienvenue(i: discord.Interaction, salonbienvenue: discord.TextChannel, rolebienvenue:discord.Role ,salonselfie:discord.TextChannel,salonlogbot: discord.TextChannel):

  guild= i.guild

  dbserver.server.update_one({"serverID": guild.id }, {"$set":{"salonbienvenue": salonbienvenue.id, "rolebienvenue": rolebienvenue.id, "salonselfie":salonselfie.id, "salonlogbot":salonlogbot.id, }}, upsert=True)  

  await i.response.send_message("Les prérequis ont bien été setup", ephemeral=True)


@bot.tree.command(name="deletecategory", description="Supprime une catégorie et son conten")
@app_commands.checks.has_permissions(administrator=True)
async def suppr(i: discord.Interaction, categorie: discord.CategoryChannel):

  await i.response.defer(thinking=True)
  for channel in categorie.channels:
    await channel.delete()
    await asyncio.sleep(0.20)
  await categorie.delete()

  await i.followup.send_message("Les salons de la catégorie `{}` ont bien été supprimés".format(categorie.name), ephemeral=True)


@bot.tree.command(name="affiche", description="Affiche diverses informations")
@commands.has_permissions(administrator=True)
@app_commands.choices(types=[
    app_commands.Choice(name="Tarifs", value="tarifs"),
    app_commands.Choice(name="Roles", value="roles"),
    app_commands.Choice(name="Règlement", value="reglement")])

async def affiche(i: discord.Interaction, types: app_commands.Choice[str], salon: discord.TextChannel):

    guild=i.guild
    tarifs=discord.Embed(title='GIVEWAYS JOIN ・ TARIFS', description="Toutes les offres ci-dessous incluent le(s) Nitro(s), à nos frais.\
                          Merci d'ajouter **5€** si un nitro boost est fourni.",
    color=EmbedColor)
    tarifs.set_footer(text=guild.name,icon_url=guild.icon)
    tarifs.add_field(name=':third_place: `Classique`・**35€**',value="```@hewre\n24 heures\nNitro Classique```",inline=False)
    tarifs.add_field(name=":second_place: `Rare`・**55€**",value="```@here + @Giveaway\n24 heures\nNitro Classique```",inline=False)
    tarifs.add_field(name=":first_place: `Légendaire` ・**80€** ",value="```@everyone\n48 heures\nNitro Classique```",inline=False)
    tarifs.add_field(name=" :trophy: `Mythique`・**90€** ",value="```@everyone\n96 heures\nNitro Classique```",inline=False)

    reglement=discord.Embed(title="Règlement",
                            description="Bienvenue à toi !\n\n**Nous mettons dans ce serveur beaucoup d'animes à la disposition de tous !**\n\
                            Par conséquent, merci de respecter les règles suivantes :\n\nPour vivre en communauté, il est important de respecter quelques règles \
                            afin de ne pas créer de quelconques divergences entre les membres et/ou le staff.\n\n**1. **Dans un cadre général, merci de respecter les \
                            [conditions d'utilisation officielles](https://discord.com/terms) de Discord\n\n**2. ** Plus spécifiquement dans ce serveur, on ne demande \
                            pas beaucoup aux membres, si ce n'est de vivre dans un minimum de respect.\n\n**3. ** Les insultes sont autorisées si elles sont adressées avec \
                            du second degré et si la personne en face est consciente que c'est de l'humour.\n\n**4. **Aucune forme de harcèlement, racisme, humiliation\
                             volontairement violente ne sera tolérée et s'ensuivra de sanctions strictes.\n\n**5. **Si vous rencontrez des problèmes sur le serveur ou les \
                            liens mega, n'hésitez pas a entrer en contact avec le staff. .\n\n**6. **L'envoi de contenu NSFW (pornographique), qu'il soit sous forme de lien, \
                            d'image ou de fichier quelconque n'est autorisé que dans le(s) salon(s) approprié(s).\n\n**7.** Les pubs, qu'elles soient en MP ou directement sur \
                            le serveur sont interdites.\n\n**8.** Il est bien entendu interdit de plagier le serveur.\n\n**9. **Si besoin de plus d'informations, veuillez \
                            contacter un staff.\n\n**10. **Réagissez à ce message pour obtenir un rôle qui prouvera votre adhésion au règlement (facultatif).\n\n**Excellent \
                            séjour à vous !**"
    ,color=EmbedColor)
    reglement.set_footer(text=guild.name,icon_url=guild.icon)
    reglement.set_image(url="https://media.giphy.com/media/DdHdXOV1rwj7ctKWN9/giphy.gif")

    roles=discord.Embed(title="AUTOROLES",description=":underage: : majeur\n:baby: : mineur\n\n👩: femme/fille.\n👨 : homme/garçon.\n\n♾️ : accéder au salon mini-jeux \
                        \n\n:smirk: : accéder au(x) salon NSFW\n\n:confetti_ball: : être prévenu(e) des nouvelles sorties"
    ,color=EmbedColor)
    roles.set_footer(text=guild.name,icon_url=guild.icon)
    roles.set_image(url="https://media.giphy.com/media/HGfVgWlpaA9uj4U5uf/giphy.gif")




    if (types.value == 'tarifs'):
        embed = tarifs
    elif (types.value == 'roles'):
        embed = roles
    elif (types.value == 'reglement'):
        embed = reglement
    
    try:
        await salon.send(embed=embed)
        await i.response.send_message(f"Le message a bien été envoyé dans {salon.name}", ephemeral=True)
    except discord.app_commands.CommandInvokeError:
        await i.response.send_message("Erreur, veuillez spécifier un salon!", ephemeral=True)



@bot.tree.command(name="myservers", description="Affiche les serveurs dans lequel je suis présent")
@commands.has_permissions(administrator=True)
async def myservers(interaction: discord.Interaction):

    serveurs=""

    for guild in bot.guilds:
      
      serveurs=serveurs+f"`{guild.name}`, **{str(guild.member_count)}** membres\n"
      

    embed= discord.Embed(title="Mes serveurs", description= serveurs)

    await interaction.response.send_message(embed=embed, ephemeral=True)
      

bot.run(TOKEN)