#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Christoph Goebel
#
# The Regents of the University of California. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# All advertising materials mentioning features or use of this software must display the following acknowledgement: “This product includes software developed by the University of California, Berkeley and its contributors.”
# Neither the name of the University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import RPi.GPIO as GPIO
import time, os, sys
from datetime import date
from lc_display import lcd
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("radio")

current_dir = os.path.realpath(__file__)
parent_dir = os.path.realpath(current_dir + "/../..")
#################
# Konfiguration #
#################
version = "2022.1"

display_operating_instrcutions = False       # display_operating_instrcutions True/False

###########################
# mpd m3u Senderablageort #
###########################
radio_playlist = parent_dir + "/conf/radio_sender.m3u"


##############################################################################
# mpc client - Passwort und Hostname fuer Bedienung via Tastenfeld und Handy #
##############################################################################
PH = "kradio@kradio"                                                  # Beispiel:  blabla@MeinRadio


#######################################################################################################
# mpc Befehle in einem Dictionary - für Dictionarys ist kein "global" in Funktionsdefinitionen nötig. #
#######################################################################################################
mpc = {
    "clear"         : "mpc -h " + str(PH) + " clear",                                      # Playlist leeren
    "update"        : "mpc -h " + str(PH) + " update",                                     # Playlist update
    "play"          : "mpc -h " + str(PH) + " play ",                                      # Abspielen beginnen
    "stop"          : "mpc -h " + str(PH) + " stop",                                       # Abspielen stoppen
    "loadlist"      : "mpc -h " + str(PH) + " load radio_sender",                          # Sender aus Datei laden
    "next"          : "mpc -h " + str(PH) + " next",                                       # Nächter Sender/Song
    "prev"          : "mpc -h " + str(PH) + " prev",                                       # Vorheriger Sender/Song
    "volumeup"      : "mpc -h " + str(PH) + " volume +5",
    "volumedown"    : "mpc -h " + str(PH) + " volume -5",
    "volumestartup" : "mpc -h " + str(PH) + " volume 20",
    "shuffle"       : "mpc -h " + str(PH) + " shuffle",                                    # Playlist zufällig zusammenstellen
    "addmusic"      : "cd " + parent_dir + "/music && mpc -h " + str(PH) + " add *.*",    # Alle MP3 Songs aus diesem Verzeichnis einlesen
    "songinfo"      : "mpc -h " + str(PH) + " current"                                     # Aktuelle Songinfo/Radioinfo
}


#############################################################
# W-LAN Konfigurator - Mögliche Zeichen für WPA  Schluessel #
#############################################################
zahlen = ['0','1','2','3','4','5','6','7','8','9']

buchstaben = ['A','a','B','b','C','c','D','d','E','e','F','f','G','g','H','h','I','i',
              'J','j','K','k','L','l','M','m','N','n','O','o','P','p','Q','q','R','r',
              'S','s','T','t','U','u','V','v','W','w','X','x','Y','y','Z','z']

sonderzeichen = [' ','_','!','"','%','&','/','(',')','<','>','|','{','}',
                 '=','?','*',"'",'+','-','#',',','.',';',':','^']

alleZeichen = zahlen + buchstaben + sonderzeichen              # alle Zeichen
sz = 10                                                        # selektiertes Zeichen beim Programmstart
aktuellesZeichen = ""                                          # Vorbelegung
bez = ""                                                       # Vorbelegung für bisher eingewaehlte Zeichen


###############################
# Board-Pin Nummern verwenden #
###############################
GPIO.setmode(GPIO.BOARD)


#############
# Pin Namen #
#############
KeyRight=7
KeyLeft=16
KeyOk=13
KeyVolumeUp=15
KeyVolumeDown=29


##################
# Pins als Input #
##################
GPIO.setup(KeyRight, GPIO.IN)
GPIO.setup(KeyLeft, GPIO.IN)
GPIO.setup(KeyOk, GPIO.IN)
GPIO.setup(KeyVolumeUp, GPIO.IN)
GPIO.setup(KeyVolumeDown, GPIO.IN)


