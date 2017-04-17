#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts
import v4l2
import os, re

V4L1_DRIVER_TYPE = 0x0001
V4L2_DRIVER_TYPE = 0x0002

class Capture:
    def __init__(self,dev):
        self.driver = V4L2_DRIVER_TYPE
        self.fichero = dev
        self.devfd = open(dev, 'rw')
        cp = v4l2.v4l2_capability()
        
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_QUERYCAP, cp)
        except:
            print "EL DISPOSITIVO " + dev + " ES V4L1"
            comando = os.popen("dov4l -q -d " + dev)
            self.driver = V4L1_DRIVER_TYPE
            def fcap(cad): return (re.search("Canonical|Image size|input name",cad))
            datos = filter(fcap,comando.readlines())
            for line in datos:
                if (line.find("interface:") != -1):
                    self.name = line[line.find("interface:")+11:]
                elif (line.find("Image size") != -1):
                    resol = line[line.find(":")+2:]
                    lresol = resol.split(",")
                    self.width = lresol[0]
                    self.height = lresol[1]
                else:
                    self.iname = line[line.find(":")+2:]
            return
        
        self.name = cp.card
        self.capabilities = cp.capabilities
        return


    
    def getPipeSrc(self):
        if (self.getFormatDescription() == "MPEG"):
            return (" filesrc location=" + self.fichero + " ! queue ! mpegpsdemux ! mpegvideoparse" + " ! ")
        elif (self.driver == V4L2_DRIVER_TYPE):
            return (" v4l2src device=" + self.fichero + " ! ")
        else:
            return (" v4lsrc device=" + self.fichero + " ! ")


    def getPipeDec(self):
        if (self.getFormatDescription() == "MPEG"):
            return (" mpeg2dec !")
        else:
            return (" ")
        

    def getPipeFileSink(self,name_file):
        comun = " mpegtsmux ! filesink location=" + name_file + " sync=false "
        if (self.getFormatDescription() == "MPEG"):
            return (comun)
        else:
            return (" ffmpegcolorspace ! ffenc_mpeg2video   ! " + comun)


    def isV4l2(self):
        return (self.driver == V4L2_DRIVER_TYPE)

        
    def getInputs(self):
        if (self.driver == V4L1_DRIVER_TYPE):
            return ""
        inputs = []
        index = 0
        while True:
            v4in = v4l2.v4l2_input()
            v4in.index = index
            try:
                v4l2.ioctl(self.devfd,v4l2.VIDIOC_ENUMINPUT, v4in)
            except:
                break
            inputs.append(v4in)
            index=index + 1
        return inputs

    def setInput(self,index):
        if (self.driver == V4L1_DRIVER_TYPE):
            return ""
        v4in = v4l2.v4l2_input()
        v4in.index=index
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_S_INPUT, v4in)
        except:
            print "Error en la seleccion de entrada"


    
    def getStds(self):
        if (self.driver == V4L1_DRIVER_TYPE):
            return ""
        stds = []
        index = 0
        while True:
            v4in = v4l2.v4l2_standard()
            v4in.index = index
            try:
                v4l2.ioctl(self.devfd,v4l2.VIDIOC_ENUMSTD, v4in)
            except:
                break
            stds.append(v4in)
            index=index + 1
        return stds


    def setStd (self,index):
        if (self.driver == V4L1_DRIVER_TYPE):
            return ""
        v4in = v4l2.v4l2_standard()
        v4in.index=index
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_S_STD, v4in)
        except:
            print "Error en la seleccion de Estandar"
            


    def getFormats(self):
        if (self.driver == V4L1_DRIVER_TYPE):
            print "DRIVER DE TIPO V4L"
            return ""

        if (not(self.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE)):
            print "ESTA ENTRADA DE VIDEO NO TIENE CAPACIDAD DE NEGOCIAR FORMATOS"
            return ""
        
        self.fmts = []
        index = 0
        while True:
            v4fmt = v4l2.v4l2_fmtdesc()
            v4fmt.index = index
            v4fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
            try:
                v4l2.ioctl(self.devfd,v4l2.VIDIOC_ENUM_FMT, v4fmt)
            except:
                break
            self.fmts.append(v4fmt)
            index=index + 1
        return self.fmts
    

    def getCurrentFormat(self,type):
        if (self.driver == V4L1_DRIVER_TYPE):
            print "DRIVER DE TIPO V4L"
            return ""
        
        v4fmt = v4l2.v4l2_fmtdesc()
        v4fmt.index = 1
        v4fo = v4l2.v4l2_format()
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_ENUM_FMT, v4fmt)
        except:
            print "Error en la lectura del formato de entrada"
        print "Type devuelto" + str(v4l2.v4l2_buf_type[v4fmt.type])
        v4fo.type = v4l2.v4l2_buf_type[v4fmt.type]
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_G_FMT, v4fo)
        except:
            print "Error en la lectura del formato de entrada"
        return v4fo
        

    def getFormatDescription (self):
        if (self.driver == V4L1_DRIVER_TYPE):
            return "RAW"
        return self.fmts[self.indexFormat].description


    

    def setFormat (self,index):
        if (self.driver == V4L1_DRIVER_TYPE):
            return ""
        
        if (not(self.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE)):
            print "ESTA ENTRADA DE VIDEO NO TIENE CAPACIDAD DE NEGOCIAR FORMATOS"
            return ""

        v4fmt = v4l2.v4l2_format()
        v4fmt.type = self.fmts[index].type

        self.indexFormat = index
        
        try:
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_G_FMT, v4fmt)
            v4fmt.fmt.pixelformat = self.fmts[index].pixelformat
            v4fmt.fmt.pix.width = 720
            v4fmt.fmt.pix.height = 576
            v4l2.ioctl(self.devfd,v4l2.VIDIOC_S_FMT, v4fmt)
            print "Cambiado formato a: " + self.fmts[index].description
        except:
            print "Error en la seleccion de formato para: " + self.fichero
        return
  
        
if __name__ == '__main__':

    #leemos dispositivos de video del directorio /dev
    dirlist = os.listdir("/dev/")
    def fmatch(cad): return (re.match("video\d+",cad))
    
    captures = {}
    for d in filter(fmatch,dirlist):
        captures["/dev/"+d]=Capture("/dev/"+d)

    for c in captures:
        print "DATOS PARA LA CAPTURADORA: " + captures[c].name
        captures[c].setInput(1)
        captures[c].setStd(3)
        formats = captures[c].getFormats()
    captures["/dev/video1"].setFormat(8)
    captures["/dev/video2"].setFormat(0)
        
