# Get arguments for CAN bus channel and log file size in Mb
while getopts c: flag
do
    case "${flag}" in
        c) channel=${OPTARG};;
    esac
done

datetime=$(date +"%Y-%m-%d_%H%M%S")

if [ -z "$channel" ]
then
    echo "Please supply the a channel i.e. /dev/ttyUSBO or /COM.."
else
    echo "Generating filter selection file";
    python3 source_tree.py; # regenerate filter_select.txt
    python3 -m can.logger -i seeedstudio -b 500000 -s 52428800 -c $channel -f logs/$datetime.log --filter $(cat filter_select.txt);
fi