'''
The Tama Main module is designed to:
- Iterate over the folders and files in the Modules folder
- Establish and control the main event loop
- Recieve and handle signals from each module file found in the modules folder
- Establish and control connections between modules so they may communicate with each other in real-time
- Maintain each module as a separate process
- Prevent race conditions by controlling access to resources
- Expose a way to safely terminate the program from any module
'''

import asyncio
import pathlib
import os
import importlib
'''
This section is going to be importing the modules in every subdirectory of the Modules folder,
as well as saving the names of these modules in a List in order to reference them against 
each module's dependencies later.
'''
# Get the absolute path Tama is in, and iterate over each folder in the Modules directory to get the list of module names.
TamaPath = os.path.dirname(__file__)
ModulesPath = TamaPath + '\\Modules'
ModulesList = []

for entry in os.scandir(ModulesPath):
    if entry.is_dir():
        try:
            exec('from Modules.{} import {}'.format(entry.name, entry.name))
            ModulesList.append(entry.name)
        except Exception as e:
            print('Module failed to import: {}'.format(e))
            continue


# Now, initialize each module.
# When modules are done initializing, they should return a list of modules they will need to connect to.
# Each of these lists will be stored, and resolved later, once every available module is initialized.
print('Modules Found: ')
print(ModulesList)
for module in ModulesList:
    try:
        exec('mod = '+ module + '.run()')
    except Exception as e:
            print('Module failed to run: {}'.format(e))
            continue