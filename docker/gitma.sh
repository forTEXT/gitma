#!/bin/bash
source /opt/conda/bin/activate  
conda activate gitma 

red='\033[31m'
green='\033[32m'
yellow='\033[33m'
blue='\033[34m'
purple='\033[35m'

bold='\033[1m'
italic='\033[3m'
ul='\033[4m'
clear='\033[0m'

color_red(){
  echo -ne $red$1$clear
}
color_green(){
	echo -ne $green$1$clear
}
color_yellow(){
  echo -ne $yellow$1$clear
}
color_blue(){
	echo -ne $blue$1$clear
}

run_jupyter() {
 echo ""
 echo "$(color_blue 'Starting jupyter')"
 echo ""
 jupyter lab \
   --notebook-dir=./src/demo/notebooks/ \
   --ip='*' \
   --port=8888 \
   --no-browser \
   --allow-root 
}

update_gitma() {
   echo ""
   echo "$(color_blue 'Updating conda')"
   echo ""
   conda update -y -n gitma --all
   echo ""
   echo "$(color_blue 'Updating GitMA')"
   echo ""
   python -m pip install --upgrade git+https://github.com/forTEXT/gitma 
   python -m pip install --upgrade "pygamma-agreement[CBC]" 
}

reinstall_demo(){
   echo ""
   echo "$(color_red 'Removing old GitMA demo files')"
   echo ""
   rm -rf ./src
   echo "Cloning GitMA demo files"
   git clone https://github.com/forTEXT/gitma.git ./src 
}

press_enter() {
  echo ""
  echo -e "$bold$(color_blue 'Press Enter to continue ')"
  read
  clear
}

incorrect_selection() {
  echo ""
  echo -e "$(color_red 'Incorrect selection!') Try again."
}

print_logo(){
  echo -ne " 
  $bold
  $blue        ___                              $purple     ___           ___      
  $blue       /  /\        ___           ___    $purple    /__/\         /  /\     
  $blue      /  /:/_      /  /\         /  /\   $purple   |  |::\       /  /::\    
  $blue     /  /:/ /\    /  /:/        /  /:/   $purple   |  |:|:\     /  /:/\:\   
  $blue    /  /:/_/::\  /__/::\       /  /:/    $purple __|__|:|\:\   /  /:/~/::\  
  $blue   /__/:/__\/\:\ \__\/\:\__   /  /::\    $purple/__/::::| \:\ /__/:/ /:/\:\ 
  $blue   \  \:\ /~~/:/    \  \:\/\ /__/:/\:\   $purple\  \:\~~\__\/ \  \:\/:/__\/ 
  $blue    \  \:\  /:/      \__\::/ \__\/  \:\  $purple \  \:\        \  \::/      
  $blue     \  \:\/:/       /__/:/       \  \:\ $purple  \  \:\        \  \:\      
  $blue      \  \::/        \__\/         \__\/ $purple   \  \:\        \  \:\     
  $blue       \__\/                             $purple    \__\/         \__\/            
       
  $clear$italic$blue                                   https://github.com/forTEXT/gitma
  $clear$italic$blue                                   v0.0.5 2023-02-17
  $clear"
}

until [ "$selection" = "0" ]; do
  clear
  print_logo
  echo -ne "
    
    $(color_blue 1):  Run jupyter
    $(color_blue 2):  Update GitMA
    $(color_blue 3):  Reinstall demo files $(color_red '(all changes will be lost!)')
 
    $(color_red q):  Exit

    $bold$(color_blue 'Enter selection'): "
  read selection

  case $selection in
    1 )                     clear ; run_jupyter ; press_enter ;;
    2 )                     clear ; update_gitma ; press_enter ;;
    3 )                     clear ; reinstall_demo ; press_enter ;;
    0 | x | X | q | ":q" )  clear ; exit ;;
    * )                     clear ; incorrect_selection ; press_enter ;;
  esac
done