###################
# Modus Variable  #
###################
global modus                                                     # Hier global, da u.a. in Hauptschleife geändert wird und über einige Funktionen abgefragt wird.


###################################################
# Hardware Funktionen inkl. & IP Adressermittlung #
###################################################
# W-LAN Adapter Ein
def wlanein():
    logger.debug("wlanein")
    os.system("sudo ip link set wlan0 up")
    time.sleep(9.0)                                              # Zeit für W-LAN Hardware geben

# W-LAN Adapter Aus
def wlanaus():
    logger.debug("wlanaus")
    os.system("sudo ip link set wlan0 down")

# Anzeige aus
def anzaus():
    logger.debug("anzaus")
    global my_lcd
    my_lcd.backlight_off()
    pass

# IP Adresse ermitteln
def ZeileC_ip_anzeige():
    logger.debug("ZeileC_ip_anzeige")
    ipadrBASH = "hostname -I | cut -f1 -d' '"                     # IP ermitteln
    ipadranz = subprocess.check_output([ipadrBASH], shell=True, text=True)   # IP in Variable
    ipadranz = ipadranz.strip("\n")                               # Umbruch durch Leerzeichen ersetzen
    ipStellen = len(ipadranz)                                     # Länge der IP ermitteln
    if ipStellen > 1:                                             # Wenn IP vergeben
        zc = str(ipadranz)
    else:
        zc = "   ---.---.---.---  "                               # wenn keine IP vergeben, dann davon ausgehen, dass Verbindung nicht möglich
    return zc                                                     # Rückgabe der Ip für Zeile B

####################
# Modus-Funktionen #
####################
# Radio oder MP3 Modus
def RAModeOrMP3Mode( pin ):
    logger.debug("RAModeOrMP3Mode")
    global modus
    if modus == 1:
        MP3Mode()

    anzahl_sender()
    RAMode()

# RunUp Modus - einmalig beim Hochfahren
def RUMode():
    logger.debug("RUMode")
    os.system(mpc["volumestartup"])
    os.system(mpc["clear"])                                          # mpc clear
    os.system(mpc["update"])                                         # mpc update
    os.system('mpg321 ' + parent_dir + '/conf/StartUp.mp3')         # Start-Sound abspielen

# Radio-Modus
def RAMode():
    logger.debug("RAMode")
    global modus, sender
    if (modus == 0) or (modus == 31) or (modus == 32):
        modus = 1
        wlanein()                                                    # W-LAN Adapter ein
    modus = 1                                                        # Modus RAMode
    os.system(mpc["clear"])                                          # mpc clear
    os.system(mpc["loadlist"])                                       # mpc load list
    os.system(mpc["play"] + str(sender))                             # mpc play letzten Sender

# MP3 Modus
def MP3Mode():
    logger.debug("MP3Mode")
    global modus
    modus = 2                                                        # Modus MP3Mode
    os.system(mpc["update"])                                         # mpc update
    os.system(mpc["clear"])                                          # mpc clear
    os.system(mpc["addmusic"])                                       # mpc addmusic
    os.system(mpc["shuffle"])                                        # mpc shuffle playliste zusammenstellen
    os.system(mpc["play"] + "1")                                     # mpc play mp3s vom ersten Song an

# Standby Modus - (D)Taste
def SBMode(pin):
    logger.debug("SBMode")
    global modus, bez
    time.sleep(0.5)                                               # Zeit für Doppeltastenbedienung geben
    if (GPIO.input(KeyRight) == GPIO.LOW) and (GPIO.input(KeyOk) == GPIO.LOW):   # Wenn (A)Taste und (D)Taste zusammen gedrückt werden, dann NEUSTART
        RBMode()
    elif (GPIO.input(KeyLeft) == GPIO.LOW) and (GPIO.input(KeyOk) == GPIO.LOW): # Wenn (B)Taste und (D)Taste zusammen gedrückt werden, dann RUNTERFAHREN
        SDMode()
    else:                                                         # Standby einleiten
        modus = 31                                                # SBMode 3 1     In den Standby
        os.system(mpc["stop"])                                    # mpc Abspielen stoppen
        wlanaus()                                                 # W-LAN Adapter aus

