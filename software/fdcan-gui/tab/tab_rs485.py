import sys
import time
import os
import socket
import serial
import serial.tools.list_ports as sp
import struct

from os import path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QFile
from PySide6.QtGui import *
from ui.ui_rs485 import *
from ui.ui_main import *
from lib.log import LogWidget
from configparser import ConfigParser

from lib.cmd import *
from lib.cmd_rs485 import *




class TabRS485(QWidget, Ui_RS485):
  def __init__(self, ui_main :Ui_MainWindow, cmd):
    super().__init__()
    self.setupUi(self)

    self.ui_main = ui_main
    self.cmd = cmd
    self.cmd_rs485 = CmdRS485(cmd)
    self.log = LogWidget(self.text_log)
    self.is_open = False
    self.loadConfig()

    self.setClickedEvent(self.btn_open, self.btnOpen)  
    self.setClickedEvent(self.btn_close, self.btnClose)
    self.setClickedEvent(self.btn_clear, self.btnClear)
    self.setClickedEvent(self.btn_send, self.btnSend)
    self.combo_return.currentIndexChanged.connect(self.saveConfig)
    self.btnUpdate()    

  def __del__(self):
    return

  def setClickedEvent(self, event_dst, event_func):
    event_dst.clicked.connect(lambda: self.btnClicked(event_dst, event_func))   

  def btnClicked(self, button, event_func):
    event_func() 

  def btnOpen(self):
    if self.is_open == True:
      self.is_open = False
      self.btnUpdate()
      return

    if self.cmd.is_open:
      err_code, resp = self.cmd_rs485.open(int(self.combo_baud.currentText()))
      if err_code == OK:
        self.is_open = True
        self.saveConfig()
    else:
      self.log.println("Not Connected")
    self.btnUpdate()

  def btnClose(self):
    if self.is_open:
      if self.cmd.is_open:
        err_code, resp = self.cmd_rs485.close()
        if err_code > 0:
          self.log.println("err_code : " + str(hex(err_code)))
      self.is_open = False;        
    self.btnUpdate()

  def btnClear(self):
    self.log.clear()

  def btnSend(self):
    text_len = len(self.text_send.text())
    if self.is_open:
      if self.combo_return.currentText() == "CR":        
        send_buf = bytes(b'\x0D')
      elif self.combo_return.currentText() == "LF":
        send_buf = bytes(b'\x0A')
      elif self.combo_return.currentText() == "CR/LF":
        send_buf = bytes(b'\x0D\x0A')
      else:
        send_buf = bytes(0)

      self.cmd_rs485.send(bytes(self.text_send.text(), 'utf-8') + send_buf)

  def btnUpdate(self):
    if self.cmd.is_open == False:
      self.is_open = False

    self.btn_open.setEnabled(not self.is_open)
    self.btn_close.setEnabled(self.is_open)
    self.btn_send.setEnabled(self.is_open)


  def loadConfig(self):        
    self.config = ConfigParser() 
    self.config.optionxform = lambda optionstr: optionstr

    self.config['config'] = {}
    self.config_item = self.config['config']

    if os.path.exists("config.ini"):
      self.config.read('config.ini')  
      try:
        if self.config_item['rs485_baud'] is not None:
          self.combo_baud.setCurrentText(self.config_item['rs485_baud'])
        if self.config_item['rs485_send_ret'] is not None:
          self.combo_return.setCurrentText(self.config_item['rs485_send_ret'])
        self.text_send.setText(self.config_item['rs485_send'])
      except Exception as e:
        print(e)
    else:
      self.saveConfig()    

  def saveConfig(self):  
    self.config_item['rs485_baud'] = str(self.combo_baud.currentText())
    self.config_item['rs485_send_ret'] = str(self.combo_return.currentText())
    self.config_item['rs485_send'] = self.text_send.text()

    with open('config.ini', 'w') as configfile:
      self.config.write(configfile)

  def rxdEvent(self, packet: CmdPacket):
    self.log.write(packet.data[:packet.length])