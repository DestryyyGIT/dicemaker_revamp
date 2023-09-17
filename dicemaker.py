import configparser, concurrent.futures, os, subprocess, threading, time, tkinter as tk, re, math
from threading import Lock, Thread
from tkinter import ttk, messagebox, Label, Entry, Button, Checkbutton, BooleanVar, font

# Initialize global variables
friend_invites_counter = 0
stop_threads = False
loop_counter = 0
total_dice = 0
close_tabs_counter = 0  # Counter to keep track of loops for closing tabs

# Constants for ADB commands and timing
ADB_SERVER_START_COMMAND = ["adb", "start-server"]
ADB_CONNECTION_BASE_COMMAND = ["adb", "-s"]
ADB_CLEAR_APPS = [
    ["shell", "pm", "clear", "com.scopely.monopolygo"],
    ["shell", "pm", "clear", "com.google.android.gms"],

]
ADB_START_ACTIVITY_COMMANDS = [
    ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d"],
    ["shell", "input", "keyevent", "KEYCODE_ENTER"]
]
TIME_BETWEEN_COMMANDS = 1
ACTIVITY_START_DELAY = 10

# Configuration setup
config = configparser.ConfigParser()
config_filename = "config.ini"

# Load saved user inputs from the configuration file if available
if config.read(config_filename):
    saved_link = config.get("UserInput", "link", fallback="")
    saved_loop_count = config.get("UserInput", "loop_count", fallback="")
    saved_device_ports = config.get("UserInput", "device_ports", fallback="")
    saved_countdown_time = config.get("UserInput", "countdown_time", fallback="")
    saved_dice_count = config.get("UserInput", "dice_count", fallback="")
    saved_milestone_progress = config.get("UserInput", "milestone_progress", fallback="")
    saved_buffer_period = config.get("UserInput", "buffer_period", fallback="")
else:
    # Initialize with default values if no saved configuration is found
    saved_link = ""
    saved_loop_count = ""
    saved_device_ports = ""
    saved_countdown_time = ""
    saved_dice_count = ""
    saved_milestone_progress = ""
    saved_buffer_period = ""

# Function to save user input data to the configuration file
def save_user_input():
    user_input_data = {
        "link": link_entry.get(),
        "loop_count": loop_count_entry.get(),
        "device_ports": device_entry.get(),
        "countdown_time": countdown_entry.get(),
        "dice_count": current_dice_count_entry.get(),
        "milestone_progress": milestone_track_entry.get(),
        "buffer_period": buffer_period_entry.get()
    }

    # Update the configuration file with the user input data
    config["UserInput"] = user_input_data
    with open(config_filename, "w") as configfile:
        config.write(configfile)
    print("User input saved.")

def exit_handler():
    global stop_threads
    
    # Set the flag to stop threads
    stop_threads = True

    # Wait for threads to finish
    time.sleep(2)  # Wait for 2 seconds (adjust this based on your thread execution time)
    
    # Create a new thread to run the disconnect_adb_ports command
    threading.Thread(target=disconnect_adb_ports, args=(device_entry.get(),)).start()
    
    # Create a popup message to inform the user
    popup_message = "Closing threads and connections. Please wait..."

    # Create a new Toplevel window for the popup
    popup = tk.Toplevel(root)
    popup.title("Exiting")

    # Create a label with the popup message
    message_label = Label(popup, text=popup_message)
    message_label.pack(pady=10, padx=10)

    # Set a timer to close the popup window automatically after 2 seconds (2000 milliseconds)
    popup.after(2000, popup.destroy)

    # Print a message to the console
    print("Exiting gracefully")

    # Proceed with destroying the main window after a delay, giving time for the user to read the popup message
    root.after(3000, root.destroy)

    # Get the width and height of the popup window
    popup.update_idletasks()
    popup_width = popup.winfo_width()
    popup_height = popup.winfo_height()

    # Get the width and height of the main window
    main_width = root.winfo_width()
    main_height = root.winfo_height()

    # Get the x and y coordinates of the main window
    main_x = root.winfo_x()
    main_y = root.winfo_y()

    # Calculate the x and y coordinates where the popup should be placed to be centered within the main window
    x = main_x + (main_width - popup_width) // 2
    y = main_y + (main_height - popup_height) // 2

    # Set the x and y coordinates of the popup window to center it within the main window
    popup.geometry(f"+{x}+{y}")

    # Run the kill_adb_server function a little later to ensure the ADB ports have disconnected
    threading.Thread(target=kill_adb_server).start()