# Reboot Modus
def RBMode():                                                         # Modus RBMode
    logger.debug("RBMode")
    global modus
    modus = 4
    os.system(mpc["stop"])                                            # Player stop
    os.system('mpg321 ' + parent_dir + '/conf/ShutDown.mp3')         # Shutdown Sound abspielen

# ShutDown Modus
def SDMode():
    logger.debug("SDMode")
    global modus
    modus = 5
    os.system(mpc["stop"])                                            # mpc-Abspielen stoppen
    os.system('mpg321 ' + parent_dir + '/conf/ShutDown.mp3')         # ShutDown Sound abspielen


######################
# Anzeige-Funktionen #
######################
# Allgemeine Anzeige-Funktion für alles 4 Zeilen
def anzeige(ZeileA,ZeileB,ZeileC,ZeileD):                             # Funktionsdefinitionsdefinition für Anzeigeausgabe
    logger.debug("anzeige")
    global my_lcd                                                     # Beispiel:
    my_lcd.display_string(ZeileA, 1)                                  #           ---<12:13>-<*** >---     ZeileA  zeit & W-LAN Empfangsqualität qual
    my_lcd.display_string(ZeileB, 2)                                  #           (06) NDR2-Nieders.       ZeileB  StationsNummer st und SenderName sn max. 15 Zeichen
    my_lcd.display_string(ZeileC, 3)                                  #           Die Fantastischen Vi     ZeileC  Sender- Song Info als Lauftext
    my_lcd.display_string(ZeileD, 4)                                  #           -<21.02.2019> <Di.>-     ZeileD  datum und Wochentag wt
    pass

# Allgemeine Anzeige-Funktion für einzeilige Änderungen
def anzeige_einzeilig(string, zeile):
    logger.debug("anzeige_einzeilig")
    my_lcd.display_string(string, zeile)
    pass

