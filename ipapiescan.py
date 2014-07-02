import biplist
import glob
import os
import re
import subprocess
import zipfile

from os.path import expanduser


def doit(basedir):
    ipas = glob.glob(basedir + "/*.ipa")

    for fn in ipas:
        x = zipfile.ZipFile(fn)

        y = x.namelist()
        infoplist = filter(lambda _: _.endswith('/Info.plist'), y)

        if not infoplist:
            return
        else:
            infoplist = infoplist[0]

        plistData = x.read(infoplist)
        plist = biplist.readPlistFromString(plistData)

        if "CFBundleDisplayName" in plist:
            appname = plist["CFBundleDisplayName"]
        elif "CFBundleName" in plist:
            appname = plist["CFBundleName"]
        else:
            appname = plist["CFBundleIdentifier"]
        appname = appname.ljust(32, ' ')

        if "CFBundleExecutable" not in plist:
            continue

        execFile = filter(lambda _: _.endswith(plist['CFBundleExecutable']), y)

        if not execFile:
            print "Cannot find execFile"
            continue
        else:
            execFile = execFile[0]

        data = x.read(execFile)
        tname = "ipapiescan_XABCDEF"
        f = open(tname, "w+b")
        f.write(data)
        f.close()

        output = subprocess.check_output(["otool", "-vh", tname])
        archstr = ""
        if output.find("ARM         V6") != -1:
            archstr += "armv6"
            bestarch = "armv6"
        if output.find("ARM         V7") != -1:
            if archstr == "":
                archstr = "      armv7"
            else:
                archstr += "|armv7"
            bestarch = "armv7"
        if bestarch == "armv6":
            archstr += "      "

        if archstr == "":
            print "%s - illegal architecture" % (appname)
            print output
        else:
            output = subprocess.check_output(["otool", "-arch", bestarch,
                                              "-vh", tname])
            pie = "PIE   " if "PIE" in output else "NO_PIE"

            output = subprocess.check_output(["otool", "-arch", bestarch,
                                              "-lv", tname])
            if output.find("LC_VERSION_MIN_IPHONEOS") == -1:
                minversion = "N/A"
            else:
                #print output
                p = re.compile('LC_VERSION_MIN_IPHONEOS[^v]*version[^0-9]+([0-9]+\.[0-9]+)', re.MULTILINE | re.DOTALL)
                x = p.search(output)
                minversion = x.groups(0)[0]

            print "%s - %s - %s - %s" % (appname, archstr, pie, minversion)

        os.unlink(tname)


if __name__ == '__main__':
    doit(expanduser("~/Music/iTunes/iTunes Media/Mobile Applications/"))