# Function to clear app data using ADB for a specific port
def adb_clear(port):
    for command in ADB_CLEAR_APPS:
        subprocess.Popen(ADB_CONNECTION_BASE_COMMAND + [f"localhost:{port}"] + command, creationflags=subprocess.CREATE_NO_WINDOW)

# Function to close tabs, disable the Chrome app, and then re-enable it after a delay for multiple ports
def close_tabs():
    try:
        device_ports_str = device_entry.get().strip()
        if not device_ports_str:
            print("No device ports provided.")
            return
        command = ["shell", "pm", "clear", "acr.browser.barebones"] 
        device_ports = device_ports_str.split()
        for port in device_ports:
            try:
                # Closing Lightning Browser Tabs
                subprocess.Popen(ADB_CONNECTION_BASE_COMMAND + [f"localhost:{port}"] + command, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                print(f"Failed to close tabs for Lightning Browser app on port {port}: {str(e)}")
        ##messagebox.showinfo("Info", "Tabs closed successfully.")
        print(f"\nClosed tabs for Lightning Browser app on all ports.\n")
    except Exception as e:
         print(f"Failed to close tabs fordisable Lightning Browser app on port {port}: {str(e)}")
    time.sleep(1)

# Function to start an activity using ADB with a specified link
def adb_start_activity(port, link):
    subprocess.Popen(ADB_CONNECTION_BASE_COMMAND + [f"localhost:{port}"] + ADB_START_ACTIVITY_COMMANDS[0] + [link], creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.Popen(ADB_CONNECTION_BASE_COMMAND + [f"localhost:{port}"] + ADB_START_ACTIVITY_COMMANDS[1], creationflags=subprocess.CREATE_NO_WINDOW)

# Function to start the ADB server
def start_adb_server():
    subprocess.run(ADB_SERVER_START_COMMAND, capture_output=True, text=True)

# Function to connect to ADB ports
def connect_adb_ports(device_ports):
    if not device_ports:
        raise ValueError("No device ports provided.")

    def connect_single_device(device_port):
        try:
            subprocess.run(["adb", "connect", f"localhost:{device_port}"], capture_output=True, text=True)
        except Exception as e:
            pass

    # Connect to each specified device port in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(device_ports))) as executor:
        executor.map(connect_single_device, device_ports)
        
# Function to disconnect from ADB ports
def disconnect_adb_ports(device_ports_str):
    if not device_ports_str:
        return
    
    device_ports = device_ports_str.strip().split()
    for port in device_ports:
        try:
            subprocess.run(["adb", "disconnect", f"localhost:{port}"], capture_output=True, text=True)
        except Exception as e:
            pass
        
# Function to start ADB server and connect ports
def start_adb_and_connect_ports():
    try:
        start_adb_server()
        device_ports = device_entry.get().strip().split()
        connect_adb_ports(device_ports)
        messagebox.showinfo("Info", "ADB server started and ports connected successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start ADB server and connect ports: {str(e)}")

# Function to kill the ADB server
def kill_adb_server():
    try:
        subprocess.run(["adb", "kill-server"], capture_output=True, text=True)
    except Exception as e:
        pass

def update_dice_count(invites):
    # Update dice count based on milestones and invites generated.
    global update_dice_count_lock
    global total_dice

    with update_dice_count_lock:
        # Define milestone rewards
        milestones = {5: 40, 15: 90, 30: 150}

        try:
            current_dice_count = int(current_dice_count_entry.get())
            milestone_track_progress = int(milestone_track_entry.get())
        except ValueError:
            # If there is an error, set it to the total_dice which keeps track of all the earned dice so far
            current_dice_count = total_dice
            return

        if not (0 <= milestone_track_progress <= 49):
            messagebox.showwarning("Invalid input", "Milestone track progress should be between 0 and 49.")
            return

        dice_earned_this_update = 0

        # Calculate the rewards for crossing milestones
        for milestone, reward in milestones.items():
            if milestone_track_progress < milestone <= milestone_track_progress + invites:
                dice_earned_this_update += reward
                print(f"Reached milestone {milestone} - Earned {reward} dice")

        # If milestone 50 is reached, add the reward and reset milestone progress
        if milestone_track_progress + invites >= 50:
            dice_earned_this_update += 250
            print("Reached milestone 50 - Earned 250 dice")

        total_dice += dice_earned_this_update

        # Update the current_dice_count based on the dice earned in this update
        current_dice_count += dice_earned_this_update

        new_milestone_track_progress = (milestone_track_progress + invites) % 50

        print(f"Ending milestone progress: {new_milestone_track_progress}/50")
        print(f"Dice count updated to {total_dice}")

        update_gui(new_milestone_track_progress, current_dice_count, dice_earned_this_update)

def update_gui(new_milestone_track_progress, current_dice_count, dice_earned_this_update):
    # Update the milestone progress bar
    milestone_percentage = (new_milestone_track_progress / 50) * 100
    milestone_progress_bar['value'] = milestone_percentage
    root.update_idletasks()  # To refresh the GUI and reflect the change immediately

    # Update labels to display the dice count
    dice_count_label.config(text=f"Earned Dice: {total_dice} dice")
    dice_count_label.config(text=f"Earned Dice: {total_dice} dice (this loop: {dice_earned_this_update})")

    total_dice_count = current_dice_count  # total_dice_count is updated based on current_dice_count
    total_dice_count_label.config(text=f"Total Dice Count: {total_dice_count} dice")

    # Update milestone_track_entry and current_dice_count_entry
    milestone_track_entry.delete(0, tk.END)
    milestone_track_entry.insert(0, str(new_milestone_track_progress))

    current_dice_count_entry.delete(0, tk.END)
    current_dice_count_entry.insert(0, str(current_dice_count))

update_dice_count_lock = Lock()
gui_update_lock = Lock()

# Function to run a single action on a device port
def run_single_action(port, link, loop_count, countdown_time, remaining_time, device_ports):
    global stop_threads
    global TIME_BETWEEN_COMMANDS

    # Update TIME_BETWEEN_COMMANDS based on the buffer_period_entry value
    buffer_period = buffer_period_entry.get().strip()
    TIME_BETWEEN_COMMANDS = 1.5 if not buffer_period else float(buffer_period)

    invites_generated = 0  # Keep track of the invites generated by this single loop

    for _ in range(loop_count):
        if stop_threads:
            break

        adb_clear(port)
        time.sleep(TIME_BETWEEN_COMMANDS)
        adb_start_activity(port, link)

        remaining_time = countdown_time  # Initialize remaining_time before countdown
        for sec in range(countdown_time + 1):  # Adjust the loop range to include the initial value
            if stop_threads:
                break
            with gui_update_lock:  # Use a lock to update GUI components safely
                countdown_label.config(text=f"Countdown: {remaining_time} seconds")
                root.update_idletasks()
            remaining_time -= 1  # Decrement the remaining_time after updating the GUI
            time.sleep(1)
        invites_generated += 1  # Increment by 1, because one invite is generated per loop

    if not stop_threads:
        return invites_generated

# Function to run actions continuously
def run_actions():
    global stop_threads
    global remaining_time
    
    stop_threads = False
    
    # Validation
    link = link_entry.get()
    if not link:
        messagebox.showerror("Error", "Link cannot be empty.")
        return
    
    # Check if the "FOREVER" box is checked
    if is_forever.get():
        loop_count = -1  # Set loop_count to -1 to indicate running forever
    else:
        loop_count_str = loop_count_entry.get()
        if not loop_count_str:
            messagebox.showerror("Error", "Loop count cannot be empty.")
            return

        try:
            loop_count = int(loop_count_str)
            if loop_count <= 0:
                messagebox.showerror("Error", "Loop count must be a positive integer.")
                return
        except ValueError:
            messagebox.showerror("Error", "Loop count must be a positive integer.")
            return
        
        milestone_str = milestone_track_entry.get()
        if milestone_str:  # If milestone is not blank
            try:
                milestone = int(milestone_str)
                if not (0 <= milestone <= 49):
                    messagebox.showerror("Error", "Milestone must be a number between 0 and 49.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Milestone must be a valid number or left blank.")
                return

    countdown_time_str = countdown_entry.get()
    try:
        countdown_time = int(countdown_time_str)
        if countdown_time < 0:
            messagebox.showerror("Error", "Countdown cannot be empty.")
            return
    except ValueError:
        messagebox.showerror("Error", "Countdown cannot be empty.")
        return
    
    links = link_entry.get().split()  # Split links by spaces
    loop_count = -1 if is_forever.get() else int(loop_count_entry.get())
    selected_ports_str = device_entry.get().strip()
    selected_ports = selected_ports_str.split()
    countdown_time = int(countdown_entry.get())

    total_actions = len(selected_ports) * loop_count * len(links) if loop_count != -1 else -1
    remaining_time = 0  # Initialize remaining_time to 0

    countdown_label.config(text=f"Countdown: {remaining_time} seconds")

    run_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    if loop_count == -1:  # Run forever
        action_thread = threading.Thread(target=run_actions_forever, args=(links, selected_ports, countdown_time, remaining_time))
    else:
        action_thread = threading.Thread(target=run_actions_thread, args=(links, loop_count, selected_ports, countdown_time, remaining_time))

    action_thread.start()
    print("Loop started.\n")

# Function to run actions continuously with specified loops
def run_actions_thread(links, loop_count, selected_ports, countdown_time, remaining_time):
    global stop_threads
    global loop_counter
    global total_dice
    global close_tabs_counter

    for link in links:  # Move the loop over links outside the loop_count loop
        if stop_threads:
            break
        print(f"Processing link: {link} \n")  # Print the current link being processed

        for _ in range(loop_count):
            if stop_threads:
                break
            run_actions_helper([link], selected_ports, countdown_time, remaining_time, selected_ports)

            loop_counter += 1
            loop_counter_label.config(text=f"Loops Completed: {loop_counter}")

            # Check if it's time to close tabs (every 5 loops)
            close_tabs_counter += 1
            if close_tabs_counter >= 5:
                close_tabs_counter = 0
                close_tabs()

# Function to run actions continuously forever
def run_actions_forever(links, selected_ports, countdown_time, remaining_time):
    global stop_threads
    global loop_counter  # Declare loop_counter as global in this function
    global close_tabs_counter  # Add a counter for closing tabs

    while not stop_threads:
        run_actions_helper(links, selected_ports, countdown_time, remaining_time, selected_ports)
        if stop_threads:
            break
        loop_counter += 1
        loop_counter_label.config(text=f"Loops Completed: {loop_counter}")

        # Check if it's time to close tabs (every 5 loops)
        close_tabs_counter += 1
        if close_tabs_counter >= 5:
            close_tabs_counter = 0
            close_tabs()
            
# Function to execute actions with multi-threading
def run_actions_helper(links, selected_ports, countdown_time, remaining_time, device_ports):
    global stop_threads
    global loop_counter
    global total_dice  # Add this line to access the global total_dice variable

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected_ports)) as executor:
        futures = []

        for link in links:
            if stop_threads:
                break
            for port in selected_ports:
                if stop_threads:
                    break
                future = executor.submit(run_single_action, port, link, 1, countdown_time, remaining_time, device_ports)
                futures.append(future)

    concurrent.futures.wait(futures)
    total_invites_generated = sum(future.result() for future in futures if future.result() is not None)

    if not stop_threads:
        update_dice_count(total_invites_generated)

    if stop_threads:
        return

    print("Loop "+str(loop_counter+1)+" completed.\n")

