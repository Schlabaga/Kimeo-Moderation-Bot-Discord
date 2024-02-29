
import discord
from discord import app_commands, ui
from discord.ui import View, Select
from discord.ext import commands
import discord_emoji
import pymongo
import datetime as dt
from fonctions import getServerInfos
from config import MongoClient, bot


db = MongoClient.user_profiles

EmbedColor=discord.Color.from_rgb(219,112,147)


class setup_modal(ui.Modal, title= "Formulaire"):
    
    prenom = ui.TextInput(label='Ton prénom', style=discord.TextStyle.short, placeholder="Ne donne jamais ton nom de famille!", max_length= 30)
    sexe = ui.TextInput(label='Ton sexe', style=discord.TextStyle.short, placeholder="Homme/femme", max_length=5)
    age = ui.TextInput(label='Ton age', style=discord.TextStyle.short, max_length=2, placeholder= "14-30 ans", )
    ville = ui.TextInput(label='Ville (évite d\'être trop précis(e))', style=discord.TextStyle.short, placeholder="Paris")
    instagram = ui.TextInput(label='Ton instagram', style=discord.TextStyle.short, placeholder= "Facultatif", required=False ,max_length=30)
    
    async def on_submit(self, interaction: discord.Interaction):
    
        guild= interaction.guild

        embedResponse=discord.Embed(title='Ton formulaire',
        color=EmbedColor)
        embedResponse.set_footer(text=guild.name,icon_url=guild.icon)
        embedResponse.add_field(name='Ton prénom',value=self.prenom,inline=True)
        embedResponse.add_field(name="Ton sexe",value=self.sexe,inline=True)
        embedResponse.add_field(name="Ton âge",value=self.age,inline=True)
        embedResponse.add_field(name="Ta ville",value=self.ville)
        embedResponse.add_field(name="Ton insta",value=self.instagram)
        #embedResponse.set_image(url="")

        await interaction.response.send_message(embed=embedResponse, ephemeral=True)


class Select(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Option 1",emoji="👌",description="This is option 1!"),
            discord.SelectOption(label="Option 2",emoji="✨",description="This is option 2!"),
            discord.SelectOption(label="Option 3",emoji="🎭",description="This is option 3!")
            ]
        super().__init__(placeholder="Select an option",max_values=1,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):

        await interaction.response.send_message(content=f"Your choice is {self.values[0]}!",ephemeral=True)


class SelectView(discord.ui.View):
    def __init__(self ):

        super().__init__()

        self.add_item(Select())




class blacklistPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(5,60, commands.BucketType.member)
        self.bot = bot

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        max_values=1,
        custom_id="persistent_view:blacklistPanel",
        placeholder='Sélectionne / recherche un utilisateur',
    )

    async def user_select(self, selectInteraction: discord.Interaction, cibleListe: discord.ui.UserSelect) -> None:

        raison = "panel"

        bucket = self.cooldown.get_bucket(selectInteraction.message)
        retry = bucket.update_rate_limit()

        if retry:
            await selectInteraction.response.send_message(f"Tu es en **cooldown**, rééssaye dans `{round(retry,1)} secondes`", ephemeral=True)
            return

        else:

            cible = cibleListe.values[0]
            
            selectSanction = discord.ui.Select(options=[
            discord.SelectOption(label=f"Bannir {cible.name}", emoji=discord_emoji.discord_to_uni("white_check_mark")),
            discord.SelectOption(label=f"Blacklist {cible.name}", emoji= discord_emoji.discord_to_uni("wastebasket")),
            discord.SelectOption(label="Annuler", emoji= discord_emoji.discord_to_uni("wastebasket")),
            ], placeholder="Quelle action veux-tu exécuter?" ) 



            async def select_callback(interaction:discord.Interaction):

                serveur = selectInteraction.guild
                raison = interaction.user.name
                description = ""
                
                if selectSanction.values[0].startswith("Bannir"):
                    
                        await serveur.ban(cible, reason = raison)
                        await interaction.response.send_message(f"L'utilisateur `{cible.name}` a bien été banni de `{serveur.name}`")

                    
                        await interaction.response.send_message(f"Je n'ai pas les permissions pour bannir cet utilisateur!")

                if selectSanction.values[0].startswith("Blacklist"):
                    print("oui")
                    for guild in bot.guilds:

                        try:
                            await guild.ban(cible)
                            description = f"{description} `{guild.name}`: débanni\n"

                        except:
                            description = f"{description} `{guild.name}`: déjà déban\n"
                    
                    blacklistListe = getServerInfos(arg="blacklist")

                    if blacklistListe:
                        for bannedUser in blacklistListe:
                            utilisateurBlacklist = bannedUser[0]

                            if cible.id == utilisateurBlacklist:

                                description = f"{cible.name} est déjà dans la blacklist, mais il/ elle a quand même été ban:\n\n{description}"
                                await interaction.response.send_message(description, ephemeral=True)                               

                            else:       

                                db.serverconfig.update_one({'serverID': serveur.id }, {'$push': {'blacklist': [cible.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
                                
                                description = f"{cible.name} a été ajouté à la blacklist:\n\n{description}"
                                await interaction.response.send_message(description, ephemeral=True)

                    else:
                        
                        db.serverconfig.update_one({'serverID': serveur.id }, {'$push': {'blacklist': [cible.id,dt.datetime.utcnow()+dt.timedelta(hours=1),raison]}}, upsert = True)
                        description = f"La blacklist a été créée, {cible.name} est maintenant blacklist:\n\n{description}"

                        await interaction.response.send_message(description,ephemeral=True)   


                if selectSanction.values[0].startswith("Annuler"):
                    await interaction.response.send_message("Opération annulée!", ephemeral = True)
                    selectSanction.disabled = True
                    
         
            selectSanction.callback = select_callback
            selectView = View(timeout=30)
            selectView.clear_items
            selectView.add_item(selectSanction)
            
            await selectInteraction.response.defer(ephemeral=True )

            await selectInteraction.followup.send("Quelle action voulez-vous exécuter?", view=selectView, ephemeral=True)
            
