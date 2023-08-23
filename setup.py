import os


def CreateFolders():
    folders = ["src", "include", "lib", "scripts"]
    print("Creating folders...")

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print("Created folder: " + folder)
        else:
            print("Folder already exists: " + folder)


def CreateMain():
    # Blink code for main.cpp
    srcMain = """
#include <stdio.h>
#include "pico/stdlib.h"

#define LED_PIN PICO_DEFAULT_LED_PIN

int main()
{
    // Init stdio
    stdio_init_all();

    // Setup the blink pin
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    // Blink the LED
    while (1)
    {
        gpio_put(LED_PIN, 1);
        sleep_ms(250);
        gpio_put(LED_PIN, 0);
        sleep_ms(250);
    }
}
"""

    # Write to main
    with open("src/main.cpp", "w") as f:
        f.write(srcMain)


def CreateCMakeLists(projectname):
    # CMakeLists.txt
    cmake = """
# Set minimum required version of CMake
cmake_minimum_required(VERSION 3.15)

# Include build functions from Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
include($ENV{PICO_SDK_PATH}/tools/CMakeLists.txt)

# Set name of project (as PROJECT_NAME) and C/C standards
"""

    # Add the project name based on the folder name the script is run in
    cmake += "project(" + projectname + " C CXX ASM)"
    cmake += """
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Creates a pico-sdk subdirectory in our project for the libraries
pico_sdk_init()

# Add the include directory to our build
include_directories(${CMAKE_BINARY_DIR}/include)

# Tell CMake where to find the executable source file
add_executable(${PROJECT_NAME} 
    ${CMAKE_CURRENT_LIST_DIR}/src/main.cpp
)

# Add all the source files in the lib directory to the project
AUX_SOURCE_DIRECTORY(lib SUB_SOURCES)

# Add the source files to the project
target_sources(${PROJECT_NAME} PUBLIC 
    ${SUB_SOURCES}
)

# Add the include directories to the project
target_include_directories(${PROJECT_NAME} PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}
)

# Link to pico_stdlib (gpio, time, etc. functions)
target_link_libraries(${PROJECT_NAME} 
    pico_stdlib
)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(${PROJECT_NAME})

# Enable usb output, disable uart output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Run the programming script to program the device
add_custom_command(TARGET ${PROJECT_NAME}
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E echo "Programming device..."
    COMMAND python3 ${CMAKE_SOURCE_DIR}/scripts/programmer.py
    DEPENDS ${CMAKE_SOURCE_DIR}/scripts/programmer.py 
    DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.u2f
    FORCE
)
"""

    # Write to CMakeLists.txt
    with open("CMakeLists.txt", "w") as f:
        f.write(cmake)


def CreateReadme(projectname):
    # README.md
    readme = "# " + projectname

    # Write to README.md
    with open("README.md", "w") as f:
        f.write(readme)


def CreateGitignore():
    # .gitignore
    gitignore = """
# VSCode
.vscode/
build/
*.uf2
"""

    # Write to .gitignore
    with open(".gitignore", "w") as f:
        f.write(gitignore)


