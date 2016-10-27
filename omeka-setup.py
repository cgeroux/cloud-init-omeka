#!/usr/bin/python3
import optparse as op
import os
import shutil
import subprocess
import glob
import string
import random
import stat
import re
import socket
import sys

def parseOptions():
  """Parses command line options
  """
  
  parser=op.OptionParser(usage="Usage %prog SERVER"
    ,version="%prog 1.0",description="Sets up mediawiki."
    +"SERVER is the base url for the server, this should be your domain name "
    +"which points to your machines IP, or your machines IP if you don't have "
    +"a domain name. This script should probably be run with sudo as it will "
    +"likely have to edit and read files which aren't editable or perhaps "
    +"not even readable by standard users.")
  
  parser.add_option("--dry-run",dest="dryRun",action="store_true",default=False
    ,help="If set will not actually do anything, only print out what it would "
    +"have done [not default]")
  parser.add_option("--omeka-version",dest="version",action="store"
    ,type="string",default="2.4"
    ,help="Set the version of omeka [default: %default].")
  parser.add_option("--omeka-patch",dest="patch",action="store"
    ,type="string",default="1"
    ,help="Set the patch level of omeka [default: %default].")
  parser.add_option("--site-name",dest="siteName",action="store"
    ,type="string",default="Test site"
    ,help="Sets the name of the omeka website [default:%defaul]")
  parser.add_option("--admin-user",dest="adminName",action="store"
    ,type="string",default=None
    ,help="Sets administrator user name, by default it is randomly "
    +"generated.")
  parser.add_option("--ssl",dest="enableSSL",action="store"
    ,type="string",default="False"
    ,help="Enables SSL by giving a \"true\" value [default: %default]")
  return parser.parse_args()
def replaceStrInFile(strMatch,strReplace,fileName,maxOccurs=None):
  """Replace all occurrences of strMatch with strReplace in file fileName
  up to maxOccurs if specified.
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  
  #how many occurrences are there
  numMatches=fileText.count(strMatch)
  
  if maxOccurs!=None:
    fileText=fileText.replace(strMatch,strReplace,max=maxOccurs)
    if numMatches>maxOccurs:
      numMatches=maxOccurs
  else:
    fileText=fileText.replace(strMatch,strReplace)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
  return numMatches
def replaceStrInFileRe(pattern,replacement,fileName,maxOccurs=None):
  """Replace all occurrences of pattern with strReplace in file fileName
  up to maxOccurs if specified. This version uses regular expression matching 
  also
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  
  #how many occurrences are there
  numMatches=len(re.findall(pattern,fileText))
  
  if maxOccurs!=None:
    fileText=re.sub(pattern,replacement,fileText,count=maxOccurs)
    if numMatches>maxOccurs:
      numMatches=maxOccurs
  else:
    fileText=re.sub(pattern,replacement,fileText)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
  return numMatches
def commentOutLineMatching(pattern,fileName,maxOccurs=None):
  """
  Adds a # to the begning of any line which matches pattern
  """
  
  file=open(fileName,mode='r')
  pattern=re.compile(pattern)
  fileText=""
  numMatches=0
  if maxOccurs==None:
    maxOccurs=sys.maxsize
    
  for line in file:
    
    if pattern.match(line) and numMatches<maxOccurs:
      fileText+="#"+line
      numMatches+=1
    else:
      fileText+=line
  file.close()
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
  return numMatches
