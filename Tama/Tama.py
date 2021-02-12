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
from queue import Queue
'''
This section is going to be importing the modules in every subdirectory of the Modules folder,
initializing the main classes they contain, and then will then run the tick() function for each
module contained in the folder, adding each returned function from tick to the event queue for 
future processing.
'''
# Get the absolute path Tama is in, and iterate over each folder in the Modules directory to get the list of module names.
TamaPath = os.path.dirname(__file__)
ModulesPath = os.path.join(TamaPath, 'Modules')
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
        #initialize each module as a class with the name stored in module
        exec('mod = {}.{}()'.format(module, module, module))
        vars()[module] = mod
    except Exception as e:
            print('Module failed to initialize: {}'.format(e))
            continue

for module in ModulesList:
    try:
        vars()[module].tick('this is a call for help')
    except Exception as e:
        print('Module failed to tick: {}'.format(e))
        continue