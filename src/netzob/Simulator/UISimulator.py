#!/usr/bin/python
# -*- coding: utf-8 -*-

#+---------------------------------------------------------------------------+
#|         01001110 01100101 01110100 01111010 01101111 01100010             | 
#+---------------------------------------------------------------------------+
#| NETwork protocol modeliZatiOn By reverse engineering                      |
#| ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+
#| @license      : GNU GPL v3                                                |
#| @copyright    : Georges Bossert and Frederic Guihery                      |
#| @url          : http://code.google.com/p/netzob/                          |
#| ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+
#| @author       : {gbt,fgy}@amossys.fr                                      |
#| @organization : Amossys, http://www.amossys.fr                            |
#+---------------------------------------------------------------------------+

#+---------------------------------------------- 
#| Global Imports
#+----------------------------------------------
import gtk
import pygtk
pygtk.require('2.0')
import logging
import os

#+---------------------------------------------------------------------------+
#| Related third party imports
#+---------------------------------------------------------------------------+
from xml.etree import ElementTree

#+---------------------------------------------- 
#| Local Imports
#+----------------------------------------------
from ..Common import ConfigurationParser
from . import XDotWidget
from ..Common.MMSTD.Tools.Parsers.MMSTDParser import MMSTDXmlParser
from ..Common.MMSTD.Actors.Network import NetworkServer
from ..Common.MMSTD.Actors.Network import NetworkClient

#+---------------------------------------------- 
#| Configuration of the logger
#+----------------------------------------------
loggingFilePath = ConfigurationParser.ConfigurationParser().get("logging", "path")
logging.config.fileConfig(loggingFilePath)

#+---------------------------------------------- 
#| UISimulator :
#|     GUI for the simulation of actors
#| @author     : {gbt,fgy}@amossys.fr
#| @version    : 0.2
#+---------------------------------------------- 
class UISimulator:
    
    
    #+---------------------------------------------- 
    #| Called when user select a new trace
    #+----------------------------------------------
    def new(self):
        pass

    def update(self):
        pass

    def clear(self):
        pass

    def kill(self):
        pass
    
    def save(self, file):
        self.log = logging.getLogger('netzob.Simuator.UISimulator.py')
        self.log.warn("The simulation process cannot be saved for the moment")
        
    
    #+---------------------------------------------- 
    #| Constructor :
    #| @param netzob: the netzob main class
    #+----------------------------------------------   
    def __init__(self, netzob):
        # create logger with the given configuration
        self.log = logging.getLogger('netzob.Simulator.UISimulator.py')
        self.netzob = netzob
        
        self.actors = []
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Main panel
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.panel = gtk.Table(rows=5, columns=2, homogeneous=False)
        self.panel.show()
        
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Table hosting the form for a new actor
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.tableFormNewActor = gtk.Table(rows=4, columns=4, homogeneous=True)
        
        # Actor's name
        label_actorName = gtk.Label("Actor's name : ")
        label_actorName.show()
        self.entry_actorName = gtk.Entry()
