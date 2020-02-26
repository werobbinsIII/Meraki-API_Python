READ_ME = '''
OPTIONS:
MIT License

Copyright (c) 2020 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Exports SSID status information to a csv file in the results folder.

Be sure to save your API key as an OS environmental variable.

The syntax will be as follows:

python3 ssid_status.py -o <ORG ID>

ex. python3 ssid_status.py -o 123456
'''

import getopt
import sys
import meraki
import csv
import os

bufferWriteList = []


def csvOut(filename, headers):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(headers)
        for row in bufferWriteList:
            writer.writerow(row)


def getStatus(orgId):

    m = meraki.DashboardAPI(base_url='https://api-mp.meraki.com/api/v1', output_log=False)
    networks = m.networks.getOrganizationNetworks(orgId)
    print('Acquiring list of APs from {0} networks for organization ID {1}'.format(len(networks), orgId))

    netIdx = 0

    apNetworks = [network for network in networks if 'wireless' in network['productTypes']]
    print('Found {0} AP networks in the org'.format(len(apNetworks)))
    for network in apNetworks:
        accessPoints = m.devices.getNetworkDevices(network['id'])
        for ap in accessPoints:
            if 'MR' in ap['model']:
                status = m.ssids.getNetworkDeviceWirelessStatus(ap['networkId'], ap['serial'])
                for k, v in status.items():
                    for bss in v:
                        if bss['enabled'] == True:
                            ap.setdefault('name')
                            bufferWriteList.append([network['name'], bss['ssidName'], bss['bssid'], bss['band'],
                                                    ap['name'], bss['channel'], bss['channelWidth'], bss['power'],
                                                    bss['visible'], bss['broadcasting'], ap['firmware']])
        print('Finished processing data from APs in network {0}'.format(network['name']))
        netIdx += 1
        print('------- {0}% COMPLETE -------\n'.format(round(100 * float(netIdx)/float(len(apNetworks)))))

    headerRow = ['Network Name', 'SSID', 'BSSID', 'Frequency Band', 'AP Name', 'Channel', 'Channel Width', 'Transmit Power',
                 'Visible', 'Broadcasting', 'Firmware']
    csvOut('./results/ssid_status.csv', headerRow)
    print('The csv file has been exported to ./results/ssid_status.csv')



def print_help():
    lines = READ_ME.split('\n')
    for line in lines:
        print('# {0}'.format(line))


def main(argv):

    try:
        opts, args = getopt.getopt(argv, "ho:")
        if len(argv) is not 2:
            print('****** # ERROR: Incorrect number of parameters given ******')
            print_help()
            sys.exit()
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print_help()
            sys.exit()
        elif opt == "-o":
            org = arg
            getStatus(org)
        else:
            print_help()
            sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])