# Function to stop all looping
def stop_actions():
    global stop_threads
    global loop_counter  # Make sure to use the global variable
    
    stop_threads = True
    loop_counter = 1  # Reset the loop counter when stopping

    loop_counter_label.config(text="Loops Completed: 0")  # Reset the label
    stop_button.config(state=tk.DISABLED)
    run_button.config(state=tk.NORMAL)  # Re-enable the "run actions" button here
    print("Actions stopped.")

# Function to toggle running actions forever
def toggle_forever():
    # Disable loop_count_entry when running forever
    loop_count_entry.config(state=tk.DISABLED if is_forever.get() else tk.NORMAL)
    print(f"\nFOREVER! toggled to {is_forever.get()}")

# Function to calculate the required loops to reach a milestone reward
def calculate_required_loops(device_ports_str, max_milestone):
    try:
        device_count = len(device_ports_str.split())  # Split and count the device ports
        if device_count == 0:
            print("No devices, no loops required")
            return 0  # No devices, no loops required

        loops_needed = math.floor(max_milestone/ (device_count))  # Calculate loops required
        print(f"Device Ports: {device_ports_str}")
        print(f"Device Count: {device_count}")
        print(f"Milestone Reward: {max_milestone}")
        print(f"Loops Needed: {loops_needed}")
        return loops_needed
    except Exception as e:
        print(f"Error calculating loops needed: {str(e)}")
        return 0  # Return 0 loops on error


