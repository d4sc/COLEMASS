from django.db import models
from django.utils import timezone
import datetime

class Hardware(models.Model):
    """ Hardware base class """
    hwid = models.CharField(max_length=8, unique=True)
    password = models.CharField(max_length=16)
    name = models.CharField(max_length=64, unique=True)
    one_time_pad = models.CharField(max_length=32)
    is_pad_used = models.BooleanField()
    pad_expires = models.DateTimeField()


    def getHwid(self):
        return self.hwid

    # def setHwid(self, newHwid):
    #     if newHwid.isalnum() and len(newHwid) <= 8:
    #         self.hwid = newHwid
    #         self.save()

    def getPassword(self):
        return self.password

    def publicPassword(self):
        return self.password[:4] + '*'*10

    def getName(self):
        return self.name

    # def setPassword(self, newPassword):
    #     if newPassword.isalnum() and len(newPassword) <= 16:
    #         self.password = newPassword
    #         self.save()

    @staticmethod
    def generateHash(hardwareId, rndBytesStr):
        import binascii
        import hashlib
        try:
            hw = Hardware.objects.get(hwid=hardwareId)
            if len(rndBytesStr) == 32:
                sha = hashlib.sha256()
                # non hex values will raise an exception
                sha.update(binascii.a2b_hex(rndBytesStr))
                sha.update(hw.password.encode('ascii'))
                return binascii.hexlify(sha.digest()).decode('ascii')
            else:
                return '0'
        except Exception:
            return '0'

    @staticmethod
    def decryptMessage(hardwareId, msg):
        from Crypto.Cipher import AES
        from Crypto.Hash import SHA256
        import binascii
        import base64
        # for debug reasons try block is commented
        # try:
        hw = Hardware.objects.get(hwid=hardwareId)
        buff = base64.urlsafe_b64decode(msg)
        buffLen = len(buff)
        # valid messages are at least 48 bytes
        if buffLen >= 48:
            sha = SHA256.new()

            # check if one_time_pad is valid
            if hw.isPadValid():
                sha.update(binascii.unhexlify(hw.one_time_pad))
                sha.update(hw.password.encode('ascii'))
                b = sha.digest()
                cip = buff[0:-32]
                sha.update(cip)
                if sha.digest() == buff[-32:]:
                    obj = AES.new(b[16:32], AES.MODE_CBC, b[0:16])
                    decr = obj.decrypt(cip).rstrip(b'\x00')
                    arg_list = decr.decode('ascii').split(",")

                    # process message
                    return Hardware.processMessage(arg_list)
                else:
                    # message was tampered
                    return '-1'
            else:
                # one time pad is not valid
                return '-5'
        else:
            # illegal message size
            return '-2'
        # for debug reasons 'try' block is commented
        # except Exception:
        # exceptional errors
    @staticmethod
    def processMessage(arg_list):
        from dishes.models import ItemTracker
        from appliances.models import Appliance
        # 3 = Appliance Logout
        if arg_list[0] == '3':
            if len(arg_list) >= 2:
                appl = Appliance.objects.get(hwid=arg_list[1])
                appl.logout()
            else:
                # bad arguments (only ApplID as argument)
                return '-10'


        # 4 = Appliance Login
        elif arg_list[0] == '4':
            if len(arg_list) >= 3:
                appl = Appliance.objects.get(hwid=arg_list[1])
                appl.login(arg_list[2])
            else:
                # bad arguments (arguments must consist of CardID + ApplID)
                return '-10'


        # 5 = Appliance Report
        elif arg_list[0] == '5':
            if len(arg_list) >= 2:
                appl = Appliance.objects.get(hwid=arg_list[1])
                appl.report()
            else:
                 # bad arguments (only ApplID as argument)
                 return '-10'

        # 6 = take dishes out
        elif arg_list[0] == '6':
            if len(arg_list) >= 3:
                return ItemTracker.takeItemOut(arg_list[1:-1], arg_list[-1])
            else:
                # bad arguments
                return '-10'

        # 7 - put dishes back
        elif arg_list[0] == '7':
            if len(arg_list) >= 3:
                return ItemTracker.putItemIn(arg_list[1:-1], arg_list[-1])
            else:
                # bad arguments
                return '-10'

        else:
            # wrong command request
            return '-3'

    def generatePad(self):
        import os
        import binascii
        self.one_time_pad = binascii.hexlify(os.urandom(16)).decode('ascii')
        self.is_pad_used=False
        self.pad_expires = timezone.now() + datetime.timedelta(seconds=10)
        self.save()
        return self.one_time_pad

    def usePad(self):
        if self.isPadValid():
            self.is_pad_used=True
            return self.one_time_pad
        else:
            return -1

    def isPadValid(self):
        if (self.is_pad_used == True) or (timezone.now() > self.pad_expires):
            return False
        else:
            return True

    def __str__(self):
        return self.name