def appendToFile(strsToAppend,fileName):
  """Append multiple string to the end of a file
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  for strToAppend in strsToAppend:
    fileText+=strToAppend
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
def genNameAndPass(length=16
  ,chars=string.ascii_uppercase+string.ascii_lowercase+string.digits):
  
  name=''
  for i in range(length):
    name+=random.SystemRandom().choice(chars)
    
  passwd=''
  for i in range(length):
    passwd+=random.SystemRandom().choice(chars)
  
  return (name,passwd)
def execute(func,*args,dry=False,**kwargs):
  if not dry:
    return func(*args,**kwargs)
  else:
    commandStr=func.__name__+"("
    firstArg=True
    for arg in args:
      if firstArg:
        commandStr+=str(arg)
        firstArg=False
      else:
        commandStr+=","+str(arg)
    for key in kwargs:
      if firstArg:
        commandStr+=key+"="+str(kwargs[key])
        firstArg=False
      else:
        commandStr+=","+key+"="+str(kwargs[key])
    commandStr+=")"
    print(commandStr)
    return None
def setupOmeka(settings={},dry=False):
  """Downloads media wiki and puts it into document root
  """
  
  (adminName,adminPassWd)=genNameAndPass()
  (dummy,dbPassWd)=genNameAndPass()
  
  defaultSettings={
    "version":"2.4"
    ,"patch":"1"
    ,"siteName":"Test site"
    ,"adminName":adminName
    ,"adminPass":adminPassWd
    ,"server":"http://127.0.0.1/"
    ,"dbserver":"localhost"
    ,"dbuser":"root"
    ,"dbpass":dbPassWd
    ,"dbname":"omeka"
    ,"documentRoot":"/var/www/html"
    ,"tmpDir":"/tmp"
    ,"owner":"www-data"
    ,"group":"www-data"
    ,"cleanUp":True
    ,"purgeDocRoot":True
    }
  
  #set settings to default if no settings given or if setting is None
  for key in defaultSettings.keys():
    
    if key not in settings.keys():
      settings[key]=defaultSettings[key]
    else:
      if settings[key]==None:
        settings[key]=defaultSettings[key]
  
  omekaName="omeka-"+settings["version"]
  if settings["patch"]!="0":#don't add zero patch numbers
    omekaName+="."+settings["patch"]
  
  tmpDir=os.path.join(settings["tmpDir"],omekaName)
  url="http://omeka.org/files/"+omekaName+".zip"
  
  #download and unzip omeka
  execute(subprocess.call,["wget",url,"--directory-prefix="
    +settings["tmpDir"]],dry=dry)
  execute(subprocess.call,["unzip",tmpDir+".zip","-d",settings["tmpDir"]],dry=dry)
  
  #remove existing files in document root
  if settings["purgeDocRoot"]:
    paths=glob.glob(settings["documentRoot"]+"/*")
    for path in paths:
      try:
        execute(os.remove,path,dry=dry)
      except IsADirectoryError:
        execute(shutil.rmtree,path,dry=dry)
  
  #move files to document root
  paths=glob.glob(tmpDir+"/*")
  paths+=glob.glob(tmpDir+"/.*")
  for path in paths:
    pathBaseName=os.path.basename(path)
    #recursively move
    execute(shutil.move,path,os.path.join(settings["documentRoot"]
      ,pathBaseName),dry=dry)
  
  #change owner and group
  for root,dirs,files in os.walk(settings["documentRoot"]):
    
    #change owner of directories
    for dir in dirs:
      execute(shutil.chown,os.path.join(root,dir)
        ,user=settings["owner"]
        ,group=settings["group"],dry=dry)#this is not recursive
   
    #change owner of files
    for file in files:
      execute(shutil.chown,os.path.join(root,file)
        ,user=settings["owner"]
        ,group=settings["group"],dry=dry)#this is not recursive
        
  #clean up temporary files
  if settings["cleanUp"]:
    execute(os.removedirs,tmpDir,dry=dry)
    execute(os.remove,tmpDir+".zip",dry=dry)
    
  #set mysql root password (initial install has no root password)
  execute(subprocess.call,["mysqladmin","-u","root","password",settings["dbpass"]],dry=dry)
  
  #create omeka database
  execute(subprocess.call,["mysql","--user="+settings["dbuser"],"--password="+settings["dbpass"],"-e","create database "+settings["dbname"]],dry=dry)
  
  #set database settings for omeka
  omekaDBSettingsfile=os.path.join(settings["documentRoot"],"db.ini")
  execute(replaceStrInFile,"host     = \"XXXXXXX\"","host     = \""+settings["dbserver"]+"\""
    ,omekaDBSettingsfile,dry=dry)
  execute(replaceStrInFile,"username = \"XXXXXXX\"","username = \""+settings["dbuser"]+"\""
    ,omekaDBSettingsfile,dry=dry)
  execute(replaceStrInFile,"password = \"XXXXXXX\"","password = \""+settings["dbpass"]+"\""
    ,omekaDBSettingsfile,dry=dry)
  execute(replaceStrInFile,"dbname   = \"XXXXXXX\"","dbname   = \""+settings["dbname"]+"\""
    ,omekaDBSettingsfile,dry=dry)
  
  #secure omekaDBSettingsfile, only owner needs read access
  execute(shutil.chown,omekaDBSettingsfile,user=settings["owner"]
    ,group=settings["group"],dry=dry)
  execute(os.chmod,omekaDBSettingsfile,0o400,dry=dry)
  
  #enable apache2 mod_rewrite
  execute(subprocess.call,["a2enmod","rewrite"],dry=dry)
  
  #edit apache2 site config to allow .htaccess file to work
  execute(replaceStrInFile
    ,"<Directory /var/www/>\n        Options Indexes FollowSymLinks\n        AllowOverride None\n"
    ,"<Directory /var/www/>\n        Options Indexes FollowSymLinks\n        AllowOverride all\n"
    ,"/etc/apache2/apache2.conf",dry=dry)
  
  #need to create a database for omeka
  #mysql command is "create database omeka;"
  #need to enable apache2 mod_rewrite with
  #command "sudo a2enmod rewrite"
  #then restart apache with "sudo service apache2 restart"
  #TODO: create a method to install plugins? At the very least install the plugins we need
  #need to change "AllowOverride None" to "AllowOverride All" under <Directory /var/www> in /etc/apache2/apache2.conf to allow the omeka .htacces file to work
  
  return (settings["adminName"],settings["adminPass"],settings)
def securePHP(dry=False):
  """Ensures some basic php security settings are set
  """
  
  #ensure register_globals is disabled
  numReplaces=execute(replaceStrInFileRe,
    "(?<!([^\s]))register_globals[\s]*=[\s]*((O|o)n|(O|o)ff)"
    ,"register_globals = Off","/etc/php5/apache2/php.ini",dry=dry)
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"register_globals = Off\n","/etc/php5/apache2/php.ini"
      ,dry=dry)
  
  #disable allow_url_fopen
  numReplaces=execute(replaceStrInFileRe,
    "(?<!([^\s]))allow_url_fopen[\s]*=[\s]*((O|o)n|(O|o)ff)"
    ,"allow_url_fopen = Off","/etc/php5/apache2/php.ini",dry=dry)
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"allow_url_fopen = Off\n","/etc/php5/apache2/php.ini"
      ,dry=dry)
  
  #ensure session.use_trans_sid is off
  numReplaces=execute(replaceStrInFileRe,
    "(?<!([^\s]))session.use_trans_sid[\s]*=[\s]*[0-1]"
    ,"session.use_trans_sid = 0","/etc/php5/apache2/php.ini",dry=dry)
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"session.use_trans_sid = 0\n"
      ,"/etc/php5/apache2/php.ini",dry=dry)
  
  #restart apache for settings to take effect
  execute(restartApache,dry=dry)
def secureMySQL(dry=False):
  """Ensures some basic MySQL security settings are set
  """
  
  #is default for mysql on ubuntu 14.0.4
  #bind-address            = 127.0.0.1
  pass
def secureApache(documentRoot,dry=False):
  """
  """
  
  #disallow any execution of files in the uploads directory
  uploadDirSettings=(
    "<Directory "+os.path.join(documentRoot,"images/")+">\n"
    "# Ignore .htaccess files\n"
    "AllowOverride None\n"
    "\n"
    "# Serve HTML as plaintext, don't execute SHTML\n"
    "AddType text/plain .html .htm .shtml .php .phtml .php5\n"
    "\n"
    "# Don't run arbitrary PHP code.\n"
    "php_admin_flag engine off\n"
    "\n"
    "# If you've other scripting languages, disable them too.\n"
    "</Directory>\n")
  execute(appendToFile,uploadDirSettings,"/etc/apache2/apache2.conf",dry=dry)
  execute(restartApache,dry=dry)
def restartApache(dry=False):
  """Restarts apache2
  """
  
  execute(subprocess.call,["service","apache2","restart"],dry=dry)
def validateDomainName(hostName):
    """source:
    https://en.wikipedia.org/wiki/Hostname#Restrictions_on_valid_host_names
    
    1) must be under 253 characters
    2) each label (seperated by ".") must be between 1 and 63 characters long
    3) each label must contain only ASCII letters 'a' - 'Z' (case-insensitive)
      , '0' - '9', and '-'
    4) labels must not start or end with a '-'
    5) must be case-insensitive (i.e. will convert upper case to lower case)
    
    """
    
    allowed=set(string.ascii_lowercase+string.digits+"-"+string.ascii_uppercase)
    
    #1) check for overall length
    if(len(hostName)>252):
      raise Exception("hostName \""+hostName+"\" is longer than 253 characters")
    
    labels=hostName.split(".")
    
    for label in labels:
      
      #2) check for length of label
      if not (len(label) <= 63 and len(label) >= 1):
        raise Exception("hostName label \""+label+"\" is "+str(len(label))
        +" characters long which is not between 1 and 63 characters long")
      
      #3) check for invalid characters
      if not (set(label) <= allowed):
        raise Exception("hostName label \""+label
          +"\" contains characters which are not allowed, \""
          +str(set(label)-allowed)+"\"")
      
      #4) must not start with a '-'
      if label[0]=='-':
        raise Exception("label \""+label
        +"\" starts with a '-' which is not allowed")
    
    return True
def isIP(ipToTest):
  """
  Returns tru if give ipToTest is an ip, else returns false
  """
  
  try:
    socket.inet_aton(ipToTest)
    return True
  except socket.error:
    return False
def ipAddressToCCCloudDomain(ipAddress):
  """Converts an IPv4 address to a Compute Canada Cloud Domain name
  """
  
  domainName=ipAddress.replace(".","-")
  domainName+=".cloud.computecanada.ca"
  return domainName
def configureSSL(domainName,dry=False):
  """Configures apache to use a self-signed SSL certificate
  """
  
  #enable ssl mod
  execute(subprocess.call,["a2enmod","ssl"],dry=dry)
  restartApache(dry=dry)
  
  #create input string for openssl command
  inputStr='CA\nNova Scotia\nHalifax\nCompute Canada\nACENET\n'+domainName+'\nno@email.com\n'
  
  #create ssl cert
  #Note that dry is fixed to be False, creating the cert doesn't really cause a problem except 
  #it might overwrite an existing cert, and if it isn't actually executed the following steps will not be able to execute
  p=execute(subprocess.Popen,["openssl","req","-x509","-nodes"
    ,"-days","3650"
    ,"-newkey","rsa:2048"
    ,"-keyout","/etc/ssl/private/server.key"
    ,"-out","/etc/ssl/certs/server.crt"]
    ,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.STDOUT,dry=dry)
  
  #have to handle dry runs in a special way as this command (dry or not) 
  #depends on p not being None
  if not dry:
    output=execute(p.communicate,input=inputStr.encode('utf-8'),dry=dry)[0]
  else:
    print("p.communicate(input="+inputStr+")")
  
  #Set correct ownership and permission of key
  execute(subprocess.call,["sudo","chown","root:ssl-cert","/etc/ssl/private/server.key"],dry=dry)
  execute(subprocess.call,["sudo","chmod","640","/etc/ssl/private/server.key"],dry=dry)
  
  #comment out any previous settings
  execute(commentOutLineMatching,".*SSLCertificateFile.*","/etc/apache2/sites-available/default-ssl.conf",dry=dry)#not matching
  execute(commentOutLineMatching,".*SSLCertificateKeyFile.*","/etc/apache2/sites-available/default-ssl.conf",dry=dry)#not matching
  execute(commentOutLineMatching,".*SSLCertificateChainFile.*","/etc/apache2/sites-available/default-ssl.conf",dry=dry)#not matching
  
  #add settings before for improved security </VirtualHost>
  execute(replaceStrInFileRe,"</VirtualHost>"
    ,"\tSSLCertificateFile      /etc/ssl/certs/server.crt\n"
    +"\t\tSSLCertificateKeyFile /etc/ssl/private/server.key\n"
    +"\t\tSSLCertificateChainFile /etc/ssl/certs/server.crt\n"
    +"\t\tServerName "+domainName+"\n"
    +"\t\tServerAlias www."+domainName+"\n"
    +"\t\tSSLProtocol all -SSLv2 -SSLv3\n"
    +"\t\tSSLCipherSuite HIGH:MEDIUM:!aNULL:!MD5:!SEED:!IDEA:!RC4\n"
    +"\t\tSSLHonorCipherOrder on\n"
    +"\t</VirtualHost>","/etc/apache2/sites-available/default-ssl.conf",dry=dry)
  
  #add redirect to https
  execute(replaceStrInFileRe,"</VirtualHost>"
    ,"\tRedirect permanent / https://"+domainName+"/\n</VirtualHost>\n"
    ,"/etc/apache2/sites-available/000-default.conf",dry=dry)
  
  #enable ssl on our virtual host
  execute(subprocess.call,["a2ensite","default-ssl.conf"])
  execute(subprocess.call,["service","apache2","restart"])
def main():
  
  #parse command line options
  (options,args)=parseOptions()
  
  #ensure we have the right number of arguments
  if len(args) != 1:
    raise Exception("Must have at least one argument specifying the "
      +"server's IP or Domain name")
  
  #set domain name
  domainName=args[0]
  
  #if domainName is an IP convert it to a Compute Canada Cloud domain name
  if isIP(domainName):
    domainName=ipAddressToCCCloudDomain(domainName)
  
  #verify that the server name is valid (will not contain an http://)
  validateDomainName(domainName)
  
  #map options onto settings
  dryRun=options.dryRun
  settings={}
  settings["version"]=options.version
  settings["patch"]=options.patch
  settings["siteName"]=options.siteName
  settings["adminName"]=options.adminName

  if options.enableSSL=="True":
    settings["enableSSL"]=True
  else:
    settings["enableSSL"]=False
  
  if settings["enableSSL"]:
    settings["server"]="https://"+domainName
  else:
    settings["server"]="http://"+domainName
  
  #adjust some php settings to improve security
  securePHP(dry=dryRun)
  
  #adjust some mysql settings to improve security
  secureMySQL(dry=dryRun)
  
  #setup omeka
  (adminUser,adminPassWd,settingsUsed)=setupOmeka(
    settings=settings,dry=dryRun)
  
  #adjust some apache settings to improve security
  secureApache(settingsUsed["documentRoot"],dry=dryRun)
  
  #
  if settingsUsed["enableSSL"]:
    configureSSL(domainName,dry=dryRun)
  
  print("Omeka Admin Username:"+adminUser)
  print("Omeka Admin password:"+adminPassWd)
if __name__ == "__main__":
 main()