# Zeilen ABCD RUMode
def ZeilenABCD_RUMode(v):
    logger.debug("ZeilenABCD_RUMode")

    # Bedienungsanleitung
    if display_operating_instrcutions:
        za = "Bedienungsanleitung "
        zb = "anzeigen? Dann nun  "
        zc = "      OK-Taste      "
        zd = "gedrückt halten.    "
        anzeige(za,zb,zc,zd)
        time.sleep(5)
        if (GPIO.input(KeyOk) == GPIO.LOW):
            za = "--------------------"
            zb = "Bedienungsanleitung "
            zc = "  wird gestartet.   "
            zd = "--------------------"
            anzeige(za,zb,zc,zd)                                       # Allgemeiner Aufruf der Anzeigefunktion mit Argumentübergabe
            time.sleep(4)

            za = ">>> >-Taste --->    "
            zb = "                    "
            zc = "Sender oder Song    "
            zd = "nach vorne springen "
            anzeige(za,zb,zc,zd)
            time.sleep(4)

            za = ">>> <-Taste --->    "
            zb = "                    "
            zc = "Sender oder Song    "
            zd = "nach hinten springen"
            anzeige(za,zb,zc,zd)
            time.sleep(4)

            za = ">>> ^-Taste --->    "
            zb = "                    "
            zc = "Lautsärke erhöhen   "
            zd = "                    "
            anzeige(za,zb,zc,zd)
            time.sleep(4)

            za = ">>> ˯-Taste --->    "
            zb = "                    "
            zc = "Lautstärke          "
            zd = "verringern          "
            anzeige(za,zb,zc,zd)
            time.sleep(4)

            za = ">>> Ok-Taste --->   "
            zb = "                    "
            zc = "Wechselt in den     "
            zd = "Standby-Modus       "
            anzeige(za,zb,zc,zd)
            time.sleep(4)

    anzahl_sender()
    # SD Karte freier Speicher in Prozent
    verw_speicherBASH = "df -h | grep /dev/root | awk '{print $5}'"                     # Befehl zum Auslesen des belegten Speichers in Prozent
    verw_speicher = subprocess.check_output([verw_speicherBASH], shell=True, text=True) # Auslesen der prozentualen Belegung
    verw_speicher = verw_speicher.strip("\n").replace('%', '')                                       # Umbruch durch Leerzeichen ersetzen
    frei_speicher = 100 - int(verw_speicher)

    # Version
    za = "--------------------"
    zb = "    RasPi Radio     "
    zc = str(v)
    zd = "--------------------"
    anzeige(za,zb,zc,zd)
    time.sleep(3)

    # Speicherplatz
    zb = "   Radiospeicher:   "
    zc = "      " + str(frei_speicher) + "% frei      "
    anzeige(za,zb,zc,zd)
    time.sleep(3)

    # IP Anzeigen
    za = "--------------------"
    zb = "     IP Adresse:    "
    zc = ZeileC_ip_anzeige()                                                         # Aufruf IP-Ermitteln
    zd = "--------------------"
    anzeige(za,zb,zc,zd)
    time.sleep(3)

    # Anzahl Sender
    za = "--------------------"
    zb = "    Starte Radio    "
    zc = "  mit (" + str(AnzSender) + ") Sendern  "
    zd = "--------------------"
    anzeige(za,zb,zc,zd)
    time.sleep(3)

# ZeileA_RAMode_MP3Mode_SBMode
def ZeileA_RAMode_MP3Mode_SBMode():                                                  # Funktionsdefinition zum Ermitteln des Strings für Zeile A im Radio-, Offline- & Standby-Modus
    logger.debug("ZeileA_RAMode_MP3Mode_SBMode")
    # Zeit
    zeit = time.strftime("%H:%M")                                                    # Aktuelle Zeit als String
    # W-LAN Signal ermitteln
    slBASH = "iwconfig wlan0 | grep Signal | awk '{print $4}' | cut -c8-9"           # Bash-Befehl zur Ermittlung des SignalLevels
    try:
        sl = int(subprocess.check_output([slBASH], shell=True, text=True))                      # Signallevel als Integer ermitteln, wenn W-LAN weg, dann kurzzeitig keine Wandlung möglich da ValueError -> dann except.
        if (sl <=25) and (sl >0):                                                    # Signalstärke sehr schlecht
            qual = "*   "
        elif (sl  >25) and (sl <51):                                                 # Signalstärke schlecht
            qual = "**  "
        elif (sl >51) and  (sl <76):                                                 # Signalstärke gut
            qual = "*** "
        elif (sl >=76):                                                              # Signalstärke sehr gut
            qual = "****"
        else:
            qual = "    "
        za = "--<" + zeit + ">---<" + qual + ">--"                                   # Zeilen-String zusammenstellen
        return za
    except ValueError:
        za = "--<" + zeit + ">---<    >--"
        time.sleep(4.0)
        return za

def get_stations():
    logger.debug("get_stations")
    stations = ""
    with open(str(radio_playlist), 'r') as f:
        stations = f.readlines()[6:]
    return [station.split('#')[1].strip() for station in stations]