# Function to handle the "Quick 530" button click
def calculate_and_set_loops():
    device_ports_str = device_entry.get().strip()
    max_milestone = 50 # Set your milestone reward here
    loops_needed = calculate_required_loops(device_ports_str, max_milestone)
    
    if loops_needed > 0:
        loop_count_entry.delete(0, tk.END)
        loop_count_entry.insert(0, str(loops_needed))
        print(f"Calculated and set loops to {loops_needed}")
        
# Create the main application window
root = tk.Tk()
root.title("Cube Maker Unofficial v1.6")
root.configure(bg="#f0f0f0")

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the center coordinates
x = (screen_width - 400) // 2  # 400 is the window width
y = (screen_height - 1000) // 2  # 1000 is the window height

# Set the window size and position it at the center
root.geometry("720x800+{}+{}".format(x, y))

# Create a frame to hold the interface elements
frame = ttk.Frame(root, padding=0)
frame.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

# Configure grid columns to have equal weight
frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

# Create a custom font configuration for bold text
button_font = ("Segoe UI", 10, "bold")

# Create the header label
header_label = Label(frame, text="Cube Maker", font=("Helvetica", 16, "bold"), padx=10, pady=10)
header_label.grid(row=0, column=0, columnspan=4, sticky="ew")

# Create the "Start ADB and Connect Ports" button
adb_button = Button(frame, text="Start ADB and Connect Ports", command=start_adb_and_connect_ports,
                    padx=20, bg="#9DA5B2", font=button_font, fg="black")
