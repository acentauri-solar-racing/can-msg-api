# Get arguments for CAN bus channel and log file size in Mb
while getopts c: flag
do
    case "${flag}" in
        c) channel=${OPTARG};;
        # b) baudrate=${OPTARG};;
    esac
done

datetime=$(date +"%Y-%m-%d_%H%M%S")

if [ -z "$channel" ]
then
    echo "Please supply the a channel i.e. /dev/ttyUSBO or /COM.."
else
    python -m can.logger -i seeedstudio -b 250000 -s 52428800 -c $channel -f logs/$datetime.log
fi