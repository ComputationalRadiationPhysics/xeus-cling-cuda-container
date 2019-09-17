echo -n "project path (default: ./builds): "
read XCC_PROJECT_PATH 
if [ "$XCC_PROJECT_PATH" == "" ];
then
	XCC_PROJECT_PATH=$PWD/builds
fi

while true;
do
	echo -n "build type [Debug, Release, RelWithDebInfo, MinSizeRel]: "
	read XCC_BUILD_TYPE
	case $XCC_BUILD_TYPE in
		[Debug]* ) break;;
		[Release]* ) break;;
		[RelWithDebInfo]* ) break;;
		[MinSizeRel]* ) break;;
	esac
done

while true ;
do
	echo -n "enter number of threads for build or leave it free to use all threads: "
	read XCC_NUM_THREADS
	if [[ $XCC_NUM_THREADS =~ ^[0-9]+$ ]]  || [ -z "$XCC_NUM_THREADS" ];
	then
		break
	fi
done


echo "{" > config.json
echo -e "\t\"XCC_PROJECT_PATH\" : \"$XCC_PROJECT_PATH\"," >> config.json
echo -e "\t\"XCC_BUILD_TYPE\" : \"$XCC_BUILD_TYPE\"," >> config.json
echo -e "\t\"XCC_NUM_THREADS\" : \"$XCC_NUM_THREADS\"" >> config.json
echo "}" >> config.json