# ZeileB_RAMode
def ZeileB_RAMode():                                                                 # Funktionsdefinition zum Ermitteln des Strings für Zeile B im RadioModus
    logger.debug("ZeileB_RAMode")
    global sender
    stBASH = "mpc -h " + str(PH) + " -f %name% | grep playing | cut -c12-13"         # Bash-mpc Befehl mit grep&cut zum SenderstationsNr.-Auslesen
    st_tmp = subprocess.check_output([stBASH], shell=True, text=True)                           # Sendernummer auslesen
    st_tmp = st_tmp.strip("\n/")                                                     # Umbruch entfernen, Slash entfernen (bei einstelligen Sendern)
    if st_tmp == "":                                                                 # Wenn der Sender mal länger zum Starten benötigt oder keine W-LAN Verbindung besteht.
        zb = "  Warte auf Sender  "                                                  # Dann Sendersuche anzeigen
        return zb
        exit
    else:
        try:
            st_int = int(st_tmp)                                                     # Sendernummer von str zu int
            sender = st_int
            if (st_int) <10:
                st = "0" + str(st_int)                                               # Wenn ausgelesene Sendernummer einstellig dann führende 0 zufügen
            else:
                st = str(st_int)                                                     # Wenn ausgelesene Sendernummer zweistellig dann 1 zu 1 in st variable
            st_anwahl = st_int -1                                                    # Senderstationsnummer -1 um in der Liste den richtigen Sendernamen zu wählen
            # Sendernamen aus playlist-Kommentaren auslesen
            sn = get_stations()
            snl = len(sn[st_anwahl])                                                 # Sendernamenlänge des durch die Stationsnummer ermittelten Namens
            if (snl > 15):                                                           # Sendernamen-String kürzen wenn länger als 15 Zeichen
                x = snl - 15                                                         # Ermitteln um wie viele Zeichen gekürzt werden muss... um x Zeichen
                sn[st_anwahl] = sn[st_anwahl][:-x]                                   # String kürzen um x Zeichen vom Ende an
            elif (snl < 15):                                                         # Sendernamen-String verlängern wenn kürzer als 15 Zeichen
                sn[st_anwahl] = '{message: <15}'.format(message=sn[st_anwahl])       # Format auf 15 Zeichen erweitern, dabei werden Leerzeichen eingefügt.
            zb = "(" + st + ") " + sn[st_anwahl]                                     # String Sendernummer und Namen
            return zb                                                                # Rückgabe String für Zeile
        except:                                                                      # Falls es Probleme bei der Sendernummererkennung gibt
            zb = "Sender nicht erkannt"                                              # z.B. wenn Radiosenderanzahl in radio_sender.m2u im laufenden Betrieb dezimiert wird
            return zb

# ZeileC_RAMode_MP3Mode
def ZeileC_RAMode_MP3Mode():                                                         # Funktionsdefinition zum Ermitteln des Strings für Zeile C im RadioModus & MP3 Modus
    logger.debug("ZeileC_RAMode_MP3Mode")
    info_tmp = subprocess.check_output([mpc["songinfo"]], shell=True, text=True)
    if not "#" in info_tmp:
        info_tmp = info_tmp.strip("\n")                                              # Umbruch raus
        info_tmp = info_tmp.strip()                                                  # Schmierzeichen entfernen
        info_tmp = ":" + info_tmp
        ldp = info_tmp.rfind(":")                                                    # Position des letzten Doppelpunktes im String suchen, gibt es sonst keinen, wird der angefügte : gefunden.
        start = ldp + 1                                                              # Start-Index für String Splicing
        zc_tmp = info_tmp[start:]                                                    # Von Start-Index String schreiben
        zc_tmp = zc_tmp.lstrip()                                                     # Leerzeichen am Anfang entfernen
        zc_tmp_laenge = len(zc_tmp)                                                  # Länge des übrigen Strings ermitteln
        return zc_tmp, zc_tmp_laenge                                                 # String und ANzahl Zeichen zurückgeben
    else:
        return "---", 3                                                              # Falls keine Senderinfo vorliegt, also # zwischen link und Sendernamen gefunden wird, dann ---

