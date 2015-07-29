import sys
import os
import re
import tempfile
import zipfile
import mimetypes
import uuid
import datetime
import urllib2
import httplib
from xml.dom import minidom
from xml.dom.minidom import Document

dcterms = ["title", "creator", "ispartof", "description", "subject", "language", "identifier", "contributor", "created"]
dcterms2 = ["title", "creator", "description", "subject", "language", "license", "identifier", "type", "contributor", "audience", "spatial", "extent", "publisher", "created", "rightsHolder"]
#falta temporal - pode ser multiple

# Crear clase Element, heredar a Tracks Catalogs Attackments...
class Element:
     def __init__(self,url=None, etype=None, mimetype=None):
          """Elementos formantes dun mediapackage MH: Manifest, Timeline, Track, Catalog, Attachment, Other"""
          self.url = url
          self.etype = etype
          self.mime = mimetype
          
class Track(Element):
     """Tracks de audio e video para introducir en MH Mediapackage"""
               
class Catalog(Element):
     """XML cos datos sobre a gravacion"""
     def __init__(self,url=None, etype=None, mimetype=None, ref=None):
          Element.__init__(self,url,etype,mimetype)
          self.ref=ref
          
class Manifest(Catalog):
     """Datos relacionados co manifest.xml"""
     def __init__(self,path = None):
          if path == None:
               path = ""
          elif path != "":
               path = path+"/"
          Catalog.__init__(self,path+"manifest.xml","metadata/dublincore","text/xml")
          
class Attachment(Element):
     """Arquivos adxuntos dun MP"""

class Other(Element):
     """Outros arquivos do MP"""

