import paramiko, socket, time, re, csv, os

def disablePaging(remote_conn):

    remote_conn.send("terminal length 0\n")
    time.sleep(1)

    return 1

def writeConfig(configFilename):

    with open(configFilename, "w+") as fileHandle:

        fileHandle.write(output)
        fileHandle.close()

with open('deviceList.txt', 'r') as deviceList:

    for device in deviceList:

        device = device.strip("\n")
        deviceStr = device.split(":")

        if deviceStr[3] == 'NONE':
            usePrivateKey = True
            privateKey = deviceStr[4]
        else:
            usePrivateKey = False
            privateKey = 'NULL'

        host = deviceStr[0].rstrip()
        port = int(deviceStr[1].rstrip())
        username = deviceStr[2].rstrip()
        password = deviceStr[3].rstrip()

        remote_conn_pre = paramiko.SSHClient()

        remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print "Attempting to connect to %s..." % host

            if usePrivateKey == True:
                remote_conn_pre.connect(host, port, username, password, key_filename=privateKey)

            elif usePrivateKey == False:
                remote_conn_pre.connect(host, port, username, password)
            
        except paramiko.BadHostKeyException:
            print "Unable to verify host key of %s" %  host
            continue
        except paramiko.AuthenticationException:
            print "Authentication error. Incorrect password?"
            continue
        except (paramiko.SSHException, socket.error):
            print "Unable to establish SSH connection with %s" % host
            continue
        except Exception as msg:
            print "Unexpected error" 
            print msg
            continue
        else:
            print "SSH connection to %s established" % host
            remote_conn = remote_conn_pre.invoke_shell()

        remote_conn.send("\n")
        disablePaging(remote_conn)
        remote_conn.send("show configuration\n")

        time.sleep(2)

        output = remote_conn.recv(999999)

        timestamp = time.strftime("%Y-%m-%d")

        # Make the hostname / IP address file name friendly by replacing dots with underscores
        hostFile = host.replace(".", "_")
        configFilename = "%s_%s.cfg" % (hostFile, timestamp)

        # If the config file already exists then prompt user to overwrite/not overwrite or view differences
        if os.path.isfile(configFilename) == True:
            while 1:
                overwriteResponse = raw_input("%s already exists! Overwrite? [Y]es/[N]o " % configFilename)
                if overwriteResponse.lower() == "yes" or overwriteResponse.lower() == "y":
                    print overwriteResponse.lower()
                    print "Overwriting %s..." % configFilename
                    try:
                        writeConfig(configFilename)
                    except:
                        print "Unable to write file! Unexpected error."
                    else:
                        print "Succesfully wrote configuration to %s." % configFilename
                    break

                elif overwriteResponse.lower() == "no" or overwriteResponse.lower() == "n":
                    print "Leaving %s alone." % configFilename
                    break
        else:

            try:
                writeConfig(configFilename)
            except:
                print "Unable to write file! Unexpected error."
            else:
                print "Succesfully wrote configuration to %s." % configFilename

        remote_conn.send("\n")
        remote_conn.send("show version\n")

        time.sleep(2)

        showVersion = remote_conn.recv(999999)

        # Search for "HW model:" in the showVersion text and group into 2 groups until first newline
        modelRegex = re.search(r"HW model: (.+)", showVersion)
        model = modelRegex.group(1)
        # Strip whitespace
        model = model.strip(" ")
        model = model.rstrip()
        
        versionRegex = re.search(r"Version: (.+)", showVersion)
        fwVersion = versionRegex.group(1)
        fwVersion = fwVersion.replace("v","")
        fwVersion = fwVersion.strip(" ")
        fwVersion = fwVersion.rstrip()
        
            
        serialRegex = re.search(r"HW S/N: (.+)", showVersion)
        serialNum = serialRegex.group(1)
        serialNum = serialNum.strip(" ")
        serialNum = serialNum.rstrip()

    
        infoList = (host, model, fwVersion, serialNum, timestamp)
        
        print "Attempting to open switchList.csv."
        try:
            with open("switchList.csv", "a+b") as fileHandle:
            
                vowels = ['a', 'e', 'i', 'o', 'u']

                if model[0].lower() in vowels:
                    indefiniteArticle = "an"
                else:
                    indefiniteArticle = "a"

                try:
                    writer = csv.writer(fileHandle, quoting=csv.QUOTE_ALL)
                    writer.writerow(infoList)
                    print "Successfully added %s %s!" % (indefiniteArticle, model) 
                except:
                    print "Unexpected error"
        except:
            print "Unexpected error" 
