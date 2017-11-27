#!/usr/bin/env python

#####################################################
#imports
#####################################################
import os, sys
import logging, logging.handlers
from re import search
from platform import system
import numpy
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas, NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib import rcParams
import extensions.smp as smp
import extensions.map as maps
import extensions.mathematics as calc
from extensions.residual_analysis import residual_analysis
from extensions.menus import HeaderInfo, GraphOptions, SaveOptions, SuperPosition
import wx
from wx.lib.agw.floatspin import FloatSpin
from extensions import mean

#####################################################
#Globals
#####################################################

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    exec_path = os.path.dirname(sys.executable)
elif __file__:
    exec_path = os.path.dirname(__file__)
name = "SnowMicroPyn"
title = "%s - The bit more complex PNT Reader for SnowMicroPen (R) Measurements" %name
version = "0.1.1"
author = "Sascha Grimm"
trademark = u"\u2122"
company = """WSL Institute for Snow and Avalanche Research SLF"""
adress = """Fluelastrasse 11\nCH-7260 Davos"""
contact = "sascha.grimm@slf.ch"
description = """%s is a software to read and analyze SnowMicroPen%s meaurements.
Supported input file format is the binary .pnt."""%(name,trademark)
licence = """
%s is free software; you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version. %s is
distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.""" %(name,name)
try:
    logo = os.path.join(exec_path,"artwork","logo_slf.png")
    icon = os.path.join(exec_path,"artwork","icon.ico")
except:
    pass
copyright = "(C) 2014 - Sascha Grimm"
link = """http://www.slf.ch """ #/ueber/organisation/schnee_permafrost/schneephysik/SnowMicroPen/index_EN"""