class Mediapackage:
     """ Clase que maneja mediapackages de Matterhon"""
     # NOTA: o Episode non ten referencia
     # NOTA2: o series ten referencia series:1
     def __init__(self, tmp="/tmp", dictionary=[], title=None, date=None, presenter=None, identifier = None):
          
          self.manifest = Manifest()
          self.episode = None # nome do arquivo donde vai o episode
          self.series = None # idem para series
          #Elementos
          self.tracks = []
          self.catalogs = []
          self.attachments = []
          self.others = []
          #Metadatos
          self.metadata_episode=dict()
          self.metadata_series=dict()
          self.date = date
          self.tmp = tmp
          if date == None: 
               self.date = datetime.datetime.now().replace(microsecond=0) #.isoformat()
          if identifier == None :
               self.id = uuid.uuid4() 
          
     # CONSIDER facer o checksum e o size cando se fai add
     # CONSIDER facer un add_element que identifique o elemento e o engada onde proceda
     def add_element(self,filepath,etype,other=None):
          pass

     def add_track (self, filepath, flavour):
          if flavour.count("/source"):
               self.tracks.append(Track(filepath,flavour,mimetypes.guess_type(filepath)[0]))
          else:
               self.tracks.append(Track(filepath,flavour+"/source",mimetypes.guess_type(filepath)[0]))
     
     def add_catalog(self, filepath, etype, ref=None):
          self.catalogs.append(Catalog(filepath, etype, "text/xml", ref))

     def add_attachment(self, filepath, etype):
          self.attachments.append(Attachment(filepath,"attachment/"+etype,mimetypes.guess_type(filepath)[0]))

     def add_other(self, filepath, etype):
          self.others.append(Other(filepath,"attachment/"+etype,mimetypes.guess_type(filepath)[0]))

     def get_mediapackage(self, name):
          """Crea un mediapackage a partir de un zip"""
          if os.path.isdir(name):
               "Getting MediaPackage from a folder"
               self.tmp=name
               self.manifest = Manifest(self.tmp)
               self.get_data()
          else:
               "Getting MediaPackage from a zip"
               z=zipfile.ZipFile(name,"r",zipfile.ZIP_DEFLATED,True)
               # z=zipfile.ZipFile(name)
               self.tmp=tempfile.mkdtemp('','gc_',os.getcwd())
               self.manifest = Manifest(self.tmp)
               z.extractall(self.tmp)
               self.get_data() #analizar manifest e add_tracks        
          return 1 #CONSIDER devolver o obxecto

     def create_xml(self): # USE para o create_mediapackage, aforrar codigo e separar partes
          # manifest
          m = open(self.tmp+"/manifest.xml", 'w')
          m.write(self.set_manifest())
          m.close()
          print "Manifest written"
          # episode
          m2 = open(self.tmp+"/"+self.episode,'w')
          m2.write(self.set_episode())
          m2.close()
          print "Episode written"
               
     def create_mediapackage(self, name):
          z = zipfile.ZipFile(name, "w",zipfile.ZIP_STORED,True) # store only (DEFAULT)

          # manifest
          m = open(self.tmp+"/manifest.xml", 'w')
          m.write(self.set_manifest())
          m.close()
          z.write(self.tmp+"/manifest.xml","manifest.xml")
          print "Manifest written"

          # episode
          m2 = open(self.tmp+"/"+self.episode,'w')
          m2.write(self.set_episode())
          m2.close()
          z.write(self.tmp+"/"+self.episode,self.episode)
          print "Episode written"

          # tracks
          for i in self.tracks:
               print i.url
               name = os.path.basename(i.url)
               if i.url == name:
                    z.write(self.tmp+"/"+i.url,name)# PATCH when saving folderMP
               else:
                    z.write(i.url,name)

          # for i in self.catalogs:
          #     if i.etype == "dublincore/series":
          #          name = os.path.basename(i.url)
          #          z.write(i.url,name)

          # series
          #m3 = open(self.tmp+"/"+self.series,'w')
          #m3.write(self.set_series())
          #m3.close()
          #z.write(self.tmp+"/"+self.series,self.series)
          z.close      
          print "Mediapackage Created"


     def get_data(self, name="manifest.xml"):
          """Obter os datos do manifest, e despois do episode e o series"""
          manifest = minidom.parse(self.tmp+"/"+name)          
          tracks = manifest.getElementsByTagName("track")
          for i in tracks:
               nome=self.checknget(i,"url")
               tipo=str(i.getAttribute("type"))
               self.add_track(nome, tipo)
               print nome
          
          catalogs = manifest.getElementsByTagName("catalog")
          for i in catalogs:
               nome=self.checknget(i,"url")
               tipo=str(i.getAttribute("type"))
               ref = None
               if i.hasAttribute("ref"):
                    ref=str(i.getAttribute("ref"))
               self.add_catalog(nome, tipo, ref)
               print nome
          
          for i in self.catalogs:               
               if i.etype.count("episode")>0:
                    print "Fetching episode data"
                    # CONSIDER introducir self.tmp en i.url en todo caso
                    episode = minidom.parse(self.tmp+"/"+i.url) 
                    for name in dcterms:
                         self.metadata_episode[name]=self.checknget(episode,"dcterms:"+name)
                         print name+":  "+ str(self.metadata_episode[name])
                         if name=="creation": #FIX en teoria so teremos created
                              self.date=datetime.datetime.strptime(self.metadata_episode[name],"%Y-%m-%dT%H:%M:%SZ")
                         if name=="modified":
                              if self.date==None:
                                   self.date=datetime.datetime.strptime(self.metadata_episode[name],"%Y-%m-%d")
               # elif re.match("series*?",i.ref):
               #     series = minidom.parse(self.tmp+"/"+i.url) 
                    # self.metadata_series[name]=self.checknget(episode,"dcterms:"+name)       

     def checknget(self,archive,name): #CONSIDER sacar a funcion fora da clase
          if archive.getElementsByTagName(name).length != 0:
               sout = archive.getElementsByTagName(name)[0].firstChild.wholeText.strip()
               sout.strip("\n")
               return sout
               
          else:
               return None

     def set_manifest(self):
          """Crear un manifest XML """
          doc = Document()
          mp = doc.createElement("mediapackage") #has oc:mp before
          #mp.setAttribute("xmlns:oc","http://mediapackage.opencastporject.org") 
          mp.setAttribute("id",self.metadata_episode["identifier"]) 
          mp.setAttribute("start",self.metadata_episode["created"])
          # duration its downwards
          doc.appendChild(mp)
          # MEDIA
          media = doc.createElement("media")          
          mp.appendChild(media)
          metadata = doc.createElement("metadata")
          mp.appendChild(metadata)
          # attach = doc.createElement("attachments")

          for t in self.tracks : #cambiar bucle
               track= doc.createElement("track")
               track.setAttribute("id", "track-"+str(self.tracks.index(t)+1))
               track.setAttribute("type", t.etype)
               mime = doc.createElement("mimetype")
               mtext = doc.createTextNode(t.mime) 
               mime.appendChild(mtext)
               url = doc.createElement("url")
               utext = doc.createTextNode(os.path.basename(t.url))
               url.appendChild(utext)
               # checksum type md5
               # size = doc.createElement("size")
               # stext = doc.createTextNode(str(os.path.getsize(t.url)))
               # size.appendChild(stext)
               duration = doc.createElement("duration")               
               comando = "mediainfo -f "+t.url+" | grep Duration | head -n 1 | cut -d ':' -f 2 | cut -d ' ' -f 2 "
               resultado = os.popen(comando).read().strip().split('.')[0]
               mp.setAttribute("duration",resultado)
               dtext = doc.createTextNode(resultado)
               duration.appendChild(dtext)
               # establecer duration con librerias de python
               # create video childs
               track.appendChild(mime)
               track.appendChild(url)
               # add checksum
               # track.appendChild(size)
               track.appendChild(duration)
               media.appendChild(track)

          # METADATA
          for t in self.catalogs:
               cat= doc.createElement("catalog")
               cat.setAttribute("id", "catalog-"+str(self.catalogs.index(t)+1))
               cat.setAttribute("type", t.etype)
               if t.ref != None: 
                    cat.setAttribute("ref", t.ref)              
                    self.episode = t.url
               loc = doc.createElement("url")
               uutext = doc.createTextNode(t.url)
               loc.appendChild(uutext)
               mim = doc.createElement("mimetype")
               mmtext = doc.createTextNode(t.mime)
               mim.appendChild(mmtext)
               cat.appendChild(mim)
               cat.appendChild(loc)
               metadata.appendChild(cat)   
          mp.setAttribute("start",self.date.isoformat())          
          mp.setAttribute("id",self.metadata_episode["identifier"]) 
          mp.setAttribute("xmlns:oc","http://mediapackage.opencastporject.org") 
          # ADD checksum
          # return doc.toprettyxml(indent="   ", newl="\n",encoding="utf-8")    
          return doc.toxml(encoding="utf-8")          
         
     def set_episode(self):
          """Crear un episode XML """
          doc = Document()
          mp = doc.createElement("dublincore")
          mp.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
          mp.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance/")
          mp.setAttribute("xsi:schemaLocation","http://www.opencastproject.org http://www.opencastproject.org/schema.xsd")
          mp.setAttribute("xmlns:dc","http://purl.org/dc/elements/1.1/")
          mp.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
          mp.setAttribute("xmlns:oc", "http://www.opencastproject.org/matterhorn")
          doc.appendChild(mp)
          for name in dcterms :
               if self.metadata_episode.has_key(name):
                    #print name+"    "+self.metadata_episode[name]
                    created = doc.createElement("dcterms:"+name)
                    text = doc.createTextNode(self.metadata_episode[name])
                    created.appendChild(text)
                    mp.appendChild(created)          
          # return doc.toprettyxml(indent="   ",newl="\n",encoding="utf-8") # FIXME meter tabulador non espazos   
          return doc.toxml(encoding="utf-8") #without encoding

     def set_series(self):
          """Crear un series XML """
          doc = Document()
          mp = doc.createElement("dublincore")
          mp.setAttribute("xmlns","http://www.opencastproject.org/xsd/1.0/dublincore/")
          mp.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance/")
          mp.setAttribute("xsi:schemaLocation","http://www.opencastproject.org http://www.opencastproject.org/schema.xsd")
          mp.setAttribute("xmlns:dc","http://purl.org/dc/elements/1.1/")
          mp.setAttribute("xmlns:dcterms","http://purl.org/dc/terms/")
          mp.setAttribute("xmlns:oc", "http://www.opencastproject.org/matterhorn")
          doc.appendChild(mp)
          for name in dcterms :
               if self.metadata_series.haskey(name):
                    created = doc.createElement("dcterms:"+name)
                    text = doc.createTextNode(self.metadata_seriese[name])
                    created.appenChild(text)
                    mp.appendChild(created)          
          # return doc.toprettyxml(indent="   ", newl="\n",encoding="utf-8")
          return doc.toxml(encoding="utf-8") #without encoding

     def ingest(self, host,  usuario="admin", 
                password="opencast", workflow="full"):
          """ Ingest the given tracks and files"""
          endpoint="/ingest/addZippedMediaPackage" #pasar a constante
          mp = self.tmp+"/temporal.zip"
          self.create_mediapackage(mp) #nome aleatorio ou construido
          self.send_zip(mp,host,usuario,password,workflow)

          authinfo = urllib2.HTTPDigestAuthHandler()
          authinfo.add_password("Opencast Matterhorn", host, 
                                usuario, password)

          #http://nightly.opencastproject.org/ingest/addZippedMediaPackage
          #catch exceptions in Track or MP

     def get_content_type(filename):
          return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

     def send_zip(self,filename, host, username="admin", password="opencast", workflow="full"):

          #Autentificacion
          endpoint = '/welcome.html'
          endpoint2="/ingest/addZippedMediaPackage"         
          authinfo = urllib2.HTTPDigestAuthHandler()
          authinfo.add_password( "Opencast Matterhorn", host, username, password)          
          opener = urllib2.build_opener(authinfo)
          urllib2.install_opener(opener)
          request = urllib2.Request('http://' + host + endpoint) 
          request.add_header( 'X-Requested-Auth', 'Digest' );

          item =urllib2.urlopen(request)
          cookie = item.info().getheader('Set-Cookie')
          print item.info()
          # print item.readlines()
          # print cookie[0:-7]
          # ---- addZippedMediaPackage


          BOUNDARY = '----------THE_FORM_BOUNDARY'
          request = urllib2.Request('http://' + host + endpoint2) 
          request.add_header( 'User-agent', 'Galicaster');
          request.add_header( 'Content-Type', 'multipart/form-data; boundary=%s' % BOUNDARY);
          request.add_header( 'Cookie', cookie[0:-7]); 
          # Quito Path de cookie ("Set-Cookie: JSESSIONID=1w2uwmkqam8wb;Path=/")

          L = []
          L.append('\r\n\r\n\r\n')
          L.append('--' + BOUNDARY)
          L.append('Content-Disposition: form-data; name="workflowDefinitionId"')
          L.append('')
          L.append(workflow)
          L.append('--' + BOUNDARY)
          L.append('Content-Disposition: form-data; name="BODY"; filename="data.zip"')
          L.append('Content-Type: application/octet-stream')
          L.append('')
          L.append(open(filename, 'r').read()) #FIXME file in memory
          L.append('--' + BOUNDARY + '--')
          L.append('')
          request.add_data('\r\n'.join(L))

          try:
               item =urllib2.urlopen(request)
               print item.readlines()
          except urllib2.URLError, (err):
               print "URL error(%s)" % (err)
               print err