adb_button.grid(row=2, column=0, columnspan=1, padx=5, pady=10, sticky="ew")

# Create the "Close Tabs" button to the right of "Start ADB"
close_tabs_button = Button(frame, text="Close Tabs (Lightning Browser Only!)", command=close_tabs,
                           padx=20, bg="#9DA5B2", font=button_font, fg="black")
close_tabs_button.grid(row=2, column=1, columnspan=1, padx=5, pady=10, sticky="ew")

# Create labels and input fields for user configuration
link_label_text = "Enter the HTTP link (space if multilink): *"
link_label = Label(frame, text=link_label_text, padx=10, pady=5)
link_label.grid(row=3, column=0, sticky="w")

link_entry = Entry(frame, width=45)
link_entry.grid(row=3, column=1, padx=10, pady=5)
link_entry.insert(0, saved_link)

device_label = Label(frame, text="Enter device port numbers (space-separated): *")
device_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
device_entry = Entry(frame, width=30)
device_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
device_entry.insert(0, saved_device_ports)

loop_count_label = Label(frame, text="Enter the number of times to run the loop: *")
loop_count_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
loop_count_entry = Entry(frame, width=10)
loop_count_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
loop_count_entry.insert(0, saved_loop_count)

is_forever = BooleanVar()
forever_button = Checkbutton(frame, text="FOREVER!", variable=is_forever, command=toggle_forever)
forever_button.grid(row=5, column=1, padx=(100, 10), pady=5, sticky="w")

