"""
Module Name:  deviceManager.py
Project:      IoTHubRestSample
Copyright (c) Microsoft Corporation.

Using [Device Indentities REST APIs](https://msdn.microsoft.com/en-us/library/azure/mt548489.aspx) to create a new device identity, retrieve a device identity, and list device identities.

This source is subject to the Microsoft Public License.
See http://www.microsoft.com/en-us/openness/licenses.aspx#MPL
All other rights reserved.

THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, 
EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
"""

import base64
import hmac
import hashlib
import time
import requests
import urllib
import json
import sys

def addDevice():
    data = dm.createDeviceId(deviceId)
    o = json.loads(data[0])
    print('New Device Created')
    print('Device Id: {0}'.format(o['deviceId']))
    print(o['authentication']['symmetricKey'])

def deleteDevice():
    data = dm.deleteDeviceId(deviceId)
    print(data)

def getDeviceKey():
    data = dm.retrieveDeviceId(deviceId)
    o = json.loads(data[0])
    print(o)
    print(o['authentication']['symmetricKey'])

def listDevices():
    data = dm.listDeviceIds()
    o = json.loads(data[0])
    for i in range(0, len(o)):
        print("Device: {0}, Keys: Primary {1} Secondary {2}".format(o[i]['deviceId'], o[i]['authentication']['symmetricKey']['primaryKey'], o[i]['authentication']['symmetricKey']['secondaryKey']))

def help():
    print('Valid Comamnds.')
    print()
    print('Add a New Devce: add deviceId')
    print('Get Device Key: key deviceId')
    print('List add Devices: list')
    print('Delete a device: delete deviceid')


options = {'add' : addDevice, 'key': getDeviceKey, 'list': listDevices, 'delete':deleteDevice, 'help':help }


def config_load():
    try:
        ConfigFile = 'config.json'
        print('Loading {0} settings'.format(ConfigFile))
        config_data = open(ConfigFile)
        config = json.load(config_data)
        return config['ConnectionString']
    except Exception as ex:
        print(ex.args)
        return None


class DeviceManager:
    
    API_VERSION = '2016-02-03'
    TOKEN_VALID_SECS = 365 * 24 * 60 * 60
    TOKEN_FORMAT = 'SharedAccessSignature sr=%s&sig=%s&se=%s&skn=%s'
    
    
    def __init__(self, connectionString=None):
        if connectionString != None:
            iotHost, keyName, keyValue = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
            self.iotHost = iotHost
            self.keyName = keyName
            self.keyValue = keyValue
    
    def _buildExpiryOn(self):
        return '%d' % (time.time() + self.TOKEN_VALID_SECS)
    
    def _buildSasToken(self):
        targetUri = self.iotHost.lower()
        expiryTime = self._buildExpiryOn()
        toSign = '%s\n%s' % (targetUri, expiryTime)
        key = base64.b64decode(self.keyValue.encode('utf-8'))
        signature = urllib.parse.quote(base64.b64encode(hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest())).replace('/', '%2F')
        return self.TOKEN_FORMAT % (targetUri, signature, expiryTime, self.keyName)


    def createDeviceId(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        body = '{deviceId: "%s"}' % deviceId
        r = requests.put(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.text, r.status_code


    def deleteDeviceId(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.delete(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken, 'If-Match' : '*'})
        return r.text, r.status_code

    
    def retrieveDeviceId(self, deviceId):
        sasToken = self._buildSasToken()
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.text, r.status_code
    
    def listDeviceIds(self, top=None):
        if top == None:
            top = 1000
        sasToken = self._buildSasToken()
        url = 'https://%s/devices?top=%d&api-version=%s' % (self.iotHost, top, self.API_VERSION)
        r = requests.get(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken})
        return r.text, r.status_code




if __name__ == '__main__':
    if (len(sys.argv) == 1):
        help()
    else:
        cmd = sys.argv[1].lower()
        if len(sys.argv) > 2:
            deviceId = sys.argv[2]
        else:
            deviceId = 'None Specified'

        print()
        print("command: {0}".format(cmd))
        print("Device: {0}".format(deviceId))
        print()
        connectionString = config_load()
        print()

        dm = DeviceManager(connectionString)

        options[cmd]()

