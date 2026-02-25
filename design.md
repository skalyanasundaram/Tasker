Description:
 This is n app. developed in python3 and Tkinter for UI. This is used to create/manage simple task, order/reorder the task and star them with different colours. Complete the task. Schdeule a reminder.

 UI design:
 This should run in system tray and also global shortkey to invoke the app. It should be a small rectangulare box appearing in the right botom corner by default. But can be places anywhere. The UI is minimalistic. I dont want the regular window title, I need a thin frame for window title. Inside the frame, like a excel sheet have a rows, each row defines a task. It should be scrollable. Once you reach the bottom you should see empty row where you simply click and type it. It also listen to shift+enter to add a new row below to current row. It should have four column in total. First column should have check box. clicking that will complete the task. Right side should be star, by default not lit up. toggling will go trough will go through different colors. Choose 6 different colors. Fourth column should have a drop down to set a date/time to remind.

 Function:
 When the reminder is hit for any task, popup and select the row. Selection of the row should show the row in different color than other rows. Pressing tab should make the current task child to previous task. Completeing the parent task completes the child tasks.

 Storage: 
 Store this in a file as single json file. The task should not be burried deep down, reason is sometime I might simply edit the json and add a task there directly. Wanted to surface the task text somewhere its easy to view and edit.

 Also the config can be changed. Have a edit/settings menu. By default this menu is not visible. but pressing alt+e will bring. This will open a dialog to show existing config and allow to choose a differnt one. I plan to choose one in onedrive that way its shared across multiple device.

 Pressing Esc should hide the app but still run in tray.

 Additional improvements 1:
  - When clicking the date time picker, it should proper date time picket not just text box. and it should be simple drop down inside the app and not popup outside.
  - When completing a task it should disappear. Another File->Show ->completed task or active task should switch between completed task and active task. When showing completed task continue to show in different color but make it uneditable.
  - First time if there is no config ask for config file location
  - Use ctrl+k, ctrl+k as keybinding to bring to front - guide if its needed to be set somewhere in windows default settings

  Additional improvements 2:
  - the whole app should be manageble by keyboard
  - Add a File->keybindings meny show available shortcut for each operation.
  - Even adding task, moving between each action through arrow keys or tabs and space or enter will do the action. The usual way of navigating a UI
  - tab should not make the task child task rather just navigate to all the component. Shift + arrow should make the task child
  - Add a short cut to switch between active and complete tasks
  - Every popup - settings, shortcut display page should go way if we press esc.
  - The completed task is uneditable - but you can unmark them to make them as active task
  - The navigation is not clear, when I move I can't see which control I am in. Something that helps see better is good.
  - Shift up should move the task up along with its childs in active view implement down as well. In completed view this should not work.
  - once in a while check the file for offline update. Or listen to file handle modification if possible and update the tasks in UI
  - Lets modify the settings page. When opening the settings page, it should have two tabs. One for choosing the task log file as it currentl does. Second is to enable Microsoft ToDo sync. The task sync should have two option. Checkbox to enable/disable the feature. And second text box to ask for Task List Name. It should be one way push to Microsoft todo task. Replace all the task in that task list and update what we can from tasker to Microsoft todo task. Do not touch other task list. It should update the cloud task after every update in background.