# ZeileD_RAMode_MP3Mode_SBMode
def ZeileD_RAMode_MP3Mode_SBMode():                                                  # Funktionsdefinition zum Ermitteln des Strings für Zeile D im Radiomodus
    logger.debug("ZeileD_RAMode_MP3Mode_SBMode")
    # Wochentag
    WoTaNa = ["Mo.","Di.","Mi.","Do.","Fr.","Sa.","So."]                             # Selbst definierte WochenTagNamen
    WoTaNu = date.today().weekday()                                                  # WochenTagNummer ermitteln 0=Montag 6=Sonntag
    wt = WoTaNa[WoTaNu]                                                              # Wochentagsabkürzung ermitteln
    # Datum
    datum = time.strftime("%d.%m.%Y")                                                # Datum Format
    # Rückgabe für Zeile D
    zd = "-<" + datum + ">-<" + wt + ">-"                                            # Zeilen-String zusammenstellen
    return zd                                                                        # Rückgabe String für Zeile

# ZeilenBC_MP3Mode
def ZeileB_MP3Mode():
    logger.debug("ZeileB_MP3Mode")
    zb = "      mp3-Mix       "
    return zb

# ZeilenBC_SBMode
def ZeilenBC_SBMode():
    logger.debug("ZeilenBC_SBMode")
    zb = "      Standby       "
    zc = "     W-LAN AUS      "
    return zb,zc

# Reboot Display Strings zusammenstellen und zur Anzeige bringen
def ZeilenABCD_RBMode():
    logger.debug("ZeilenABCD_RBMode")
    za = "--------------------"
    zb = "      Neustart      "
    zc = "    Bitte warten    "
    zd = "--------------------"
    return za,zb,zc,zd

# Anzeige SDMode
def ZeilenABCD_SDMode():
    logger.debug("ZeilenABCD_SDMode")
    za = "--------------------"
    zb = "     Radio wird     "
    zc = "  heruntergefahren  "
    zd = "--------------------"
    return za,zb,zc,zd

# Anzeige Favorit gespeichert
def ZeilenBC_FAVMode():
    logger.debug("ZeilenBC_FAVMode")
    zb = "       Favorit      "
    zc = "     gespeichert    "
    return zb,zc

# Anzeige Keine Funktion in diesem Modus
def ZeileBC_KeineFunktion():
    logger.debug("ZeileBC_KeineFunktion")
    zb = "  In diesem Modus   "
    zc = "  keine Funktion!   "
    return zb,zc

# Anzeige Song gemerkt
def ZeileBC_MERK():
    logger.debug("ZeileBC_MERK")
    zb = "Song wurde gemerkt! "
    zc = "smb: conf/merk.txt  "
    return zb,zc


############################
# Senderwechsel und Merker #
############################
# Senderwechsel/Songwechsel hoch SWH bzw. in W-LAN Konfigurationsmodus  - Buchstabe vor
def SWH(pin):
    logger.debug("Taste hoch")
    global sender, AnzSender, modus, sz
    if modus == 1:                                                                      # Das wird im Radio Modus gemacht
        anzahl_sender()                                                                   # Anzahl Sender aktualisieren
        time.sleep(0.3)                                                                   # Zeit für Doppelbedienung geben,
        sender = sender + 1                                                           # Sender +1
        if sender > AnzSender :                                                           # Wenn Senderliste am Ende dann mit erstem Sender weiter
            sender = sender - AnzSender
        os.system(mpc["play"] + str(sender))
    elif modus == 2:                                                                      # Das wird im MP3 Modus gemacht
        os.system(mpc["next"])

