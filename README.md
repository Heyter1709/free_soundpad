download the finished exe file - https://drive.google.com/file/d/12Rr0-LsDaUYMN4wttz5t7tUGdOWd2mba/view?usp=sharing
<img width="1456" height="955" alt="изображение" src="https://github.com/user-attachments/assets/b2f88c8c-0199-459b-bbbb-0e1849480910" />
To use it you need to create a virtual cable - https://vb-audio.com/Cable/
Pre-setting
    Virtual audio cable - for correct operation of passthrough and audio output to OBS / Discord, etc. It is recommended to install the free VB‑Cable or Voicemeeter.
    Device selection - in the top panel, select:
        Virtual Cable (out) - the device to which the SoundPad will send the final mix (sounds + microphone).
        Microphone (in) - your physical microphone or line input.
        Then click on the Passthrough: OFF switch - it should turn green and start mixing.
    💡 If passthrough is not enabled, sounds will be played to a standard output device (usually speakers/headphones).
    
Interface and main actions
Left panel (library)
    📚 All Sounds - all downloaded sounds.
    Folders - If you have created folders, they appear here. Contain the sounds you put in them.
    ＋ New Folder - creates a new folder.

Drag&Drop - Drag a sound from All Sounds or another folder onto a folder in the left pane to quickly assign it to that folder.
Central area (sound tiles)
    Displays sounds depending on the selected category (All Sounds or a specific folder).
    Double click / click on the Play button - stops the currently playing sound (if it is playing) and starts the selected one.
    Right mouse button on a tile - context menu: rename, crop, add/remove from folder, delete.

Bottom panel (sound details)
Appears when any sound is selected. Allows:
    Change volume (slider)
    Assign a global hotkey - the combination will always work, regardless of the active folder.
    Assign a key to the current folder - if the sound belongs to a folder, a separate section with the name of the folder will appear. The assigned key only works when that folder is active in the left pane (it's convenient to have the same keys work differently in different contexts).
    Open the trim editor (✂ Trim) or delete the sound.

Global settings (⚙ Settings)
    Hotkeys for the entire application - next track, previous track, stop all.
    Selecting the interface language (restart is not required, but you may need to manually re-open the settings window to apply it).
    Clear All Hotkeys button - resets only global transport combinations (does not affect sound keys).

Trim editor
    Displays the waveform (simplified for performance).
    You can drag the green (start) and red (end) marks, or use sliders.
    Preview button - plays the selected fragment without saving.
    Save Trim - Exports the trimmed portion to a new WAV file and replaces the original audio in the library (all key and folder bindings are preserved).

Playback Control
    Stop All (red button at the top) - stops all sounds and clears the passthrough buffer.
    Global Stop key - if assigned in the settings, stops everything instantly.
    Next / Prev Track - switches between sounds in the current context (All Sounds or current folder). Stops the current sound and starts the next/previous one.
