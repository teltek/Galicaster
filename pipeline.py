epi="/dev/video1"
hau="/dev/video0"
dhau="/dev/video32"


class Pipeline:
    def get(name,file0,file1):
        if name == "new":
            return Pipeline.getNew(file0,file1)
        if name == "default":
            return Pipeline.getDefault(file0,file1)
        if name == "dev":
            return Pipeline.getDev(file0,file1)
        if name == "desktop":
            return Pipeline.getDesktop(file0,file1)
        if name == "only":
            return Pipeline.getOnly(file0,file1)
        if name == "only2":
            return Pipeline.getOnly2(file0,file1)
        if name == "vumeter":
            return Pipeline.getVumeter(file0,file1)
        if name == "audio":
            return Pipeline.getAudio(file0,file1)
        if name == "improved":
            return Pipeline.getImproved(file0,file1)



    def getDefault(file0, file1):
        """Pipeline por defecto en OC-MH. Usa tarjeta VGA2USV y hauppauge."""
        pipestr = (
            ' filesrc location=/dev/video1 name=CAM ! tee name=aud ! '
            ' mpegdemux ! audio/mpeg ! queue name=q1 ! mux2. '
            ' v4lsrc device=/dev/video2 name=VID ! tee name=epi ! ' 
            ' ffmpegcolorspace ! ffenc_mpeg2video ! queue name=q2 ! mux2. '            
            ' v4l2src device=/dev/video33 name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' epi. ! queue name=queue_epi ! ffmpegcolorspace ! xvimagesink name=pre2 '
            #' vum. ! queue ! decodebin ! monoscope ! fakesink name=vumetro '
            #' vum. ! queue ! filesink location=' + self.files[2] +''                
            ' aud. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 +
            ' mpegtsmux name=mux2 ! valve name=valvula2 drop=false ! filesink name=record2 location=' + file1 ) 
            #' alsasrc name=voz ! audioconvert ! lamemp3enc target=bitrate cbr=true bitrate=128 ! '
            #' tee name=t ! queue ! mux. t. ! queue ! mux2. '
        return pipestr

    def getNew(file0, file1):
        """Pipeline de desarrollo para o bug #145"""
        pipestr = (
            ' filesrc location=/dev/video1 name=CAM ! tee name=tcam ! '
            ' mpegdemux ! audio/mpeg ! queue name=qaudio ! valve name=valvula2 drop=false mux2. '
            ' v4lsrc device=/dev/video2 name=VID ! tee name=tscr ! ' 
            ' ffmpegcolorspace ! ffenc_mpeg2video ! queue name=qepi ! valve name=valvula3 drop=false ! mux2. '            
            ' v4l2src device=/dev/video33 name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tscr. ! queue name=queue_epi ! ffmpegcolorspace ! xvimagesink name=pre2 '
            #' vum. ! queue ! decodebin ! monoscope ! fakesink name=vumetro '
            #' vum. ! queue ! filesink location=' + self.files[2] +''                
            ' tcam. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 +
            ' mpegtsmux name=mux2 ! filesink name=record2 location=' + file1 ) 
            #' alsasrc name=voz ! audioconvert ! lamemp3enc target=bitrate cbr=true bitrate=128 ! '
            #' tee name=t ! queue ! mux. t. ! queue ! mux2. '
        return pipestr

    def getVumeter(file0, file1):
        """Pipeline de desarrollo para o bug #145"""
        time=100*1000*1000 # 100 ms
        interval = str(time)
        
        pipestr = (
            ' filesrc location=/dev/video1 name=CAM ! tee name=tcam ! '
            ' mpegdemux ! audio/mpeg ! tee name=audio ! queue name=qaudio ! valve name=valvula2 drop=false mux2. '
            ' v4lsrc device=/dev/video2 name=VID ! tee name=tscr ! ' 
            ' ffmpegcolorspace ! ffenc_mpeg2video ! queue name=qepi ! valve name=valvula3 drop=false ! mux2. '            
            ' v4l2src device=/dev/video33 name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tscr. ! queue name=queue_epi ! ffmpegcolorspace ! xvimagesink name=pre2 '
             ' audio. ! queue ! flump3dec name=flump3dec ! level name=VUMETER message=true interval='+ interval +' ! pulsesink name=pre3 '
            # ' tcam. queue ! decodebin2 ! autoaudiosink name=pre3 '
            ' tcam. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 +
            ' mpegtsmux name=mux2 ! filesink name=record2 location=' + file1 ) 
            # ' alsasrc name=voz ! audioconvert ! lamemp3enc target=bitrate cbr=true bitrate=128 ! '
            # ' tee name=t ! queue ! mux. t. ! queue ! mux2. '

        return pipestr   