def CreateProgrammer(projectname):
    # programmer.py
    programmer = "file_name = \"" + projectname + ".uf2\""
    programmer += """
file_path = "../build/" + file_name

# Pico constants for detecting the device
device_target = "RPI-RP2"
vendor_id = "2E8A"
product_id = "000A"


# Import the required modules
import os
import sys
import shutil
import subprocess
import time


# Fix the path so that the script can be run from any directory
file_path = os.path.abspath(file_path)


# if the operating system is windows, check if the 'pywin32' module is installed and install it if not
if os.name == "nt":
    # check if the 'pywin32' module is installed and install it if not
    try:
        import win32api
    except ImportError:
        print("The 'pywin32' module is not installed. Installing now...")
        subprocess.call([sys.executable, "-m", "pip", "install", "pywin32"])
        import win32api


# Scan for a particular device and return true if found
def Scan_For_MassStorage(device_name):
    if os.name == "nt":  # Windows
        # get a list of all mounted volumes using the win32api module
        volumes = win32api.GetLogicalDriveStrings()
        volumes = volumes.split('\x00')[:-1]

        # loop over the mounted volumes and look for a volume with the correct label
        for volume in volumes:
            try:
                label = win32api.GetVolumeInformation(volume)[0]
            except:
                # skip this volume if there is an error accessing the label
                continue

            if label == device_name:
                return True
            
    else:  # Linux
        # get all the connected devices
        for partition in psutil.disk_partitions():
            # check if the device name is in the partition device name
            if device_name in partition.mountpoint:
                return True
            
        return False
    

# Wait for the device to be mounted
def Wait_For_MassStorage_Device():
    print("Waiting for the device to be mounted...")
    while(True):
        # check if the device is mounted
        if Scan_For_MassStorage(device_target):
            break
        else:
            time.sleep(0.5)


# Transfer the uf2 file to the mounted device
def Transfer_File():
    # i am too lazy to write a proper check if this works or not so we just wrap it in a try except block
    try:
        # check the operating system and create the destination file path accordingly
        if os.name == "nt":  # Windows
            # get a list of all mounted volumes using the win32api module
            volumes = win32api.GetLogicalDriveStrings()
            volumes = volumes.split('\x00')[:-1]

            # loop over the mounted volumes and look for a volume with the correct label
            destination_found = False
            for volume in volumes:
                try:
                    label = win32api.GetVolumeInformation(volume)[0]
                except:
                    # skip this volume if there is an error accessing the label
                    continue

                if label == device_target:
                    # create the destination file path by joining the volume and the file name
                    destination_file_path = os.path.join(volume, file_name)
                    destination_found = True
                    shutil.copy2(file_path, destination_file_path)
                    output = f"The uf2 has been copied to '{destination_file_path}'"
                    print(output)

            if not destination_found:
                output = f"Could not find a volume with the label '{device_target}'"
                print(output)
                exit()

        else:  # Linux
            # create the destination file path by joining the mount point and the file name
            destination_file_path = os.path.join("/media/", os.getlogin(), device_target, file_name)
            shutil.copy2(file_path, destination_file_path)
            output = f"The uf2 has been copied to '{destination_file_path}'"
            print(output)
    except:
        print("Something went wrong, please try again")
        exit()


# Check if the uf2 file exists
if not os.path.exists(file_path):
    print(f"The uf2 file '{file_path}' does not exist, please build the project first")
    exit()

# Check if the mount point exists
if Scan_For_MassStorage(device_target):
    # Transfer the uf2 file to the mounted device
    Transfer_File()
else:
    # Wait for the device to be mounted
    subprocess.call(["picotool", "reboot", "-f", "-u"])
    Wait_For_MassStorage_Device()
    # Transfer the uf2 file to the mounted device
    Transfer_File()

"""

    # Write to programmer.py
    with open("scripts/programmer.py", "w") as f:
        f.write(programmer)


