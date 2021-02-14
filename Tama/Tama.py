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
from task import task
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

#searches the task pool for the first task where target_module is module, and returns the index.
def find_task(module, task_pool):
    for idx, task in enumerate(task_pool):
        if str(task.get_module()) == module:
            return idx
    return None

for entry in os.scandir(ModulesPath):
    if entry.is_dir():
        try:
            if entry.name in ModulesList:
                raise ImportError('Module {} has same name as another module. Module Folders must have unique names.'.format(entry.name))
            exec('from Modules.{} import {}'.format(entry.name, entry.name))
            exec('mod = {}.{}()'.format(entry.name, entry.name, entry.name))
            ModulesList.append(entry.name)
            vars()[entry.name] = mod
        except Exception as e:
            print('Module failed to import: {}'.format(e))
            continue


# Now, initialize each module.
# When modules are done initializing, they should return a list of modules they will need to connect to.
# Each of these lists will be stored, and resolved later, once every available module is initialized.
print('Modules Found: ')
print(ModulesList)

#task_pool will be a list of tuples with three entries. (target_module (string), target_function (string), argument_list (list of strings))
#task_pool will be updated after every module tick, if response is populated with a tupl, or 'EXIT TAMA'. Else, response will be ignored.
task_pool = [task('CLI', 'print_welcome', [])]
exit_condition = False
while not exit_condition:
    for module in ModulesList:
        try:
            task_idx = find_task(module, task_pool)
            if task_idx is not None and task_idx < len(task_pool):
                task = task_pool[task_idx]
                response = vars()[module].tick(task)
            if type(response) is type(task):
                task_pool.append(response)
            if response == 'EXIT TAMA':
                exit_condition = True
        except Exception as e:
            print('Module failed to tick: {}'.format(e))
            continue
