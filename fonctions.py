from configuration import dbuser, dbserver, dbbot

def getUserInfos(arg, userID):
    #arg : age / date_creation / insta / prenom / sexe / userName / public / selfie / likes / likeurs / situation / villeName / villeID / posted / presentation
    dict= dbuser.user.find_one({"userID":userID})
    if dict:
        try:
            return dict[arg]
        except KeyError as e:
            print(str(e))
 
def getServerInfos(arg= None, serverID = 904028283203641365):
    #arg : rolebienvenue / salonbienvenue / salonlikes / salonselfie / salondate / quoifeur / ajouterrole / blacklist / salonlogbot / salonprofil
    dict= dbserver.server.find_one({"serverID":serverID})
    if arg:
        try:
            return dict[arg]
        except KeyError as e:      
            print(str(e))
    else:
        return dict
    

def isInDatabase(arg, dataset, ID):
  
  if dataset == "serveronfig":
    cle= "serverID"

    if arg in dbserver.serverconfig.find_one({cle:ID}):
      return True
    
    else:     
      return False
    
  elif dataset == "users":
    cle = "userID"

    if arg in dbuser.users.find_one({cle:ID}):
      return True
    
    else:
      return False
    
  else:
    return "Argument invalide"