current_dice_count_label = Label(frame, text="Enter your current dice count:")
current_dice_count_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
current_dice_count_entry = Entry(frame, width=10)
current_dice_count_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
current_dice_count_entry.insert(0, saved_dice_count)

milestone_track_label = Label(frame, text="Enter your milestone track progress (0-49):")
milestone_track_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
milestone_track_entry = Entry(frame, width=10)
milestone_track_entry.grid(row=7, column=1, padx=10, pady=5, sticky="w")
milestone_track_entry.insert(0, saved_milestone_progress)

countdown_label = Label(frame, text="Enter countdown time (typically 10-35s): *")
countdown_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")
countdown_entry = Entry(frame, width=10)
countdown_entry.grid(row=8, column=1, padx=10, pady=5, sticky="w")
countdown_entry.insert(0, saved_countdown_time)

buffer_period_label = Label(frame, text="Enter buffer period in between loops (Default 1.5s) :")
buffer_period_label.grid(row=9, column=0, padx=10, pady=5, sticky="w")
buffer_period_entry = Entry(frame, width=10)
buffer_period_entry.grid(row=9, column=1, padx=10, pady=5, sticky="w")
buffer_period_entry.insert(0, saved_buffer_period)

# Create a label for countdown
countdown_label = Label(frame, text="Countdown: 0 seconds")
countdown_label.grid(row=11, column=0, columnspan=2, padx=10, pady=5)

# Create buttons to save user input and run actions
save_button = Button(frame, text="Save Input", command=save_user_input, padx=20, bg="#96BFFD", font=button_font, fg="black")
save_button.grid(row=12, column=0, columnspan=1, padx=5, pady=10, sticky="ew")

run_button = Button(frame, text="Run Actions", command=run_actions, padx=20, bg="#66B266", font=button_font, fg="black")
run_button.grid(row=12, column=1, columnspan=1, padx=5, pady=10, sticky="ew")

quick_530_button = Button(frame, text="Quick 530", command=calculate_and_set_loops,
                       padx=20, bg="#FFA500", font=button_font, fg="black")
quick_530_button.grid(row=12, column=2, padx=5, pady=10, sticky="ew")

# Create a button to stop actions (initially disabled)
stop_button = Button(frame, text="STOP", command=stop_actions, state=tk.DISABLED, padx=20, bg="#FF0000",
                     width=10, font=button_font, fg="black", disabledforeground="black")
stop_button.grid(row=13, column=0, columnspan=4, padx=5, pady=10, sticky="ew")

# Adding labels for milestones (0 to 50) above the progress bar
milestone_labels_frame = ttk.Frame(frame)
milestone_labels_frame.grid(row=18, column=0, columnspan=4, sticky="ew")
for i, milestone in enumerate(range(0, 51, 5)):  # Creating labels at intervals of 5
    lbl = Label(milestone_labels_frame, text=str(milestone))
    lbl.grid(row=0, column=i, sticky="n")
    milestone_labels_frame.grid_columnconfigure(i, weight=1)  # This ensures even distribution of labels