#####################################################
#User Interface
#####################################################
class UI(wx.Frame):
    """main user interface"""
    def __init__(self, files, **kwargs):
        wx.Frame.__init__(self, None, -1, size = (800, 600))

        #self.setIcon()
        self.create_menu()
        self.create_status_bar()
        self.create_tool_bar()
        self.create_main_panel()
        self.File = []
        self.current = int(0)
        self.create_plot()
        self.ToggleItems(False)
        self.plotOptions = GraphOptions(self)
        self.saveOptions = SaveOptions(self)
        self.Maximize()
        self.OpenFiles(files)

        self.pathOpen = wx.StandardPaths.Get().GetDocumentsDir()
        self.pathSave = wx.StandardPaths.Get().GetDocumentsDir()

    def setIcon(self):

        tbicon = wx.TaskBarIcon()
        tbicon.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_ICO),"Icon")


    #####################################################
    #menu constructor
    #####################################################
    def create_menu(self):
        """ create menubar with file, data and help menu"""

        self.menu = wx.Menu()
        self.menu.Append(-1,'Item 1')
        self.menu.Append(-1,'Item 2')


        self.menubar = wx.MenuBar()

        #####################################################
        #file menu
        #####################################################
        self.fileMenu = wx.Menu()
        qmo = self.fileMenu.Append(wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnOpen, qmo)
        qms = self.fileMenu.Append(wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSave, qms)
        qmsa = self.fileMenu.Append(wx.ID_SAVEAS, "Save A&ll \tCtrl+Shift+a")
        self.Bind(wx.EVT_MENU, self.OnSaveAll, qmsa)
        qmc = self.fileMenu.Append(wx.ID_CLOSE, "Close File \tCtrl+w")
        self.Bind(wx.EVT_MENU, self.OnClose, qmc)
        qma = self.fileMenu.Append(wx.ID_CLOSE_ALL, "Close All \tCtrl+k")
        self.Bind(wx.EVT_MENU, self.OnCloseAll, qma)

        export = wx.Menu()
        meh = export.Append(wx.ID_ANY, "Header")
        self.Bind(wx.EVT_MENU, self.OnExportHeader, meh)
        mep = export.Append(wx.ID_ANY, "Plot")
        self.Bind(wx.EVT_MENU, self.OnExportPlot, mep)
        med = export.Append(wx.ID_ANY, "Data")
        self.Bind(wx.EVT_MENU, self.OnExportData, med)
        export.AppendSeparator()
        meg = export.Append(wx.ID_ANY, "GPS Data")
        self.Bind(wx.EVT_MENU, self.OnExportGPS, meg)
        men = export.Append(wx.ID_ANY, "Noise, Drift and Offset")
        self.Bind(wx.EVT_MENU, self.OnExportNoise, men)
        mem = export.Append(wx.ID_ANY, "Maximum Forces, Surface and Ground")
        self.Bind(wx.EVT_MENU, self.OnExportForce, mem)
        #mesn = export.Append(wx.ID_ANY, "Shot Noise Parameters")
        #self.Bind(wx.EVT_MENU, self.OnExportShotNoise, mesn)

        self.fileMenu.AppendMenu(100, "&Export", export)

        self.fileMenu.AppendSeparator()

        qmi = wx.MenuItem(self.fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.OnQuit, qmi)
        self.fileMenu.AppendItem(qmi)

        #####################################################
        #Data Menu
        #####################################################
        self.dataMenu = wx.Menu()
        msm = wx.MenuItem(self.dataMenu, 201, "&GPS Map View")
        self.Bind(wx.EVT_MENU, self.OnShowMap,msm)
        msh = wx.MenuItem(self.dataMenu, 202, "Measurement &Info")
        self.Bind(wx.EVT_MENU, self.OnShowHeader,msh)
        mss = wx.MenuItem(self.dataMenu, 203, "&Superpose Measurements")
        self.Bind(wx.EVT_MENU, self.OnSuperpose, mss)
        mshmean = wx.MenuItem(self.dataMenu, 204, "&Range Mean Value, Offset and Drift")
        self.Bind(wx.EVT_MENU, self.OnMean, mshmean)
        #mshhist = wx.MenuItem(self.dataMenu, 205, "&Force Histogram")
        #self.Bind(wx.EVT_MENU, self.OnHist, mshhist)

        self.viewMenu = wx.Menu()

        self.shmf = self.viewMenu.Append(301, "Show Maximum Force","Show Maximum Force", kind=wx.ITEM_CHECK)
        self.shsf = self.viewMenu.Append(302, "Show Surface", "Show Surface", kind=wx.ITEM_CHECK)
        self.shgnd = self.viewMenu.Append(306, "Show Ground", "Show ground on measurements with overload", kind=wx.ITEM_CHECK)
        #self.showLayers = self.viewMenu.Append(307, "Manage Layers", "Manage and show Layers", kind=wx.ITEM_CHECK)
        self.shnd = self.viewMenu.Append(303, "Show Noise, Drift & Offset", "Show Noise, Drift & Offset", kind=wx.ITEM_CHECK)
        self.shgrad = self.viewMenu.Append(304, "Show Gradient", "Show derivation of the force signal", kind=wx.ITEM_CHECK)
        self.shmed = self.viewMenu.Append(305, "Raw Data Minus Median", "Subtract median window from original signal", kind=wx.ITEM_CHECK)

        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shmf)
        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shsf)
        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shnd)
        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shgrad)
        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shgnd)
        self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shmed)
        #self.Bind(wx.EVT_MENU, self.OnLayers, self.showLayers)
        #self.Bind(wx.EVT_MENU, self.UpdateFigure,self.shhn)

        self.dataMenu.AppendItem(msh)
        #self.dataMenu.AppendMenu(300, "&Analysis", self.viewMenu)
        self.dataMenu.AppendItem(mss)
        self.dataMenu.AppendItem(mshmean)
        #self.dataMenu.AppendItem(mshhist)
        self.dataMenu.AppendItem(msm)

        #self.fft = self.dataMenu.Append(wx.ID_ANY,
        #                                "Frequency Analysis",
        #                                "Butterworth low pass filter, automatic calculated cut off frequency by residual analysis.",
        #                                )
        #self.Bind(wx.EVT_MENU, self.OnFilter, self.fft)

        self.dataMenu.AppendSeparator()

        qmp = self.dataMenu.Append(wx.ID_PREFERENCES, "&Graph Options")
        self.Bind(wx.EVT_MENU, self.OnSettings, qmp)

        #####################################################
        #Help Menu
        #####################################################
        self.helpMenu = wx.Menu()
        about = wx.MenuItem(self.helpMenu, wx.ID_ABOUT, "&About... \tF1")
        self.helpMenu.AppendItem(about)
       # help = self.helpMenu.Append(wx.ID_CONTEXT_HELP, "&Help \tF2")

        self.Bind(wx.EVT_MENU, self.OnAbout, about)
       # self.Bind(wx.EVT_MENU, self.OnHelp, help)

        #####################################################
        #set menu bar
        #####################################################

        self.menubar.Append(self.fileMenu, "&File")
        self.menubar.Append(self.dataMenu, "&Data")
        self.menubar.Append(self.viewMenu, "&View")
        self.menubar.Append(self.helpMenu, "&Help")
        self.SetMenuBar(self.menubar)

    def create_status_bar(self):
        """create statub bar"""
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("Welcome to %s Version %s"%(name,version))

    def create_tool_bar(self):
        """create toolbar for most important user actions"""
        self.toolbar = self.CreateToolBar()

        try:
            quit_ico =  wx.Image(os.path.join(exec_path,"artwork","icon_quit.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            save_all_ico = wx.Image(os.path.join(exec_path,"artwork","icon_save_all.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            save_ico = wx.Image(os.path.join(exec_path,"artwork","icon_save.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            new_ico = wx.Image(os.path.join(exec_path,"artwork","icon_open.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            close_all_ico = wx.Image(os.path.join(exec_path,"artwork","icon_clear.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            close_ico = wx.Image(os.path.join(exec_path,"artwork","icon_delete.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            info_ico = wx.Image(os.path.join(exec_path,"artwork","icon_info.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            pref_ico = wx.Image(os.path.join(exec_path,"artwork","icon_properties.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            back_ico = wx.Image(os.path.join(exec_path,"artwork","icon_go-previous.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            forward_ico = wx.Image(os.path.join(exec_path,"artwork","icon_go-next.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        except:
            quit_ico = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR,(24,24))
            save_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR,(24,24))
            save_all_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR,(24,24))
            new_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR,(24,24))
            close_all_ico = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR,(24,24))
            close_ico = wx.ArtProvider.GetBitmap(wx.ART_CLOSE, wx.ART_TOOLBAR,(24,24))
            info_ico = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR,(24,24))
            pref_ico = wx.ArtProvider.GetBitmap(wx.ART_HELP_PAGE, wx.ART_TOOLBAR,(24,24))
            back_ico = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR,(24,24))
            forward_ico = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR,(24,24))

        self.quitTool = self.toolbar.AddSimpleTool(wx.ID_EXIT, quit_ico, "Quit", "Exit Program")
        self.newTool = self.toolbar.AddSimpleTool(wx.ID_OPEN, new_ico, "Open", "Open .pnt File")
        self.closeAllTool = self.toolbar.AddSimpleTool(wx.ID_CLOSE_ALL, close_all_ico, "Close All", "Close all files")
        self.closeTool = self.toolbar.AddSimpleTool(wx.ID_CLOSE, close_ico, "Close", "Close File")
        self.saveTool = self.toolbar.AddSimpleTool(wx.ID_SAVEAS, save_all_ico, "Save All", "Save all open files")
        self.saveSingleTool = self.toolbar.AddSimpleTool(wx.ID_SAVE, save_ico, "Save Single", "Save current file")
        self.infoTool = self.toolbar.AddSimpleTool(wx.ID_ANY, info_ico, "About", "Show %s About" %name)
        self.Bind(wx.EVT_TOOL, self.OnShowHeader, self.infoTool)

        self.menuButton = self.toolbar.AddSimpleTool(wx.ID_PREFERENCES, pref_ico, "Graph Options","Set plot options")

        self.toolbar.AddSeparator()

        self.prevButton = self.toolbar.AddSimpleTool(wx.ID_BACKWARD, back_ico, "Previous Image","Show previous measurement")

        self.choice = wx.Choice(self.toolbar, wx.ID_ANY,size=(200,-1))
        self.choiceTool = self.toolbar.AddControl(self.choice)

        self.nextButton = self.toolbar.AddSimpleTool(wx.ID_FORWARD, forward_ico, "Next Image","Show next measurement")

        self.textbox = wx.TextCtrl(self.toolbar,
                                   wx.TE_CENTRE,
                                   size=(100,-1),
                                   style=wx.TE_PROCESS_ENTER)

        self.textboxTool = self.toolbar.AddControl(self.textbox)
        self.toolbar.AddSeparator()

        self.surfacelabel = wx.StaticText(self.toolbar,-1, 'Surface:')
        self.toolbar.AddControl(self.surfacelabel)
        self.surface = FloatSpin(self.toolbar,wx.ID_ANY,size = (100,-1),value=-1,min_val=0,max_val=2500,increment=0.1,digits=2)
        self.surfaceTool = self.toolbar.AddControl(self.surface)
        self.Bind(wx.EVT_SPINCTRL, self.OnSurface, self.surface)

        self.groundlabel = wx.StaticText(self.toolbar,-1, 'Ground:')
        self.toolbar.AddControl(self.groundlabel)
        self.ground = FloatSpin(self.toolbar,wx.ID_ANY,size = (100,-1),value=-1,min_val=0,max_val=2500,increment=0.1,digits=2)
        self.groundTool = self.toolbar.AddControl(self.ground)
        self.Bind(wx.EVT_SPINCTRL, self.OnGround, self.ground)

        self.Bind(wx.EVT_TOOL, self.OnSettings,self.menuButton)

        self.Bind(wx.EVT_CHOICE, self.OnChoice ,self.choiceTool)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter, self.textboxTool)
        self.Bind(wx.EVT_TOOL, self.OnNext,self.nextButton)
        self.Bind(wx.EVT_TOOL, self.OnPrev,self.prevButton)

        self.toolbar.Realize()

    def create_main_panel(self):
        """the main panel"""
        self.panel = wx.Panel(self)
        self.panel.SetFocus()
        self.SetTitle("%s Version: %s" %(title,version))
        self.SetMinSize((600,400))
        self.Centre()
        self.Show()

    def create_plot(self):

        rcParams["agg.path.chunksize"] = 10000
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.axes = self.fig.add_subplot(111)

        self.plot_toolbar = NavigationToolbar(self.canvas)
        self.plot_toolbar.DeleteToolByPos(8)
        self.plot_toolbar.DeleteToolByPos(7)
        self.plot_toolbar.DeleteToolByPos(6)

        self.plot_toolbar.home = self.onHome

        self.plot_toolbar.Realize()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.plot_toolbar, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.vbox.Add(self.hbox, 0, flag = wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

        self.canvas.mpl_connect('button_press_event', self.OnCanvas)
        self.canvas.mpl_connect('scroll_event', self.OnCanvas)
        self.canvas.mpl_connect('key_press_event', self.OnKey)

        self.plotFlag = False

    def onHome(self,event):
        print "Home"
        self.draw_figure(True, True)

    def OnKey(self, event):
        """deal with keyboard events on canvas"""

        if event.key in ("left","down"):
            self.OnPrev(event)
        elif event.key in ("right","up"):
            self.OnNext(event)

    def OnCanvas(self,event):
        """deal with mouse events on canvas"""

        if event.button == 1:
            x = event.xdata
            y = event.ydata
            status = "x: %.3f mm, y: %.3f N" %(x,y)
            self.updateStatus(status)

        elif event.button == "up" or event.button == "down":
            self.zoom(event)

        if event.button == 1 and event.key == "control":
            self.OnSurface(event, event.xdata)

        if event.button == 1 and event.key == "shift":
            self.OnGround(event, event.xdata)

    def zoom(self, event):
        """zoom in and out of canvas using scroll button"""

        if event.button == "up":
            factor = 0.95
        else:
            factor = 1.05

        curr_xlim = self.axes.get_xlim()
        curr_ylim = self.axes.get_ylim()

        new_width = (curr_xlim[1]-curr_xlim[0])*factor
        new_height= (curr_ylim[1]-curr_ylim[0])*factor

        relx = (curr_xlim[1]-event.xdata)/(curr_xlim[1]-curr_xlim[0])
        rely = (curr_ylim[1]-event.ydata)/(curr_ylim[1]-curr_ylim[0])

        self.axes.set_xlim([event.xdata-new_width*(1-relx),
                    event.xdata+new_width*(relx)])
        self.axes.set_ylim([event.ydata-new_height*(1-rely),
                            event.ydata+new_height*(rely)])
        self.canvas.draw()

        event.guiEvent.GetEventObject().ReleaseMouse()

    def draw_figure(self, show=True, autozoom=True):
        """
        Redraws the figure
        """

        self.axes.clear()

        if self.current not in range(len(self.File)): # actually not (!?) necessary, implemented for Scheebeli
            print "index %d out of range [%d-%d]" %(self.current, 0, len(self.File)-1)
            self.current = len(self.File) -1

        xlim = self.File[self.current].xlim
        ylim = self.File[self.current].ylim
        if xlim != None:
            self.axes.set_xlim(xlim)
            self.axes.set_ylim(ylim)

        x = (self.File[self.current].data[:,0])
        y = (self.File[self.current].data[:,1])

        x_smooth = calc.downsample(x, self.plotOptions.sampling)
        y_smooth = calc.downsample(y, self.plotOptions.sampling)

        if not self.plotOptions.auto_x:
            self.axes.set_xlim(self.plotOptions.xlim[0],self.plotOptions.xlim[1])

        if not self.plotOptions.auto_y:
            self.axes.set_ylim(self.plotOptions.ylim[0],self.plotOptions.ylim[1])

        self.axes.set_xlabel(self.plotOptions.xlabel)
        self.axes.set_ylabel(self.plotOptions.ylabel)

        self.axes.set_title(self.File[self.current].filename+"\n\n")

        if not self.plotOptions.auto_yticks:
            self.axes.yaxis.set_major_locator(MaxNLocator(self.plotOptions.yticks))
        if not self.plotOptions.auto_xticks:
            self.axes.xaxis.set_major_locator(MaxNLocator(self.plotOptions.xticks))

        self.axes.grid(True)

        self.axes.tick_params(labeltop=self.plotOptions.mirrorx,labelright=self.plotOptions.mirrory)

        self.axes.plot(x_smooth, y_smooth,
                       color = self.plotOptions.color,
                       linestyle = self.plotOptions.style,
                       linewidth = self.plotOptions.width
                       )

        if self.shgrad.IsChecked():
            amp = self.File[self.current].header['Samples Dist [mm]']
            grad = calc.downsample(numpy.gradient(y,amp),self.plotOptions.grad_sampling)
            x_grad = calc.downsample(x,self.plotOptions.grad_sampling)
            self.axes.plot(x_grad, grad,
                           color = self.plotOptions.grad_color,
                           linestyle = self.plotOptions.grad_style,
                           linewidth = self.plotOptions.grad_width)

        text = ""

        if self.shsf.IsChecked():
            if self.File[self.current].surface == 0:
                self.File[self.current].surface = calc.GetSurface(self.File[self.current].data[:,0], self.File[self.current].data[:,1])

            surface = self.File[self.current].surface
            self.surface.SetValue(surface)
            self.drawSurface(surface)
            text += "Surface: %.2f mm\n" %surface

        if self.shgnd.IsChecked():
            self.ground.SetValue(self.File[self.current].ground)
            self.drawGround(self.File[self.current].ground)
            text += "Ground: %.2f mm\n" %self.File[self.current].ground

        if self.shmf.IsChecked():
            fmax,xfmax = self.GetMaxForce()
            text += "Max Force: %.2f N at %.2f mm\n" %(fmax,xfmax)

        if self.shnd.IsChecked():
            x_fit,y_fit,m,c,std = calc.linFit(x, y, surface)
            self.axes.plot(x_fit, y_fit, color = "black", ls = "--", linewidth=1)
            self.axes.plot(x_fit, y_fit + std, color = "red", ls = ":", linewidth=2)
            self.axes.plot(x_fit, y_fit - std, color = "red", ls = ":", linewidth=2)
            self.axes.axvline(x_fit[-1],ymax=0.5,color="b",ls = ":")
            text += "Offset: %.3f N\nDrift: %.2e N/m\nNoise: %.2e N\n" %(c, m * 1000, std)


        props = dict(boxstyle="round", facecolor="white")
        if text != "" and not self.plotFlag:
            self.plotFlag = True
            box = self.axes.get_position()
            self.axes.set_position([box.x0, box.y0, box.width * 0.85, box.height])
        elif text == "" and self.plotFlag:
            box = self.axes.get_position()
            self.axes.set_position([box.x0, box.y0, box.width * 1.15, box.height])
            self.plotFlag = False

        #self.axes.text(0.05, 0.9, text, transform=self.axes.transAxes, va="top", bbox=props)
        self.axes.text(1.03, 0.5, text, transform=self.axes.transAxes, va="top", bbox=props)

        if self.plotOptions.logscale:
            self.axes.set_yscale('log')

        self.drawMedian(x_smooth,y_smooth)

        if show: self.canvas.draw()

    def drawMedian(self,x,y):
        if self.shmed.IsChecked():
            x_median, y_median = calc.subtractMedian(x, y, self.plotOptions.median_sampling)
            self.axes.plot(x_median, y_median,
                           color = self.plotOptions.median_color,
                           linestyle = self.plotOptions.median_style,
                           linewidth = self.plotOptions.median_width)

    def drawSurface(self, surface):

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        dx = (xlim[1]-xlim[0])/40
        dy = (ylim[1]-ylim[0])*0.8

        self.axes.text(surface-dx,dy,"Surface",rotation="vertical")
        self.axes.axvline(x=surface,color="r",ls="--")

        self.updateStatus("Surface found at %.2f mm" %surface)

    def drawGround(self, ground):

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        dx = (xlim[1]-xlim[0])/40
        dy = (ylim[1]-ylim[0])*0.8

        self.axes.text(ground-dx,dy,"Ground",rotation="vertical")
        self.axes.axvline(x=ground,color="brown",ls="--")

        self.updateStatus("Surface found at %.2f mm" %ground)

    def saveZoom(self):
        self.File[self.current].xlim = self.axes.get_xlim()
        self.File[self.current].ylim = self.axes.get_ylim()

    def UpdateFigure(self,e):

        self.saveZoom()

        if self.shnd.IsChecked():
            self.shsf.Check(True)

        if self.shsf.IsChecked():
            self.surface.Show()
            self.surfacelabel.Show()
        else:
            self.surface.Hide()
            self.surfacelabel.Hide()

        if self.shgnd.IsChecked():
            self.ground.Show()
            self.groundlabel.Show()
        else:
            self.ground.Hide()
            self.groundlabel.Hide()

        self.draw_figure(autozoom=False)

    def updateIndex(self):

        length = len(self.File)
        if self.current >=  length or self.current < 0:
            self.current = 0
        self.textbox.SetValue("File %d / %d" %(self.current+1,length))

        if length == 0:
            self.textbox.SetValue("File 0 / 0")

        choices = []
        for entry in self.File:
            choices.append(os.path.basename(entry.filename))
        self.choice.SetItems(choices)
        self.choice.SetSelection(self.current)

    def OnQuit(self, e):
        """Quit Event"""

        question="""Do you really want to quit program?"""
        if ask(question):
            self.Close()
            self.Destroy()
            print "User Exit"

        e.Skip()

    def OnOpen(self,e):
        """Open File(s) Event"""
        openFiles = []
        for entry in self.File:
            openFiles.append(entry.filename)
        print "open files: %s" %openFiles

        files = fileDialog(self)
        if files != None:

            pulse_dlg = wx.ProgressDialog("Open Pnt Binaries", "Opening %s, File %d/%d\n" %(files[0],0,len(files)), len(files),self,wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME|wx.PD_SMOOTH)
            i=0

            for entry in files:
                cont,skip = pulse_dlg.Update(i,"Opening %s, File %d/%d\n" %(files[i],i,len(files)))
                if not cont:
                    break
                else:
                    i += 1
                    try:
                        if entry in openFiles:
                            dlg = wx.MessageDialog(self,
                            message = "Following file already open:\n%s\nWon't reload file." %entry,
                            caption = "Info",
                            style = wx.OK | wx.ICON_INFORMATION)
                            dlg.ShowModal()
                            dlg.Destroy()
                        else:
                            data = smp.Pnt(entry)
                            print data.ground
                            data.surface = calc.GetSurface(data.data[:,0], data.data[:,1])
                            data.ground = calc.GetGround(data)
                            data.ylim = None
                            data.xlim = None
                            self.File.append(data)
                    except:
                        dlg = wx.MessageDialog(self,
                                               message = "ERROR: Could not read %s" %entry,
                                               caption = "Error",
                                               style = wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()

            pulse_dlg.Destroy()
            self.statusbar.SetStatusText("Finished open files")
            self.ToggleItems(True)
            self.current = len(self.File)-1
            self.updateIndex()
            self.draw_figure()

        else:
            self.statusbar.SetStatusText("No Files Selected")

        e.Skip()

    def OnClose(self,e):
        """Close single file event"""

        question="""Do you really want to close current File?"""
        if ask(question):
            self.updateStatus("Removed %s from Workspace" %self.File[(self.current)].filename)
            self.File.pop(self.current)
            if len(self.File) == 0:
                self.ToggleItems(False)
                self.current = -1
                self.statusbar.SetStatusText("Ready")
                self.axes.clear()
                self.canvas.draw()
            if self.current >= len(self.File):
                self.current = len(self.File) - 1
            self.updateIndex()

            if len(self.File) > 0:
                self.draw_figure()
            else:
                self.axes.clear()
                self.canvas.draw()
        e.Skip()

    def OnCloseAll(self,e):
        question="""Do you really want to close ALL Files?"""
        if ask(question):
            self.File=[]
            self.current = -1
            self.surface.SetValue(0.0)
            self.axes.clear()
            self.canvas.draw()
            self.updateIndex()
            self.ToggleItems(False)
            self.updateStatus()

        e.Skip()

    def OnNext(self,e):
        self.saveZoom()
        self.current += 1
        self.current %= len(self.File)
        self.updateIndex()
        self.draw_figure()
        self.updateStatus("Selected File %s" %self.File[self.current].filename)

        try:
            e.Skip()
        except:
            pass


    def OnPrev(self,e):
        self.saveZoom()
        self.current-=1
        if self.current < 0:
            self.current = len(self.File)-1
        self.updateIndex()
        self.draw_figure()
        self.updateStatus("Selected File %s" %self.File[self.current].filename)

        try:
            e.Skip()
        except:
            pass

    def OnAbout(self, e):

        info = wx.AboutDialogInfo()
        try:
            info.SetIcon(wx.Icon(logo, wx.BITMAP_TYPE_PNG))
            #info.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_ICO))
        except:
            pass
        info.SetName(name)
        info.SetVersion(version)
        info.SetDescription(description)
        info.SetCopyright(copyright+"\n"+company)
        info.SetWebSite(link)
        info.SetLicence(licence)
        info.AddDeveloper(author)
        info.AddDocWriter(author)
        info.AddArtist(author)
        wx.AboutBox(info)

        e.Skip()

    def OnMean(self,e):
        mean.Drift(self.File[self.current].data[:,0],self.File[self.current].data[:,1])

        e.Skip()

    def OnHist(self,e):
        calc.forceDrops(self.File[self.current].data[:,0],self.File[self.current].data[:,1])

        e.Skip()

    def OnLayers(self, event):
        wx.MessageBox('Not implemented yet', 'Info',
                           wx.OK | wx.ICON_INFORMATION)

    def OnSave(self,e):
        """Save single file Event"""

        if self.saveOptions.ShowModal() == wx.ID_OK:
            dlg = wx.DirDialog(self,
                               message="Select Saving Directory",
                               defaultPath=os.getcwd(),
                               style=wx.DD_DEFAULT_STYLE)

            dlg.SetPath(self.pathSave)
            if dlg.ShowModal() == wx.ID_OK:
                self.pathSave = dlg.GetPath()
                if self.saveOptions.plot():
                    self.SaveGraph(self.pathSave)
                if self.saveOptions.header():
                    self.SaveHeader(self.pathSave)
                if self.saveOptions.data():
                    self.SaveData(self.pathSave,precision = self.saveOptions.Precision())
                if self.saveOptions.shotnoise():
                    self.SaveShotNoise(self.pathSave, window = self.saveOptions.Window(), overlap = self.saveOptions.Overlap() )

            dlg.Destroy()
        e.Skip()

    def OnSaveAll(self,e):
        """Save All Event"""

        if self.saveOptions.ShowModal() == wx.ID_OK:
            dlg = wx.DirDialog(
                self,
                message="Select Saving Directory",
                defaultPath=os.getcwd(),
                style=wx.DD_DEFAULT_STYLE)

            dlg.SetPath(self.pathSave)
            if dlg.ShowModal() == wx.ID_OK:
                self.pathSave = dlg.GetPath()

                pulse_dlg = wx.ProgressDialog("Save All", "Working on %s, File %d/%d" %(self.File[self.current].filename,0,len(self.File)), len(self.File),self,wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME|wx.PD_SMOOTH)
                for i in range(len(self.File)):
                    self.current = ((self.current+1) % len(self.File))
                    self.updateIndex()
                    message = "Working on %s, File %d/%d\n" %(self.File[self.current].filename,i+1,len(self.File))
                    cont,skip = pulse_dlg.Update(i+1,message)
                    if self.saveOptions.plot():
                        self.SaveGraph(self.pathSave)
                    if self.saveOptions.header():
                        self.SaveHeader(self.pathSave)
                    if self.saveOptions.data():
                        self.SaveData(self.pathSave)
                    if self.saveOptions.shotnoise():
                        self.SaveShotNoise(self.pathSave, window = self.saveOptions.Window(), overlap = self.saveOptions.Overlap())

                    if not cont:
                        break

                pulse_dlg.Destroy()
                self.updateStatus("Saved %d Measurements to %s" % (i+1,self.pathSave))

            dlg.Destroy()
            self.draw_figure()
        e.Skip()

    def SaveGraph(self,path = os.getcwd()):

        filename = self.File[self.current].filename
        filename = os.path.basename(filename)
        filename = filename.replace(".pnt","_Graph.pdf")
        filename = os.path.join(path,filename)
        self.draw_figure(False)
        self.canvas.print_figure(filename, dpi = self.dpi)
        self.updateStatus("Saved %s" %filename)

    def SaveHeader(self,path = os.getcwd(),filename = ""):
        if filename == "":
            filename = self.File[self.current].filename
            filename = os.path.basename(filename)
            filename = filename.replace(".pnt","_Header.txt")

        filename = os.path.join(path,filename)
        file = open(filename, "w")
        file.write("#Automatic written Header by %s\n"
                "#%s\n\n" %(name,company))

        for entry, value in sorted(self.File[self.current].header.items()):
            line="%s %s\n" %(entry.ljust(15), str(value))
            file.write(line)

        file.close()
        self.updateStatus("Saved Header to %s" % path)

    def SaveData(self,path=os.getcwd(),filename="", precision = 3):

        if filename == "":
                    filename = self.File[self.current].filename
                    filename = os.path.basename(filename)
                    filename = filename.replace(".pnt","_Data.dat")

        filename = os.path.join(path,filename)

        numpy.savetxt(filename,
                      self.File[self.current].data,
                      delimiter = "\t",
                      newline = "\n",
                      fmt = "%." + "%d" %precision + "f",
                      header="Depth [mm]\tForce[N]")

        self.updateStatus("Saved Data to %s" % path)

    def SaveShotNoise(self,path=os.getcwd(),filename="", window = 2.5, overlap = 50):

        if filename == "":
                    filename = self.File[self.current].filename
                    filename = os.path.basename(filename)
                    filename = filename.replace(".pnt",".shn")

        filename = os.path.join(path,filename)

        numpy.savetxt(filename,
                      calc.getSNParams(self.File[self.current], window, overlap),
                      delimiter = "\t",
                      newline = "\n",
                      fmt = "%3g",
                      header="""Automatic written Shot Noise Parameters by %s %s\n
                      File: %s\n
                      Window: %.2f mm\n
                      Overlap: %.2f\n
                      Lambda\tMedian [N]\tDelta\tL""" %(name,version, self.File[self.current].filename,window,overlap))

        self.updateStatus("Saved Shot Noise Parameters to %s" % path)

    def SaveMaxForce(self,path=os.getcwd(),filename="_MaxForce.txt"):

        filename = os.path.join(path,filename)

        save=[]
        for i in range(len(self.File)):
            surface = "%0.2f" %self.File[i].surface
            ground =  "%0.2f" %self.File[i].ground
            y,x = self.GetMaxForce(i)
            y = "%0.3f"%y
            file = self.File[i].filename
            file = os.path.basename(file)
            save.append([file, surface, ground, y])
        header = "Filename\tSurface [mm]\tGround [mm]\tForce [N]"
        numpy.savetxt(filename, save, "%s", "\t", "\n",header=header)

    def SaveNoise(self,path=os.getcwd(),filename="_Noise.txt"):

        filename = os.path.join(path,filename)

        save=[]
        for i in range(len(self.File)):
            x = self.File[i].data[:,0]
            y = self.File[i].data[:,1]
            surface = self.File[i].surface
            x,y_fit,drift,offset,noise = calc.linFit(x, y, surface)
            file = os.path.basename(self.File[i].filename)
            save.append([file, "%.3g"%offset, "%.3g"%drift, "%.3g"%noise])

        av = numpy.array(save)
        av_offset = numpy.mean(av[:,1].astype(float))
        sd_offset = numpy.std(av[:,1].astype(float))
        av_drift = numpy.mean(av[:,2].astype(float))
        sd_drift = numpy.std(av[:,2].astype(float))
        av_noise = numpy.mean(av[:,3].astype(float))
        sd_noise = numpy.std(av[:,3].astype(float))

        save.append(["Average","%.3g"%av_offset,"%.3g"%av_drift,"%.3g"%av_noise])
        save.append(["Deviation","%.3g"%sd_offset,"%.3g"%sd_drift,"%.3g"%sd_noise])

        header = "Filename\tOffset [N]\tDrift [N/mm]\tNoise [N]"
        numpy.savetxt(filename, save, "%s", "\t", "\n",header=header)

    def GetMaxForce(self, index=-1, surface=0):
        if index == -1:
            index = self.current

        surface = self.File[index].surface

        x = self.File[index].data[:,0]
        y = self.File[index].data[:,1]

        max = numpy.argmax(y)

        self.axes.axvline(x=x[max],color="r",ls="--")

        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        dx = (xlim[1]-xlim[0])/40
        dy = (ylim[1]-ylim[0])*0.8
        self.axes.text(x[max]-dx,dy,"Max Force",rotation="vertical")

        #self.updateStatus("Maximum Force: %.2f N, Penetration Depth: %.2f mm" %(y[max], x[max]-surface))
        self.updateStatus("Maximum Force: %.2f N" %y[max])

        return [y[max], x[max]-surface]

    def GetHardness(self, index=-1, df=0.05):

        if index == -1:
            index = self.current
        surface = self.File[index].surface

        x = self.File[index].data[:,0]
        y = self.File[index].data[:,1]

        xHardness = []
        yHardness = []

        for force in self.hardness:
            try:
                index = numpy.where(y>=force+df)[0][0]
                y_temp = y[:index]
                delta = numpy.abs(y_temp-force)
                minimum = numpy.argmin(delta)
                xmin = x[minimum]
                ymin = y[minimum]

                self.axes.axvline(x=xmin,color="y",ls="--")

            except:
                xmin = None
                ymin = None

            if xmin != None:
                xHardness.append(xmin-surface)
            else:
                xHardness.append(None)

            yHardness.append(ymin)

        return[xHardness,yHardness]

    def SaveHardness(self,path=os.getcwd(),filename="_Hardness.txt"):

        filename = os.path.join(path,filename)

        save = []
        for i in range(len(self.File)):
            x,y = self.GetHardness(i)
            file = self.File[i].filename
            file = os.path.basename(file)
            line = "\t".join((str(w) for w in x))
            save.append([file,line])

        header = "Filename\tDistance [mm] " + numpy.array2string(self.hardness, max_line_width=200, separator="N\t")
        numpy.savetxt(filename, save, "%s", "\t", "\n", header = header)

    def OnExportPlot(self,e):

        file_choices = "PDF (*.pdf)|*.PDF"
        filename = self.File[self.current].filename.replace(".pnt","_Graph.pdf")

        dlg = wx.FileDialog(
            self,
            message = "Save Plot as...",
            defaultDir = os.path.dirname(filename),
            defaultFile = os.path.basename(filename),
            wildcard = file_choices,
            style = wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = os.path.dirname(path)
            self.SaveGraph(path)

        dlg.Destroy()

    def OnExportHeader(self,e):

        file_choices = "TXT (*.txt)|*.txt"
        filename = self.File[self.current].filename.replace(".pnt","_Header.txt")

        dlg = wx.FileDialog(
            self,
            message = "Save Header as...",
            defaultDir = os.path.dirname(filename),
            defaultFile = os.path.basename(filename),
            wildcard = file_choices,
            style = wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            filename = os.path.basename(path)
            path = os.path.dirname(path)
            self.SaveHeader(path, filename)

        dlg.Destroy()

    def OnExportData(self,e):

        file_choices = "DAT (*.dat)|*.dat"
        filename = self.File[self.current].filename.replace(".pnt","_Data.dat")

        dlg = wx.FileDialog(
            self,
            message="Save data as...",
            defaultDir=os.path.dirname(filename),
            defaultFile=os.path.basename(filename),
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            filename = os.path.basename(path)
            path = os.path.dirname(path)
            self.SaveData(path, filename)
        dlg.Destroy()

    def OnExportNoise(self,e):

        file_choices = "DAT (*.dat)|*.dat"

        dlg = wx.FileDialog(
            self,
            message="Save Noise, Drift and Offset as...",
            defaultDir=os.getcwd(),
            defaultFile="Noise.dat",
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPath()
            filename = os.path.basename(file)
            path = os.path.dirname(file)
            self.SaveNoise(path,filename)
            self.updateStatus("Wrote Noise, Offset and Drift to %s" %file)

        dlg.Destroy()
        self.draw_figure()

    def OnExportForce(self,e):

        file_choices = "DAT (*.dat)|*.dat"

        dlg = wx.FileDialog(
            self,
            message="Save Maximum Forces, Surface and Ground Levels as...",
            defaultDir=os.getcwd(),
            defaultFile="MaxForce.dat",
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPath()
            filename = os.path.basename(file)
            path = os.path.dirname(file)
            self.SaveMaxForce(path,filename)
            self.updateStatus("Wrote Forces to %s" %file)
        dlg.Destroy()

    def OnExportGPS(self,e):

        file_choices = "COORD (*.coord)|*.COORD"

        dlg = wx.FileDialog(
            self,
            message="Save Coordinates as...",
            defaultDir=os.getcwd(),
            defaultFile="SMP_Coordinates.coord",
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            f = open(path, "w")
            f.write("#Automatic written Coordinates by %s\n"
                "#%s\n\n"
                "#Filename\tLongitude\tLatitude\tPdop\n" %(name,company))

            for i in range(len(self.File)):
                line = "%s\t%f\t%f\t%.2f\n" %(os.path.basename(self.File[i].filename),
                                              self.File[i].header["Longitude"],
                                              self.File[i].header["Latitude"],
                                              self.File[i].header["PDOP"])
                f.write(line)
            f.close()

        dlg.Destroy()

        self.updateStatus("Wrote GPS Data to %s" %path)

    def OnExportShotNoise(self,e):
        file_choices = "SHN (*.shn)|*.shn"

        dlg = wx.FileDialog(
            self,
            message="Save Shot Noise Parameters...",
            defaultDir=os.getcwd(),
            defaultFile="ShotNoise.shn",
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPath()
            filename = os.path.basename(file)
            path = os.path.dirname(file)
            self.SaveShotNoise(path,filename)
            self.updateStatus("Wrote Shot Noise Parameters to %s" %file)

    def OnTextEnter(self, e):
        self.saveZoom()
        regex = self.textbox.GetValue()
        self.current = int(search("\d+",regex).group())-1
        self.updateIndex()
        self.draw_figure()

    def OnChoice(self, e):
        self.saveZoom()
        self.current = self.choice.GetCurrentSelection()
        self.updateIndex()
        self.draw_figure()

    def OnSettings(self,e):
        self.saveZoom()
        self.plotOptions.Show()

    def Txt2Number(self, string=""):
        return float(search("\d+(\.\d+)?",string.group()))

    def OnShowMap(self,e):
        maps.Map(self,-1,self.File)

    def OnShowHeader(self,e):
        info = HeaderInfo(self,-1,self.File[self.current].header)
        info.Show()

    def OnSuperpose(self,e):
        SuperPosition(self,self.File)

    def OnSurface(self,e, surface = None):
        self.saveZoom()
        data = self.File[self.current].data
        max_x = numpy.max(data[:,0])
        if surface == None:
            surface = self.surface.GetValue()
        if  surface > max_x:
            self.surface.SetValue(max_x)
            self.File[self.current].surface = max_x
        elif surface == 0.0:
            self.File[self.current].surface = calc.GetSurface(data[:,0], data[:,1])
        else:
            self.File[self.current].surface = surface
        self.draw_figure(autozoom=False)

    def OnGround(self,e, ground = None):
        self.saveZoom()
        data = self.File[self.current]
        max_x = numpy.max(data.data[:,0])
        if ground == None:
            ground = self.ground.GetValue()
        if  ground > max_x or ground <= 0:
            self.ground.SetValue(max_x)
            self.File[self.current].ground = max_x
        elif ground < data.surface:
            self.File[self.current].ground = data.surface + 1
        else:
            self.File[self.current].ground = ground
        self.draw_figure(autozoom=False)

    def OnFilter(self,e):
        """Filter Event. Call Low Pass Filter """
        self.saveZoom()
        data = self.File[self.current].data
        f = 1/self.File[self.current].header["Samples Dist [mm]"]
        residual_analysis(data[:,1], freq=f, show=True,)
        self.draw_figure(autozoom=False)

        e.Skip()

    def updateStatus(self,status="Ready"):
        self.statusbar.SetStatusText(status)

    def ToggleItems(self, enable=False):
        self.fileMenu.Enable(wx.ID_CLOSE, enable)
        self.fileMenu.Enable(wx.ID_SAVE, enable)
        self.fileMenu.Enable(wx.ID_CLOSE_ALL, enable)
        self.fileMenu.Enable(100,enable)
        self.fileMenu.Enable(wx.ID_SAVEAS,enable)
        self.dataMenu.Enable(201,enable)
        self.dataMenu.Enable(202,enable)
        self.dataMenu.Enable(203,enable)
        self.dataMenu.Enable(204,enable)
        self.dataMenu.Enable(205,enable)
        self.viewMenu.Enable(301,enable)
        self.viewMenu.Enable(302,enable)
        self.viewMenu.Enable(303,enable)
        self.viewMenu.Enable(304,enable)
        self.viewMenu.Enable(305,enable)
        self.viewMenu.Enable(306,enable)
        self.viewMenu.Enable(307,enable)
        self.dataMenu.Enable(wx.ID_PREFERENCES,enable)
        #self.dataMenu.Enable(self.fft.GetId(),enable)
        self.plot_toolbar.Enable(enable)
        self.textbox.Enable(enable)
        self.toolbar.EnableTool(wx.ID_CLOSE,enable)
        self.toolbar.EnableTool(wx.ID_CLOSE_ALL,enable)
        self.toolbar.EnableTool(wx.ID_SAVE,enable)
        self.toolbar.EnableTool(wx.ID_SAVEAS,enable)
        self.choice.Enable(enable)
        self.toolbar.EnableTool(wx.ID_FORWARD,enable)
        self.toolbar.EnableTool(wx.ID_BACKWARD,enable)
        self.toolbar.EnableTool(self.infoTool.GetId(),enable)
        self.toolbar.EnableTool(wx.ID_PREFERENCES,enable)

        if self.shsf.IsChecked() and enable:
            self.surface.Show()
            self.surfacelabel.Show()

        else:
            self.surface.Hide()
            self.surfacelabel.Hide()

        if self.shgnd.IsChecked() and enable:
            self.ground.Show()
            self.groundlabel.Show()

        else:
            self.ground.Hide()
            self.groundlabel.Hide()

    def OpenFiles(self,files):
        if len(files) != 0:
            print "passed files: %s" %files
            for entry in files:
                try:
                    data = smp.Pnt(entry)
                    data.surface = calc.GetSurface(data.data[:,0], data.data[:,1])
                    data.ground = calc.GetGround(data)
                    data.ylim = None
                    data.xlim = None
                    self.File.append(data)
                except:
                    dlg = wx.MessageDialog(self,
                                           message = "ERROR: Could not read %s" %entry,
                                           caption = "Error",
                                           style = wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()

            self.statusbar.SetStatusText("Read %d .pnt files" %len(files))
            self.ToggleItems(True)
            self.current = len(self.File)-1
            self.updateIndex()
            self.draw_figure()

def ask(question, caption = "Confirm"):
    """show yes/no dialog"""
    dlg = wx.MessageDialog(None, question, caption, wx.YES_NO | wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result

def fileDialog(self):
    """Open File Dialog"""

    filters = "SMP files (*.pnt)|*.pnt"
    dlg = wx.FileDialog( None,
                         message = "Select SMP binaries...",
                         wildcard = filters,
                         style = wx.OPEN | wx.MULTIPLE |wx.FD_CHANGE_DIR)
    print("Selected Files:\n")
    dlg.SetDirectory(self.pathOpen)
    if dlg.ShowModal() == wx.ID_OK:
        selected = dlg.GetPaths()
        for selection in selected:
            print(""), selection
    else:
        return None
        print("Nothing selected")
    dlg.Destroy()

    try:
        self.pathOpen = os.path.dirname(selected[0])
    except:
        pass
    return selected

def getVersions():
    """
    get numpy, matpltolib, wx, and SnowMicroPyn versions for debugging
    """
    versions = {"numpy":numpy.__version__,
                "wx": wx.__version__,
                "mpl": mpl.__version__,
                "SnowMicroPyn":version}
    return versions

class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

def __initLogger__():
    """
    initialize logger
    return logger object
    """

    log = logging.getLogger('SnowMicroPynLog')
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(os.path.join(exec_path,".SnowMicroPyn.log"), maxBytes=(1048576*5), backupCount=2)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    #redirect out to logfile
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    return log

if __name__ == "__main__":
    """main application"""
    logger = __initLogger__()

    print "starting %s version %s" %(name, version)
    opsys = system()
    print("%s operating system detected" %opsys)
    print "using versions: %s" %getVersions()
    app = wx.App()
    print "wx app created"
    UI(sys.argv[1:])
    if "Darwin" in opsys:
        app.SetMacSupportPCMenuShortcuts(True)
    app.MainLoop()