# Senderwechsel/Songwechsel runter SWR bzw. in W-LAN Konfigurationsmodus  - Buchstabe zurück
def SWR(pin):
    logger.debug("Taste runter")
    global sender, AnzSender, modus, sz
    if modus == 1:                                                                      # Das wird im Radio Modus gemacht
        anzahl_sender()                                                                   # Anzahl Sender aktualisieren
        time.sleep(0.3)                                                                   # Zeit für Doppelbedienung geben
        sender = sender -1                                                            # Sender -1
        if sender > AnzSender :                                                           # Wenn Senderliste am Ende dann mit erstem Sender weiter
            sender = sender - AnzSender
        elif sender <1:                                                                   # Wenn Senderliste auf erstem Sender, dann zu letztem Sender
            sender = AnzSender
        os.system(mpc["play"] + str(sender))
    elif modus == 2:                                                                      # Das wird im MP3 Modus gemacht
        os.system(mpc["prev"])

# Anzahl der gefundenen Sender aus Sender-Datei
def anzahl_sender():
    logger.debug("anzahl_sender")
    global AnzSender
    sn = get_stations()
    AnzSender = len(sn)                                                            # Umwandeln in int

# ShutDown Modus
def VolumeUp(pin):
    logger.debug("VolumeUp")
    os.system(mpc["volumeup"])

# ShutDown Modus
def VolumeDown(pin):
    logger.debug("VolumeDown")
    os.system(mpc["volumedown"])


####################
# Beim Systemstart #
####################
a = 0                          # Einmalige Initialisierung für Zeile C Startindex der Ausgabe
z = 20                         # Einmalige Initialisierung für Zeile C Endindex der Ausgabe
AnzSender = 0                  # Senderanzahl als GLOBAL Variable da Interrupt-Aufrufe keine Rückgabe liefern, 0 als Vorbelegung
sender = 1                     # Aktuelle Sendernummer als GLOBAL Variable da Interrupt-Aufrufe keine Rückgabe liefern, 1 als erster Sender nach Start
modus = 0
my_lcd = lcd()                 # LCD initialisieren
RUMode()                   # RunUp sobald
ZeilenABCD_RUMode(version) # RunUp Anzeige mit Übergabe der Versionsnummer
RAMode()                   # Radio nach RunUp ohne Interrupt starten


######################################
# TastenInerrupts mit Multithreading #
######################################
# Next station
GPIO.add_event_detect(KeyRight, GPIO.FALLING, callback=SWH, bouncetime = 200)
# Previous station
GPIO.add_event_detect(KeyLeft, GPIO.FALLING, callback=SWR, bouncetime = 200)
# OK Key
GPIO.add_event_detect(KeyOk, GPIO.FALLING, callback=SBMode, bouncetime = 200)
# Volume Up Key
GPIO.add_event_detect(KeyVolumeUp, GPIO.FALLING, callback=VolumeUp, bouncetime = 200)
# Volume Down Key
GPIO.add_event_detect(KeyVolumeDown, GPIO.FALLING, callback=VolumeDown, bouncetime = 200)