#        self.entry_actorName.set_width_chars(50)
        self.entry_actorName.set_text("")
        self.entry_actorName.show()
        self.tableFormNewActor.attach(label_actorName, 0, 1, 0, 1, xoptions=gtk.FILL | gtk.EXPAND, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.entry_actorName, 1, 2, 0, 1, xoptions=gtk.FILL | gtk.EXPAND, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)

        # Available grammars
        label_grammar = gtk.Label("Grammar : ")
        label_grammar.show()
        self.combo_grammar = gtk.combo_box_entry_new_text()
        self.combo_grammar.set_model(gtk.ListStore(str))
        possible_grammars = self.getAvailableGrammars()
        for i in range(len(possible_grammars)):
            self.combo_grammar.append_text(possible_grammars[i])
        self.combo_grammar.show()
        self.tableFormNewActor.attach(label_grammar, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.combo_grammar, 1, 2, 1, 2, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        
        # Type of actor
        label_typeOfActor = gtk.Label("Type of actor : ")
        label_typeOfActor.show()
        self.combo_typeOfActor = gtk.combo_box_entry_new_text()
        self.combo_typeOfActor.set_model(gtk.ListStore(str))
        self.combo_typeOfActor.append_text("CLIENT")
        self.combo_typeOfActor.append_text("MASTER")
        self.combo_typeOfActor.show()
        self.tableFormNewActor.attach(label_typeOfActor, 0, 1, 2, 3, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.combo_typeOfActor, 1, 2, 2, 3, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        
        # Network layer actor
        label_typeOfNetworkActor = gtk.Label("Network layer : ")
        label_typeOfNetworkActor.show()
        self.combo_typeOfNetworkActor = gtk.combo_box_entry_new_text()
        self.combo_typeOfNetworkActor.set_model(gtk.ListStore(str))
        self.combo_typeOfNetworkActor.append_text("CLIENT")
        self.combo_typeOfNetworkActor.append_text("SERVER")
        self.combo_typeOfNetworkActor.show()
        self.tableFormNewActor.attach(label_typeOfNetworkActor, 2, 3, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.combo_typeOfNetworkActor, 3, 4, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        
        # IP
        label_IP = gtk.Label("IP : ")
        label_IP.show()
        self.entry_IP = gtk.Entry()
#        self.entry_IP.set_width_chars(50)
        self.entry_IP.set_text("")
        self.entry_IP.show()
        self.tableFormNewActor.attach(label_IP, 2, 3, 1, 2, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.entry_IP, 3, 4, 1, 2, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)

        # PORT
        label_Port = gtk.Label("Port : ")
        label_Port.show()
        self.entry_Port = gtk.Entry()
#        self.entry_Port.set_width_chars(50)
        self.entry_Port.set_text("")
        self.entry_Port.show()
        self.tableFormNewActor.attach(label_Port, 2, 3, 2, 3, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableFormNewActor.attach(self.entry_Port, 3, 4, 2, 3, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        
        # Add actor button
        self.button_addActor = gtk.Button(gtk.STOCK_OK)
        self.button_addActor.set_label("Add actor")
        self.button_addActor.connect("clicked", self.addActor)
        self.button_addActor.show()
        self.tableFormNewActor.attach(self.button_addActor, 3, 4, 3, 4, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
                
        self.tableFormNewActor.show()
        self.panel.attach(self.tableFormNewActor, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Panel hosting the list of curent actors
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        scroll_listActiveActors = gtk.ScrolledWindow()
        self.treestore_listActiveActors = gtk.TreeStore(str, str) # actor's name, typ
        
#        self.treestore_listActiveActors.append(None, ["actor1", "Server"])
#        self.treestore_listActiveActors.append(None, ["actor2", "Client"])
#        self.treestore_listActiveActors.append(None, ["actor3", "Client"])
#        self.treestore_listActiveActors.append(None, ["actor4", "Client"])
#        self.treestore_listActiveActors.append(None, ["actor5", "Client"])
        
        treeview_listActiveActors = gtk.TreeView(self.treestore_listActiveActors)
        treeview_listActiveActors.get_selection().set_mode(gtk.SELECTION_SINGLE)
        treeview_listActiveActors.set_size_request(500, -1)
        treeview_listActiveActors.connect("cursor-changed", self.actorDetails)
        cell = gtk.CellRendererText()
        # main col
        column_listActiveActors_name = gtk.TreeViewColumn('Active actors')
        column_listActiveActors_name.pack_start(cell, True)
        column_listActiveActors_name.set_attributes(cell, text=0)
        treeview_listActiveActors.append_column(column_listActiveActors_name)
        treeview_listActiveActors.show()
        scroll_listActiveActors.add(treeview_listActiveActors)
        scroll_listActiveActors.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_listActiveActors.show()
        self.panel.attach(scroll_listActiveActors, 1, 2, 0, 1, xoptions=gtk.FILL | gtk.EXPAND, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Inputs
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        scroll_inputs = gtk.ScrolledWindow()
        self.treestore_inputs = gtk.TreeStore(str, str) # date, input message
        
#        self.treestore_inputs.append(None, ["12:45:01", "message 1"])
#        self.treestore_inputs.append(None, ["12:45:11", "message 2"])
#        self.treestore_inputs.append(None, ["12:45:21", "message 3"])
#        self.treestore_inputs.append(None, ["12:45:23", "message 4"])
#        self.treestore_inputs.append(None, ["12:45:23", "message 5"])
        
        treeview_inputs = gtk.TreeView(self.treestore_inputs)
        treeview_inputs.get_selection().set_mode(gtk.SELECTION_NONE)
        treeview_inputs.set_size_request(500, -1)
#        treeview_listActiveActors.connect("cursor-changed", self.packet_details)
        cell = gtk.CellRendererText()
        # col date
        column_inputs_date = gtk.TreeViewColumn('Date')
        column_inputs_date.pack_start(cell, True)
        column_inputs_date.set_attributes(cell, text=0)
        # col message
        column_inputs_message = gtk.TreeViewColumn('Received message')
        column_inputs_message.pack_start(cell, True)
        column_inputs_message.set_attributes(cell, text=1)
        treeview_inputs.append_column(column_inputs_date)
        treeview_inputs.append_column(column_inputs_message)
        treeview_inputs.show()
        scroll_inputs.add(treeview_inputs)
        scroll_inputs.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_inputs.show()
        self.panel.attach(scroll_inputs, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)
               
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Outputs
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        scroll_outputs = gtk.ScrolledWindow()
        self.treestore_outputs = gtk.TreeStore(str, str) # date, output message
        
#        self.treestore_outputs.append(None, ["12:45:01", "message 1"])
#        self.treestore_outputs.append(None, ["12:45:11", "message 2"])
#        self.treestore_outputs.append(None, ["12:45:21", "message 3"])
#        self.treestore_outputs.append(None, ["12:45:23", "message 4"])
#        self.treestore_outputs.append(None, ["12:45:23", "message 5"])
        
        treeview_outputs = gtk.TreeView(self.treestore_outputs)
        treeview_outputs.get_selection().set_mode(gtk.SELECTION_NONE)
        treeview_outputs.set_size_request(500, -1)
#        treeview_listActiveActors.connect("cursor-changed", self.packet_details)
        cell = gtk.CellRendererText()
        # col date
        column_outputs_date = gtk.TreeViewColumn('Date')
        column_outputs_date.pack_start(cell, True)
        column_outputs_date.set_attributes(cell, text=0)
        # col message
        column_outputs_message = gtk.TreeViewColumn('Emitted message')
        column_outputs_message.pack_start(cell, True)
        column_outputs_message.set_attributes(cell, text=1)
        treeview_outputs.append_column(column_outputs_date)
        treeview_outputs.append_column(column_outputs_message)
        treeview_outputs.show()
        scroll_outputs.add(treeview_outputs)
        scroll_outputs.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_outputs.show()
        self.panel.attach(scroll_outputs, 0, 1, 2, 3, xoptions=gtk.FILL, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Memory
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        scroll_memory = gtk.ScrolledWindow()
        self.treestore_memory = gtk.TreeStore(str, str, str) # name, type, value
        
#        self.treestore_memory.append(None, ["var1", "IP", "192.168.0.10"])
#        self.treestore_memory.append(None, ["var2", "WORD", "PSEUDO"])
#        self.treestore_memory.append(None, ["var3", "IP", "192.178.12.12"])
        
        treeview_memory = gtk.TreeView(self.treestore_memory)
        treeview_memory.get_selection().set_mode(gtk.SELECTION_NONE)
        treeview_memory.set_size_request(500, -1)
#        treeview_listActiveActors.connect("cursor-changed", self.packet_details)
        cell = gtk.CellRendererText()
        # col name
        column_memory_name = gtk.TreeViewColumn('Variable')
        column_memory_name.pack_start(cell, True)
        column_memory_name.set_attributes(cell, text=0)
        # col type
        column_memory_type = gtk.TreeViewColumn('Type')
        column_memory_type.pack_start(cell, True)
        column_memory_type.set_attributes(cell, text=1)
        # col Value
        column_memory_value = gtk.TreeViewColumn('Value')
        column_memory_value.pack_start(cell, True)
        column_memory_value.set_attributes(cell, text=2)
        
        treeview_memory.append_column(column_memory_name)
        treeview_memory.append_column(column_memory_type)
        treeview_memory.append_column(column_memory_value)
        treeview_memory.show()
        scroll_memory.add(treeview_memory)
        scroll_memory.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_memory.show()
        self.panel.attach(scroll_memory, 0, 1, 3, 5, xoptions=gtk.FILL, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)
                
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Panel for the Model
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.xdotWidget = XDotWidget.XDotWidget()        
        
        self.xdotWidget.show_all()
        self.xdotWidget.set_size_request(500, 500)        
        self.panel.attach(self.xdotWidget, 1, 2, 1, 4, xoptions=gtk.FILL, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Break and stop
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.tableForBreakAndStop = gtk.Table(rows=1, columns=3, homogeneous=True)
        # Add start button
        self.button_startActor = gtk.Button(gtk.STOCK_OK)
        self.button_startActor.set_label("START")
        self.button_startActor.connect("clicked", self.startSelectedActor)
        self.button_startActor.show()
        self.tableForBreakAndStop.attach(self.button_startActor, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        # Add break button
        self.button_breakActor = gtk.Button(gtk.STOCK_OK)
        self.button_breakActor.set_label("PAUSE")
#        self.button_breakActor.connect("clicked", self.startAnalysis_cb)
        self.button_breakActor.show()
        self.tableForBreakAndStop.attach(self.button_breakActor, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        # Add stop button
        self.button_stopActor = gtk.Button(gtk.STOCK_OK)
        self.button_stopActor.set_label("STOP")
#        self.button_breakActor.connect("clicked", self.startAnalysis_cb)
        self.button_stopActor.show()
        self.tableForBreakAndStop.attach(self.button_stopActor, 2, 3, 0, 1, xoptions=gtk.FILL, yoptions=0, xpadding=5, ypadding=5)
        self.tableForBreakAndStop.show()        
        self.panel.attach(self.tableForBreakAndStop, 1, 2, 4, 5, xoptions=gtk.FILL | gtk.EXPAND, yoptions=gtk.FILL | gtk.EXPAND, xpadding=5, ypadding=5)


    def getAvailableGrammars(self):
        # Scan the directory of grammars and retrieve them
        grammar_directory = ConfigurationParser.ConfigurationParser().get("automata", "path")  
        # a temporary list in which all the files
        temporaryListOfFiles = []
         
        # list all the files (except .svn)
        for file in os.listdir(grammar_directory):
            pathOfAutomata = grammar_directory + "/" + file
            
            if os.path.isfile(pathOfAutomata) :
                temporaryListOfFiles.append(file)
            
        # Sort and add to the entry
        return sorted(temporaryListOfFiles)
    
    def startSelectedActor(self, widget):
        self.selectedActor.start()
    
    def addActor(self, widget):
        # Retrieves the value of the form to create the actor
        actorName = self.entry_actorName.get_text()
        actorGrammar = self.combo_grammar.get_active_text()
        actorGrammarType = self.combo_typeOfActor.get_active_text()
        actorNetworkType = self.combo_typeOfNetworkActor.get_active_text()
        actorIP = self.entry_IP.get_text()
        actorPort = self.entry_Port.get_text()
        
        # We verify we have everything and the actor's name is unique
        for actor in self.actors :
            if actor.getName() == actorName :
                self.log.warn("Impossible to create the requested actor since another one has the same name")
                return
        
        self.log.info("Will add an actor named " + actorName + " (" + actorGrammar + ")")
        
        # First we load the xml definition of the automata     
        grammar_directory = ConfigurationParser.ConfigurationParser().get("automata", "path")    
        xmlFile = grammar_directory + "/" + actorGrammar
        tree = ElementTree.ElementTree()
        tree.parse(xmlFile)
        # Load the automata based on its XML definition
        automata = MMSTDXmlParser.MMSTDXmlParser.loadFromXML(tree.getroot())
        
        # We create an actor based on given informations
        if actorGrammarType == "MASTER" :
            isMaster = True
        else :
            isMaster = False
            
        # Create the network layer
        if actorNetworkType == "SERVER" :
            actor = NetworkServer.NetworkServer(actorName, automata, isMaster, actorIP, int(actorPort))
        else :
            actor = NetworkClient.NetworkClient(actorName, automata, isMaster, actorIP, int(actorPort))
            
        # add the actor to the list
        self.actors.append(actor)
        
        # update the list of actors
        self.updateListOfActors()
        
    def updateListOfActors(self):        
        self.treestore_listActiveActors.clear()
        for actor in self.actors :
            type = "Server"
            if not actor.isMaster :
                type = "Client"            
            self.treestore_listActiveActors.append(None, [actor.getName(), type])
    
    def actorDetails(self, treeview):
        self.selectedActor = None
        actorName = ""
        (model, iter) = treeview.get_selection().get_selected()
        
        if(iter):
            if(model.iter_is_valid(iter)):
                actorName = model.get_value(iter, 0)
                actorType = model.get_value(iter, 1)
                self.log.info("Selected actor : " + actorName)
        
        for actor in self.actors :
            if actor.getName() == actorName :
                self.selectedActor = actor
        
        if self.selectedActor == None :
            self.log.warn("Impossible to retrieve the requested actor")
            return
        
        # Now we update the GUI based on the actor
        self.updateGUIForActor()
        
    
        
    def updateGUIForActor(self):
        # First we display its model 
        automata = self.selectedActor.getModel()    
        self.xdotWidget.drawAutomata(automata)
        self.xdotWidget.show_all()
        
        # Now we display its received message
        self.treestore_inputs.clear()
        for inputMessage in self.selectedActor.getInputMessages() :
            self.treestore_inputs.append(None, inputMessage)
            
        # Now we display its emitted message
        self.treestore_outputs.clear()
        for outputMessage in self.selectedActor.getOutputMessages() :
            self.treestore_outputs.append(None, outputMessage)
            
        # Now we update its memory
        self.treestore_memory.clear()
        for memory in self.selectedActor.getMemory() :
            self.treestore_memory.append(None, memory)
        