def CreateVSFiles():
    # Create the .vscode folder
    if not os.path.exists(".vscode"):
        os.makedirs(".vscode")
        print("Created folder: .vscode")

    # Create the c_cpp_properties.json file
    c_cpp_properties = """
{
  "configurations": [
    {
      "name": "Pico",
      "includePath": [
        "${workspaceFolder}/**",
        "${env:PICO_SDK_PATH}/**"
      ],
      "defines": [],
      "compilerPath": "${env:PICO_INSTALL_PATH}/gcc-arm-none-eabi/bin/arm-none-eabi-gcc.exe",
      "cStandard": "c11",
      "cppStandard": "c++11",
      "intelliSenseMode": "linux-gcc-arm",
      "configurationProvider": "ms-vscode.cmake-tools"
    }
  ],
  "version": 4
}
"""

    cmake_kits = """
[
  {
    "name": "Pico ARM GCC",
    "description": "Pico SDK Toolchain with GCC arm-none-eabi",
    "toolchainFile": "${env:PICO_SDK_PATH}/cmake/preload/toolchains/pico_arm_gcc.cmake"
  }
]
"""

    extensions = """
{
  "recommendations": [
    "marus25.cortex-debug",
    "ms-vscode.cmake-tools",
    "ms-vscode.cpptools",
    "ms-vscode.cpptools-extension-pack",
    "ms-vscode.vscode-serial-monitor"
  ]
}
"""

    launch = """
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Pico Debug (Cortex-Debug)",
      "cwd": "${workspaceFolder}",
      "executable": "${command:cmake.launchTargetPath}",
      "request": "launch",
      "type": "cortex-debug",
      "servertype": "openocd",
      "gdbPath": "arm-none-eabi-gdb",
      "device": "RP2040",
      "configFiles": [
        "interface/cmsis-dap.cfg",
        "target/rp2040.cfg"
      ],
      "svdFile": "${env:PICO_SDK_PATH}/src/rp2040/hardware_regs/rp2040.svd",
      "runToEntryPoint": "main",
      "openOCDLaunchCommands": [
        "adapter speed 1000"
      ]
    },
    {
      "name": "Pico Debug (Cortex-Debug with external OpenOCD)",
      "cwd": "${workspaceFolder}",
      "executable": "${command:cmake.launchTargetPath}",
      "request": "launch",
      "type": "cortex-debug",
      "servertype": "external",
      "gdbTarget": "localhost:3333",
      "gdbPath": "arm-none-eabi-gdb",
      "device": "RP2040",
      "svdFile": "${env:PICO_SDK_PATH}/src/rp2040/hardware_regs/rp2040.svd",
      "runToEntryPoint": "main"
    },
    {
      "name": "Pico Debug (C++ Debugger)",
      "type": "cppdbg",
      "request": "launch",
      "cwd": "${workspaceFolder}",
      "program": "${command:cmake.launchTargetPath}",
      "MIMode": "gdb",
      "miDebuggerPath": "arm-none-eabi-gdb",
      "miDebuggerServerAddress": "localhost:3333",
      "debugServerPath": "openocd",
      "debugServerArgs": "-f interface/cmsis-dap.cfg -f target/rp2040.cfg -c \"adapter speed 1000\"",
      "serverStarted": "Listening on port .* for gdb connections",
      "filterStderr": true,
      "stopAtEntry": true,
      "hardwareBreakpoints": {
        "require": true,
        "limit": 4
      },
      "preLaunchTask": "Flash",
      "svdPath": "${env:PICO_SDK_PATH}/src/rp2040/hardware_regs/rp2040.svd"
    }
  ]
}
"""

    settings = """
{
    // These settings tweaks to the cmake plugin will ensure
    // that you debug using cortex-debug instead of trying to launch
    // a Pico binary on the host
    "cmake.statusbar.advanced": {
        "debug": {
            "visibility": "hidden"
        },
        "launch": {
            "visibility": "hidden"
        },
        "build": {
            "visibility": "hidden"
        },
        "buildTarget": {
            "visibility": "hidden"
        }
    },
    "cmake.buildBeforeRun": true,
    "cmake.configureOnOpen": true,
    "cmake.configureSettings": {
      "CMAKE_MODULE_PATH": "${env:PICO_INSTALL_PATH}/pico-sdk-tools"
    },
    "cmake.generator": "Ninja",
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools"
}
"""

    tasks = """
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Flash",
      "type": "shell",
      "command": "openocd",
      "args": [
        "-f",
        "interface/cmsis-dap.cfg",
        "-f",
        "target/rp2040.cfg",
        "-c",
        "adapter speed 1000; program {${command:cmake.launchTargetPath}} verify reset exit"
      ],
      "problemMatcher": []
    },
    {
      "label": "Build",
      "type": "cmake",
      "command": "build",
      "problemMatcher": "$gcc",
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
"""

    # Write to c_cpp_properties.json
    with open(".vscode/c_cpp_properties.json", "w") as f:
        f.write(c_cpp_properties)

    # Write to cmake-kits.json
    with open(".vscode/cmake-kits.json", "w") as f:
        f.write(cmake_kits)

    # Write to extensions.json
    with open(".vscode/extensions.json", "w") as f:
        f.write(extensions)

    # Write to launch.json
    with open(".vscode/launch.json", "w") as f:
        f.write(launch)

    # Write to settings.json
    with open(".vscode/settings.json", "w") as f:
        f.write(settings)

    # Write to tasks.json
    with open(".vscode/tasks.json", "w") as f:
        f.write(tasks)


def CreateWorkspaceFile(projectname):
    workspace = """
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"files.associations": {
			"type_traits": "cpp",
			"cmath": "cpp",
		}
	}
}
"""

    # Get the name of the workspace
    workspace_file = projectname + ".code-workspace"

    # Write to .vscode/tasks.json
    with open(workspace_file, "w") as f:
        f.write(workspace)


# Get the name of the project
projectname = os.getcwd().split("\\")[-1].replace(" ", "_")

CreateFolders()
CreateMain()
CreateCMakeLists(projectname)
CreateReadme(projectname)
CreateGitignore()
CreateProgrammer(projectname)
CreateVSFiles()
CreateWorkspaceFile(projectname)

# Self destruct
os.remove("setup.py")