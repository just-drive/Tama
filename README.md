

## Tama - The Friend in Your PC (DEVELOPMENT IN PROGRESS)

### General Idea:

There’s something in your PC! What is it? Nothing other than Tama, of course. You have to take basic
care of it, but if you do, it will help you do things around your PC. It
can become your own personal assistant, and might just make things
easier in your life on your computer. It’s a Tamagotchi with benefits.
An extensible productivity tool.
Find Tama here:​ ​https://github.com/just-drive/Tama


Tama will run until the health meter reaches 0. Feed files to Tama in order to keep him alive.

### Features/Basic Requirements User Story:

_*words marked in “quotations” are nuanced forms of the word used, usually this nuance is because the
word is used as a variable name, folder name, or status in the application._

#### Milestone 1 Features – Basic Needs and CLI - Due By: March 1st, 2021 (Sprint 1)

Begin with a command line interface (CLI) that serves to inspect the status of Tama and interact with
Tama. Tama will parse text input as a regular expression and respond to things with basic emoticons so
you know how it is feeling. The following items are basic upkeep tasks that make Tama feel more like a
desktop friend/pet and will be a part of the basic Tama system (in the main module).

1. Tama can get hungry, tired, happy, or sad.
    a. Tama gets hungry at a rate that can be set.
       i. When Tama’s hunger levels hit a certain threshold, Tama will attempt to
          consume a file from its “food” folder, permanently deleting it, and decreasing
          Tama’s hunger levels proportionally to the size of the file deleted.
    b. Tama gets sleepy when you ask it to do things for long periods of time, or when it gets
       bored.
       
2. Extensibility, or how moddable Tama is, is a core feature that is desired in Tama’s system. Our
    wish for Tama is to allow knowledgeable users to modify, create, add, and remove features to fit
    their own preferences. Thus, we need to provide a system that accepts “modules” that serve as
    extensions or modifiers to Tama. Future additions from our team will be implemented as
    modules, to keep with this idea of easily applicable extensions.
       a. The Tama main module will have a framework that allows modules as .py files to be
          included in the “Tama Modules” folder, which will scan each module file, and include it
          in the running processes whenever it is successfully scanned.

#### Milestone 2 Features – Productivity Tools - Due By: March 22nd, 2021 (Sprint 2)

After implementing the CLI and module system to interact with and modify Tama, we will need to
implement the basic productivity tasks that Tama should be able to do for you. These tasks will be added
to Tama’s system as separate modules that speak with Tama behind the scenes.

1. Record macro - when activated, captures mouse movements, clicks, keypresses, etc. until
    deactivated. Then stores these movements as a macro that can be used as an action for the hotkey
    service.
2. Copy x - Serves as an extension of the OS’s built-in clipboard, allowing one to intuitively store
    and recall more than one item from the clipboard at a time.
3. Hold Window - Drag Tama onto a window on your desktop and it will “grab” the window,
    pinning it at the top of all the windows on your desktop, until the window is minimized or Tama
    is taken off it.

#### Milestone 3 Features – Animation and GUI Polishing - Due By: April 5th (Sprint 3)

After implementing Tama’s productivity functionalities, we will need to provide a more intuitive and
endearing GUI for Tama. To do this, we will better polish Tama’s model, and will animate Tama to
perform behaviors based on what is happening to it. This will complete the feeling of Tama being a
“desktop pet” or “desktop friend.”

1. Record hotkey - Captures keypresses and stores them, when a match is found later while Tama is
    running, Tama will perform an action associated with a hotkey when it detects the hotkey as
    having been pressed.
2. Tama’s development form will be a slime. This allows for easy animation (physics body) and
    emotion (emojis) to be displayed and evident to the user.
3. Tama’s Settings GUI will be included as a separate program that can be opened from within
    Tama’s main folder. This will allow users to modify program data in a menu-based format. Data
    changed in the settings menu application can be immediately applied from within this application.
4. Future Tama “skins” and animations can be applied via an extension module by outside
    programmers and animators if they wish to make Tama look or behave differently.


#### Milestone 4 Features – Final Release - Due By: April 26th (Sprint 4)

#### 1. Tama for Linux ​ - A Linux version of Tama designed to run on Debian-based systems such as

#### Ubuntu ​.

2. Any additional features that our customers and users may request to be implemented should be
    implemented here
3. Release v1.0 - Final Deliverable and fully-featured release for Tama.
4. Child-safety features may be implemented to ease concerns of younger users causing irreparable
    damage to OS as a result of Tama.

### Tama Competition - What We Do

Our program will be an executable-equivalent type file (For Windows and Linux) which allows the user to
interact with on the desktop while running. Compared to the above list of programs, our program is 
unique in that it combines the features of AutoHotkey, Macro Editor, Productivity Tools, Tamagotchi, 
Desktop Pet, etc. as one single program. The interface will be minimalistic in the sense that a majority 
of the user’s interactions will be hotkey based, similar to AutoHotkey, in order to reduce the impact 
that Tama will have on productivity and focus. Whereas Tama can be directly interacted with as an avatar 
that will be placed on the user’s desktop and which can be moved around the user’s screen, similar to 
Desktop Pet:Shimeji-ee. The settings interface will be a separate application that a knowledgeable user 
can use to modify the core variables that drive Tama’s behavior, in order to prevent the number of 
running processes during day-to-day use. On top of this, Tama’s functionalities will be governed with 
extension modules, similar to AutoHotkey, and most users will not need to have coding or scripting 
experience to use Tama for casual purposes.

Keep him fed, and he will stay funky.