#################
# Dauerschleife #
#################
logger.debug("Start work loop...")
while True:
    try:
        if modus == 1:
            logger.debug("Mode 1: Radio")
            za = ZeileA_RAMode_MP3Mode_SBMode()
            zb = ZeileB_RAMode()
            zc_tmp, zc_tmp_len = ZeileC_RAMode_MP3Mode()      # Gibt die Sender-Song Info zurück n Zeichen
            if zc_tmp_len > 20:                               # Wenn Songinfo 20 Zeichen (Displayzeile) überschreitet, dann Überhang ermitteln
                ueberhang = zc_tmp_len -20                    # Ermittle Überhang von Zeichen also die Über die Displayreihe hinaus gehen
                if a <= ueberhang:                            # Solange machen bis alle Überhangzeichen abgearbeitet sind,
                    zc = zc_tmp[a:z]                          # Ausgeben und verschieben der Ausgabe des Strings immer um ein Zeichen nach rechts,
                    a = a+1                                   # Wenn a +1 den Überhang erreicht hat, ist der Text einmal komplett durchgelaufen.
                    z = z+1                                   # Z also Ende der Ausgabe muss mit rücken
                else:
                    a = 0                                     # Sobald alle Überhangzeichen durchgelaufen wieder a auf 0
                    z = 20                                    # Sobald alle Überhangzeichen durchgelaufen wieder z auf 0
            else:
                zc = zc_tmp                                   # Wenn Text nicht laenger als Displayzeichen dann normal ausgeben
            zd = ZeileD_RAMode_MP3Mode_SBMode()
            anzeige(za,zb,zc,zd)
        elif modus == 2:
            logger.debug("Mode 1: MP3 Player")
            za = ZeileA_RAMode_MP3Mode_SBMode()
            zb = ZeileB_MP3Mode()
            zc_tmp, zc_tmp_len = ZeileC_RAMode_MP3Mode()      # Gibt die Sender-Song Info zurück n Zeichen
            if zc_tmp_len > 20:                               # Wenn Songinfo 20 Zeichen (Displayzeile) überschreitet, dann Überhang ermitteln
                ueberhang = zc_tmp_len -20                    # Ermittle Überhang von Zeichen also die Über die Displayreihe hinaus gehen
                if a <= ueberhang:                            # Solange machen bis alle Überhangzeichen abgearbeitet sind,
                    zc = zc_tmp[a:z]                          # Ausgeben und verschieben der Ausgabe des Strings immer um ein Zeichen nach rechts,
                    a = a+1                                   # Wenn a +1 den Überhang erreicht hat, ist der Text einmal komplett durchgelaufen.
                    z = z+1                                   # Z also Ende der Ausgabe muss mit rücken
                else:
                    a = 0                                     # Sobald alle Überhangzeichen durchgelaufen wieder a auf 0
                    z = 20                                    # Sobald alle Überhangzeichen durchgelaufen wieder z auf 0
            else:                                             # Wenn Text nicht laenger als Displayzeichen dann normal ausgeben
                zc = zc_tmp
            zd = ZeileD_RAMode_MP3Mode_SBMode()
            anzeige(za,zb,zc,zd)
        elif modus == 31:
            logger.debug("Mode 1: Going into standby")
            za = ZeileA_RAMode_MP3Mode_SBMode()
            (zb,zc) = ZeilenBC_SBMode()
            zd = ZeileD_RAMode_MP3Mode_SBMode()
            anzeige(za,zb,zc,zd)
            time.sleep(3.0)
            za = "--------------------"                       # Schaut besser aus wenn die Zeitleiste ausgeblendet wird
            zd = "--------------------"                       # Schaut besser aus wenn die Datumsleiste ausgeblendet wird
            anzeige(za,zb,zc,zd)
            time.sleep(1.0)
            anzaus()
            modus=32                                          # SB Phase 2 für "bereits im Standby" setzen
        elif modus == 32:
            logger.debug("Mode 1: Standby")
            time.sleep(1.0)                                   # Energie sparen, Schleifendurchlauf verzögern, CPU in Pause.
        elif modus == 4:
            logger.debug("Mode 1: Reboot")
            (za,zb,zc,zd) = ZeilenABCD_RBMode()
            anzeige(za,zb,zc,zd)
            time.sleep(3.0)
            os.system("sudo reboot")                          # Reboot
            time.sleep(3.0)
        elif modus == 5:
            logger.debug("Mode 1: Shutdown")
            (za,zb,zc,zd) = ZeilenABCD_SDMode()
            anzeige(za,zb,zc,zd)
            time.sleep(3.0)
            os.system("sudo halt")                            # Raspi runterfahren
            sys.exit()
        time.sleep(0.2)                                       # Display Aktualisierungszeit z.B. für Scrolltext, also nach welcher Zeit soll die Schleife wieder von oben anfangen.

    except KeyboardInterrupt:                                 # Sonderbehandlung bei STRG+C
        GPIO.cleanup()                                        # Pinbelegung zurücksetzen
        os.system(mpc["stop"])                                # Musik stoppen
        anzaus()                                              # Anzeige aus
        sys.exit()                                            # Aussteigen