# Create a progress bar for milestones
milestone_progress_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
milestone_progress_bar.grid(row=19, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

# Create labels to display earned and total dice counts
dice_count_label = Label(frame, text="Earned Dice: 0 dice")
dice_count_label.grid(row=14, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

total_dice_count_label = Label(frame, text="Dice Count: 0 dice")
total_dice_count_label.grid(row=15, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

# Create a label to display the number of loops completed
loop_counter_label = Label(frame, text="Loops Completed: 0")
loop_counter_label.grid(row=16, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

# Create a button to reset dice counts
def reset_dice_counts():
    global total_dice
    global loop_counter
    total_dice = 0
    loop_counter = 0
    dice_count_label.config(text="Earned Dice: 0 dice (this loop: 0)")
    total_dice_count_label.config(text="Total Dice Count: 0 dice")
    loop_counter_label.config(text="Loops Completed: 0")
    milestone_track_entry.delete(0, tk.END)
    milestone_track_entry.insert(0, "0")
    current_dice_count_entry.delete(0, tk.END)
    current_dice_count_entry.insert(0, "0")
    milestone_progress_bar['value'] = 0  # Reset the progress bar value to 0

# Create a button to reset individual input fields
def reset_entry(entry):
    entry.delete(0, tk.END)

reset_link_button = Button(frame, text="Reset", command=lambda: reset_entry(link_entry))
reset_link_button.grid(row=3, column=2, padx=10, pady=5, sticky="w")

reset_device_button = Button(frame, text="Reset", command=lambda: reset_entry(device_entry))
reset_device_button.grid(row=4, column=2, padx=10, pady=5, sticky="w")

reset_loop_count_button = Button(frame, text="Reset", command=lambda: reset_entry(loop_count_entry))
reset_loop_count_button.grid(row=5, column=2, padx=10, pady=5, sticky="w")

reset_current_dice_count_button = Button(frame, text="Reset", command=lambda: reset_entry(current_dice_count_entry))
reset_current_dice_count_button.grid(row=6, column=2, padx=10, pady=5, sticky="w")

reset_milestone_track_button = Button(frame, text="Reset", command=lambda: reset_entry(milestone_track_entry))
reset_milestone_track_button.grid(row=7, column=2, padx=10, pady=5, sticky="w")

reset_countdown_button = Button(frame, text="Reset", command=lambda: reset_entry(countdown_entry))
reset_countdown_button.grid(row=8, column=2, padx=10, pady=5, sticky="w")

reset_buffer_period_button = Button(frame, text="Reset", command=lambda: reset_entry(buffer_period_entry))
reset_buffer_period_button.grid(row=9, column=2, padx=10, pady=5, sticky="w")

# Create a button to reset dice counts
reset_button = Button(frame, text="Reset", command=reset_dice_counts)
reset_button.grid(row=17, column=0, padx=(7.5, 5), pady=10, sticky="w")

# Create a footer frame and labels for additional information
footer_frame = ttk.Frame(root, padding=10)
footer_frame.grid(row=19, column=0, columnspan=2, padx=10, pady=10, sticky="w")

footer_label = Label(footer_frame, text="* = Required.", bg="#f0f0f0")
footer_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

footer_label_spooky = Label(footer_frame, text="Original code developed by SpookyFlush and otreborob. Unofficial update by josh1121 on Discord.", bg="#f0f0f0")
footer_label_spooky.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="n")

# Create a style for the progress bar
style = ttk.Style()
style.configure("TProgressbar", thickness=7, relief='flat', background='#00aaff')

# Configure grid weights for resizing
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

stop_threads = False
remaining_time = 0

def only_numbers(P):
    if P == "":
        return True
    try:
        float(P)
        return True
    except ValueError:
        return False

validate_cmd = root.register(only_numbers)

# Apply the validation to the appropriate Entry widgets
loop_count_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
current_dice_count_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
milestone_track_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
countdown_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
buffer_period_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))

# Start the main event loop
root.protocol("WM_DELETE_WINDOW", exit_handler)  # Bind the exit_handler to window close
root.mainloop()