# ESTAS SON AS 2 pipelines BOAS
    def getAudio(file0, file1):
        """Pipeline de desarrollo para o bug #145"""
        time=100*1000*1000 # 100 ms
        interval = str(time)  
        pipestr = (
            ' filesrc location='+hau+' name=CAM ! tee name=tcam ! queue name=qaudio !  mpegdemux ! audio/mpeg ! '
            ' flump3dec ! level name=VUMETER message=true interval='+ interval +' ! audioconvert ! audioresample ! autoaudiosink name=pre3 '            
            ' v4lsrc device='+epi+' name=VID ! videorate silent=true ! video/x-raw-yuv,framerate=10/1 ! tee name=tscr ! queue ! ffmpegcolorspace ! xvimagesink name=pre2 ' 
            ' v4l2src device='+dhau+' name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tcam. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 +' '
            ' tscr. ! queue ! ffmpegcolorspace ! ffenc_mpeg2video ! valve name=valvula2 drop=false ! '
            ' mpegtsmux name=mux2 ! filesink name=record2 location=' + file1 ) 
        return pipestr 

    def getImproved(file0, file1):
        """Pipeline de desarrollo para o bug #145"""
        time=100*1000*1000 # 100 ms
        interval = str(time)  
        pipestr = (
            ' filesrc location='+hau+' name=CAM ! tee name=tcam ! queue name=qaudio !  mpegdemux ! audio/mpeg ! '
            ' flump3dec ! level name=VUMETER message=true interval='+ interval +' ! audioconvert ! audioresample ! autoaudiosink name=pre3 '            
            ' v4lsrc device='+epi+' name=VID ! tee name=tscr ! queue ! ffmpegcolorspace ! xvimagesink name=pre2 ' 
            ' v4l2src device='+dhau+' name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tcam. ! queue ! valve name=valvula1 drop=false !  filesink name=record1 location=' + file0 +' '
            ' tscr. ! queue !  videorate silent=true ! ffmpegcolorspace ! xvidenc ! valve name=valvula2 drop=false ! '
            ' avimux name=mux2 ! filesink name=record2 location=' + file1 ) 
        return pipestr 

    def getOnly2(file0,file1):
        """Pipeline que solo recibe senhal de la Hauppage"""
        time=100*1000*1000 # 100 ms
        interval = str(time)     
        pipestr = (
            ' filesrc location='+hau+' name=CAM ! tee name=tcam ! queue ! decodebin2 ! '
            ' level name=VUMETER message=true interval='+ interval +' ! pulsesink name=pre3 '
            ' v4l2src device='+dhau+' name=CAM_RAW ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tcam. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 )
        return pipestr


    def getOnly(file0,file1):
        """Pipeline que solo recibe senhal de la Hauppage"""
        pipestr = (
            ' filesrc location=/dev/video1 name=CAM ! tee name=tcam ! '
            ' mpegdemux ! audio/mpeg ! queue name=qaudio ! valve name=valvula2 drop=false mux2. '
            ' v4l2src device=/dev/video33 name=CAM_RAW ! queue name=queue33 ! ffmpegcolorspace ! xvimagesink name=pre1 '
            ' tcam. ! queue ! valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 )
        return pipestr
        
    def getDev(file0, file1):
        """Pipeline de prueba para desarrollo. Se usa videotestsrc y audiotestsrc."""
        # FIXME Falta audio
        pipestr = (
            ' videotestsrc pattern=snow name=CAM ! tee name=tee_cam ! xvimagesink name=pre1 '
            ' tee_cam. ! queue ! ffmpegcolorspace ! ffenc_mpeg2video ! queue ! mpegtsmux ! '
            ' valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 + 
            ' videotestsrc name=VID ! tee name=tee_vid ! xvimagesink name=pre2 '
            ' tee_vid. ! queue ! ffmpegcolorspace ! ffenc_mpeg2video ! queue ! mpegtsmux  ! '
            ' valve name=valvula2 drop=false ! filesink name=record2 location=' + file1 ) 
        return pipestr

    def getDesktop(file0, file1):
        """Pipeline de captura de un escritorio y una Webcam."""
        # FIXME Falta audio
        pipestr = (
            ' v4l2src name=CAM ! tee name=tee_cam ! xvimagesink name=pre1 '
            ' tee_cam. ! queue ! ffmpegcolorspace ! ffenc_mpeg2video ! queue ! mpegtsmux ! '
            ' valve name=valvula1 drop=false ! filesink name=record1 location=' + file0 + 
            ' ximagesrc name=VID ! tee name=tee_vid ! ffmpegcolorspace ! xvimagesink name=pre2 '
            ' tee_vid. ! queue ! ffmpegcolorspace ! ffenc_mpeg2video ! queue ! mpegtsmux  ! '
            ' valve name=valvula2 drop=false ! filesink name=record2 location=' + file1 ) 
        return pipestr
    def getPipes():
        return ["default", "dev", "new", "desktop"]
   
    get = staticmethod(get)
    getAudio = staticmethod(getAudio)
    getImproved = staticmethod(getImproved)
    getDev = staticmethod(getDev)
    getDefault = staticmethod(getDefault)
    getDesktop = staticmethod(getDesktop)
    getNew = staticmethod(getNew)
    getVumeter = staticmethod(getVumeter)
    getOnly = staticmethod(getOnly)
    getOnly2 = staticmethod(getOnly2)
    getPipes = staticmethod(getPipes)
